#!/usr/bin/env python3
"""
secp256r1 / NIST P-256 control catalog.

Writes ONLY under ARCHIVE/briefcase/R1/ — does not touch k1 exhibits.

Purpose: contrast curve for packet/defect bookkeeping.
NOT for β x-slot machinery (a = -3; no shared-y β orbit).
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import NIST256p

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "R1"

curve = NIST256p.curve
gen = NIST256p.generator

p = curve.p()
n = gen.order()
a = curve.a() % p
b = curve.b()
Gx = gen.x()
Gy = gen.y()

BITS = 256
TWO_BITS = 1 << BITS
FIELD_DEFECT = TWO_BITS - p  # = 2^224 - 2^192 - 2^96 + 1
ORDER_DEFECT = p - n  # positive for P-256
ORDER_CEILING_DEFECT = TWO_BITS - n  # = field_defect + order_defect


def cube_roots_of_unity(mod: int) -> list[int]:
    """Nontrivial β with β³ ≡ 1 mod p, if any (needs p ≡ 1 mod 3)."""
    if (mod - 1) % 3 != 0:
        return []
    # find generator of subgroup of order 3: g^{(p-1)/3}
    # try random bases until β ≠ 1
    import random

    random.seed(1)
    for _ in range(200):
        g = random.randrange(2, mod - 1)
        beta = pow(g, (mod - 1) // 3, mod)
        if beta != 1 and pow(beta, 3, mod) == 1:
            return sorted({beta, pow(beta, 2, mod)})
    return []


def on_curve(x: int, y: int) -> bool:
    return (pow(y, 2, p) - (pow(x, 3, p) + a * x + b)) % p == 0


def y_sq(x: int) -> int:
    return (pow(x, 3, p) + a * x + b) % p


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    betas = cube_roots_of_unity(p)
    has_beta = len(betas) > 0

    # β-orbit test on Gx: for a=0 curves, y²(x)=y²(βx). For P-256 a=-3, expect fail.
    beta_orbit = []
    shared_y_sq = True
    if has_beta:
        y2_g = y_sq(Gx)
        for beta in betas:
            bx = (beta * Gx) % p
            y2b = y_sq(bx)
            same = y2b == y2_g
            shared_y_sq = shared_y_sq and same
            beta_orbit.append({
                "beta": str(beta),
                "beta_Gx": str(bx),
                "y_sq_beta_Gx": str(y2b),
                "y_sq_equals_y_sq_Gx": same,
            })
    else:
        shared_y_sq = False

    # packets (both y and p-y branches)
    packet_y = Decimal(f"{Gx}.{Gy}")
    packet_pmy = Decimal(f"{Gx}.{(p - Gy) % p}")
    packet_p = packet_y / Decimal(p)
    packet_n = packet_y / Decimal(n)
    packet_2 = packet_y / Decimal(TWO_BITS)
    packet_p_pmy = packet_pmy / Decimal(p)

    floor_p = int(packet_p * Decimal(p))
    floor_n = int(packet_p * Decimal(n))
    map_p_to_n_gx = (n * Gx) // p
    off_by = floor_n - map_p_to_n_gx

    # Rulers on the same gaps (note: base and value order matter):
    #   field-base:     log_(2^256 − p)(p − n)     ≈ 0.5628
    #   order-ceiling:  log_(2^256 − n)(p − n)     ≈ 0.5628  (≈ field-base; ocd ≈ fd)
    #   reciprocal:     log_(p − n)(2^256 − n)     ≈ 1.7768  (how ceiling gap scales vs inner gap)
    fd = Decimal(FIELD_DEFECT)
    od = Decimal(abs(ORDER_DEFECT))
    ocd = Decimal(ORDER_CEILING_DEFECT)
    assert ORDER_CEILING_DEFECT == FIELD_DEFECT + ORDER_DEFECT

    field_base_exp = od.ln() / fd.ln() if fd > 1 and od > 1 else None
    order_ceiling_exp = od.ln() / ocd.ln() if ocd > 1 and od > 1 else None
    reciprocal_ceiling_exp = ocd.ln() / od.ln() if ocd > 1 and od > 1 else None
    reciprocal_field_exp = fd.ln() / od.ln() if fd > 1 and od > 1 else None
    # alias used below
    defect_exp = field_base_exp

    # compare to k1-style "fourth power shell" — does order_defect ≈ field_defect^4?
    shell4 = FIELD_DEFECT**4
    if shell4:
        correction = Decimal(abs(ORDER_DEFECT)) / Decimal(shell4)
    else:
        correction = None

    # field_defect closed form check
    fd_closed = (1 << 224) - (1 << 192) - (1 << 96) + 1
    assert FIELD_DEFECT == fd_closed

    constants = {
        "curve_name": "secp256r1 / NIST P-256",
        "folder": "ARCHIVE/briefcase/R1/",
        "role": "control curve — packet/defect only, not β-slot machinery",
        "equation": "y^2 = x^3 - 3x + b mod p",
        "a": str(a),
        "a_signed": -3,
        "b": str(b),
        "p": str(p),
        "n": str(n),
        "cofactor_h": 1,
        "bits": BITS,
        "Gx": str(Gx),
        "Gy": str(Gy),
        "G_on_curve": on_curve(Gx, Gy),
        "field_defect": str(FIELD_DEFECT),
        "field_defect_formula": "2^256 - p = 2^224 - 2^192 - 2^96 + 1",
        "order_defect": str(ORDER_DEFECT),
        "order_defect_formula": "p - n",
        "order_ceiling_defect": str(ORDER_CEILING_DEFECT),
        "order_ceiling_defect_formula": "2^256 - n = (2^256 - p) + (p - n)",
        "p_mod_3": p % 3,
        "has_beta_cube_root_of_unity": has_beta,
        "betas": [str(x) for x in betas],
        "beta_orbit_shares_y_sq_with_Gx": shared_y_sq,
        "beta_orbit": beta_orbit,
    }

    packet = {
        "branch_y": {
            "packet": str(packet_y),
            "packet_p": format(packet_p, "f"),
            "packet_n": format(packet_n, "f"),
            "packet_2_256": format(packet_2, "f"),
            "floor_packet_p_times_p": str(floor_p),
            "floor_packet_p_times_n": str(floor_n),
            "map_p_to_n_Gx": str(map_p_to_n_gx),
            "off_by_map_p_to_n": off_by,
            "matches_Gx_integer": floor_p == Gx,
        },
        "branch_p_minus_y": {
            "packet": str(packet_pmy),
            "packet_p": format(packet_p_pmy, "f"),
            "floor_packet_p_times_p": str(int(packet_p_pmy * Decimal(p))),
            "matches_Gx_integer": int(packet_p_pmy * Decimal(p)) == Gx,
        },
        "identity": "packet * p - packet * n = packet * (p - n)",
        "packet_times_order_defect": format(packet_p * Decimal(ORDER_DEFECT), "f"),
    }

    defect_ladder = {
        "ceilings": [
            "2^256",
            f"field_defect = {FIELD_DEFECT} = 2^224 - 2^192 - 2^96 + 1",
            "p",
            f"order_defect = {ORDER_DEFECT} = p - n",
            "n",
            f"order_ceiling_defect = {ORDER_CEILING_DEFECT} = 2^256 - n",
        ],
        "identity": "2^256 - n = (2^256 - p) + (p - n)",
        "exponents": {
            "field_base": {
                "formula": "log_(2^256 - p)(p - n)",
                "value": format(field_base_exp, "f") if field_base_exp is not None else None,
                "meaning": "how p-n scales against the field-prime gap under the 256-bit ceiling",
            },
            "order_ceiling_base": {
                "formula": "log_(2^256 - n)(p - n)",
                "value": format(order_ceiling_exp, "f") if order_ceiling_exp is not None else None,
                "meaning": (
                    "how p-n scales against the full ceiling-to-order gap; "
                    "nearly equal to field_base because 2^256-n ≈ 2^256-p"
                ),
            },
            "reciprocal_order_ceiling": {
                "formula": "log_(p - n)(2^256 - n)",
                "value": format(reciprocal_ceiling_exp, "f") if reciprocal_ceiling_exp is not None else None,
                "meaning": (
                    "how the full ceiling-to-order gap scales against the inner p-n gap; "
                    "this is the 1.7768... reading (reciprocal of order_ceiling_base)"
                ),
                "note": (
                    "If written as log_(2^256-n)(p-n) the value is ~0.5628, not 1.7768. "
                    "1.7768 is log_(p-n)(2^256-n) = 1 / log_(2^256-n)(p-n)."
                ),
            },
            "reciprocal_field": {
                "formula": "log_(p - n)(2^256 - p)",
                "value": format(reciprocal_field_exp, "f") if reciprocal_field_exp is not None else None,
                "meaning": "reciprocal of field_base; nearly equal to reciprocal_order_ceiling",
            },
        },
        "field_base_exp": format(field_base_exp, "f") if field_base_exp is not None else None,
        "order_ceiling_exp": format(order_ceiling_exp, "f") if order_ceiling_exp is not None else None,
        "reciprocal_order_ceiling_exp": (
            format(reciprocal_ceiling_exp, "f") if reciprocal_ceiling_exp is not None else None
        ),
        "field_defect_pow4": str(shell4),
        "correction_if_shell4": format(correction, "f") if correction is not None else None,
        "k1_style_fourth_power_shell": {
            "applies": False,
            "reason": (
                "secp256k1 has tiny field_defect (2^32+977) and order_defect ≈ field_defect^4.0108. "
                "P-256 field_defect is huge (~2^224); order_defect is smaller. "
                "correction = order_defect / field_defect^4 is ~0 — not a fourth-power echo."
            ),
            "correction": format(correction, "f") if correction is not None else None,
        },
        "note": "same defect (p-n), different ruler — change the ruler, change the exponent",
    }

    contrast_k1 = {
        "secp256k1": {
            "a": 0,
            "equation": "y^2 = x^3 + 7",
            "field_defect": "2^32 + 977",
            "order_defect": "p - N ≈ (2^32+977)^4.0108",
            "has_beta_slots": True,
            "y_model": "parity branches only; x has 3 β slots",
        },
        "secp256r1": {
            "a": -3,
            "equation": "y^2 = x^3 - 3x + b",
            "field_defect": "2^224 - 2^192 - 2^96 + 1",
            "order_defect": "p - n (small vs field_defect)",
            "has_beta_slots": False,
            "y_model": "no shared-y β orbit; packet/defect only",
        },
        "transfers": [
            "packet = Decimal(Gx.Gy) / p",
            "packet * p - packet * n = packet * (p - n)",
            "map_p_to_n vs floor(packet * n) off-by-one bookkeeping",
            "field_defect / order_defect ladder (different shape)",
        ],
        "does_not_transfer": [
            "β x-slot orbit with shared y^2",
            "fourth-power defect shell (B^4 * correction)",
            "Λ / β spend-line bridges (Bitcoin-specific ledger)",
        ],
    }

    catalog = {
        "exhibit": "R1_secp256r1_control_catalog",
        "constants": constants,
        "packet_G": packet,
        "defect_ladder": defect_ladder,
        "contrast_vs_secp256k1": contrast_k1,
        "verdict": {
            "status": "CATALOGUED",
            "beta_slot_machinery": False,
            "packet_defect_bookkeeping": True,
            "fourth_power_shell_like_k1": False,
            "role": "control curve — proves what disappears when a ≠ 0",
        },
    }

    (OUT / "catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    # markdown catalog
    lines = [
        "# R1 — secp256r1 / NIST P-256 control catalog",
        "",
        "Folder: `ARCHIVE/briefcase/R1/`",
        "",
        "**Role:** control curve for packet / modulus-defect bookkeeping.",
        "**Not** for β x-slot machinery (`a = -3`; no shared-y β orbit).",
        "",
        "Rebuild: `python build_r1_catalog.py`",
        "",
        "## Constants",
        "",
        "```text",
        "curve:  secp256r1 / NIST P-256",
        "form:   y² = x³ − 3x + b mod p",
        f"a:      -3  (mod p = {a})",
        f"b:      {b}",
        f"p:      {p}",
        f"n:      {n}",
        f"h:      1",
        f"Gx:     {Gx}",
        f"Gy:     {Gy}",
        f"G on curve: {on_curve(Gx, Gy)}",
        "```",
        "",
        "## Defect ladder",
        "",
        "```text",
        "2^256",
        f"  ↓ field_defect = 2^256 − p = {FIELD_DEFECT}",
        "     = 2^224 − 2^192 − 2^96 + 1",
        "p",
        f"  ↓ order_defect = p − n = {ORDER_DEFECT}",
        "n",
        "",
        f"2^256 − n = order_ceiling_defect = {ORDER_CEILING_DEFECT}",
        "         = (2^256 − p) + (p − n)",
        "```",
        "",
        "### Rulers (base order matters)",
        "",
        "| Label | Formula | Value |",
        "|-------|---------|-------|",
        f"| **field-base** | `log_(2^256 − p)(p − n)` | `{field_base_exp}` |",
        f"| **order-ceiling-base** | `log_(2^256 − n)(p − n)` | `{order_ceiling_exp}` |",
        f"| **reciprocal order-ceiling** | `log_(p − n)(2^256 − n)` | `{reciprocal_ceiling_exp}` |",
        f"| **reciprocal field** | `log_(p − n)(2^256 − p)` | `{reciprocal_field_exp}` |",
        "",
        "```text",
        "2^256 − p : how far the field prime sits below the 256-bit ceiling",
        "p − n     : how far the scalar order sits below the field prime",
        "2^256 − n : total ceiling gap down to the scalar order",
        "         = (2^256 − p) + (p − n)",
        "```",
        "",
        "Note: `1.7768…` is **not** `log_(2^256−n)(p−n)` (that is still `≈ 0.5628`).",
        "It is the reciprocal: `log_(p−n)(2^256−n) = 1 / log_(2^256−n)(p−n)`.",
        "",
        "Same gaps, different ruler. Change the ruler, change the exponent.",
        "",
        "**k1-style fourth-power shell?** `False`",
        "",
        f"`order_defect / field_defect^4` = `{correction}` (≈ 0 — not a shell echo)",
        "",
        "## β cube roots of unity",
        "",
        f"`p ≡ {p % 3} (mod 3)` → nontrivial β exists: **{has_beta}**",
        "",
    ]
    if has_beta:
        lines.append("β values exist, but **shared y² orbit fails** because `a ≠ 0`:")
        lines.append("")
        lines.append("```text")
        lines.append("(βx)³ − 3(βx) + b ≠ x³ − 3x + b   in general")
        lines.append("```")
        lines.append("")
        for row in beta_orbit:
            lines.append(
                f"- β=`…{row['beta'][-8:]}` y²(βGx)==y²(Gx)? **{row['y_sq_equals_y_sq_Gx']}**"
            )
        lines.append("")
        lines.append(f"**beta_orbit_shares_y_sq_with_Gx:** `{shared_y_sq}`")
    else:
        lines.append("No nontrivial cube root of unity mod p.")
    lines.extend([
        "",
        "## Packet (generator G)",
        "",
        "Branch `y` (primary for R1 catalog):",
        "",
        f"- packet_p = `{format(packet_p, 'f')}`",
        f"- floor(packet_p · p) = `{floor_p}` (matches Gx: `{floor_p == Gx}`)",
        f"- floor(packet_p · n) = `{floor_n}`",
        f"- map_p_to_n(Gx) = `{map_p_to_n_gx}`",
        f"- off_by_map_p_to_n = `{off_by}`",
        "",
        "Identity (transfers from k1):",
        "",
        "```text",
        "packet × p − packet × n = packet × (p − n)",
        "```",
        "",
        f"packet × (p−n) = `{format(packet_p * Decimal(ORDER_DEFECT), 'f')}`",
        "",
        "## What transfers vs secp256k1",
        "",
        "| Transfers | Does not transfer |",
        "|-----------|-------------------|",
        "| packet = Decimal(Gx.Gy)/p | β x-slot orbit with shared y² |",
        "| packet×(p−n) displacement | fourth-power defect shell |",
        "| map_p_to_n / floor drift | Λ / β spend-line bridges |",
        "| ceiling defect ladder (different shape) | Bitcoin RSZ ledger objects |",
        "",
        "## Verdict",
        "",
        "```text",
        "R1 = control courtroom",
        "packet/defect bookkeeping: YES",
        "β-slot geometry:            NO",
        "fourth-power shell (k1):    NO",
        "role: prove what disappears when a ≠ 0",
        "```",
        "",
        "Judge Popcorn: **same size cousin, different furniture. "
        "Use R1 to audit the ruler, not to move the β chairs.**",
        "",
    ])
    (OUT / "catalog.md").write_text("\n".join(lines), encoding="utf-8")

    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/R1 — secp256r1 / NIST P-256",
            "",
            "Control curve catalog. Does **not** overwrite k1 / `real/` exhibits.",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `catalog.md` / `.json` | Full R1 constants, packet, defect ladder, β-negative |",
            "",
            "Rebuild: `python build_r1_catalog.py`",
            "",
            "```text",
            "Use for:     packet/defect contrast vs secp256k1",
            "Do not use:  β slots, Λ bridges, Bitcoin RSZ",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print("R1 catalogued")
    print(f"  has_beta={has_beta} shared_y_sq={shared_y_sq}")
    print(f"  field_defect bits~{FIELD_DEFECT.bit_length()}")
    print(f"  order_defect bits~{ORDER_DEFECT.bit_length()}")
    print(f"  off_by_map_p_to_n={off_by}")
    print(f"  wrote {OUT / 'catalog.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
