#!/usr/bin/env python3
"""
Build ORGANIZED_MATH_RESEARCH folder tree with symlink stubs + MASTER_MANIFEST.md.
Does NOT delete or move originals. Large files (>100MB) are manifest-only references.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT_OUT = Path(r"C:\Users\mitch\Desktop\ORGANIZED_MATH_RESEARCH")

# Scan only math/puzzle research paths. F: is allowlisted — never scan all of F: (business files).
SCAN_ROOTS = [
    Path(r"C:\Users\mitch\Desktop\secp256k1"),
    Path(r"F:\New folder\secp256k1"),  # D/A notes + math copies only
]

# Desktop root is NOT scanned (avoids mixing unrelated Desktop files).
# F: is NEVER scanned at drive root — only explicit math paths in SCAN_ROOTS.

# User-specified F: top-level folders that are NOT math (never traverse if F: widened).
F_TOPLEVEL_NON_MATH = {
    "att",
    "bobby",
    "book",
    "business",
    "eptstein",
    "epstein",
    "iphonetools",
    "jda",
    "kent",
    "mitchell ray vs. town of rosepine",
    "mitchell ray vs town of rosepine",
    "music",
    "school",
    "system volume information",
    "tax seasons 2022",
    "taxes 2025",
    "youtube",
}

F_BUSINESS_BLOCKLIST = F_TOPLEVEL_NON_MATH | {
    "accounting", "invoices", "payroll", "hr", "contracts",
    "marketing", "sales", "quickbooks", "xero", "llc", "corp",
}

SKIP_DIR_PARTS = {
    "node_modules",
    ".git",
    "__pycache__",
    "graphify-out",
    "Vulcan",
    ".cursor",
    "MinGW",
    "terminals",
    "h160_lane_exports",  # 257 generated KeyHunt bats — manifest via make_h160_lane_exports.py
    "p160_billion_even_checkpoints",  # multi-GB spawn logs — manifest-only by size anyway
}
SKIP_EXT = {".bin", ".exe", ".dll", ".pdb", ".obj", ".o", ".lib", ".sqlite", ".db"}
MANIFEST_ONLY_BYTES = 100 * 1024 * 1024  # 100 MB

PROBLEMS = [
    {
        "id": "01",
        "folder": "01_Does_p_minus_N_create_a_scalar_coordinate_bridge",
        "question": "Does p-N create a scalar-coordinate bridge?",
        "status": "PROMISING",
        "reason": "p-N defect is a real constant; bridge scripts exist but no P135 key recovered.",
        "next_test": "Run bridge/normalization scripts on solved puzzles 65-130; verify d*G==P.",
        "confirm_criteria": "Candidate d in band with d*G==P135 from p-N bridge alone.",
        "patterns": [
            r"p_minus", r"p-minus", r"p_n", r"defect", r"bridge", r"n_side", r"normalization",
            r"intquotient", r"concat", r"transport_tower", r"gap_new", r"nbroke", r"p_and_n",
            r"complexity_simplified", r"generate_bridge",
        ],
    },
    {
        "id": "02",
        "folder": "02_Do_D8_lanes_predict_key_location",
        "question": "Do D/8 lanes predict key location?",
        "status": "FAILED",
        "reason": "Epsilon/lane sweeps on P160 produced 0 hits at tested scales.",
        "next_test": "Narrow lane to h160 shelf only with EC gate, not brute billion scroll.",
        "confirm_criteria": "Lane predicts d for 3+ held-out solved puzzles before P160.",
        "patterns": [
            r"d8", r"d/8", r"epsilon", r"lane", r"ladder", r"shoot", r"two32", r"billion_even",
            r"keyhunt", r"h160_lane", r"leader_harvest", r"gpu_d_harvest", r"tdad",
        ],
    },
    {
        "id": "03",
        "folder": "03_Does_double_and_add_reconstruct_solved_puzzles",
        "question": "Does double-and-add reconstruct solved puzzles?",
        "status": "PROMISING",
        "reason": "D/A chains match P1-P70; P71+ combinatorics explode.",
        "next_test": "Regenerate P71-P74 with strict alternation; verify rem=0 on all solved.",
        "confirm_criteria": "Unique D/A chain for P135 matching known key without search.",
        "patterns": [
            r"double_and_add", r"double.and.add", r"puzzleda", r"puzzle_da", r"\bda\.py",
            r"script_load_da", r"d\(k\)", r"a\(k\)", r"user_da",
        ],
    },
    {
        "id": "04",
        "folder": "04_Do_RMD160_barcodes_match_prior_solution_offsets",
        "question": "Do RMD160 barcodes match prior solution offsets?",
        "status": "PROMISING",
        "reason": "Barcode/h160 structure correlates with bands; no P135 solve.",
        "next_test": "Blind test: predict band_frac from barcode on puzzles 100-130 only.",
        "confirm_criteria": "Barcode predicts d band for held-out puzzles better than random.",
        "patterns": [
            r"barcode", r"hash160", r"ripemd", r"checksum", r"bucket", r"address_checksum",
            r"puzzle71barcode", r"h160_", r"hash_pipeline", r"log2_d_hash160",
        ],
    },
    {
        "id": "05",
        "folder": "05_Can_fractional_exponents_project_into_the_key_range",
        "question": "Can fractional exponents project into the key range?",
        "status": "PROMISING",
        "reason": "Hinge/sqrt/band_frac folds land near band on some puzzles; off-curve towers.",
        "next_test": "Gate all fold anchors with d*G==P on solved set; measure band hit rate.",
        "confirm_criteria": "Fold produces d with d*G==P135 without post-hoc search.",
        "patterns": [
            r"hinge", r"fold", r"sqrt", r"band_frac", r"fraction", r"arrest", r"log2",
            r"tower", r"scroll", r"resonance", r"decimal_resonance", r"flip_surround",
            r"transport", r"cube", r"py\^2",
        ],
    },
    {
        "id": "06",
        "folder": "06_Does_ECDSA_r_s_z_constrain_k_and_d",
        "question": "Does ECDSA r/s/z constrain k and d?",
        "status": "CONFIRMED",
        "reason": "s*k = z + r*d mod N verified on puzzle table; algebra is standard.",
        "next_test": "Use RSZ line to shrink d search with EC verify only on candidates.",
        "confirm_criteria": "Already confirmed for ECDSA identity; extend to predictive d, not just identity.",
        "patterns": [
            r"rsz", r"r_s_z", r"hashkeys_rsz", r"ecdlp", r"mod_n_minus", r"mod7_log7",
            r"inverted_ksz", r"dual_gate.*rsz", r"k_bridge", r"band_fraction_probe",
        ],
    },
    {
        "id": "07",
        "folder": "07_Do_N_minus_8_reflections_create_a_checksum",
        "question": "Do N-8 reflections create a checksum?",
        "status": "FAILED",
        "reason": "Complement/mirror/N-8 scans tested; no P160 hit above random.",
        "next_test": "Test N-8 reflection only on solved puzzles' d offsets, blind.",
        "confirm_criteria": "Reflection predicts d for 3+ solved puzzles; recovers P160.",
        "patterns": [
            r"complement", r"mirror", r"reflection", r"n_minus_8", r"n-8", r"inverted",
            r"flip", r"backward_shell", r"rx.?px", r"neg_",
        ],
    },
    {
        "id": "08",
        "folder": "08_Do_factorial_expansions_encode_puzzle_keys",
        "question": "Do factorial expansions encode puzzle keys?",
        "status": "GUESS",
        "reason": "Sparse factorial-themed notes; no reproducible key recovery.",
        "next_test": "Formalize factorial map; test on P65-P80 solved keys only.",
        "confirm_criteria": "Factorial formula reproduces d for 5+ solved puzzles.",
        "patterns": [r"factorial", r"perm", r"combin", r"!\b", r"omega2"],
    },
    {
        "id": "09",
        "folder": "09_Do_midpoint_drifts_follow_a_high_low_pattern",
        "question": "Do midpoint drifts follow a high/low pattern?",
        "status": "PROMISING",
        "reason": "Mid/h160/prior anchors and band drift patterns seen; not predictive yet.",
        "next_test": "Track band_frac drift P115-P135-P160 on solved chain only.",
        "confirm_criteria": "Monotonic drift rule predicts P135 band_frac within 1%.",
        "patterns": [
            r"midpoint", r"drift", r"high_low", r"prior_1p5", r"shelf", r"schedule_pipeline",
            r"prefix_direction", r"ground_zero", r"p115", r"p130",
        ],
    },
    {
        "id": "10",
        "folder": "10_Do_genesis_strings_or_rE_mark_structural_offsets",
        "question": "Do genesis strings or rE mark structural offsets?",
        "status": "GUESS",
        "reason": "Genesis/rE notes exist; no verified offset map to keys.",
        "next_test": "Map genesis block strings to d offsets on P1-P20 solved only.",
        "confirm_criteria": "Genesis-derived offset hits d for multiple solved puzzles.",
        "patterns": [
            r"genesis", r"\bre\b", r"almost", r"kangaroo", r"start_kangaroo", r"135kanga",
            r"135log", r"equating", r"figured_it_out", r"tax_", r"gem1",
        ],
    },
]

STATUS_DIRS = ["FACT", "TEST", "GUESS", "FAILED", "PROMISING", "CONFIRMED", "NEEDS_REVIEW"]

FACT_PATTERNS = [
    r"puzzle_keys", r"hashkeys_rsz", r"p135_common", r"puzzleconfig",
    r"\.pub$", r"53125", r"secp256k1.*param",
]
CONFIRMED_PATTERNS = [
    r"proof_check", r"formula_verify", r"arrest_formula_verify", r"k_bridge_proof",
    r"hashkeys_rsz", r"ecdlp_full_pipeline",
]
FAILED_PATTERNS = [
    r"falsify", r"no hit", r"no_hit", r"0 hit", r"0_hit", r"failed", r"rejected",
    r"dual_gate_complement", r"inverted_ksz",
]
PROMISING_PATTERNS = [
    r"promising", r"scorecard", r"bridge", r"gap_new", r"catalog", r"alignment",
]
GUESS_PATTERNS = [
    r"maybe", r"possibilities", r"figured", r"guess", r"song", r"tarot", r"masturbation",
    r"fucking_quantum", r"paperwork", r"trial\.txt",
]


@dataclass
class FileEntry:
    src: Path
    problem_id: str
    problem_folder: str
    status: str
    why_problem: str
    why_status: str
    linked: bool
    note: str = ""


def _f_toplevel_blocked(path: Path) -> bool:
    """If path is on F:, reject unless under an allowed math root; block known non-math top dirs."""
    parts = [p.lower() for p in path.parts]
    if not parts or parts[0] != "f:":
        return False
    if len(parts) >= 2:
        top = parts[1]
        if top in F_TOPLEVEL_NON_MATH:
            return True
        for biz in F_BUSINESS_BLOCKLIST:
            if biz in top or top in biz:
                return True
    return False


def should_skip(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if parts & SKIP_DIR_PARTS:
        return True
    if path.suffix.lower() in SKIP_EXT:
        return True
    if path.name.startswith("."):
        return True
    if _f_toplevel_blocked(path):
        return True
    low = str(path).lower().replace("\\", "/")
    # F: must stay inside allowlisted SCAN_ROOTS subtrees
    if low.startswith("f:/") and "new folder/secp256k1" not in low:
        return True
    for biz in F_BUSINESS_BLOCKLIST:
        if f"/{biz}/" in low or low.endswith(f"/{biz}"):
            return True
    return False


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in SKIP_DIR_PARTS and not d.startswith(".")
            ]
            for fn in filenames:
                p = Path(dirpath) / fn
                if should_skip(p):
                    continue
                if p.suffix.lower() in {".py", ".txt", ".md", ".json", ".csv", ".log", ".bat", ".ps1", ".pdf", ".pub", ".html"}:
                    out.append(p)
    except OSError:
        pass
    return out


def classify_problem(rel: str, name: str) -> tuple[str, str, str]:
    hay = (rel + "/" + name).lower().replace("\\", "/")
    for prob in PROBLEMS:
        for pat in prob["patterns"]:
            if re.search(pat, hay, re.I):
                return prob["id"], prob["folder"], f"matched pattern `{pat}` in `{hay}`"
    return "00", "NEEDS_REVIEW", f"no problem pattern matched for `{hay}`"


def read_snippet(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit].lower()
    except OSError:
        return ""


def classify_status(path: Path, problem_id: str) -> tuple[str, str]:
    name = path.name.lower()
    rel = str(path).lower()
    snippet = read_snippet(path) if path.suffix.lower() in {".txt", ".md", ".log"} else ""

    for pat in FACT_PATTERNS:
        if re.search(pat, name) or re.search(pat, rel):
            return "FACT", f"matched FACT pattern `{pat}`"

    if problem_id == "06" and "hashkeys_rsz" in name:
        return "FACT", "RSZ table / signature constants"

    for pat in CONFIRMED_PATTERNS:
        if re.search(pat, name):
            if "verify" in name or "proof" in name or "formula_verify" in name:
                return "CONFIRMED", f"verification script `{name}`"
            if name == "hashkeys_rsz.py":
                return "FACT", "canonical RSZ data module"

    for pat in FAILED_PATTERNS:
        if re.search(pat, name) or re.search(pat, snippet):
            return "FAILED", f"failed/falsify signal in name or output (`{pat}`)"

    if "no hit" in snippet or "result: no hit" in snippet or "0 hits" in snippet:
        return "FAILED", "output snippet reports no hit"

    for pat in GUESS_PATTERNS:
        if re.search(pat, name) or re.search(pat, rel):
            return "GUESS", f"speculative note pattern `{pat}`"

    for pat in PROMISING_PATTERNS:
        if re.search(pat, name):
            return "PROMISING", f"promising/bridge pattern `{pat}`"

    if path.suffix.lower() == ".py":
        if re.search(r"test_|_test|probe|scan|sweep|verify", name):
            return "TEST", "executable test/probe script"
        return "TEST", "Python script (default TEST bucket)"

    if path.suffix.lower() in {".bat", ".ps1"}:
        return "TEST", "runner script"

    if path.suffix.lower() in {".txt", ".log", ".md"}:
        if "hit=" in snippet and "hit=none" in snippet.replace(" ", ""):
            return "FAILED", "log shows hit=None"
        return "TEST", "text output / notes default to TEST"

    return "NEEDS_REVIEW", "extension/body not auto-classified"


def safe_link_name(src: Path) -> str:
    base = src.name
    if len(base) < 200:
        return base
    stem, suf = src.stem[:180], src.suffix
    return stem + "__trunc" + suf


def try_symlink(link_path: Path, target: Path) -> tuple[bool, str]:
    try:
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link_path.exists() or link_path.is_symlink():
            return True, "already exists"
        # Cross-drive (C: vs F:) cannot use relative symlinks on Windows
        if link_path.drive.upper() != target.drive.upper():
            os.symlink(str(target), link_path)
        else:
            rel = os.path.relpath(target, link_path.parent)
            os.symlink(rel, link_path)
        return True, "symlink created"
    except OSError as e:
        return False, f"symlink failed: {e}"


def main() -> int:
    ROOT_OUT.mkdir(parents=True, exist_ok=True)
    for prob in PROBLEMS:
        for st in STATUS_DIRS:
            (ROOT_OUT / prob["folder"] / st).mkdir(parents=True, exist_ok=True)
    (ROOT_OUT / "NEEDS_REVIEW").mkdir(parents=True, exist_ok=True)
    for st in STATUS_DIRS:
        (ROOT_OUT / "NEEDS_REVIEW" / st).mkdir(parents=True, exist_ok=True)

    seen: dict[str, Path] = {}
    entries: list[FileEntry] = []

    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for src in iter_files(scan_root):
            key = str(src.resolve()).lower()
            if key in seen:
                continue
            seen[key] = src
            try:
                size = src.stat().st_size
            except OSError:
                continue
            rel = str(src.relative_to(scan_root)) if src.is_relative_to(scan_root) else str(src)
            pid, pfolder, why_p = classify_problem(rel, src.name)
            status, why_s = classify_status(src, pid)

            if pid == "00":
                dest_base = ROOT_OUT / "NEEDS_REVIEW" / status
            else:
                dest_base = ROOT_OUT / pfolder / status

            link_name = safe_link_name(src)
            # disambiguate duplicate basenames
            dest = dest_base / link_name
            if dest.exists():
                dest = dest_base / f"{src.parent.name}__{link_name}"

            linked = False
            note = ""
            if size > MANIFEST_ONLY_BYTES:
                note = f"LARGE_FILE_REFERENCE only ({size:,} bytes); no symlink"
            else:
                ok, msg = try_symlink(dest, src.resolve())
                linked = ok
                note = msg

            entries.append(
                FileEntry(
                    src=src.resolve(),
                    problem_id=pid,
                    problem_folder=pfolder if pid != "00" else "NEEDS_REVIEW",
                    status=status,
                    why_problem=why_p,
                    why_status=why_s,
                    linked=linked,
                    note=note,
                )
            )

    # CSV export
    csv_path = ROOT_OUT / "organized_math_manifest.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "source_path", "problem_folder", "status", "linked",
            "why_problem", "why_status", "note", "size_bytes", "mtime",
        ])
        for e in entries:
            try:
                st = e.src.stat()
                w.writerow([
                    str(e.src), e.problem_folder, e.status, e.linked,
                    e.why_problem, e.why_status, e.note, st.st_size,
                    datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                ])
            except OSError:
                w.writerow([str(e.src), e.problem_folder, e.status, e.linked, e.why_problem, e.why_status, e.note, "", ""])

    # Tree export
    tree_path = ROOT_OUT / "organized_tree.txt"
    lines_tree: list[str] = []

    def walk_tree(d: Path, prefix: str = "") -> None:
        try:
            kids = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        for i, kid in enumerate(kids):
            connector = "└── " if i == len(kids) - 1 else "├── "
            tag = ""
            if kid.is_symlink():
                try:
                    tag = f" -> {os.readlink(kid)}"
                except OSError:
                    tag = " -> [symlink]"
            lines_tree.append(f"{prefix}{connector}{kid.name}{tag}")
            if kid.is_dir() and not kid.is_symlink():
                extension = "    " if i == len(kids) - 1 else "│   "
                walk_tree(kid, prefix + extension)

    lines_tree.append(str(ROOT_OUT))
    walk_tree(ROOT_OUT)
    tree_path.write_text("\n".join(lines_tree) + "\n", encoding="utf-8")

    # MASTER_MANIFEST.md
    by_problem: dict[str, list[FileEntry]] = defaultdict(list)
    for e in entries:
        by_problem[e.problem_folder].append(e)

    manifest_lines = [
        "# MASTER_MANIFEST — Organized Math Research",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Root: `{ROOT_OUT}`",
        "",
        "## Rules applied",
        "",
        "- Originals **not deleted** or renamed.",
        "- Organized copies are **symlinks** where possible (< 100 MB).",
        "- Large files are **manifest-only** references.",
        "- Unmatched files → `NEEDS_REVIEW/`.",
        "- **F: drive:** only `F:\\New folder\\secp256k1` scanned.",
        "- **F: excluded (non-math):** ATT, Bobby, Book, Business, eptstein, iphonetools, jda, kent, Mitchell Ray vs. Town of Rosepine, music, school, System Volume Information, tax seasons 2022, taxes 2025, YouTube.",
        "- **Desktop root** not scanned — only `Desktop\\secp256k1`.",
        "",
        f"Total files indexed: **{len(entries)}**",
        f"Symlinks created: **{sum(1 for e in entries if e.linked)}**",
        f"Manifest-only (large/unlinked): **{sum(1 for e in entries if not e.linked)}**",
        "",
        "---",
        "",
    ]

    for prob in PROBLEMS:
        folder = prob["folder"]
        files = by_problem.get(folder, [])
        status_counts = defaultdict(int)
        for fe in files:
            status_counts[fe.status] += 1

        manifest_lines += [
            f"## {prob['id']} — {folder}",
            "",
            f"**Question:** {prob['question']}",
            "",
            f"**Current status (problem-level):** {prob['status']}",
            "",
            f"**Reason:** {prob['reason']}",
            "",
            f"**What would move to CONFIRMED:** {prob['confirm_criteria']}",
            "",
            f"**Next test:** {prob['next_test']}",
            "",
            f"**File counts by bucket:** {dict(status_counts)}",
            "",
            "### Files placed",
            "",
        ]
        # group by status
        for st in STATUS_DIRS:
            bucket = [fe for fe in files if fe.status == st]
            if not bucket:
                continue
            manifest_lines.append(f"#### {st} ({len(bucket)})")
            manifest_lines.append("")
            for fe in sorted(bucket, key=lambda x: str(x.src))[:80]:
                link_note = "symlink" if fe.linked else f"REF ONLY — {fe.note}"
                manifest_lines.append(f"- `{fe.src}`")
                manifest_lines.append(f"  - Why problem: {fe.why_problem}")
                manifest_lines.append(f"  - Why {st}: {fe.why_status}")
                manifest_lines.append(f"  - Link: {link_note}")
            if len(bucket) > 80:
                manifest_lines.append(f"- … and {len(bucket) - 80} more (see `organized_math_manifest.csv`)")
            manifest_lines.append("")

    # NEEDS_REVIEW section
    nr = by_problem.get("NEEDS_REVIEW", [])
    manifest_lines += [
        "## NEEDS_REVIEW",
        "",
        f"**Count:** {len(nr)}",
        "",
        "Files that did not match any problem keyword pattern.",
        "",
    ]
    for fe in sorted(nr, key=lambda x: str(x.src))[:100]:
        manifest_lines.append(f"- `{fe.src}` → **{fe.status}** — {fe.why_problem}")
    if len(nr) > 100:
        manifest_lines.append(f"- … and {len(nr) - 100} more in CSV")

    manifest_lines += [
        "",
        "---",
        "",
        "## Audit exports",
        "",
        f"- `{csv_path}`",
        f"- `{tree_path}`",
        f"- `{ROOT_OUT / 'classification_summary.json'}`",
        "",
    ]

    (ROOT_OUT / "MASTER_MANIFEST.md").write_text("\n".join(manifest_lines), encoding="utf-8")

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_files": len(entries),
        "by_problem": {k: len(v) for k, v in by_problem.items()},
        "by_status": dict(defaultdict(int, {e.status: 0 for e in entries})),
    }
    sc = defaultdict(int)
    for e in entries:
        sc[e.status] += 1
    summary["by_status"] = dict(sc)
    (ROOT_OUT / "classification_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"Wrote {ROOT_OUT / 'MASTER_MANIFEST.md'}")
    print(f"Files: {len(entries)}, linked: {sum(1 for e in entries if e.linked)}")
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
