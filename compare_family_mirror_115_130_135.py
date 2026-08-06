#!/usr/bin/env python3
"""Compare family bridge + mirror defect: P115 (solved+d+k), P130 (d only), P135 (open)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_GX,
    N,
    P115_D,
    P115_K,
    P115_OFFSET_BITS,
    PuzzleConfig,
    apply_puzzle_defaults,
    all_cube_roots_mod_p,
    delta,
    p,
    puzzle_band,
    y_even,
)
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402

P130_D = 1103873984953507439627945351144005829577


def pubkey_from_d(d: int) -> tuple[int, int]:
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    return int.from_bytes(pub[1:33], "big"), int.from_bytes(pub[33:65], "big")


def px_triple_from_py(py: int) -> list[int]:
    c = (py * py - 7) % p
    return sorted(all_cube_roots_mod_p(c))


def rx_triple_from_ry(ry: int) -> list[int]:
    c = (ry * ry - 7) % p
    return sorted(all_cube_roots_mod_p(c))


def analyze(n: int, known_d: int | None = None, known_k: int | None = None) -> dict:
    cfg = PuzzleConfig(puzzle_num=n, known_d=known_d, known_k=known_k)
    apply_puzzle_defaults(cfg)

    if n == 130:
        px0, py0 = pubkey_from_d(P130_D)
        rsz = PUZZLE_RSZ[130]
        r_pt = recover_r_point_from_sig(rsz.r)
        if not r_pt:
            raise RuntimeError("cannot recover R from P130 signature r")
        _, ry = r_pt
        px_roots = px_triple_from_py(py0)
        rx_roots = rx_triple_from_ry(ry)
        cfg.Px = px_roots
        cfg.rx = rx_roots
        cfg.Py = py0
        cfg.ry = ry
        cfg.Gx = list(DEFAULT_GX)
        cfg.row = px_roots.index(px0)
        cfg.known_d = P130_D
        cfg.known_k = None

    st = bridge_state(cfg)
    lo, hi, top = puzzle_band(n)
    af = st["af"]
    oitc = st["oitc"]
    lns = st["lambda_ns"]
    row = cfg.row
    lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, p)) % p
    lam_n_row = lns[row]
    fam = (lns[0] * lns[1] * lns[2]) % N
    off = af.offset_shelf2
    terms = dict(st["terms"])
    hits = [(name, v) for name, v in terms.items() if off is not None and v == off]

    d_val = known_d or cfg.known_d
    m = None
    if d_val and cfg.known_k:
        m = (d_val * pow(cfg.known_k, -1, N)) % N
    elif n == 130 and d_val:
        # bridge m = d*k^-1 needs k — report RSZ-only partials
        rsz = PUZZLE_RSZ[130]
        m_partial_z = (rsz.z * pow(rsz.s, -1, N)) % N  # NOT k; pipeline lane only

    return {
        "n": n,
        "row": row,
        "d": d_val,
        "k": cfg.known_k,
        "m_dk": m,
        "Px_row": cfg.Px[row],
        "rx_row": cfg.rx[row],
        "shelf2": oitc.shelf2,
        "shelf3": oitc.shelf3,
        "shelf_y": oitc.shelf_y,
        "offset": off,
        "offset_bits": af.offset_bits,
        "gap_mod_lo": (lam_n_row - lam_p) % lo,
        "Lambda_p_row": lam_p,
        "Lambda_N_row": lam_n_row,
        "Lambda_N_family": fam,
        "defect_lo": (delta + lo) % N,
        "defect_hi": (delta + top) % N,
        "mirror_lo": N - (hi + 1),
        "mirror_hi": N - lo,
        "lo": lo,
        "term_hits": hits,
        "C_floor": oitc.c_floor,
        "d_cube_lift2": oitc.d_cube_lift2,
        "epsilon_p": (cfg.Px[row] * pow(lam_p, -1, p) * pow(cfg.rx[row], -1, p)) % p,  # should be 1
    }


def main() -> None:
    r115 = analyze(115, P115_D, P115_K)
    r130 = analyze(130)
    r135 = analyze(135)

    print("FAMILY BRIDGE + MIRROR DEFECT — P115 vs P130 vs P135\n")

    hdr = (
        "puzzle",
        "row",
        "offset_bits",
        "H-10?",
        "shelf2-lo bits",
        "gap%LO bits",
        "Lambda_N_family bits",
    )
    print("\t".join(hdr))
    for r in (r115, r130, r135):
        lo = r["lo"]
        print(
            "\t".join(
                str(x)
                for x in (
                    r["n"],
                    r["row"],
                    r["offset_bits"] if r["offset_bits"] is not None else "—",
                    "Y" if r["offset_bits"] == r["n"] - 10 else "N",
                    (r["shelf2"] - lo).bit_length(),
                    r["gap_mod_lo"].bit_length(),
                    r["Lambda_N_family"].bit_length(),
                )
            )
        )

    print("\n--- P115 (solved, d+k) ---")
    print(f"  d           = {r115['d']}")
    print(f"  k           = {r115['k']}")
    print(f"  m = d*k^-1  = {r115['m_dk']}")
    print(f"  shelf2      = {r115['shelf2']}")
    print(f"  offset      = {r115['offset']}  ({r115['offset_bits']} bits)")
    print(f"  bridge term hits for offset: {r115['term_hits'][:5]}")

    print("\n--- P130 (d only, no k) ---")
    print(f"  d           = {r130['d']}")
    print(f"  shelf2      = {r130['shelf2']}")
    print(f"  offset      = {r130['offset']}  ({r130['offset_bits']} bits)")
    print(f"  H-10 pred   = {130 - 10} bits -> match={r130['offset_bits'] == 120}")
    print(f"  bridge term hits: {r130['term_hits'][:5]}")
    rsz = PUZZLE_RSZ[130]
    k_from_r_only = rsz.r  # wrong as k; show user cannot close ECDSA without k
    print(f"  RSZ r (tx)    = {rsz.r}")
    print(f"  NOTE: without k, m=d*k^-1 and ECDSA back-solve for k are OPEN")

    print("\n--- P135 (open, RSZ only) ---")
    print(f"  shelf2      = {r135['shelf2']}")
    print(f"  shelf2 mod LO = {r135['shelf2'] % r135['lo']}")
    print(f"  offset      = UNKNOWN (no d)")
    print(f"  if H-10 law: expect ~125-bit offset from shelf2")
    print(f"  defect window: [{r135['defect_lo']}, {r135['defect_hi']}]")
    print(f"  mirror scalars: LO'={r135['mirror_lo']}, HI'={r135['mirror_hi']}")

    print("\n--- Cross-puzzle residues mod LO (correlation) ---")
    for label, r in [("P115", r115), ("P130", r130), ("P135", r135)]:
        lo = r["lo"]
        dmod = (r["d"] % lo) if r["d"] else None
        print(f"  {label}: (d-shelf2)%LO = {r['offset']}")
        print(f"         gap%LO         = {r['gap_mod_lo']}")
        if dmod is not None:
            print(f"         d%LO bits      = {dmod.bit_length()}")

    print("\n--- What P135 is missing vs P115 ---")
    print("  1. Known d  -> cannot verify shelf2+offset or rank bridge terms")
    print("  2. Known k  -> cannot verify m=d*k^-1, true R=kG vs rx triple")
    print("  3. P115 offset hits a named bridge term; P135 must discover which term")
    print(f"  4. P115 offset_bits={P115_OFFSET_BITS} (= puzzle_height - 10)")
    if r130["offset_bits"]:
        print(f"     P130 offset_bits={r130['offset_bits']} -> {'CONFIRMS' if r130['offset_bits']==120 else 'BREAKS'} H-10 on middle puzzle")


if __name__ == "__main__":
    main()
