#!/usr/bin/env python3
"""P135 upper-gap point: Q = P - [U]G with U = 2^135 - 1.

Locked facts:
  Q = [d - U]G = -[g]G,  g = U - d,  2^134 <= d <= U
  (Q_x < G_x, Q_y > G_y)  — exact for this point; NOT a scalar threshold proof

Meaningful landmarks (scalar space):
  Q = O     <=>  d = U
  Q = -G    <=>  d = U - 1
  Q = -[2]G <=>  d = U - 2
  ...
  How far is Q from O, -G, -2G, ...  == upper-bound interval DLP

0 verified bits. Coordinate inequalities do not cut g.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.numbertheory import square_root_mod_prime

from dual_domain_wrap_tracer import (
    G_X,
    G_Y,
    N_MOD,
    P_MOD,
    subtract_points_with_trace,
)

P135_COMPRESSED = (
    "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16"
)
U = (1 << 135) - 1
L = 1 << 134  # band floor (half-open lower)

# User-locked Q (even-y branch)
Q_X_LOCKED = 52886041483769761904968341876867358442579522291679760649513667751265486773330
Q_Y_LOCKED = 63913543214727770248777694773511805483462696697028811296623304851008216065287


def recover_p135_affine() -> tuple[int, int]:
    """Affine P from compressed pubkey (parity from 02/03 prefix)."""
    raw = bytes.fromhex(P135_COMPRESSED)
    prefix, px = raw[0], int.from_bytes(raw[1:], "big")
    y2 = (pow(px, 3, P_MOD) + 7) % P_MOD
    y = square_root_mod_prime(y2, P_MOD)
    if prefix == 0x02 and (y & 1):
        y = P_MOD - y
    elif prefix == 0x03 and not (y & 1):
        y = P_MOD - y
    elif prefix not in (0x02, 0x03):
        raise ValueError(f"bad prefix {prefix:#x}")
    return px, y


def point_mul_g(k: int) -> tuple[int, int]:
    pt = SECP256k1.generator * (k % N_MOD)
    return pt.x(), pt.y()


def point_sub(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    curve = SECP256k1.curve
    pa = Point(curve, a[0], a[1], N_MOD)
    pb = Point(curve, b[0], b[1], N_MOD)
    r = pa + (-pb)
    return r.x(), r.y()


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 upper-gap Q = P-[U]G ledger")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("logs/wrap_tracer/p135_upper_gap_Q.json"),
    )
    args = ap.parse_args()

    px, py = recover_p135_affine()
    assert (py & 1) == 0, "compressed 02 requires even y"
    ug = point_mul_g(U)
    qx, qy = point_sub((px, py), ug)

    # Dual-domain p-wrap on the subtraction path (implementation ledger only)
    wrap = subtract_points_with_trace((px, py), ug)

    # Landmarks in scalar space (not coordinate thresholds)
    neg_g = (G_X, (-G_Y) % P_MOD)
    neg_2g = point_mul_g(N_MOD - 2)
    landmarks = {
        "Q_is_O": False,  # affine infinity not represented; Q is finite
        "Q_equals_neg_G": (qx, qy) == neg_g,
        "Q_equals_neg_2G": (qx, qy) == neg_2g,
        "meaning": {
            "Q=O": "d=U",
            "Q=-G": "d=U-1",
            "Q=-[2]G": "d=U-2",
            "Q=-[g]G": "g=U-d (upper gap)",
        },
    }

    # Wrong-branch trap: odd y (p-y) yields a different Q
    py_odd = P_MOD - py
    qx_wrong, qy_wrong = point_sub((px, py_odd), ug)

    payload: dict[str, Any] = {
        "object": "P135_upper_gap_Q",
        "status": "LOCKED_FACT_ZERO_BITS",
        "definition": {
            "U": U,
            "U_hex": hex(U),
            "Q": "P135 - [U]G",
            "scalar": "Q = [d-U]G = -[g]G with g=U-d",
            "band": "2^134 <= d <= U = 2^135-1",
        },
        "pubkey": {
            "compressed": P135_COMPRESSED,
            "Px": px,
            "Py_even": py,
            "Py_odd_p_minus_y": py_odd,
            "note": "Must use even Py for 02-prefix; file 'Py' fields sometimes store p-y",
        },
        "U_G": {"x": ug[0], "y": ug[1]},
        "Q": {"x": qx, "y": qy},
        "matches_locked_user_coords": qx == Q_X_LOCKED and qy == Q_Y_LOCKED,
        "vs_generator_thresholds": {
            "Qx_lt_Gx": qx < G_X,
            "Qy_gt_Gy": qy > G_Y,
            "pair": "(Qx < Gx, Qy > Gy)",
            "Gx": G_X,
            "Gy": G_Y,
            "warning": (
                "Exact for this point. As g changes by 1, coordinates of -[g]G "
                "do not move monotonically past Gx/Gy. Inequalities do NOT prove "
                "a scalar threshold on g."
            ),
        },
        "better_object": (
            "How far is Q from O, -G, -2G, ... in scalar space? "
            "That is the upper-bound interval discrete-log problem."
        ),
        "landmarks": landmarks,
        "wrong_y_branch_Q": {
            "x": qx_wrong,
            "y": qy_wrong,
            "equals_locked": False,
            "note": "Using odd y (p-y) as if it were Py produces a different Q",
        },
        "p_wrap_on_P_minus_UG": {
            "operation": wrap.get("operation"),
            "p_wrap_event": wrap.get("p_wrap_event"),
            "n_wrap": None,
            "note": "N-wrap unknown: d unknown. p-wrap is affine-path only.",
        },
        "band_floor_contrast": {
            "L": L,
            "L_hex": hex(L),
            "usual_S01": "Q_floor = P - [L]G = [d-L]G with u=d-L in [0, 2^134)",
            "upper_gap": "Q = P - [U]G = -[g]G with g=U-d in [0, 2^134)",
            "relation": "u + g = U - L = 2^134 - 1",
        },
        "verified_bits": 0,
    }

    # Consistency: u+g = 2^134-1 when both defined
    payload["band_floor_contrast"]["u_plus_g"] = U - L

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("P135 upper-gap Q = P - [U]G")
    print(f"  match locked coords: {payload['matches_locked_user_coords']}")
    print(f"  (Qx < Gx, Qy > Gy): {payload['vs_generator_thresholds']['pair']}")
    print(f"  Qx < Gx: {payload['vs_generator_thresholds']['Qx_lt_Gx']}")
    print(f"  Qy > Gy: {payload['vs_generator_thresholds']['Qy_gt_Gy']}")
    print(f"  Q == -G: {landmarks['Q_equals_neg_G']}")
    print(f"  verified_bits: 0")
    print(f"wrote {args.output}")
    return 0 if payload["matches_locked_user_coords"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
