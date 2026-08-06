#!/usr/bin/env python3
"""
Audit archives and folders for sensitive wallet material without exposing full secrets.

This is the Python companion to Invoke-ArchiveAudit.ps1. It scans ZIP/IPA archives,
folders, JSON, plist, text, and SQLite files, then writes a redacted Markdown report
and optional CSV.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import plistlib
import re
import sqlite3
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SENSITIVE_NAME_RE = re.compile(
    r"(private|priv|secret|seed|mnemonic|wif|wallet|key|xprv|password|passphrase|"
    r"recovery|entropy|phrase)",
    re.IGNORECASE,
)

PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "bitcoin_wif_private_key",
        re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])[5KL][1-9A-HJ-NP-Za-km-z]{50,51}(?![1-9A-HJ-NP-Za-km-z])"),
        "Looks like a Bitcoin WIF private key.",
    ),
    (
        "extended_private_key",
        re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])(xprv|tprv|yprv|zprv|uprv|vprv)[1-9A-HJ-NP-Za-km-z]{80,120}(?![1-9A-HJ-NP-Za-km-z])"),
        "Looks like an extended private key.",
    ),
    (
        "possible_64_hex_secret",
        re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])"),
        "64 hex characters; could be a private key, hash, or other binary value.",
    ),
    (
        "bitcoin_legacy_address",
        re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])[13][1-9A-HJ-NP-Za-km-z]{25,34}(?![1-9A-HJ-NP-Za-km-z])"),
        "Looks like a Bitcoin legacy address.",
    ),
    (
        "bitcoin_bech32_address",
        re.compile(r"(?<![a-zA-Z0-9])bc1[ac-hj-np-z02-9]{11,90}(?![a-zA-Z0-9])", re.IGNORECASE),
        "Looks like a Bitcoin bech32 address.",
    ),
]

TEXT_EXTENSIONS = {
    ".txt",
    ".json",
    ".plist",
    ".xml",
    ".csv",
    ".log",
    ".md",
    ".strings",
    ".conf",
    ".ini",
    ".ps1",
    ".py",
}


@dataclass
class Finding:
    path: str
    kind: str
    location: str
    redacted: str
    fingerprint: str
    reason: str


@dataclass
class FileRecord:
    path: str
    kind: str
    size: int
    sha256: str
    notes: list[str] = field(default_factory=list)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact(value: str, reveal: int = 6) -> str:
    compact = value.replace("\r", "\\r").replace("\n", "\\n")
    if len(compact) <= reveal * 2 + 3:
        return "<redacted>"
    return f"{compact[:reveal]}...{compact[-reveal:]}"


def fingerprint(value: str) -> str:
    return sha256_bytes(value.encode("utf-8", errors="replace"))[:16]


def printable_text(data: bytes) -> str:
    return "".join(chr(byte) if byte in (9, 10, 13) or 32 <= byte <= 126 else " " for byte in data)


def utf8_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def classify_path(path: str, data: bytes) -> str:
    lower = path.lower()
    if data.startswith(b"SQLite format 3\x00") or lower.endswith((".sqlite", ".sqlite3", ".db")):
        return "sqlite"
    if data.startswith(b"bplist00"):
        return "binary-plist"
    if lower.endswith(".plist"):
        return "plist"
    if lower.endswith(".json"):
        return "json"
    if Path(lower).suffix in TEXT_EXTENSIONS:
        return "text"
    return "binary"


def walk_values(value: Any, prefix: str = "$") -> Iterable[tuple[str, Any]]:
    yield prefix, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_values(child, f"{prefix}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from walk_values(child, f"{prefix}[{index}]")


def make_finding(path: str, kind: str, reason: str, location: str, value: str) -> Finding:
    if value == "<values not printed>":
        redacted = value
        fp = fingerprint(f"{path}|{location}|{kind}")
    else:
        redacted = redact(value)
        fp = fingerprint(value)
    return Finding(path=path, kind=kind, location=location, redacted=redacted, fingerprint=fp, reason=reason)


def scan_text(path: str, text: str, location: str = "content") -> list[Finding]:
    findings: list[Finding] = []
    for kind, pattern, reason in PATTERNS:
        for match in pattern.finditer(text):
            findings.append(make_finding(path, kind, reason, location, match.group(0)))
    return findings


def scan_structured(path: str, obj: Any) -> list[Finding]:
    findings: list[Finding] = []
    for loc, value in walk_values(obj):
        if SENSITIVE_NAME_RE.search(loc):
            findings.append(
                make_finding(
                    path,
                    "sensitive_field_name",
                    "Field name suggests sensitive wallet or credential data.",
                    loc,
                    str(value),
                )
            )
        if isinstance(value, (str, int, float)):
            findings.extend(scan_text(path, str(value), loc))
    return findings


def try_parse_plist(data: bytes) -> Any | None:
    try:
        return plistlib.loads(data)
    except Exception:
        return None


def try_parse_json(data: bytes) -> Any | None:
    try:
        return json.loads(utf8_text(data))
    except Exception:
        return None


def sqlite_audit(path: str, data: bytes, max_rows: int) -> tuple[list[str], list[Finding]]:
    notes: list[str] = []
    findings: list[Finding] = []

    raw = printable_text(data)
    schema_re = re.compile(r"CREATE\s+(?:UNIQUE\s+)?(?:TABLE|INDEX)\s+[^;]{1,1000}", re.IGNORECASE)
    for match in schema_re.finditer(raw):
        schema = re.sub(r"\s+", " ", match.group(0)).strip()
        notes.append(schema)
        if SENSITIVE_NAME_RE.search(schema):
            findings.append(
                make_finding(
                    path,
                    "sensitive_sqlite_schema",
                    "SQLite schema contains sensitive-looking names.",
                    "schema",
                    schema,
                )
            )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            tables = [
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            notes.append("tables=" + ", ".join(tables) if tables else "tables=<none>")
            for table in tables:
                safe_table = '"' + table.replace('"', '""') + '"'
                columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({safe_table})")]
                count = conn.execute(f"SELECT COUNT(*) AS c FROM {safe_table}").fetchone()["c"]
                notes.append(f"{table}: rows={count}, columns={', '.join(columns)}")
                for column in columns:
                    if SENSITIVE_NAME_RE.search(column):
                        findings.append(
                            make_finding(
                                path,
                                "sensitive_sqlite_column",
                                "SQLite column name suggests sensitive wallet or credential data.",
                                f"{table}.{column}",
                                "<values not printed>",
                            )
                        )

                if max_rows <= 0:
                    continue

                rows = conn.execute(f"SELECT * FROM {safe_table} LIMIT ?", (max_rows,)).fetchall()
                for row_index, row in enumerate(rows):
                    for column in columns:
                        value = row[column]
                        if value is None:
                            continue
                        value_text = printable_text(value) if isinstance(value, bytes) else str(value)
                        loc = f"{table}[{row_index}].{column}"
                        if SENSITIVE_NAME_RE.search(column):
                            findings.append(
                                make_finding(
                                    path,
                                    "sensitive_sqlite_value",
                                    "Value is in a sensitive-looking SQLite column.",
                                    loc,
                                    value_text,
                                )
                            )
                        findings.extend(scan_text(path, value_text, loc))
        finally:
            conn.close()
    except Exception as exc:
        notes.append(f"sqlite_parse_error={exc}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    findings.extend(scan_text(path, raw, "sqlite.raw"))
    return notes, findings


def read_inputs(target: Path) -> Iterable[tuple[str, bytes]]:
    if target.is_dir():
        for root, _, files in os.walk(target):
            for name in files:
                file_path = Path(root) / name
                rel = file_path.relative_to(target).as_posix()
                try:
                    yield rel, file_path.read_bytes()
                except OSError:
                    continue
        return

    data = target.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                yield info.filename, archive.read(info)
    else:
        yield target.name, data


def audit(target: Path, max_rows: int) -> tuple[list[FileRecord], list[Finding]]:
    records: list[FileRecord] = []
    findings: list[Finding] = []

    for path, data in read_inputs(target):
        kind = classify_path(path, data)
        record = FileRecord(path=path, kind=kind, size=len(data), sha256=sha256_bytes(data))

        if SENSITIVE_NAME_RE.search(path):
            findings.append(
                make_finding(
                    path,
                    "sensitive_path_name",
                    "File path suggests sensitive wallet or credential data.",
                    "path",
                    path,
                )
            )

        if kind == "sqlite":
            notes, sqlite_findings = sqlite_audit(path, data, max_rows)
            record.notes.extend(notes)
            findings.extend(sqlite_findings)
        elif kind in {"plist", "binary-plist"}:
            obj = try_parse_plist(data)
            if obj is None:
                record.notes.append("plist_text_scan")
                text = printable_text(data)
                if SENSITIVE_NAME_RE.search(text):
                    findings.append(
                        make_finding(
                            path,
                            "sensitive_plist_text",
                            "Plist contains sensitive-looking readable strings.",
                            "plist.raw",
                            text,
                        )
                    )
                findings.extend(scan_text(path, text, "plist.raw"))
            else:
                record.notes.append("plist_parsed")
                findings.extend(scan_structured(path, obj))
        elif kind == "json":
            obj = try_parse_json(data)
            if obj is None:
                record.notes.append("json_parse_error")
                findings.extend(scan_text(path, utf8_text(data)))
            else:
                record.notes.append("json_parsed")
                findings.extend(scan_structured(path, obj))
        elif kind == "text" or len(data) <= 5_000_000:
            findings.extend(scan_text(path, printable_text(data)))

        records.append(record)

    return records, findings


def escape_md(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown_report(output: Path, target: Path, records: list[FileRecord], findings: list[Finding]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Archive Audit Report\n\n")
        handle.write(f"Target: `{target}`\n\n")
        handle.write(f"Files scanned: {len(records)}\n\n")
        handle.write(f"Findings: {len(findings)}\n\n")
        handle.write("## Findings\n\n")
        if not findings:
            handle.write("No sensitive-looking values were detected.\n\n")
        else:
            handle.write("| Path | Kind | Location | Redacted | Fingerprint | Reason |\n")
            handle.write("| --- | --- | --- | --- | --- | --- |\n")
            for item in findings:
                cells = [item.path, item.kind, item.location, item.redacted, item.fingerprint, item.reason]
                handle.write("| " + " | ".join(escape_md(cell) for cell in cells) + " |\n")
            handle.write("\n")

        handle.write("## Inventory\n\n")
        handle.write("| Path | Type | Size | SHA-256 | Notes |\n")
        handle.write("| --- | --- | ---: | --- | --- |\n")
        for record in records:
            cells = [record.path, record.kind, str(record.size), record.sha256, "; ".join(record.notes)]
            handle.write("| " + " | ".join(escape_md(cell) for cell in cells) + " |\n")


def write_csv_report(output: Path, findings: list[Finding]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "kind", "location", "redacted", "fingerprint", "reason"],
        )
        writer.writeheader()
        for item in findings:
            writer.writerow(item.__dict__)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit an archive/folder for sensitive wallet material.")
    parser.add_argument("target", help="Path to a ZIP/IPA archive, SQLite DB, plist, JSON file, or extracted folder.")
    parser.add_argument("--out", default="audit-report.md", help="Markdown report path. Default: audit-report.md")
    parser.add_argument("--csv", default="", help="Optional CSV findings path.")
    parser.add_argument("--max-sqlite-rows", type=int, default=20, help="Rows sampled per SQLite table. Default: 20")
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"Target not found: {target}", file=sys.stderr)
        return 2

    records, findings = audit(target, max(0, args.max_sqlite_rows))
    out_path = Path(args.out).expanduser().resolve()
    write_markdown_report(out_path, target, records, findings)
    if args.csv:
        write_csv_report(Path(args.csv).expanduser().resolve(), findings)

    print(f"Scanned {len(records)} files.")
    print(f"Findings: {len(findings)}")
    print(f"Report: {out_path}")
    if args.csv:
        print(f"CSV: {Path(args.csv).expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
