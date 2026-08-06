#!/usr/bin/env python3
"""
Fractional hex lens — right side of the decimal point.

H = hex digits (not a magic variable).
0x.H = fractional bit placement = int(H,16) / 16^{len(H)}
     = int(H,16) / 2^{4*len(H)}

For 256-bit objects (64 hex digits):
  frac_hex_256(v) = v / 2^256

Coordinate packets still:
  stitch x.y  then  normalize / p
  (decimal stitch is explicit; do not promote stitch to a giant int first)

Writes ONLY under ARCHIVE/briefcase/ecdlp_range/
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import N, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "ecdlp_range"
TWO256 = 1 << 256


def hex_digits(v: int, width: int = 64) -> str:
    """Zero-padded hex digit string H (no 0x prefix)."""
    return f"{v:0{width}x}"


def frac_hex(H: str) -> Decimal:
    """
    0x.H = int(H,16) / 16^{len(H)} = int(H,16) / 2^{4*len(H)}
    """
    H = H.lower().replace("0x", "").replace(".", "")
    if not H:
        return Decimal(0)
    return Decimal(int(H, 16)) / (Decimal(16) ** len(H))


def frac_hex_256(v: int) -> Decimal:
    """Fractional placement of a ≤256-bit value under the binary roof."""
    if v < 0 or v >= TWO256:
        v = v % TWO256
    return Decimal(v) / Decimal(TWO256)


def frac_hex_demo_fad() -> dict:
    H = "FAD"
    val = frac_hex(H)
    # binary fraction bits
    n = int(H, 16)
    bits = f"{n:0{4*len(H)}b}"
    return {
        "H": H,
        "meaning": "hex digits only — not a magic constant",
        "whole_wrong_lens": int(H, 16),
        "fractional_hex": f"0x.{H}",
        "fractional_binary": f"0b.{bits}",
        "decimal_fraction": format(val, "f"),
        "formula": "int(0xFAD)/16^3 = 4013/4096",
        "matches_tail_979736328125": str(val).endswith("979736328125")
        or format(val, "f").endswith("979736328125"),
    }


def decimal_stitch_packet(px: int, y_digits: int) -> Decimal:
    """Existing packet lens: Decimal(str(Px)+'.'+str(Y)) / p."""
    return Decimal(f"{px}.{y_digits}") / Decimal(p)


def process_puzzle(n: int, e) -> dict:
    rec: dict = {
        "puzzle": n,
        "solved": e.solved and e.private_key > 0,
        "has_pubkey": bool(e.public_key),
    }
    if not e.public_key:
        rec["status"] = "NO_PUBKEY"
        return rec

    px, py = pubkey_xy(e.public_key)
    pmy = (p - py) % p

    # Right lens: fractional hex placement under 2^256
    Hx = hex_digits(px)
    Hy = hex_digits(py)
    Hpmy = hex_digits(pmy)

    rec["status"] = "OK"
    rec["fractional_hex_lens"] = {
        "Px": {
            "H": Hx,
            "wrong_lens_whole_int": str(px),
            "right_lens_0x_dot_H": f"0x.{Hx}",
            "frac_hex_256": format(frac_hex_256(px), "f"),
            "equals_Px_over_2_256": True,
        },
        "Py": {
            "H": Hy,
            "frac_hex_256": format(frac_hex_256(py), "f"),
        },
        "p_minus_y": {
            "H": Hpmy,
            "frac_hex_256": format(frac_hex_256(pmy), "f"),
        },
    }

    # Packet: stitch then normalize (decimal stitch explicit)
    rec["packet"] = {
        "stitch_decimal": f"{px}.{pmy}",
        "normalize_by_p": format(decimal_stitch_packet(px, pmy), "f"),
        "note": "stitch x.y first, then / p — do not promote stitch to a giant int",
    }

    # Compare: frac_hex_256(Px) vs decimal packet (different geometries)
    rec["lens_contrast"] = {
        "frac_hex_256_Px": format(frac_hex_256(px), "f"),
        "decimal_packet_pmy_over_p": format(decimal_stitch_packet(px, pmy), "f"),
        "frac_hex_256_Px_over_p_field": format(Decimal(px) / Decimal(p), "f"),
        "note": (
            "frac_hex_256 = placement under 2^256 roof; "
            "Px/p = placement under field prime; "
            "decimal stitch packet = digit-concatenation geometry (different silhouette)"
        ),
    }

    if e.solved and e.private_key > 0:
        d = e.private_key
        q = (N - d) % N
        rec["scalar_fractional_hex"] = {
            "d": {
                "H": hex_digits(d),
                "frac_hex_256": format(frac_hex_256(d), "f"),
                "in_d_window_bits": True,
            },
            "N_minus_d": {
                "H": hex_digits(q),
                "frac_hex_256": format(frac_hex_256(q), "f"),
                "note": "N-mirror placement under 2^256 roof",
            },
        }
    return rec


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    demo = frac_hex_demo_fad()

    catalog = load_catalog()
    rows = [process_puzzle(n, catalog[n]) for n in range(1, 161)]

    # P135 spotlight
    p135 = next(r for r in rows if r["puzzle"] == 135)

    payload = {
        "exhibit": "fractional_hex_lens",
        "location": "ARCHIVE/briefcase/ecdlp_range/",
        "H_means": "hex digits only — not a magic variable that changes from 1",
        "demo_FAD": demo,
        "rules": {
            "wrong_lens": "H as whole number → giant int → decimal",
            "right_lens": "0x.H as fractional bit placement",
            "one_hex_digit": "4 binary bits",
            "full_256": "0x.<64 hex digits> = int(H,16) / 2^256",
            "packet": "stitch x.y first, then normalize / p",
            "phrase": (
                "H does not change. The decimal point changes the courtroom."
            ),
        },
        "P135": p135,
        "puzzles": rows,
        "ruling": (
            "Seeing the wrong binary structure (whole int vs fractional placement) "
            "scrambles pattern work. Always place hex after the point for placement "
            "geometry; stitch packets before normalizing."
        ),
    }

    (OUT / "fractional_hex_lens.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# fractional_hex_lens",
        "",
        "## H is just the hex digits",
        "",
        "```text",
        "H does not change.",
        "The decimal point changes the courtroom.",
        "",
        "0x1  = 1",
        "0x.1 = 1/16 = 0.0625",
        "```",
        "",
        "## Demo: .FAD",
        "",
        f"- fractional hex: `{demo['fractional_hex']}`",
        f"- fractional binary: `{demo['fractional_binary']}`",
        f"- decimal: `{demo['decimal_fraction']}`",
        f"- wrong lens (whole): `{demo['whole_wrong_lens']}`",
        "",
        "## 256-bit rule",
        "",
        "```text",
        "0x.<64 hex digits> = int(H,16) / 2^256 = v / 2^256",
        "```",
        "",
        "## Packets",
        "",
        "```text",
        "stitch first:   x.y",
        "then normalize: x.y / p",
        "```",
        "",
        "Do not promote the stitch to a giant integer first.",
        "",
        "## P135 under the right lens",
        "",
    ]
    if p135.get("fractional_hex_lens"):
        fx = p135["fractional_hex_lens"]["Px"]
        lines.append(f"- Px as `0x.H`: `{fx['right_lens_0x_dot_H'][:20]}…`")
        lines.append(f"- frac_hex_256(Px): `{fx['frac_hex_256']}`")
        lines.append(
            f"- decimal packet / p: `{p135['packet']['normalize_by_p'][:42]}…`"
        )
        lines.append(
            f"- Px/p (field placement): `{p135['lens_contrast']['frac_hex_256_Px_over_p_field']}`"
        )

    lines.extend([
        "",
        "## Ruling",
        "",
        "Wrong binary structure (whole-int silhouette) would scramble every pattern.",
        "Right structure: fractional bitstring after the point, then normalize.",
        "",
        "Judge Popcorn: **same digits, different side of the dot — different courtroom.**",
        "",
        "Rebuild: `python build_fractional_hex_lens.py`",
        "",
    ])

    (OUT / "fractional_hex_lens.md").write_text("\n".join(lines), encoding="utf-8")

    # README pointer
    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if "fractional_hex" not in prev:
        readme.write_text(
            prev.rstrip()
            + "\n\n| `fractional_hex_lens.*` / `exhibit_fractional_hex_lens.md` | "
            "0x.H fractional bit placement |\n\n"
            "```text\npython build_fractional_hex_lens.py\n```\n",
            encoding="utf-8",
        )

    print("FAD demo:", demo["decimal_fraction"], demo["fractional_binary"])
    print("P135 frac_hex_256(Px):", p135["fractional_hex_lens"]["Px"]["frac_hex_256"][:40])
    print("P135 packet/p:", p135["packet"]["normalize_by_p"][:40])
    print(f"wrote {OUT / 'fractional_hex_lens.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
