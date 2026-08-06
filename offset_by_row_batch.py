#!/usr/bin/env python3
"""Row-stratified distribution of H - offset_bits (shelf2->d gap) across solved puzzles."""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from compare_family_mirror_batch import PUZZLE_LIST, analyze_one, build_config  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def pct(sorted_vals: list[int], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def summarize_gap(name: str, gaps: list[int]) -> list[str]:
    if not gaps:
        return [f"{name}: (no data)"]
    ctr = Counter(gaps)
    s = sorted(gaps)
    lines = [
        f"{name}  n={len(gaps)}",
        f"  H - offset_bits: min={s[0]}  p25={pct(s, 0.25):.1f}  "
        f"median={statistics.median(s):.1f}  mean={statistics.mean(s):.2f}  "
        f"p75={pct(s, 0.75):.1f}  max={s[-1]}",
        f"  mode(s): {ctr.most_common(3)}",
        f"  value counts: {dict(sorted(ctr.items()))}",
    ]
    return lines


def main() -> None:
    keys = parse_53125()
    solved: list[dict] = []
    errors: list[tuple[int, str]] = []

    for n in PUZZLE_LIST:
        if n == 135 or n not in keys:
            continue
        pk = keys[n]
        if pk.d == 0:
            continue
        try:
            row = analyze_one(pk)
            row["h_minus_offset"] = row["n"] - row["offset_bits"]
            row["h_minus_offset_minus_row"] = row["h_minus_offset"] - row["row"]
            solved.append(row)
        except Exception as e:
            errors.append((n, str(e)))

    by_row: dict[int, list[dict]] = defaultdict(list)
    for r in solved:
        by_row[r["row"]].append(r)

    lines = [
        "ROW-STRATIFIED H - offset_bits ANALYSIS",
        f"solved puzzles analyzed: {len(solved)}  (53125.txt, batch list step 5)",
        "offset_bits = bit_length((d - shelf2) mod LO);  gap = H - offset_bits",
        "",
        "UNIVERSAL H-10 (offset_bits == H-10):",
        f"  all rows: {sum(1 for r in solved if r['h10_match'])}/{len(solved)}",
        "",
    ]

    all_gaps = [r["h_minus_offset"] for r in solved]
    lines += summarize_gap("ALL ROWS", all_gaps)
    lines.append("")

    for row_id in (0, 1, 2):
        grp = sorted(by_row[row_id], key=lambda x: x["n"])
        gaps = [r["h_minus_offset"] for r in grp]
        lines.append("=" * 72)
        lines += summarize_gap(f"ROW {row_id}", gaps)
        lines.append(
            f"  H-10 hits in row {row_id}: "
            f"{sum(1 for r in grp if r['h10_match'])}/{len(grp)}"
        )
        # Test row-shifted constant: gap == 10 - row? gap == 1 + row? etc.
        for target in range(0, 12):
            hits = sum(1 for g in gaps if g == target)
            if hits:
                lines.append(f"  gap == {target}: {hits}/{len(grp)}")
        lines.append("")
        lines.append(
            f"  {'H':>4} {'off_bits':>8} {'gap':>4} {'gap-row':>7}  "
            f"{'H-10':>4}  offset mod LO (first 20 digits)"
        )
        lines.append("  " + "-" * 68)
        for r in grp:
            off = r["offset"] or 0
            lines.append(
                f"  {r['n']:4d} {r['offset_bits']:8d} {r['h_minus_offset']:4d} "
                f"{r['h_minus_offset_minus_row']:7d}  "
                f"{'Y' if r['h10_match'] else 'N':>4}  {str(off)[:20]}..."
            )
        lines.append("")

    # Candidate row laws
    lines.append("=" * 72)
    lines.append("ROW-LAW CANDIDATES (solved set only)")
    laws = [
        ("gap == 1", lambda r: r["h_minus_offset"] == 1),
        ("gap == 2", lambda r: r["h_minus_offset"] == 2),
        ("gap == 1 or 2", lambda r: r["h_minus_offset"] in (1, 2)),
        ("gap == 10 - row", lambda r: r["h_minus_offset"] == 10 - r["row"]),
        ("gap == 11 - row", lambda r: r["h_minus_offset"] == 11 - r["row"]),
        ("gap == 12 - row", lambda r: r["h_minus_offset"] == 12 - r["row"]),
        ("gap + row == 10", lambda r: r["h_minus_offset"] + r["row"] == 10),
        ("gap + row == 11", lambda r: r["h_minus_offset"] + r["row"] == 11),
        ("gap == row + 1", lambda r: r["h_minus_offset"] == r["row"] + 1),
        ("offset_bits == H - row - 1", lambda r: r["offset_bits"] == r["n"] - r["row"] - 1),
        ("offset_bits == H - 10 + row", lambda r: r["offset_bits"] == r["n"] - 10 + r["row"]),
    ]
    for label, pred in laws:
        hits = [r for r in solved if pred(r)]
        if not hits:
            continue
        by_r = Counter(r["row"] for r in hits)
        lines.append(
            f"  {label:<32} {len(hits):2d}/{len(solved)}  "
            f"by row {dict(sorted(by_r.items()))}"
        )

    # P115 / P130 callouts
    lines += [
        "",
        "TIERED GAP LAW (offset_bits = H - gap, gap in {1,2}):",
    ]
    for row_id in (0, 1, 2):
        grp = by_row[row_id]
        g12 = [r for r in grp if r["h_minus_offset"] in (1, 2)]
        lines.append(f"  row {row_id}: gap in {{1,2}} -> {len(g12)}/{len(grp)}")
    g12_all = [r for r in solved if r["h_minus_offset"] in (1, 2)]
    lines.append(f"  all rows: {len(g12_all)}/{len(solved)}")
    outliers = [r for r in solved if r["h_minus_offset"] not in (1, 2)]
    lines.append(
        "  outliers (gap not 1 or 2): "
        + ", ".join(f"P{r['n']}(row{r['row']},gap={r['h_minus_offset']})" for r in outliers)
    )

    lines += [
        "",
        "OUTLIERS:",
        "  P115 (row 0): only universal H-10 hit; gap=10",
        "  P130 (row 0): gap=3 — breaks row-0 mode=1 cluster",
    ]

    if errors:
        lines += ["", "ERRORS:"]
        for n, msg in errors:
            lines.append(f"  P{n}: {msg}")

    report = "\n".join(lines) + "\n"
    print(report)

    out_txt = ROOT / "ARCHIVE" / "offset_by_row_report.txt"
    out_csv = ROOT / "ARCHIVE" / "offset_by_row.csv"
    out_txt.write_text(report, encoding="utf-8")

    fields = [
        "n",
        "row",
        "d",
        "shelf2",
        "offset",
        "offset_bits",
        "h_minus_offset",
        "h_minus_offset_minus_row",
        "h_minus_10",
        "h10_match",
        "offset_eq_l2_l1",
        "n_term_hits",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(solved, key=lambda r: (r["row"], r["n"])))

    print(f"wrote {out_txt}")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()
