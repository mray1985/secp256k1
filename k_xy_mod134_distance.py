#!/usr/bin/env python3
"""
k_x / k_y → mod 2^134, +2^134, mod (2^135-1) then distance to priv d.

Transforms (per user spec):
  r134      = k mod 2^134
  result1   = r134 + 2^134
  result2   = k mod (2^135 - 1)

Distance to d: |d - result| and (d - result) mod LO circular.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import PUZZLE_LIST, build_config  # noqa: E402
from ecdlp_full_pipeline import N, p, puzzle_band  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

M134 = 1 << 134
MTOP = (1 << 135) - 1


def puzzle_k_transforms(n: int, k: int) -> dict:
    """Per-puzzle mod convention (see ARCHIVE/PUZZLE_MOD_CONVENTION.md).

    Puzzle N (range height), LO = 2^(N-1), TOP = 2^N - 1:
      r1 floor_lift     = (k mod 2^(N-1)) + 2^(N-1)   always in [LO, TOP]
      r2 height_residue = k mod (2^N - 1), lifted into [LO, TOP] when below LO
    """
    lo = 1 << (n - 1)
    top = (1 << n) - 1
    r1 = (k % lo) + lo
    r2_raw = k % top
    if r2_raw == 0:
        r2 = top
    elif r2_raw < lo:
        r2 = r2_raw + lo
    else:
        r2 = r2_raw
    return {
        "k": k,
        "puzzle_n": n,
        "lo": lo,
        "top": top,
        "mod_2_n_m1": k % lo,
        "floor_lift": r1,
        "height_residue": r2,
        "height_residue_raw": r2_raw,
        # legacy P135 names
        "mod_2_134": k % M134 if n == 135 else k % lo,
        "plus_2_134": r1 if n == 135 else (k % lo) + lo,
        "mod_2_135_m1": r2 if n == 135 else r2,
    }


def transforms(k: int, *, puzzle_n: int = 135) -> dict:
    return puzzle_k_transforms(puzzle_n, k)

# P135 barcode / pipeline scalars (pubkey-x lane)
P135_K_PX = 19089036453356401353257357002647987614981495902151757130742235757133693952525
P135_K_PY = 90508964219557991953548570402867934097841441951106365697884749206559245429888
P135_PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
P135_PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800


def map_p_to_n(k_mod_p: int) -> int:
    return (N * k_mod_p) // p




def dist_row(d: int, t: dict, lo: int) -> dict:
    r1, r2 = t["plus_2_134"], t["mod_2_135_m1"]
    d1 = abs(d - r1)
    d2 = abs(d - r2)
    # circular mod LO (for band-relative view)
    c1 = min((d - r1) % lo, lo - (d - r1) % lo) if lo else d1
    c2 = min((d - r2) % lo, lo - (d - r2) % lo) if lo else d2
    return {
        "dist_result1": d1,
        "dist_result1_bits": d1.bit_length(),
        "dist_result2": d2,
        "dist_result2_bits": d2.bit_length(),
        "circ_result1_mod_lo": c1,
        "circ_result1_bits": c1.bit_length(),
        "circ_result2_mod_lo": c2,
        "circ_result2_bits": c2.bit_length(),
        "result1_in_band": lo <= r1 < (lo * 2),
        "result2_in_band": lo <= r2 < (lo * 2),
    }


def bridge_k_pair(cfg) -> tuple[int, int, int, int]:
    """Return k_x_map, k_y_same_map, k_y_opp_map, Lambda_mod_p."""
    st = bridge_state(cfg)
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    py, ry = cfg.Py, cfg.ry
    assert py is not None and ry is not None
    lam_p = (px[row] * pow(rx[row], -1, p)) % p
    lam_y = (py * pow(ry, -1, p)) % p
    k_y_same = (lam_y * pow(lam_p, -1, p)) % p
    k_y_opp = (p - k_y_same) % p
    k_x_map = map_p_to_n(lam_p)
    k_y_same_map = map_p_to_n(k_y_same)
    k_y_opp_map = map_p_to_n(k_y_opp)
    return k_x_map, k_y_same_map, k_y_opp_map, lam_p


def main() -> None:
    keys = parse_53125()
    rows: list[dict] = []

    def process(n: int, d: int | None, label: str, k: int) -> None:
        lo, hi, _ = puzzle_band(n if n != 0 else 135)
        t = transforms(k)
        rec = {
            "puzzle": n,
            "source": label,
            "k_bits": k.bit_length(),
            **{f"k_{a}": v for a, v in t.items() if a != "k"},
        }
        if d is not None:
            rec.update(dist_row(d, t, lo if n != 0 else M134))
        rows.append(rec)

    # --- P135 fixed k scalars ---
    from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults

    c135 = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(c135)
    kx, ky_s, ky_o, _ = bridge_k_pair(c135)

    p135_sources = {
        "k_x_map floor(N*Lambda/p)": kx,
        "k_y_same_map floor(N*ky/p)": ky_s,
        "k_y_opp_map": ky_o,
        "barcode_k_Px": P135_K_PX,
        "barcode_k_Py": P135_K_PY,
    }

    print("=" * 80)
    print("P135 k transforms (d unknown) — mod 2^134 / +2^134 / mod(2^135-1)")
    print("=" * 80)
    print(f"{'source':<32} {'mod2^134':>22} {'+2^134':>22} {'mod(2^135-1)':>22}")
    for name, k in p135_sources.items():
        t = transforms(k)
        print(
            f"{name:<32} {t['mod_2_134']:>22} {t['plus_2_134']:>22} {t['mod_2_135_m1']:>22}"
        )

    # RSZ barcode k for P135
    rsz135 = PUZZLE_RSZ[135]
    sinv = pow(rsz135.s, -1, N)
    k_from_px = (rsz135.z + rsz135.r * P135_PX) % N
    k_from_px = (k_from_px * sinv) % N
    k_from_py = (rsz135.z + rsz135.r * P135_PY) % N
    k_from_py = (k_from_py * sinv) % N
    for name, k in [
        ("rsz_lane_k_Px", k_from_px),
        ("rsz_lane_k_Py", k_from_py),
    ]:
        t = transforms(k)
        print(f"{name:<32} {t['mod_2_134']:>22} {t['plus_2_134']:>22} {t['mod_2_135_m1']:>22}")

    print()
    print("=" * 80)
    print("Solved puzzles: distance from result1/result2 to priv d")
    print("(moduli fixed at 2^134 and 2^135-1 per your spec)")
    print("=" * 80)

    for n in PUZZLE_LIST:
        if n == 135 or n not in keys or keys[n].d == 0:
            continue
        d = keys[n].d
        try:
            cfg = build_config(keys[n])
            kx, ky_s, ky_o, _ = bridge_k_pair(cfg)
        except Exception as exc:
            print(f"P{n}: skip ({exc})")
            continue

        sources: dict[str, int] = {
            "k_x_map": kx,
            "k_y_same": ky_s,
            "k_y_opp": ky_o,
        }
        rsz = PUZZLE_RSZ.get(n)
        if rsz is not None:
            sinv = pow(rsz.s, -1, N)
            px = cfg.Px[cfg.row]
            py = cfg.Py or 0
            sources["rsz_k_Px"] = (rsz.z + rsz.r * px) % N * sinv % N
            sources["rsz_k_Py"] = (rsz.z + rsz.r * py) % N * sinv % N
            if rsz.k is not None:
                sources["ecdsa_k"] = rsz.k
            elif d:
                sources["ecdsa_k_recovered"] = (sinv * (rsz.z + rsz.r * d)) % N

        print(f"\n--- P{n}  d={d}  (d bits={d.bit_length()}) ---")
        print(f"{'source':<20} {'|d-r1|':>12} {'bits':>4}  {'|d-r2|':>12} {'bits':>4}  r1 in band?")
        for name, k in sources.items():
            t = transforms(k)
            dr = dist_row(d, t, M134)
            process(n, d, name, k)
            print(
                f"{name:<20} {dr['dist_result1']:>12} {dr['dist_result1_bits']:>4}  "
                f"{dr['dist_result2']:>12} {dr['dist_result2_bits']:>4}  "
                f"{'Y' if dr['result1_in_band'] else 'N'}"
            )

    out = ROOT / "ARCHIVE" / "k_xy_mod134_distance.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
