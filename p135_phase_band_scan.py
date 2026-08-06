#!/usr/bin/env python3
"""
P135 phase-aware band scan.

Meaning of Lambda / 120-degree landings:
  - Lambda = CP1*CR1^-1 is the P<->r bridge (mod p), NOT a cube root.
  - n1,n2,n3 (N^(1/3) mod p) rotate Gx,Px,rx into A/B/C frames; n2/n1=beta, n3/n1=beta^2.
  - After Lambda acts: Px/(Lambda*rx_i) lands in {1, beta, beta^2}.
  - Puzzle 135 pubkey sits on rx3 row -> landing = 1 (unity phase).

Useful for d search:
  - d lives in [2^134, 2^135-1]; write d = 2^134 + t.
  - Use N-side shelf2 + phase offsets (beta^k mod LO) + k-lane residues as t seeds.
  - Only acceptance test: d*G == P.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ecdsa import SECP256k1

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "ECDLP"))

LO = 1 << 134
TOP = (1 << 135) - 1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

K_PX = 19089036453356401353257357002647987614981495902151757130742235757133693952525
K_PY = 90508964219557991953548570402867934097841441951106365697884749206559245429888

# 120-degree phase (beta^3 = 1 mod p); use mod LO for band offsets
BETA = 55594575648329892869085402983802832744385952214688224221778511981742606582254
BETA2 = pow(BETA, 2, P)

G = SECP256k1.generator


def ec_hit(d: int) -> bool:
    if d <= 0:
        return False
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def phase_offsets(t: int) -> list[tuple[str, int]]:
    """Unity row landed on rx3; still scan beta shifts on each seed."""
    t %= LO
    return [
        ("t", t),
        ("t+beta", (t + BETA) % LO),
        ("t+beta^2", (t + BETA2) % LO),
        ("t-beta", (t - BETA) % LO),
    ]


def build_seeds() -> dict[str, int]:
    seeds: dict[str, int] = {}

    def add(name: str, val: int) -> None:
        seeds[name] = val % LO

    add("Px_mod_lo", PX)
    add("k_Px_mod_lo", K_PX)
    add("k_Py_mod_lo", K_PY)
    add("Px_mod_lo - k_Px", PX - K_PX)
    add("k_Py - k_Px", K_PY - K_PX)

    try:
        from p135_carry_remainder_report import build_p135_bridge

        b = build_p135_bridge(puzzle_row=2)
        for key in ("shelf2", "d_cube_lift2", "d_cube_lift3", "GAP", "C_floor"):
            if key in b:
                add(key, b[key])
        add("shelf2+GAP", b.get("shelf2", 0) + b.get("GAP", 0))
    except Exception as exc:  # noqa: BLE001
        print(f"bridge seeds skipped: {exc}", file=sys.stderr)

    return seeds


def scan(radius: int) -> int | None:
    seeds = build_seeds()
    t_set: set[int] = set()

    for name, t0 in seeds.items():
        for pname, t in phase_offsets(t0):
            for dt in range(-radius, radius + 1):
                t_set.add((t + dt) % LO)

    print(f"Phase seeds: {len(seeds)} base -> {len(seeds)*4} with beta orbit")
    print(f"Radius ±{radius:,} -> {len(t_set):,} candidates for d = 2^134 + t")
    print("Gate: d*G == P")
    print()

    t_start = time.perf_counter()
    n = 0
    for t in t_set:
        d = LO + t
        if d > TOP:
            continue
        n += 1
        if ec_hit(d):
            elapsed = time.perf_counter() - t_start
            print("=" * 72)
            print("MATCH")
            print(f"  d     = {d}")
            print(f"  d hex = {hex(d)}")
            print(f"  t     = {t}")
            print(f"  tested {n:,} in {elapsed:.1f}s")
            return d
        if n % 1_000_000 == 0:
            rate = n / (time.perf_counter() - t_start)
            print(f"  ... {n:,} @ {rate:,.0f}/s")

    elapsed = time.perf_counter() - t_start
    print(f"No match ({n:,} tested, {elapsed:.1f}s, {n/max(elapsed,1e-9):,.0f}/s)")
    return None


def calibrate_p115() -> None:
    """Check if solved P115 d mod LO aligns with beta phase (sanity on framework)."""
    from ecdlp_full_pipeline import P115_D, puzzle_band

    lo115, _, _ = puzzle_band(115)
    d = P115_D
    t = d - lo115
    print("P115 calibration (solved):")
    print(f"  d - 2^114 = {t}")
    print(f"  t mod beta (as offset)? t-beta={t-BETA} (informal)")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", type=int, default=65_536)
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()

    print("=" * 72)
    print("P135 PHASE BAND SCAN (Lambda landing = unity on rx3)")
    print("=" * 72)
    if args.calibrate:
        calibrate_p115()
    found = scan(args.radius)
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
