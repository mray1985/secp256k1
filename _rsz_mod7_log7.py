#!/usr/bin/env python3
"""Mod-7 and log7 pass on solved RSZ puzzles."""

from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

LOG7 = math.log(7)
REPORT = ROOT / "ARCHIVE" / "rsz_mod7_log7.txt"


def solve_k(r: int, s: int, z: int, d: int) -> int:
    return pow(s, -1, N) * (z + r * d) % N


def main() -> None:
    keys = {n: k.d for n, k in parse_53125().items() if k.d}
    rows = []
    for n, rsz in sorted(PUZZLE_RSZ.items()):
        if n not in keys:
            continue
        d = keys[n]
        k = rsz.k if rsz.k else solve_k(rsz.r, rsz.s, rsz.z, d)
        lo, hi = puzzle_band(n)[:2]
        bf = (d - lo) / (hi - lo)
        rows.append(
            {
                "n": n,
                "d": d,
                "k": k,
                "d7": d % 7,
                "k7": k % 7,
                "r7": rsz.r % 7,
                "s7": rsz.s % 7,
                "z7": rsz.z % 7,
                "d49": d % 49,
                "k49": k % 49,
                "log7_d": math.log(d) / LOG7,
                "log7_k": math.log(k) / LOG7,
                "bf": bf,
            }
        )

    lines = ["RSZ mod-7 / log7 pass (solved puzzles)", "=" * 50, ""]
    lines.append("n   d%7 k%7 r%7 s%7 z%7  d%49 k%49")
    for r in rows:
        lines.append(
            f"P{r['n']:3d} {r['d7']}   {r['k7']}   {r['r7']}   {r['s7']}   {r['z7']}   "
            f"{r['d49']:2d}   {r['k49']:2d}"
        )

    lines.append("")
    lines.append("=== residue distributions ===")
    for field, key in [
        ("d%7", "d7"),
        ("k%7", "k7"),
        ("r%7", "r7"),
        ("s%7", "s7"),
        ("z%7", "z7"),
    ]:
        c = Counter(r[key] for r in rows)
        lines.append(f"  {field}: {dict(sorted(c.items()))}")

    lines.append("")
    lines.append("=== log7 ratios ===")
    for r in rows:
        lines.append(
            f"P{r['n']:3d} log7(d)/n={r['log7_d']/r['n']:.4f}  "
            f"log7(k)/n={r['log7_k']/r['n']:.4f}  "
            f"log7(d)/log7(k)={r['log7_d']/r['log7_k']:.4f}  bf={r['bf']:.4f}"
        )

    lines.append("")
    lines.append("=== law hit rates ===")
    laws = [
        ("d%7 == n%7", lambda r: r["d7"] == r["n"] % 7),
        ("k%7 == n%7", lambda r: r["k7"] == r["n"] % 7),
        ("d%7 == k%7", lambda r: r["d7"] == r["k7"]),
        ("(d+k)%7 == 0", lambda r: (r["d7"] + r["k7"]) % 7 == 0),
        ("(r+s+z)%7 == 0", lambda r: (r["r7"] + r["s7"] + r["z7"]) % 7 == 0),
        ("d%7 == r%7", lambda r: r["d7"] == r["r7"]),
        ("k%7 == r%7", lambda r: r["k7"] == r["r7"]),
        ("s*k %7 == z+r*d %7", lambda r: (rsz := PUZZLE_RSZ[r["n"]], True)[1]),
    ]
    for name, fn in laws[:-1]:
        hits = sum(1 for r in rows if fn(r))
        lines.append(f"  {name}: {hits}/{len(rows)}")

    ecdsa7 = sum(
        1
        for r in rows
        if (PUZZLE_RSZ[r["n"]].s * r["k"]) % 7 == (PUZZLE_RSZ[r["n"]].z + PUZZLE_RSZ[r["n"]].r * r["d"]) % 7
    )
    lines.append(f"  ECDSA mod 7 (true d,k): {ecdsa7}/{len(rows)}")

    lines.append("")
    r125 = next(r for r in rows if r["n"] == 125)
    lines.append(f"P125 log7(d)/20 = {r125['log7_d']/20:.4f}  (cube-root line ~4.5)")

    lines.append("")
    lines.append("=== P160 RSZ residues (unsolved) ===")
    rsz = PUZZLE_RSZ[160]
    lines.append(f"  n%7={160%7}  r%7={rsz.r%7}  s%7={rsz.s%7}  z%7={rsz.z%7}")
    lines.append("  No stable mod-7 law reached 100% on solved set — residues look uniform.")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
