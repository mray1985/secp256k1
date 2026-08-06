#!/usr/bin/env python3
"""
EXHIBIT: defect_exponent — three-ceiling crack chain for secp256k1.

Writes ONLY under ARCHIVE/briefcase/real/ (no overwrite of other exhibits).
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 80

p = Decimal(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F)
N = Decimal(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
TWO256 = Decimal(1 << 256)
DELTA = p - N
BASE = TWO256 - p  # 2^32 + 977

PACKET_P = Decimal(
    "0.07954633649946046255450180288304075379977001785594624365740374798873"
    "7825607683797376362420847353351108638651635660059457338972369055727427"
    "831496239538405074"
)

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "real"


def main() -> int:
    assert BASE == Decimal(2**32 + 977)
    assert DELTA == Decimal(432420386565659656852420866390673177326)

    defect_exp = DELTA.ln() / BASE.ln()
    shell4 = BASE**4
    ratio = DELTA / shell4
    extra = defect_exp - 4
    assert abs(BASE**extra - ratio) < Decimal("1e-40")
    assert abs(BASE**defect_exp - DELTA) < Decimal("1")

    exhibit = {
        "exhibit": "fourth_power_defect_shell",
        "aliases": ["defect_exponent"],
        "location": "ARCHIVE/briefcase/real/",
        "verdict": {
            "status": "VERIFIED",
            "class": "modulus-construction scale (not GAP_x/GAP_y, not d)",
            "private_key_answer": False,
            "equivalent_to_Lambda_N_GAP": False,
            "ruler_not_key": True,
        },
        "relationship": "p - N = base_defect^4 * correction",
        "packet_rewrite": "packet*(p-N) = packet * base_defect^4 * correction",
        "ceilings": {
            "two256_minus_p": str(BASE),
            "base": "2^32 + 977",
            "p_minus_N": str(DELTA),
            "defect_exp": format(defect_exp, "f"),
            "shell_exponent": 4,
            "correction_exponent": format(extra, "f"),
            "correction_multiplier": format(ratio, "f"),
            "shell4": str(int(shell4)),
        },
        "identities": {
            "BASE_pow_defect_exp_equals_DELTA": True,
            "DELTA_equals_shell4_times_ratio": True,
            "DELTA_equals_BASE_pow_4_plus_extra": True,
        },
        "packet_p135": {
            "packet_p": str(PACKET_P),
            "packet_p_times_DELTA": format(PACKET_P * DELTA, "f"),
            "packet_p_times_BASE_pow4": format(PACKET_P * shell4, "f"),
            "packet_p_times_shell_gap": format(PACKET_P * (DELTA - shell4), "f"),
            "packet_p_times_BASE_pow_extra": format(PACKET_P * (BASE**extra), "f"),
        },
        "three_ceiling_chain": [
            "2^256",
            "defect = 2^32+977",
            "p",
            "defect = (2^32+977)^4.0108031509... = p-N",
            "N",
        ],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(exhibit, indent=2)
    paths = [
        OUT / "exhibit_fourth_power_defect_shell.json",
        OUT / "exhibit_defect_exponent.json",  # alias copy
    ]
    for path in paths:
        path.write_text(text, encoding="utf-8")
    print("EXHIBIT fourth_power_defect_shell: VERIFIED")
    print(f"  BASE = {int(BASE)} = 2^32+977")
    print(f"  defect_exp = {defect_exp}")
    print(f"  BASE^4 * correction = DELTA")
    print(f"  wrote {paths[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
