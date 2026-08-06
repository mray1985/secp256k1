#!/usr/bin/env python3
"""
Per solved puzzle: how private key d flows to hash160 and Base58 address.

Pipeline (Bitcoin P2PKH):
  d  ->  P = d*G  ->  compressed pubkey (02|03 || x)
     ->  SHA256(pubkey)  ->  RIPEMD160  = hash160 (20 bytes)
     ->  0x00 || hash160 || checksum  ->  Base58Check address

Also builds vertical digit/nibble stacks for d, hash160, and address prefix.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import pubkey_from_scalar  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT_TXT = ARCHIVE / "d_hash160_address_breakdown.txt"
STACK_TSV = ARCHIVE / "d_hash160_address_breakdown.tsv"
REPORT_PDF = ARCHIVE / "d_hash160_address_breakdown.pdf"

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def hash160_compressed(x: int, y: int) -> tuple[bytes, bytes, bytes]:
    """Return (compressed_pubkey, sha256_digest, hash160)."""
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    comp = pref + x.to_bytes(32, "big")
    sha = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    return comp, sha, h160


def hash160_to_address(h160: bytes) -> str:
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    n = int.from_bytes(payload, "big")
    result = ""
    while n:
        n, r = divmod(n, 58)
        result = ALPHABET[r] + result
    for byte in payload:
        if byte == 0:
            result = "1" + result
        else:
            break
    return result


def head_hex(b: bytes, nibbles: int) -> str:
    h = b.hex()
    return h[:nibbles]


def tail_hex(b: bytes, nibbles: int) -> str:
    h = b.hex()
    return h[-nibbles:] if len(h) >= nibbles else h


def head_str(s: str, n: int) -> str:
    return s[:n] if len(s) >= n else s


def digit_columns(values: list[str], width: int, *, from_left: bool) -> list[str]:
    if from_left:
        clipped = [v[:width] if len(v) >= width else v.rjust(width) for v in values]
    else:
        clipped = [v.rjust(width) if len(v) <= width else v[-width:] for v in values]
    return ["".join(row[i] for row in clipped) for i in range(width)]


def chunk_lines(label: str, col: str, puzzles: list[int], chunk: int = 40) -> list[str]:
    out = []
    for start in range(0, len(col), chunk):
        seg = col[start : start + chunk]
        p0 = puzzles[start]
        p1 = puzzles[min(start + len(seg) - 1, len(puzzles) - 1)]
        out.append(f"  {label} P{p0:>3}-P{p1:<3}  {seg}")
    return out


def breakdown_one(n: int, d: int, px_exp: int, py_exp: int) -> dict:
    x, y = pubkey_from_scalar(d)
    comp, sha, h160 = hash160_compressed(x, y)
    addr = hash160_to_address(h160)
    return {
        "n": n,
        "d": d,
        "d_bits": d.bit_length(),
        "d_hex": format(d, "x"),
        "d_tail3": str(d)[-3:],
        "pub_prefix": comp[:1].hex(),
        "pub_y_parity": "even" if y % 2 == 0 else "odd",
        "px": x,
        "py": y,
        "px_match": x == px_exp,
        "py_match": y == py_exp,
        "compressed_pubkey_hex": comp.hex(),
        "sha256_hex": sha.hex(),
        "hash160_hex": h160.hex(),
        "hash160_head4": head_hex(h160, 4),
        "hash160_tail4": tail_hex(h160, 4),
        "address": addr,
        "address_head4": head_str(addr, 4),
        "address_tail4": addr[-4:] if len(addr) >= 4 else addr,
        "checksum_hex": hashlib.sha256(hashlib.sha256(b"\x00" + h160).digest()).digest()[:4].hex(),
    }


def write_pdf(text: str, path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    _, h = letter
    x, y = 36, h - 36
    c.setFont("Courier", 6)
    for line in text.splitlines():
        if y < 36:
            c.showPage()
            c.setFont("Courier", 6)
            y = h - 36
        c.drawString(x, y, line[:130])
        y -= 8
    c.save()


def main() -> int:
    ap = argparse.ArgumentParser(description="d -> hash160 -> address breakdown")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--detail-max-n", type=int, default=20, help="full step-by-step for puzzles <= this n")
    args = ap.parse_args()

    keys = parse_53125()
    rows: list[dict] = []
    for n in sorted(keys):
        pk = keys[n]
        if pk.d <= 0:
            continue
        rows.append(breakdown_one(n, pk.d, pk.px, pk.py))

    puzzles = [r["n"] for r in rows]
    lines = [
        "PRIVATE KEY d -> HASH160 -> ADDRESS (solved puzzles)",
        "",
        "Pipeline:",
        "  1. P = d * G  (secp256k1 scalar multiply)",
        "  2. compressed pubkey = (02 if y even else 03) || x  (33 bytes)",
        "  3. sha256 = SHA256(compressed pubkey)",
        "  4. hash160 = RIPEMD160(sha256)   [NOT RIPEMD160(d)]",
        "  5. payload = 0x00 || hash160 || checksum4",
        "  6. address = Base58Check(payload)",
        "",
        f"solved keys: {len(rows)}",
        "",
        "=== summary table ===",
        "",
        f"{'P':>4} {'bits':>4} {'d_t3':>4} {'y%2':>4} {'h160..4':>10} {'h160_t4':>8} {'addr_head4':>10} {'addr':>36}",
    ]
    for r in rows:
        lines.append(
            f"P{r['n']:>3} {r['d_bits']:>4} {r['d_tail3']:>4} {r['pub_y_parity'][:1]:>4} "
            f"{r['hash160_head4']:>10} {r['hash160_tail4']:>8} {r['address_head4']:>10} {r['address']:>36}"
        )
    lines.append("")

    # Full step-by-step for small puzzles
    lines.append(f"=== step-by-step (P1..P{args.detail_max_n}) ===")
    lines.append("")
    for r in rows:
        if r["n"] > args.detail_max_n:
            break
        lines.extend([
            f"--- P{r['n']} ---",
            f"  d (dec)     = {r['d']}",
            f"  d (hex)     = {r['d_hex']}",
            f"  d*G         px = {r['px']}",
            f"              py = {r['py']}  ({r['pub_y_parity']})",
            f"  compressed  = {r['compressed_pubkey_hex']}",
            f"  SHA256      = {r['sha256_hex']}",
            f"  hash160     = {r['hash160_hex']}",
            f"  checksum    = {r['checksum_hex']}",
            f"  address     = {r['address']}",
            f"  53125 match px={r['px_match']} py={r['py_match']}",
            "",
        ])

    # Vertical stacks
    h160_hex = [r["hash160_hex"] for r in rows]
    addrs = [r["address"] for r in rows]
    d_tails = [r["d_tail3"] for r in rows]

    lines.append("=== hash160 hex — vertical nibble stack (40 nibbles = 20 bytes) ===")
    for i, col in enumerate(digit_columns(h160_hex, 40, from_left=False)):
        pos = i - 40 + 1
        lines.extend(chunk_lines(f"h160[{pos:+d}]", col, puzzles))
    lines.append("")

    lines.append("=== address — first 6 Base58 chars stacked ===")
    for i, col in enumerate(digit_columns(addrs, 6, from_left=True)):
        lines.extend(chunk_lines(f"addr[{i}]", col, puzzles))
    lines.append("")

    lines.append("=== d decimal tail3 — stacked (does NOT map linearly to hash160) ===")
    lines.extend(chunk_lines("d_t3[0]", "".join(t[0] if len(t) > 0 else " " for t in d_tails), puzzles))
    lines.extend(chunk_lines("d_t3[1]", "".join(t[1] if len(t) > 1 else " " for t in d_tails), puzzles))
    lines.extend(chunk_lines("d_t3[2]", "".join(t[2] if len(t) > 2 else " " for t in d_tails), puzzles))
    lines.append("")

    # Stats
    lines.append("=== hash160 head4 recurrence ===")
    c4 = Counter(r["hash160_head4"] for r in rows)
    for h, cnt in c4.most_common(10):
        lines.append(f"  {h}: {cnt}x")
    lines.append("")

    lines.append("=== address head4 recurrence ===")
    ca = Counter(r["address_head4"] for r in rows)
    for h, cnt in ca.most_common(10):
        lines.append(f"  {h}: {cnt}x")
    lines.append("")

    lines.append("=== y parity (compressed prefix) ===")
    even = sum(1 for r in rows if r["pub_y_parity"] == "even")
    lines.append(f"  even (02): {even}   odd (03): {len(rows) - even}")
    lines.append("")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")

    fields = [
        "n", "d", "d_bits", "d_hex", "d_tail3", "pub_prefix", "pub_y_parity",
        "px_match", "py_match", "sha256_hex", "hash160_hex", "hash160_head4",
        "hash160_tail4", "checksum_hex", "address", "address_head4", "address_tail4",
        "compressed_pubkey_hex",
    ]
    with STACK_TSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(text[:6000])
    if len(text) > 6000:
        print(f"... ({len(text)} chars total)")
    print(f"wrote {REPORT_TXT}")
    print(f"wrote {STACK_TSV}")
    if args.pdf:
        write_pdf(text, REPORT_PDF)
        print(f"wrote {REPORT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
