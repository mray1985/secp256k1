#!/usr/bin/env python3
"""
Vertical stack of private keys d across solved Bitcoin puzzles.

Aligns decimal and hex digits column-by-column down puzzle number so
recurring heads/tails and lane patterns are visible at a glance.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT_TXT = ARCHIVE / "d_vertical_stack_report.txt"
STACK_TSV = ARCHIVE / "d_vertical_stack.tsv"
REPORT_PDF = ARCHIVE / "d_vertical_stack_report.pdf"


def head_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[:digits] if len(s) >= digits else s


def tail_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[-digits:] if len(s) >= digits else s


def pad_left(s: str, width: int) -> str:
    return s.rjust(width)


def pad_right(s: str, width: int) -> str:
    return s.ljust(width)


def digit_columns_right(values: list[str], width: int) -> list[str]:
    """One string per column, MSB column index 0 = leftmost of window."""
    padded = [pad_left(v, width) for v in values]
    return ["".join(row[i] for row in padded) for i in range(width)]


def digit_columns_left(values: list[str], width: int) -> list[str]:
    """Take leftmost `width` digits (leading / head window)."""
    clipped = [v[:width] if len(v) >= width else v.rjust(width) for v in values]
    return ["".join(row[i] for row in clipped) for i in range(width)]


def hex_tail(value: int, nibbles: int) -> str:
    h = format(value, "x")
    return h[-nibbles:] if len(h) >= nibbles else h


def chunk_lines(label: str, col: str, puzzles: list[int], chunk: int = 40) -> list[str]:
    lines = []
    for start in range(0, len(col), chunk):
        seg = col[start : start + chunk]
        p0 = puzzles[start]
        p1 = puzzles[min(start + len(seg) - 1, len(puzzles) - 1)]
        lines.append(f"  {label} P{p0:>3}-P{p1:<3}  {seg}")
    return lines


def build_rows(keys: dict) -> list[dict]:
    rows = []
    for n in sorted(keys):
        pk = keys[n]
        if pk.d <= 0:
            continue
        d = pk.d
        dec = str(d)
        hx = format(d, "x")
        rows.append({
            "n": n,
            "d": d,
            "d_bits": d.bit_length(),
            "d_dec_len": len(dec),
            "d_dec": dec,
            "d_hex": hx,
            "head2": head_dec(d, 2),
            "head3": head_dec(d, 3),
            "tail3": tail_dec(d, 3),
            "hex_tail4": hex_tail(d, 4),
            "lane3": n % 3,
            "lane5": n % 5,
            "bit_delta": d.bit_length() - n,
        })
    return rows


def lane_stats(rows: list[dict], key: str, field: str) -> list[str]:
    lines = [f"-- by {key} --"]
    for lane in sorted({r[key] for r in rows}):
        sub = [r for r in rows if r[key] == lane]
        heads = Counter(r[field] for r in sub)
        lines.append(f"  {key}={lane} (n={len(sub)}): top {field} " + ", ".join(
            f"{h}({c})" for h, c in heads.most_common(5)
        ))
    lines.append("")
    return lines


def write_pdf(text: str, path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    try:
        pdfmetrics.registerFont(TTFont("Consolas", "consola.ttf"))
        font = "Consolas"
    except Exception:
        font = "Courier"
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter
    x, y = 36, h - 36
    c.setFont(font, 6)
    for line in text.splitlines():
        if y < 36:
            c.showPage()
            c.setFont(font, 6)
            y = h - 36
        c.drawString(x, y, line[:130])
        y -= 8
    c.save()


def main() -> int:
    ap = argparse.ArgumentParser(description="Vertical stack private keys d")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--max-n", type=int, default=160)
    args = ap.parse_args()

    keys = parse_53125()
    rows = [r for r in build_rows(keys) if args.min_n <= r["n"] <= args.max_n]
    if not rows:
        print("no keys")
        return 1

    puzzles = [r["n"] for r in rows]
    decs = [r["d_dec"] for r in rows]
    max_dec_len = max(len(d) for d in decs)
    max_hex_len = max(len(r["d_hex"]) for r in rows)

    lines = [
        "PRIVATE KEY d — VERTICAL STACK (solved puzzles from 53125.txt)",
        "",
        f"puzzles: {len(rows)}  dec width: {max_dec_len}  hex width: {max_hex_len}",
        "bit_length ~ puzzle number (d_bits - n is usually 0 or small)",
        "",
        "=== per-puzzle d (decimal, right-aligned) ===",
        "",
    ]

    for r in rows:
        lines.append(
            f"P{r['n']:>3}  bits={r['d_bits']:>3}  "
            f"h2={r['head2']:>3} h3={r['head3']:>4} t3={r['tail3']:>3}  "
            f"{pad_left(r['d_dec'], max_dec_len)}"
        )
    lines.append("")

    # Leading decimal stack (first 6 digits = coarse head)
    head_w = min(8, max_dec_len)
    lines.append(f"=== leading {head_w} decimal digits — vertical columns ===")
    for i, col in enumerate(digit_columns_left(decs, head_w)):
        lines.extend(chunk_lines(f"head[{i}]", col, puzzles))
    lines.append("")

    # Trailing decimal stack (last 8 digits)
    tail_w = min(8, max_dec_len)
    lines.append(f"=== trailing {tail_w} decimal digits — vertical columns ===")
    tail_cols = digit_columns_right(decs, tail_w)
    for i, col in enumerate(tail_cols):
        pos = i - tail_w + 1
        lines.extend(chunk_lines(f"tail[{pos:+d}]", col, puzzles))
    lines.append("")

    # Hex trailing nibbles
    hex_w = min(16, max_hex_len)
    hexes = [r["d_hex"] for r in rows]
    lines.append(f"=== trailing {hex_w} hex nibbles — vertical columns ===")
    hex_padded = [pad_left(h, hex_w) for h in hexes]
    for i, col in enumerate(["".join(row[i] for row in hex_padded) for i in range(hex_w)]):
        pos = i - hex_w + 1
        lines.extend(chunk_lines(f"hex[{pos:+d}]", col, puzzles))
    lines.append("")

    lines.append("=== head2 / head3 / tail3 lane stats ===")
    lines.append("")
    lines.extend(lane_stats(rows, "lane3", "head2"))
    lines.extend(lane_stats(rows, "lane5", "tail3"))
    lines.extend(lane_stats(rows, "lane3", "tail3"))

    # bit_length vs puzzle number
    lines.append("=== d_bits - n (should be ~0) ===")
    deltas = Counter(r["bit_delta"] for r in rows)
    for delta, cnt in sorted(deltas.items()):
        lines.append(f"  delta={delta:+d}: {cnt} puzzles")
    lines.append("")

    # unsolved gaps in sequence
    have = set(puzzles)
    missing = [n for n in range(args.min_n, args.max_n + 1) if n not in have]
    lines.append(f"=== no d in 53125 ({len(missing)} puzzles) ===")
    lines.append("  " + ", ".join(f"P{x}" for x in missing[:60]))
    if len(missing) > 60:
        lines.append(f"  ... +{len(missing) - 60} more")
    lines.append("")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")

    fields = [
        "n", "d", "d_bits", "d_dec_len", "head2", "head3", "tail3",
        "hex_tail4", "lane3", "lane5", "bit_delta", "d_dec", "d_hex",
    ]
    with STACK_TSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(text[:8000])
    if len(text) > 8000:
        print(f"... ({len(text)} chars total)")
    print(f"wrote {REPORT_TXT}")
    print(f"wrote {STACK_TSV}")
    if args.pdf:
        write_pdf(text, REPORT_PDF)
        print(f"wrote {REPORT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
