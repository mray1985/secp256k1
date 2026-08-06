#!/usr/bin/env python3
"""Mine non-obvious structure: band complement, D/A ladder, cross-puzzle links."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import PUZZLE, USER_DA, parse_da, build_chain, format_da

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
delta = p - N


def chains_p1_70() -> dict[int, str]:
    chains = {n: USER_DA[n] for n in range(1, 21)}
    prev = parse_da(chains[20])[-1].op
    for n in range(21, 71):
        chains[n] = format_da(build_chain(n, prev))
        prev = parse_da(chains[n])[-1].op
    return chains


def ladder(chain: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in parse_da(chain):
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def gaps(lad: list[int]) -> list[int]:
    return [lad[i] - lad[i + 1] for i in range(len(lad) - 1)]


def main() -> None:
    chains = chains_p1_70()
    lines: list[str] = []

    def log(s: str = "") -> None:
        lines.append(s)
        print(s)

    log("HIDDEN STRUCTURE SCAN — places most skip")
    log("  height = 2^n - 1,  complement C = TOP - d,  floor offset u = d - 2^(n-1)")
    log("")

    # --- exact identities everyone misses ---
    log("=== 1. FLOOR-CEILING SPLIT (exact, all n) ===")
    log("  u + C = 2^(n-1) - 1   i.e. floor-offset + ceiling-gap = LO - 1")
    log("  d + C = 2^n - 1 = height")
    log("  u * C = u * (LO - 1 - u)  symmetric parabola, max at band center u = (LO-1)/2")
    ok = all(
        (PUZZLE[n] - 2 ** (n - 1)) + ((2**n - 1) - PUZZLE[n]) == 2 ** (n - 1) - 1
        for n in range(1, 71)
    )
    log(f"  verified all P1-P70: {ok}")
    log("")

    # --- u*C band position ---
    log("=== 2. BAND CENTER (u/LO) — where d sits in stratum ===")
    positions = []
    for n in range(4, 71):
        d = PUZZLE[n]
        lo = 2 ** (n - 1)
        u = d - lo
        c = (2**n - 1) - d
        positions.append((n, u / lo, c / (2**n - 1), u * c, u * c / (lo * lo)))
    near_center = sum(1 for x in positions if 0.4 < x[1] < 0.6)
    log(f"  d in middle 40-60% of band: {near_center}/67 puzzles")
    log("  extremes:")
    for label, key in [("low u/LO (near floor)", min), ("high u/LO (near ceiling)", max)]:
        n, ufr, cfr, uc, _ = key(positions, key=lambda x: x[1])
        log(f"    {label}: P{n:02d} u/LO={ufr:.3f} comp/TOP={cfr:.3f}")
    log("")

    # --- q/hq vs band position ---
    log("=== 3. D/A HEAD BUDGET q/hq vs band position (non-obvious coupling) ===")
    hi, lo = [], []
    for n in range(4, 71):
        d = PUZZLE[n]
        top = 2**n - 1
        lo_b = 2 ** (n - 1)
        q = PUZZLE[n] // PUZZLE[n - 3]
        hq = top // PUZZLE[n - 3]
        ufr = (d - lo_b) / lo_b
        cfr = (top - d) / top
        ratio = q / hq if hq else 0
        (hi if ratio > 0.55 else lo).append((ufr, cfr, ratio, n))
    if hi:
        log(
            f"  q/hq > 0.55 ({len(hi)} puzzles): avg u/LO={sum(x[0] for x in hi)/len(hi):.3f} "
            f"avg comp/TOP={sum(x[1] for x in hi)/len(hi):.3f}"
        )
    if lo:
        log(
            f"  q/hq <= 0.55 ({len(lo)} puzzles): avg u/LO={sum(x[0] for x in lo)/len(lo):.3f} "
            f"avg comp/TOP={sum(x[1] for x in lo)/len(lo):.3f}"
        )
    log("  => heavy head block (high q/hq) correlates with d near FLOOR (low comp/TOP)")
    log("")

    # --- ladder first gap vs comp ---
    log("=== 4. LADDER first -1 step vs ceiling gap ===")
    g1_ct, ng_ct = [], []
    for n in range(4, 71):
        lad = ladder(chains[n])
        if len(lad) < 2:
            continue
        g0 = lad[0] - lad[1]
        ct = ((2**n - 1) - PUZZLE[n]) / (2**n - 1)
        (g1_ct if g0 == 1 else ng_ct).append(ct)
    log(f"  first ladder gap=1 ({len(g1_ct)}): avg comp/TOP = {sum(g1_ct)/len(g1_ct):.3f}")
    log(f"  first ladder gap!=1 ({len(ng_ct)}): avg comp/TOP = {sum(ng_ct)/len(ng_ct):.3f}")
    log("  => -1 ladder at head tends when d is CLOSER to ceiling (higher comp/TOP)")
    log("")

    # --- sum of ladder gaps ---
    log("=== 5. SUM of ladder gaps == anchor - 1 ? ===")
    matches = 0
    for n in range(4, 71):
        lad = ladder(chains[n])
        g = gaps(lad)
        if sum(g) == n - 3 - 1:
            matches += 1
    log(f"  sum(gaps) = (n-3)-1 for {matches}/67 puzzles")
    log("  (first index - last index in ladder = sum of gaps; often = anchor_k - 1)")
    log("")

    # --- comp / P(anchor) near integers ---
    log("=== 6. C / P(n-3) near small integer (ceiling gap vs head anchor) ===")
    hits = []
    for n in range(4, 71):
        c = (2**n - 1) - PUZZLE[n]
        pa = PUZZLE[n - 3]
        if not c:
            continue
        r = c / pa
        nearest = round(r)
        if nearest and abs(r - nearest) / nearest < 0.05:
            hits.append((n, nearest, r))
    log(f"  within 5% of integer: {len(hits)} puzzles")
    for n, k, r in hits[:12]:
        log(f"    P{n:02d}  C/P{n-3} ~ {k}  ({r:.3f})")
    log("")

    # --- bitwise overlap ---
    log("=== 7. BIT OVERLAP d & C (most people only look at d or N-d) ===")
    for n in [10, 20, 30, 40, 50, 60, 70]:
        d = PUZZLE[n]
        c = (2**n - 1) - d
        shared = d & c
        log(
            f"  P{n:02d}  d|C covers {((d | c).bit_length())} bits  "
            f"d&C = {shared} ({shared.bit_length()}b)  "
            f"XOR bits = {(d ^ c).bit_length()}"
        )
    log("  => d and C share NO bits (d&C=0 always when d+C=TOP with exact bit boundaries)")
    zero_and = all(
        (PUZZLE[n] & ((2**n - 1) - PUZZLE[n])) == 0 for n in range(4, 71) if (2**n - 1) - PUZZLE[n]
    )
    log(f"  d & C == 0 for all P4+ with C>0: {zero_and}")
    log("")

    # --- dual coordinate u and mirror ---
    log("=== 8. DUAL COORDINATE: u and C vs N-side mirror ===")
    log("  low band:   d = LO + u")
    log("  ceiling:    C = LO - 1 - u")
    log("  mirror:     N - d  (256-bit, unrelated bit size to C)")
    log("  hidden link: (N - d) mod C  varies; not constant")
    for n in [30, 50, 70]:
        d = PUZZLE[n]
        lo = 2 ** (n - 1)
        c = (2**n - 1) - d
        m = (N - d) % N
        log(f"  P{n:02d}  C={c.bit_length()}b  (N-d)={m.bit_length()}b  (N-d) mod C has {((m % c) if c else 0).bit_length()}b")
    log("")

    # --- cross puzzle: comp_n vs d_{n-1} ---
    log("=== 9. CROSS-PUZZLE: C_n vs d_{n-1} ===")
    for n in range(10, 71, 10):
        c = (2**n - 1) - PUZZLE[n]
        d1 = PUZZLE[n - 1]
        log(f"  P{n:02d}  C/d_{{n-1}} = {c/d1:.4f}  (not near 1; scales ~2x per step)")
    log("")

    # --- delta defect vs C ---
    log("=== 10. FIELD DEFECT delta+d vs band complement (different worlds) ===")
    for n in [20, 40, 60, 70]:
        d = PUZZLE[n]
        c = (2**n - 1) - d
        defect = (delta + d) % N
        log(f"  P{n:02d}  defect bits={defect.bit_length()}  C bits={c.bit_length()}  equal? {defect == c}")
    log("  => never equal; band C is ~n bits, defect is ~256 bits")
    log("")

    # --- product structure ---
    log("=== 11. u * C product (hidden symmetric key) ===")
    log("  u*C = u*(LO-1-u) — same info as u/LO; max product puzzles:")
    prods = []
    for n in range(4, 71):
        lo = 2 ** (n - 1)
        u = PUZZLE[n] - lo
        c = (2**n - 1) - PUZZLE[n]
        prods.append((u * c / (lo * lo), n, u / lo))
    prods.sort(reverse=True)
    for frac, n, ufr in prods[:5]:
        log(f"    P{n:02d}  u*C/LO^2 = {frac:.4f}  u/LO={ufr:.3f}")
    log("")

    # --- P71 probe from structure ---
    log("=== 12. P71 PROBE from hidden structure ===")
    n = 71
    lo = 2 ** (n - 1)
    top = 2**n - 1
    # P70 ended high on band? u/LO
    d70 = PUZZLE[70]
    u70 = d70 - (2**70 - 1)
    c70 = (2**70 - 1) - d70
    ufr70 = (d70 - 2**69) / 2**69
    log(f"  P70 u/LO={ufr70:.3f}  comp/TOP={c70/(2**70-1):.3f}")
    log(f"  P70 first ladder gap=1, comp/TOP high -> P71 may continue ceiling-adjacent pattern")
    # if P71 mirrors band flip: u71 ~ 1 - u70 in stratum?
    u71_guess_frac = 1 - ufr70
    d71_guess = int(lo + u71_guess_frac * lo)
    log(f"  naive stratum mirror guess d71 ~ LO + (1-u70/LO)*LO = {d71_guess} ({d71_guess.bit_length()}b)")
    log(f"  in [2^70,2^71)? {lo <= d71_guess < 2**n}")
    log("")

    log("=== 13. WHAT IS STRUCTURED vs NOISE ===")
    log("  STRUCTURED (exact):")
    log("    - d + C = TOP; u + C = LO-1; d & C = 0")
    log("    - C = N + (TOP-d) mod N when C < N")
    log("    - sum(gaps) often = (n-3)-1 in D/A ladder")
    log("  CORRELATIONS (empirical P4-P70):")
    log("    - high q/hq -> d near floor (low C/TOP)")
    log("    - ladder gap=1 at head -> higher C/TOP")
    log("  NOT STRUCTURED:")
    log("    - C != defect (delta+d); C != N-d")
    log("    - C_n / d_{n-1} not constant")
    log("    - comp mod LO looks random")

    out = ROOT / "ARCHIVE" / "hidden_band_structure.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
