#!/usr/bin/env python3
"""
Patch: correct packet silhouette for every pubkey puzzle.

Right lens:
  stitch x.y as decimal placement (NOT a giant int first)
  → ~156-digit decimal number (len(str(Px)) + len(str(Y)))
  → then normalize:
       stitched / 2^256   (fixed binary placement)
       stitched / p       (coordinate packet / field)

Also hex stitch:
  0x.<64 hex Px><64 hex Y> = int(Hx+Hy,16) / 2^512

Primary branch: p−y (and y recorded).

Writes ONLY under ARCHIVE/briefcase/ecdlp_range/
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import N, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 120

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "ecdlp_range"
TWO256 = Decimal(1 << 256)
TWO512 = Decimal(1 << 512)


def stitch_decimal(px: int, y_digits: int) -> tuple[Decimal, str, int, int]:
    """
    Stitch as decimal placement: 'Px.Y'
    Returns (stitched Decimal, string, int_digits, frac_digits).
    """
    s_px = str(px)
    s_y = str(y_digits)
    s = f"{s_px}.{s_y}"
    return Decimal(s), s, len(s_px), len(s_y)


def stitch_hex(px: int, y_digits: int) -> tuple[Decimal, str]:
    """0x.<64 hex px><64 hex y> = int(Hx+Hy,16) / 2^512"""
    Hx = f"{px:064x}"
    Hy = f"{y_digits:064x}"
    H = Hx + Hy
    return Decimal(int(H, 16)) / TWO512, f"0x.{H}"


def branch_packet(px: int, y_digits: int, label: str) -> dict:
    stitched, stitched_s, n_int, n_frac = stitch_decimal(px, y_digits)
    total_digits = n_int + n_frac  # ~156
    hex_frac, hex_s = stitch_hex(px, y_digits)

    return {
        "branch": label,
        "silhouette": "decimal_stitch_then_normalize",
        "stitched_decimal_string": stitched_s,
        "stitched_decimal": format(stitched, "f"),
        "integer_digits": n_int,
        "fractional_digits": n_frac,
        "total_decimal_digits": total_digits,
        # three lenses — do not bleed
        "lens_fixed_binary": {
            "formula": "stitched / 2^256",
            "value": format(stitched / TWO256, "f"),
        },
        "lens_packet_field": {
            "formula": "stitched / p",
            "value": format(stitched / Decimal(p), "f"),
        },
        "lens_hex_stitch_512": {
            "formula": "0x.<Hx><Hy> = int(H,16) / 2^512",
            "hex": hex_s,
            "value": format(hex_frac, "f"),
        },
        # single-coordinate fixed placements (for contrast — NOT the packet)
        "not_the_packet": {
            "Px_over_2_256": format(Decimal(px) / TWO256, "f"),
            "Y_over_2_256": format(Decimal(y_digits) / TWO256, "f"),
            "Px_over_p": format(Decimal(px) / Decimal(p), "f"),
            "Y_over_p": format(Decimal(y_digits) / Decimal(p), "f"),
            "warning": "Px/p or Py/p alone is courtroom placement, not the stitched packet",
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    rows = []
    digit_totals = []

    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            rows.append({"puzzle": n, "status": "NO_PUBKEY"})
            continue
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        y_branch = branch_packet(px, py, "y")
        pmy_branch = branch_packet(px, pmy, "p_minus_y")
        digit_totals.append(pmy_branch["total_decimal_digits"])

        rec = {
            "puzzle": n,
            "status": "SOLVED" if e.solved and e.private_key > 0 else "UNSOLVED_PUBKEY",
            "Px": str(px),
            "Py": str(py),
            "p_minus_y": str(pmy),
            "primary_branch": "p_minus_y",
            "branch_y": y_branch,
            "branch_p_minus_y": pmy_branch,
            "primary_packet": {
                "stitched": pmy_branch["stitched_decimal_string"],
                "total_decimal_digits": pmy_branch["total_decimal_digits"],
                "x_y_over_2_256": pmy_branch["lens_fixed_binary"]["value"],
                "x_y_over_p": pmy_branch["lens_packet_field"]["value"],
            },
        }
        if e.solved and e.private_key > 0:
            d = e.private_key
            q = (N - d) % N
            rec["scalar_fixed_binary"] = {
                "d_over_2_256": format(Decimal(d) / TWO256, "f"),
                "N_minus_d_over_2_256": format(Decimal(q) / TWO256, "f"),
            }
        rows.append(rec)

    with_pub = [r for r in rows if r.get("status") != "NO_PUBKEY"]
    p135 = next(r for r in rows if r["puzzle"] == 135)

    payload = {
        "exhibit": "packet_silhouette_patch",
        "location": "ARCHIVE/briefcase/ecdlp_range/",
        "keeper": "H does not change. The decimal point changes the courtroom.",
        "patch": {
            "wrong": "promote x||y or H to whole int first",
            "right": "stitch x.y as placement, then / 2^256 or / p",
            "expected_digit_count": "~156 = len(str(Px)) + len(str(Y))",
            "observed_digit_counts": {
                "min": min(digit_totals) if digit_totals else None,
                "max": max(digit_totals) if digit_totals else None,
                "mean": sum(digit_totals) / len(digit_totals) if digit_totals else None,
            },
        },
        "three_lenses": {
            "fixed_binary": "stitched / 2^256   (= x.y / 2^256)",
            "packet_field": "stitched / p       (= x.y / p)",
            "hex_stitch_512": "0x.<Hx><Hy> / 2^512",
        },
        "P135_primary": p135.get("primary_packet"),
        "summary": {
            "pubkey_puzzles": len(with_pub),
            "all_have_stitched_packet": all(
                "primary_packet" in r for r in with_pub
            ),
        },
        "puzzles": rows,
    }

    (OUT / "packet_silhouette_patch.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    # per-puzzle compact files
    per = OUT / "packets"
    per.mkdir(exist_ok=True)
    for r in with_pub:
        n = r["puzzle"]
        (per / f"puzzle_{n:03d}_packet.json").write_text(
            json.dumps(r, indent=2), encoding="utf-8"
        )

    lines = [
        "# packet_silhouette_patch",
        "",
        "Patched silhouette for every pubkey puzzle.",
        "",
        "```text",
        "stitch:  x.y   (decimal placement, ~156 digits)",
        "then:    x.y / 2^256     fixed binary lens",
        "         x.y / p         packet / field lens",
        "",
        "Also:    0x.<Hx><Hy> / 2^512   hex stitch",
        "```",
        "",
        f"Digit counts (int+frac): min={payload['patch']['observed_digit_counts']['min']} "
        f"max={payload['patch']['observed_digit_counts']['max']} "
        f"mean={payload['patch']['observed_digit_counts']['mean']:.2f}",
        "",
        "## P135 primary (p−y)",
        "",
    ]
    pp = p135["primary_packet"]
    lines.append(f"- stitched digits: **{pp['total_decimal_digits']}**")
    lines.append(f"- stitched: `{pp['stitched'][:40]}…{pp['stitched'][-40:]}`")
    lines.append(f"- x.y / 2^256: `{pp['x_y_over_2_256']}`")
    lines.append(f"- x.y / p: `{pp['x_y_over_p']}`")

    lines.extend([
        "",
        "## Per-puzzle primary packets (p−y)",
        "",
        "| P | digits | x.y/2^256 (head) | x.y/p (head) |",
        "|---|--------|------------------|--------------|",
    ])
    for r in with_pub:
        pp = r["primary_packet"]
        lines.append(
            f"| {r['puzzle']} | {pp['total_decimal_digits']} | "
            f"`{pp['x_y_over_2_256'][:22]}…` | `{pp['x_y_over_p'][:22]}…` |"
        )

    lines.extend([
        "",
        "Full strings in `packets/puzzle_NNN_packet.json`.",
        "",
        "Rebuild: `python build_packet_silhouette_patch.py`",
        "",
    ])

    (OUT / "packet_silhouette_patch.md").write_text("\n".join(lines), encoding="utf-8")

    # update three_lenses exhibit with patch pointer
    lenses = OUT / "exhibit_three_lenses.md"
    if lenses.exists():
        text = lenses.read_text(encoding="utf-8")
        if "packet_silhouette_patch" not in text:
            lenses.write_text(
                text.rstrip()
                + "\n\n## Patch applied\n\n"
                + "Silhouette fixed in `packet_silhouette_patch.*` / `packets/`.\n"
                + "Every pubkey puzzle has stitched `x.y` (~156 digits), "
                + "`x.y/2^256`, and `x.y/p`.\n",
                encoding="utf-8",
            )

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if "packet_silhouette_patch" not in prev:
        readme.write_text(
            prev.rstrip()
            + "\n\n| `packet_silhouette_patch.*` / `packets/` | "
            "stitched x.y (~156 digits), /2^256 and /p |\n\n"
            "```text\npython build_packet_silhouette_patch.py\n```\n",
            encoding="utf-8",
        )

    print(
        f"pubkey={len(with_pub)} digit_range="
        f"{payload['patch']['observed_digit_counts']}"
    )
    print(f"P135 digits={pp['total_decimal_digits']}")
    print(f"P135 x.y/2^256={pp['x_y_over_2_256'][:50]}")
    print(f"P135 x.y/p={pp['x_y_over_p'][:50]}")
    print(f"wrote {OUT / 'packet_silhouette_patch.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
