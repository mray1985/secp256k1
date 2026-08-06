#!/usr/bin/env python3
"""How far back from the lead do consecutive puzzle factoradics agree before breaking?"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_AGREE_DEPTH.txt")


def to_fac(n: int) -> list[int]:
    digs: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digs.append(x % i)
        x //= i
        i += 1
    return digs


def first_break_offset(a: list[int], b: list[int]) -> int:
    """Offset from high end where digits first differ (0 = lead slot differs)."""
    kmax = max(len(a), len(b)) - 1
    for off in range(0, kmax + 1):
        k = kmax - off
        da = a[k] if 0 <= k < len(a) else 0
        db = b[k] if 0 <= k < len(b) else 0
        if da != db:
            return off
    return kmax + 1  # identical


def main() -> None:
    rows: list[tuple[int, int, list[int]]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            rows.append((n, d, to_fac(d)))

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    # All consecutive puzzle pairs
    breaks = [first_break_offset(rows[i - 1][2], rows[i][2]) for i in range(1, len(rows))]
    w("=" * 72)
    w("FACTORADIC AGREE DEPTH — how far back before consecutive puzzles break")
    w("=" * 72)
    w(f"pairs = {len(breaks)} (from {rows[0][0]}..{rows[-1][0]})")
    w()
    w("First-mismatch offset from lead (0 = leads already differ):")
    c = Counter(breaks)
    for off in sorted(c):
        w(f"  offset {off:2d}: {c[off]:3d}  {'#' * c[off]}")
    w()
    w("Still agreeing after looking back r slots from the high end:")
    total = len(breaks)
    for r in range(0, 12):
        # r=0: always 'agree on 0 slots looked'; r=1 means lead matched (break offset >=1)
        still = sum(1 for b in breaks if b >= r)
        w(f"  back {r:2d}: {still:3d}/{total} = {still / total:6.1%}")

    mean = sum(breaks) / len(breaks)
    med = sorted(breaks)[len(breaks) // 2]
    w()
    w(f"mean break-offset = {mean:.2f}   median = {med}")
    w(f"break at offset <=5: {sum(1 for b in breaks if b <= 5)}/{total}")
    w(f"break by offset 5 (i.e. offset < 5 means broke within first 5): "
      f"{sum(1 for b in breaks if b < 5)}/{total}")
    w(f"survived full 5-back (offset >= 5): {sum(1 for b in breaks if b >= 5)}/{total} "
      f"= {sum(1 for b in breaks if b >= 5)/total:.1%}")

    # Same max_k plateau only
    w()
    w("-" * 72)
    w("WITHIN same max_k plateau only")
    w("-" * 72)
    by_k: dict[int, list[tuple[int, list[int]]]] = defaultdict(list)
    for n, d, digs in rows:
        by_k[len(digs) - 1].append((n, digs))
    plat_breaks: list[int] = []
    for k in sorted(by_k):
        grp = by_k[k]
        if len(grp) < 2:
            continue
        w(f"  max_k={k:2d} puzzles={[n for n,_ in grp]}")
        for i in range(1, len(grp)):
            off = first_break_offset(grp[i - 1][1], grp[i][1])
            plat_breaks.append(off)
            w(f"    {grp[i-1][0]}->{grp[i][0]}  break@offset {off}")
    if plat_breaks:
        w()
        w(f"plateau pairs mean break-offset = {sum(plat_breaks)/len(plat_breaks):.2f}")
        w(f"plateau survived 5-back (offset>=5): "
          f"{sum(1 for b in plat_breaks if b >= 5)}/{len(plat_breaks)} "
          f"= {sum(1 for b in plat_breaks if b >= 5)/len(plat_breaks):.1%}")
        w(f"plateau broke within first 5 (offset<5): "
          f"{sum(1 for b in plat_breaks if b < 5)}/{len(plat_breaks)} "
          f"= {sum(1 for b in plat_breaks if b < 5)/len(plat_breaks):.1%}")
        cp = Counter(plat_breaks)
        w("plateau offset histogram:")
        for off in sorted(cp):
            w(f"  offset {off:2d}: {cp[off]:3d}")

    # Another reading: from each key's lead, how many consecutive nonzero high terms
    # before a zero (gap) — 'runs back'
    w()
    w("-" * 72)
    w("Per key: how far back from lead until first ZERO digit (gap)")
    w("-" * 72)
    gaps = []
    for n, d, digs in rows:
        mk = len(digs) - 1
        back = 0
        for off in range(0, mk + 1):
            if digs[mk - off] == 0:
                break
            back += 1
        gaps.append(back)
        if n <= 70 or n % 5 == 0:
            w(f"  n={n:3d} max_k={mk:2d} nonzero_run_from_lead={back}")
    w()
    cg = Counter(gaps)
    w("nonzero-run histogram:")
    for g in sorted(cg):
        w(f"  run={g:2d}: {cg[g]:3d}")
    w(f"mean run={sum(gaps)/len(gaps):.2f}  median={sorted(gaps)[len(gaps)//2]}")
    w(f"run == 5: {sum(1 for g in gaps if g == 5)}/{len(gaps)}")
    w(f"run <= 5: {sum(1 for g in gaps if g <= 5)}/{len(gaps)} "
      f"= {sum(1 for g in gaps if g <= 5)/len(gaps):.1%}")
    w(f"run >= 5: {sum(1 for g in gaps if g >= 5)}/{len(gaps)} "
      f"= {sum(1 for g in gaps if g >= 5)/len(gaps):.1%}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
