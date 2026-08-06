#!/usr/bin/env python3
"""
Vertical digit-stack alignment of N-gap transport fingerprints across all puzzles.

Reads anchor values from build_ctx (same as full transport hunt) and renders:
  - per-puzzle rows with gap_head2/3, lhs/rhs tails, rx tail, bridge lane
  - digit columns aligned vertically (gap, lhs mod N, rhs mod N)
  - lane recurrence stats (n mod 3, n mod 5)
  - RSZ vs bridge-default split
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from puzzle_keys_53125 import parse_53125  # noqa: E402
from unsolved_full_transport_hunt import (  # noqa: E402
    ALL_PUZZLES,
    build_ctx,
    head_dec,
)

ARCHIVE = ROOT / "ARCHIVE"
REPORT_TXT = ARCHIVE / "transport_vertical_stack_report.txt"
STACK_TSV = ARCHIVE / "transport_vertical_stack.tsv"
REPORT_PDF = ARCHIVE / "transport_vertical_stack_report.pdf"


def bridge_row(r_source: str) -> int | None:
    if "row 1" in r_source:
        return 1
    if "row 2" in r_source:
        return 2
    if "row 3" in r_source:
        return 3
    return None


def is_rsz(r_source: str) -> bool:
    return "RSZ" in r_source or "hashkeys" in r_source


def is_bridge_default(r_source: str) -> bool:
    return "bridge row" in r_source


def pad_digits(s: str, width: int) -> str:
    return s.rjust(width) if len(s) <= width else s[-width:]


def digit_columns(values: list[str], width: int) -> list[str]:
    """Return width strings, each one digit position across all puzzles."""
    padded = [pad_digits(v, width) for v in values]
    cols: list[str] = []
    for col in range(width):
        cols.append("".join(row[col] for row in padded))
    return cols


def stack_block(title: str, rows: list[dict]) -> list[str]:
    gaps = [r["gap"] for r in rows]
    w = max(len(g) for g in gaps)
    lines = [title, ""]
    lines.append(f"{'P':>4}  {'gap_h2':>5} {'gap_h3':>5} {'lhs':>5} {'rhs':>5} {'rx':>5}  row  rsz")
    for r in rows:
        br = r.get("bridge_row", "")
        lines.append(
            f"P{r['n']:>3}  {r['gap_h2']:>5} {r['gap_h3']:>5} {r['lhs_tail']:>5} "
            f"{r['rhs_tail']:>5} {r['rx_tail']:>5}  {str(br):>4}  {'Y' if r['rsz'] else 'n'}"
        )
    lines.append("")
    puzzles = [r["n"] for r in rows]
    cols = digit_columns(gaps, w)
    lines.append(f"gap vertical stack (right-aligned {w} decimal digits):")
    for i, col in enumerate(cols):
        chunk = 40
        for start in range(0, len(col), chunk):
            seg = col[start : start + chunk]
            p0 = puzzles[start]
            p1 = puzzles[min(start + len(seg) - 1, len(puzzles) - 1)]
            lines.append(f"  col{-w + i:>+3} P{p0:>3}-P{p1:<3}  {seg}")
    lines.append("")
    return lines


def build_rows() -> list[dict]:
    keys = parse_53125()
    rows: list[dict] = []
    for n in ALL_PUZZLES:
        try:
            ctx = build_ctx(n, keys)
        except Exception as exc:
            rows.append({"n": n, "error": str(exc)})
            continue
        br = bridge_row(ctx.r_source)
        rows.append({
            "n": n,
            "solved": n in keys and keys[n].d > 0,
            "rsz": is_rsz(ctx.r_source),
            "bridge_row": br if br is not None else "",
            "lane3": n % 3,
            "lane5": n % 5,
            "gap": str(ctx.anchor_gap),
            "gap_h2": head_dec(ctx.anchor_gap, 2),
            "gap_h3": head_dec(ctx.anchor_gap, 3),
            "lhs_n": str(ctx.anchor_lhs),
            "rhs_n": str(ctx.anchor_rhs),
            "lhs_tail": str(ctx.anchor_lhs)[-3:],
            "rhs_tail": str(ctx.anchor_rhs)[-3:],
            "rx_tail": str(ctx.rx)[-3:],
            "r_source": ctx.r_source,
        })
    return rows


def lane_summary(rows: list[dict]) -> list[str]:
    lines = ["=== lane recurrence (bridge-default rows only) ===", ""]
    bridge = [r for r in rows if "error" not in r and is_bridge_default(r["r_source"])]
    for mod, key in ((3, "lane3"), (5, "lane5")):
        lines.append(f"-- n mod {mod} --")
        by_lane: dict[int, Counter] = defaultdict(Counter)
        for r in bridge:
            by_lane[r[key]][(r["gap_h2"], r["lhs_tail"], r["rx_tail"])] += 1
        for lane in sorted(by_lane):
            top = by_lane[lane].most_common(3)
            lines.append(f"  lane{mod}={lane}: " + " | ".join(
                f"gap_h2={t[0][0]} lhs={t[0][1]} rx={t[0][2]} ({t[1]}x)" for t in top
            ))
        lines.append("")
    lines.append("-- RSZ / known_k puzzles (break the 3-row tower) --")
    rsz = [r for r in rows if "error" not in r and r["rsz"]]
    for r in sorted(rsz, key=lambda x: x["n"]):
        lines.append(
            f"  P{r['n']:>3} gap_h2={r['gap_h2']} gap_h3={r['gap_h3']} "
            f"lhs...{r['lhs_tail']} rx...{r['rx_tail']}"
        )
    lines.append("")
    lines.append("-- unsolved batch (n≡0 mod 5, RSZ rx) --")
    for r in rows:
        if "error" in r:
            continue
        if r["n"] in (135, 140, 145, 150, 155, 160):
            lines.append(
                f"  P{r['n']} gap_h2={r['gap_h2']} gap_h3={r['gap_h3']} "
                f"lhs...{r['lhs_tail']} rx...{r['rx_tail']}  {r['r_source'][:40]}"
            )
    lines.append("")
    return lines


def write_tsv(rows: list[dict], path: Path) -> None:
    ok = [r for r in rows if "error" not in r]
    if not ok:
        return
    fields = [
        "n", "solved", "rsz", "bridge_row", "lane3", "lane5",
        "gap_h2", "gap_h3", "lhs_tail", "rhs_tail", "rx_tail",
        "gap", "lhs_n", "rhs_n", "r_source",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(ok)


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
    x, y = 40, h - 40
    lh = 9
    c.setFont(font, 7)
    for line in text.splitlines():
        if y < 40:
            c.showPage()
            c.setFont(font, 7)
            y = h - 40
        c.drawString(x, y, line[:120])
        y -= lh
    c.save()


def main() -> int:
    ap = argparse.ArgumentParser(description="Vertical stack transport fingerprints")
    ap.add_argument("--pdf", action="store_true")
    args = ap.parse_args()

    rows = build_rows()
    ok = [r for r in rows if "error" not in r]
    puzzles = [r["n"] for r in ok]

    lines = ["TRANSPORT VERTICAL STACK — all puzzles", ""]
    lines.append("Three bridge towers (default rx, not RSZ):")
    lines.append("  row1: gap_h2=29 gap_h3=292 lhs...776 rx...219")
    lines.append("  row2: gap_h2=14 gap_h3=148 lhs...768 rx...368")
    lines.append("  row3: gap_h2=52 gap_h3=529 lhs...255 rx...739")
    lines.append("  rhs always ...962 (bridge DEFAULT_RY)")
    lines.append("")
    lines.extend(stack_block("=== full vertical table ===", ok))
    lines.extend(lane_summary(ok))

    # lhs tail vertical (3 digits) — shows meet fingerprint stack
    lines.append("=== lhs (x^3+4) mod N — last 3 decimal digits stacked ===")
    lhs_tails = [r["lhs_tail"] for r in ok]
    for i, ch in enumerate(range(3)):
        col = "".join(t[i] for t in lhs_tails)
        for start in range(0, len(col), 40):
            seg = col[start : start + 40]
            p0 = puzzles[start]
            p1 = puzzles[min(start + len(seg) - 1, len(puzzles) - 1)]
            lines.append(f"  lhs[{i}] P{p0:>3}-P{p1:<3}  {seg}")
    lines.append("")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    write_tsv(ok, STACK_TSV)
    print(text)
    print(f"wrote {REPORT_TXT}")
    print(f"wrote {STACK_TSV}")
    if args.pdf:
        write_pdf(text, REPORT_PDF)
        print(f"wrote {REPORT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
