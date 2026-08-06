#!/usr/bin/env python3
"""
EXHIBIT: coordinate_packet_shadow (P135)

Verifies the coordinate-packet p/N/2^256 identities and the off-by-one
vs map_p_to_n(Px). Does NOT touch Lambda_N / GAP_x / GAP_y.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 200

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DELTA = p - N
TWO256 = 1 << 256

# P135 pubkey x (compressed 02…)
Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 69440582532487379038177105219556131878098716909078780397935812212458092996863
P_MINUS_Y = (p - Py) % p

PACKET_P = Decimal(
    "0.07954633649946046255450180288304075379977001785594624365740374798873"
    "7825607683797376362420847353351108638651635660059457338972369055727427"
    "831496239538405074"
)

# Slightly different packet for binary ceiling (user trial)
PACKET_2 = Decimal(
    "0.07954633649946046255450180288304075379977001785594624365740374798873"
    "4875069406537743799106298763806661973809828622217933566852172005103163"
    "257072714691601734"
)

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "exhibit_coordinate_packet_shadow.json"


def map_p_to_n(x: int) -> int:
    """Integer-only map: floor(x * N / p)."""
    return (N * x) // p


def main() -> int:
    assert DELTA == 432420386565659656852420866390673177326

    field = PACKET_P * Decimal(p)
    field_int = int(field)
    field_frac = field - field_int
    assert field_int == Px, "packet_p * p integer part must be Px"

    frac_digits = format(field_frac, "f").split(".")[1]
    assert frac_digits.startswith(str(P_MINUS_Y)), (
        "fractional digits of packet_p*p must start with p-y branch"
    )

    scalar = PACKET_P * Decimal(N)
    scalar_int = int(scalar)
    integer_only = map_p_to_n(Px)
    assert scalar_int == integer_only + 1, (
        "coordinate-packet floor must be one above map_p_to_n(Px)"
    )

    defect = PACKET_P * Decimal(DELTA)
    assert abs((field - scalar) - defect) < Decimal("1e-40"), (
        "packet_p*(p-N) must equal field_packet - scalar_packet"
    )

    bin_ceil = PACKET_2 * Decimal(TWO256)
    assert int(bin_ceil) == Px, "packet_2 * 2^256 integer part must be Px"

    exhibit = {
        "exhibit": "coordinate_packet_shadow",
        "puzzle": 135,
        "verdict": {
            "status": "VERIFIED",
            "class": "coordinate bookkeeping",
            "equivalent_to_Lambda_N_GAP": False,
            "direct_d_k_recovery": False,
        },
        "maps": {
            "integer_only": {
                "formula": "floor(Px * N / p) = map_p_to_n(Px)",
                "value": str(integer_only),
            },
            "coordinate_packet": {
                "formula": "floor((Px.y) * N / p)",
                "value": str(scalar_int),
                "off_by_one_vs_integer_only": scalar_int - integer_only,
                "note": "decimal witness (p-y fraction) nudges floor over the line",
            },
        },
        "identities": {
            "packet_p": str(PACKET_P),
            "packet_p_times_p_int": str(field_int),
            "packet_p_times_N_int": str(scalar_int),
            "packet_p_times_DELTA_int": str(int(defect)),
            "DELTA": str(DELTA),
            "Px": str(Px),
            "p_minus_y": str(P_MINUS_Y),
        },
        "not_these": {
            "GAP_x": "Lambda_N - Lambda mod N",
            "GAP_y": "lambda_y_N - Lambda_N mod N",
            "reason": "bridge-ratio gaps; this exhibit is coordinate-packet displacement",
        },
    }
    OUT.write_text(json.dumps(exhibit, indent=2), encoding="utf-8")
    print("EXHIBIT coordinate_packet_shadow: VERIFIED")
    print(f"  map_p_to_n(Px)     = …{str(integer_only)[-4:]}")
    print(f"  floor(packet*N)    = …{str(scalar_int)[-4:]}  (+1)")
    print(f"  packet*p int == Px: {field_int == Px}")
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
