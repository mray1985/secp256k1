#!/usr/bin/env python3
"""RSZ pass: residues mod (puzzle_n - 1) on solved puzzles."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "rsz_mod_n_minus_1.txt"


def solve_k(r: int, s: int, z: int, d: int) -> int:
    return pow(s, -1, N) * (z + r * d) % N


def main() -> None:
    keys = {n: k.d for n, k in parse_53125().items() if k.d}
    rows = []
    for n, rsz in sorted(PUZZLE_RSZ.items()):
        if n not in keys:
            continue
        m = n - 1
        if m < 1:
            continue
        d = keys[n]
        k = rsz.k if rsz.k else solve_k(rsz.r, rsz.s, rsz.z, d)
        lo, hi = puzzle_band(n)[:2]
        rows.append(
            {
                "n": n,
                "m": m,
                "d": d,
                "k": k,
                "dr": d % m,
                "kr": k % m,
                "rr": rsz.r % m,
                "sr": rsz.s % m,
                "zr": rsz.z % m,
                "bf": (d - lo) / (hi - lo),
            }
        )

    lines = [
        "RSZ mod (puzzle_n - 1) pass",
        "=" * 55,
        "",
        "m = n-1   residues: d% m, k% m, r% m, s% m, z% m",
        "",
    ]

    for r in rows:
        lines.append(
            f"P{r['n']:3d} m={r['m']:3d}  "
            f"d%{r['m']}={r['dr']:3d}  k%{r['m']}={r['kr']:3d}  "
            f"r%{r['m']}={r['rr']:3d}  s%{r['m']}={r['sr']:3d}  z%{r['m']}={r['zr']:3d}  "
            f"bf={r['bf']:.4f}"
        )

    lines.append("")
    lines.append("=== law hit rates (per-puzzle modulus) ===")

    def rate(name: str, hits: int, total: int) -> None:
        lines.append(f"  {name}: {hits}/{total} ({100*hits/total:.1f}%)")

    total = len(rows)
    rate("d%(n-1) == 0", sum(1 for r in rows if r["dr"] == 0), total)
    rate("k%(n-1) == 0", sum(1 for r in rows if r["kr"] == 0), total)
    rate("d%(n-1) == 1", sum(1 for r in rows if r["dr"] == 1), total)
    rate("k%(n-1) == 1", sum(1 for r in rows if r["kr"] == 1), total)
    rate("d%(n-1) == k%(n-1)", sum(1 for r in rows if r["dr"] == r["kr"]), total)
    rate("d%(n-1) == r%(n-1)", sum(1 for r in rows if r["dr"] == r["rr"]), total)
    rate("k%(n-1) == r%(n-1)", sum(1 for r in rows if r["kr"] == r["rr"]), total)
    rate("d%(n-1) == z%(n-1)", sum(1 for r in rows if r["dr"] == r["zr"]), total)
    rate("(d+k)%(n-1) == 0", sum(1 for r in rows if (r["d"] + r["k"]) % r["m"] == 0), total)
    rate("(d-k)%(n-1) == 0", sum(1 for r in rows if (r["d"] - r["k"]) % r["m"] == 0), total)
    rate("(r+s+z)%(n-1) == 0", sum(1 for r in rows if (r["rr"] + r["sr"] + r["zr"]) % r["m"] == 0), total)
    rate(
        "ECDSA mod (n-1): s*k == z+r*d",
        sum(
            1
            for r in rows
            if (PUZZLE_RSZ[r["n"]].s * r["k"]) % r["m"]
            == (PUZZLE_RSZ[r["n"]].z + PUZZLE_RSZ[r["n"]].r * r["d"]) % r["m"]
        ),
        total,
    )

    lines.append("")
    lines.append("=== band_frac vs d%(n-1) / (n-2) when n>2 ===")
    for r in rows:
        if r["n"] <= 2:
            continue
        frac = r["dr"] / (r["n"] - 2)
        lines.append(f"  P{r['n']:3d}  d%(n-1)/(n-2) = {frac:.6f}  bf={r['bf']:.4f}")

    lines.append("")
    lines.append("=== P160 projection (m = 159) ===")
    rsz = PUZZLE_RSZ[160]
    m160 = 159
    lines.append(
        f"  r%159={rsz.r % m160}  s%159={rsz.s % m160}  z%159={rsz.z % m160}"
    )
    # if d%159 == r%159 pattern from solved
    hits_dr_eq_rr = sum(1 for r in rows if r["dr"] == r["rr"])
    lines.append(f"  solved: d%(n-1)==r%(n-1) hit {hits_dr_eq_rr}/{total}")
    if hits_dr_eq_rr:
        for r in rows:
            if r["dr"] == r["rr"]:
                lines.append(f"    P{r['n']} both residue {r['dr']} mod {r['m']}")

    lines.append("")
    lines.append("=== d%(n-1) == 0 cases (if any) ===")
    z = [r for r in rows if r["dr"] == 0]
    if z:
        for r in z:
            lines.append(f"  P{r['n']} d divisible by {r['m']}")
    else:
        lines.append("  none")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
