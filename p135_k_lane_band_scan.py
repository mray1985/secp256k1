#!/usr/bin/env python3
"""Scan Puzzle 135 band d = 2^134 + t using k-lane residue seeds; gate d*G == P."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ecdsa import SECP256k1

sys.path.insert(0, str(Path(__file__).resolve().parent / "ECDLP"))

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Barcode / RSZ lane (user-confirmed)
S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951
R = 90653255469745952335985143920649543885181555095025199315947044135806663628368

PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800

K_PX = 19089036453356401353257357002647987614981495902151757130742235757133693952525
K_LO = 73122516293330220904946986341402006911610605034389268402057892234619410896840
K_TOP = 2369132014955645563534129335893169829385209995274273875750530787065419108482

LO = 1 << 134
TOP = (1 << 135) - 1
G = SECP256k1.generator


def k_for_x(x: int) -> int:
    return (pow(S, -1, N) * (Z + R * x)) % N


def skm(k: int) -> int:
    return (S * k - Z) % N


def build_seeds() -> dict[str, int]:
    """Residue seeds mod LO (t = d - 2^134)."""
    seeds: dict[str, int] = {}

    def add(name: str, val: int) -> None:
        seeds[name] = val % LO

    add("k_Px_mod_lo", K_PX)
    add("k_lo_mod_lo", K_LO)
    add("k_top_mod_lo", K_TOP)
    add("Px_mod_lo", PX)
    add("skm_Px_mod_lo", skm(K_PX))
    add("skm_lo_mod_lo", skm(K_LO))
    add("skm_top_mod_lo", skm(K_TOP))

    add("gap_klo_kpx", K_LO - K_PX)
    add("gap_ktop_kpx", K_TOP - K_PX)
    add("gap_ktop_klo", K_TOP - K_LO)
    add("Px_minus_kpx", PX - K_PX)

    # shelf2 from carry bridge when available
    try:
        from p135_carry_remainder_report import build_p135_bridge

        bridge = build_p135_bridge(puzzle_row=2)
        add("shelf2", bridge["shelf2"])
        add("d_cube_lift2", bridge["d_cube_lift2"])
        add("d_cube_lift3", bridge["d_cube_lift3"])
        add("GAP", bridge["GAP"])
    except Exception as exc:  # noqa: BLE001
        print(f"note: bridge seeds skipped ({exc})", file=sys.stderr)

    # pairwise sums/diffs of primary k residues
    base = [K_PX % LO, K_LO % LO, K_TOP % LO, PX % LO]
    labels = ["k_Px", "k_lo", "k_top", "Px"]
    for i, a in enumerate(base):
        for j, b in enumerate(base):
            if i < j:
                add(f"sum_{labels[i]}_{labels[j]}", a + b)
                add(f"diff_{labels[i]}_{labels[j]}", a - b)

    return seeds


def ec_match(d: int) -> bool:
    if d <= 0 or d >= N:
        return False
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def scan(radius: int, extra_offsets: list[int] | None = None) -> int | None:
    seeds = build_seeds()
    t_candidates: set[int] = set()

    offsets = list(range(-radius, radius + 1))
    if extra_offsets:
        offsets.extend(extra_offsets)

    for name, t0 in seeds.items():
        for dt in offsets:
            t = (t0 + dt) % LO
            t_candidates.add(t)

    print(f"Seeds: {len(seeds)}")
    for name in sorted(seeds):
        print(f"  {name:24} = {seeds[name]}")
    print(f"Radius ±{radius} -> {len(t_candidates):,} unique t in [0, 2^134)")
    print(f"Target: d in [{LO}, {TOP}], check d*G == P")
    print()

    t0 = time.perf_counter()
    tested = 0
    for t in sorted(t_candidates):
        d = LO + t
        if d > TOP:
            continue
        tested += 1
        if ec_match(d):
            elapsed = time.perf_counter() - t0
            print("=" * 72)
            print("MATCH: d*G == P")
            print(f"  d     = {d}")
            print(f"  d hex = {hex(d)}")
            print(f"  t     = d - 2^134 = {t}")
            print(f"  tested {tested:,} / {len(t_candidates):,} in {elapsed:.1f}s")
            k_tx = (pow(S, -1, N) * (Z + R * d)) % N
            print(f"  k_tx  = {k_tx}")
            print(f"  k_tx*G.x mod N == r? {((k_tx * G).x() % N) == R}")
            return d
        if tested % 500_000 == 0 and tested:
            rate = tested / (time.perf_counter() - t0)
            print(f"  ... {tested:,} tested ({rate:,.0f}/s)")

    elapsed = time.perf_counter() - t0
    print(f"No match in {tested:,} candidates ({elapsed:.1f}s, {tested/elapsed:,.0f}/s)")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="P135 k-lane band scan (EC-gated)")
    parser.add_argument(
        "--radius",
        type=int,
        default=262_144,
        help="±window around each seed mod 2^134 (default 262144)",
    )
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Also run radius 2^20 after default pass",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("P135 K-LANE BAND SCAN")
    print("=" * 72)

    found = scan(args.radius)
    if found is None and args.wide:
        print()
        print("--- wide pass radius 2^20 ---")
        found = scan(1 << 20)

    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
