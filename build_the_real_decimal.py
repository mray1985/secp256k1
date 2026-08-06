#!/usr/bin/env python3
"""
The Real Decimal — full briefcase under the corrected silhouette.

Folder: ARCHIVE/briefcase/The Real Decimal/

Lenses (do not bleed):
  1. fixed binary:   v / 2^256
  2. courtroom:      v / p  or  v / N
  3. packet stitch:  x.y then / 2^256 and / p

Never promote stitch to a giant int first.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    DELTA,
    Gx,
    LAMBDA,
    LAMBDA1,
    N,
    Px,
    inv,
    p,
    rx,
)
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

getcontext().prec = 120

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
TWO256 = Decimal(1 << 256)
TWO512 = Decimal(1 << 512)

# Standard G (slot-2 / middle of CS triple is generator x)
GX = Gx[1]
GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def frac256(v: int) -> str:
    v = v % (1 << 256)
    return format(Decimal(v) / TWO256, "f")


def frac_p(v: int) -> str:
    return format(Decimal(v % p) / Decimal(p), "f")


def frac_N(v: int) -> str:
    return format(Decimal(v % N) / Decimal(N), "f")


def fixed_width_object(name: str, v: int, courtroom: str | None = None) -> dict:
    """Fixed-width ≤256-bit object under correct lenses."""
    H = f"{v % (1 << 256):064x}"
    rec = {
        "name": name,
        "value": str(v),
        "hex": hex(v),
        "H": H,
        "lens_fixed_binary": {
            "formula": "v / 2^256",
            "fractional_hex": f"0x.{H}",
            "value": frac256(v),
        },
    }
    if courtroom == "field":
        rec["lens_courtroom"] = {"formula": "v / p", "value": frac_p(v)}
    elif courtroom == "scalar":
        rec["lens_courtroom"] = {"formula": "v / N", "value": frac_N(v)}
    elif courtroom == "both":
        rec["lens_field"] = {"formula": "v / p", "value": frac_p(v)}
        rec["lens_scalar"] = {"formula": "v / N", "value": frac_N(v)}
    return rec


def packet_xy(px: int, y_digits: int, label: str) -> dict:
    """Stitch x.y (~156 digits), then /2^256 and /p."""
    s_px, s_y = str(px), str(y_digits)
    stitched_s = f"{s_px}.{s_y}"
    stitched = Decimal(stitched_s)
    H = f"{px:064x}{y_digits:064x}"
    return {
        "branch": label,
        "silhouette": "decimal_stitch_then_normalize",
        "stitched_decimal_string": stitched_s,
        "integer_digits": len(s_px),
        "fractional_digits": len(s_y),
        "total_decimal_digits": len(s_px) + len(s_y),
        "lens_fixed_binary": {
            "formula": "x.y / 2^256",
            "value": format(stitched / TWO256, "f"),
        },
        "lens_packet_field": {
            "formula": "x.y / p",
            "value": format(stitched / Decimal(p), "f"),
        },
        "lens_hex_stitch_512": {
            "formula": "0x.<Hx><Hy> / 2^512",
            "hex": f"0x.{H}",
            "value": format(Decimal(int(H, 16)) / TWO512, "f"),
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "puzzles").mkdir(exist_ok=True)
    (OUT / "globals").mkdir(exist_ok=True)

    catalog = load_catalog()
    rsz_cache: dict = {}
    if CACHE_PATH.exists():
        rsz_cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    # --- globals ---
    globals_list = [
        fixed_width_object("p", p, "field"),
        fixed_width_object("N", N, "scalar"),
        fixed_width_object("DELTA_p_minus_N", DELTA, "both"),
        fixed_width_object("B_2_32_plus_977", (1 << 32) + 977, "both"),
        fixed_width_object("B4", pow((1 << 32) + 977, 4), "both"),
        fixed_width_object("Gx", GX, "field"),
        fixed_width_object("Gy", GY, "field"),
        fixed_width_object("BETA", BETA, "field"),
        fixed_width_object("BETA_SQ", BETA_SQ, "field"),
        fixed_width_object("LAMBDA", LAMBDA, "field"),
        fixed_width_object("LAMBDA1", LAMBDA1, "field"),
    ]
    # G and P135 β-slot triples from CS ledger
    for i, v in enumerate(Gx, 1):
        globals_list.append(fixed_width_object(f"Gx_slot_{i}", v, "field"))
    for i, v in enumerate(Px, 1):
        globals_list.append(fixed_width_object(f"P135_Px_slot_{i}", v, "field"))
    for i, v in enumerate(rx, 1):
        globals_list.append(fixed_width_object(f"P135_rx_slot_{i}", v, "both"))

    # G packet (generator)
    g_packet_y = packet_xy(GX, GY, "y")
    g_packet_pmy = packet_xy(GX, (p - GY) % p, "p_minus_y")

    globals_doc = {
        "keeper": "H does not change. The decimal point changes the courtroom.",
        "lenses": {
            "fixed_binary": "v / 2^256",
            "field": "v / p",
            "scalar": "v / N",
            "packet": "x.y / 2^256 and x.y / p (stitch first)",
        },
        "fixed_width_objects": globals_list,
        "generator_packets": {
            "primary_branch": "p_minus_y",
            "branch_y": g_packet_y,
            "branch_p_minus_y": g_packet_pmy,
        },
    }
    (OUT / "globals" / "constants.json").write_text(
        json.dumps(globals_doc, indent=2), encoding="utf-8"
    )

    # --- every puzzle ---
    index_rows = []
    for n in range(1, 161):
        e = catalog[n]
        rec: dict = {
            "puzzle": n,
            "address": e.address,
            "hash160": e.hash160,
            "solved": e.solved,
            "has_pubkey": bool(e.public_key),
            "d_window": f"[2^{n-1}, 2^{n})",
            "N_mirror": f"[N-2^{n}+1, N-2^{n-1}]",
            "range_lo": str(e.range_min),
            "range_hi": str(e.range_max),
        }

        # hash160 / address as fixed-width when possible
        if e.hash160:
            h160 = int(e.hash160, 16)
            rec["hash160"] = fixed_width_object("hash160", h160)

        if not e.public_key:
            rec["status"] = "NO_PUBKEY"
            rec["note"] = "No x,y — only range / address / hash160 lenses"
            (OUT / "puzzles" / f"puzzle_{n:03d}.json").write_text(
                json.dumps(rec, indent=2), encoding="utf-8"
            )
            index_rows.append(rec)
            continue

        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        rec["status"] = "SOLVED" if e.solved and e.private_key > 0 else "UNSOLVED_PUBKEY"
        rec["Px"] = str(px)
        rec["Py"] = str(py)
        rec["p_minus_y"] = str(pmy)

        # single-coordinate lenses (not the packet)
        rec["coordinates"] = {
            "Px": fixed_width_object("Px", px, "field"),
            "Py": fixed_width_object("Py", py, "field"),
            "p_minus_y": fixed_width_object("p_minus_y", pmy, "field"),
            "Px1": fixed_width_object("Px1", (px * inv(BETA_SQ, p)) % p, "field"),
            "Px2": fixed_width_object("Px2", (px * inv(BETA, p)) % p, "field"),
        }

        # packets — the ~156 digit stitch
        rec["packets"] = {
            "primary_branch": "p_minus_y",
            "branch_y": packet_xy(px, py, "y"),
            "branch_p_minus_y": packet_xy(px, pmy, "p_minus_y"),
        }
        primary = rec["packets"]["branch_p_minus_y"]
        rec["primary_packet"] = {
            "stitched": primary["stitched_decimal_string"],
            "total_decimal_digits": primary["total_decimal_digits"],
            "x_y_over_2_256": primary["lens_fixed_binary"]["value"],
            "x_y_over_p": primary["lens_packet_field"]["value"],
            "hex_stitch_over_2_512": primary["lens_hex_stitch_512"]["value"],
        }

        # β-slot packets (Px_i with shared y branch p-y)
        rec["beta_slot_packets"] = {
            "Px1_pmy": packet_xy((px * inv(BETA_SQ, p)) % p, pmy, "Px1.pmy"),
            "Px2_pmy": packet_xy((px * inv(BETA, p)) % p, pmy, "Px2.pmy"),
            "Px3_pmy": packet_xy(px, pmy, "Px3.pmy"),
        }

        # RSZ if cached
        rsz = rsz_cache.get(str(n))
        if rsz:
            rec["rsz"] = {
                "r": fixed_width_object("r", int(rsz["r"]), "both"),
                "s": fixed_width_object("s", int(rsz["s"]), "scalar"),
                "z": fixed_width_object("z", int(rsz["z"]), "scalar"),
            }
            if rsz.get("txid"):
                rec["rsz"]["txid"] = rsz["txid"]

        # solved scalar
        if e.solved and e.private_key > 0:
            d = e.private_key
            q = (N - d) % N
            rec["scalar"] = {
                "d": fixed_width_object("d", d, "scalar"),
                "N_minus_d": fixed_width_object("N_minus_d", q, "scalar"),
                "d_in_d_window": e.range_min <= d <= e.range_max,
                "N_minus_d_in_N_mirror": (
                    (N - (1 << n) + 1) <= q <= (N - (1 << (n - 1)))
                ),
            }

        (OUT / "puzzles" / f"puzzle_{n:03d}.json").write_text(
            json.dumps(rec, indent=2), encoding="utf-8"
        )
        index_rows.append(rec)

    # manifest / index
    with_pub = [r for r in index_rows if r.get("has_pubkey")]
    digit_counts = [
        r["primary_packet"]["total_decimal_digits"] for r in with_pub
    ]

    manifest = {
        "folder": "ARCHIVE/briefcase/The Real Decimal/",
        "keeper": "H does not change. The decimal point changes the courtroom.",
        "lenses": {
            "1_fixed_binary": "v / 2^256",
            "2_courtroom": "v / p or v / N",
            "3_packet": "x.y / 2^256 and x.y / p (stitch first, never int(x||y))",
        },
        "primary_branch": "p_minus_y",
        "counts": {
            "puzzles": 160,
            "with_xy_packets": len(with_pub),
            "no_pubkey": 160 - len(with_pub),
            "digit_min": min(digit_counts) if digit_counts else None,
            "digit_max": max(digit_counts) if digit_counts else None,
            "digit_mean": sum(digit_counts) / len(digit_counts) if digit_counts else None,
        },
        "globals": "globals/constants.json",
        "puzzles_glob": "puzzles/puzzle_NNN.json",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # index markdown
    lines = [
        "# The Real Decimal",
        "",
        "Full briefcase under the corrected silhouette.",
        "",
        "```text",
        "H does not change.",
        "The decimal point changes the courtroom.",
        "",
        "1. fixed binary:   v / 2^256",
        "2. courtroom:      v / p  or  v / N",
        "3. packet:         x.y / 2^256  and  x.y / p",
        "```",
        "",
        "Stitch `x.y` first (~152–156 decimal digits). Never promote to a giant int.",
        "",
        f"Pubkey puzzles with packets: **{len(with_pub)}**/160",
        f"Digit counts: min={manifest['counts']['digit_min']} "
        f"max={manifest['counts']['digit_max']} "
        f"mean={manifest['counts']['digit_mean']:.2f}",
        "",
        "## Globals",
        "",
        "`globals/constants.json` — p, N, Δ, B, B4, G, β, Λ, P135 slots, G packet",
        "",
        "## Puzzles",
        "",
        "| P | status | digits | x.y/2^256 (head) | x.y/p (head) |",
        "|---|--------|--------|------------------|--------------|",
    ]
    for r in index_rows:
        if not r.get("has_pubkey"):
            lines.append(f"| {r['puzzle']} | NO_PUBKEY | — | — | — |")
            continue
        pp = r["primary_packet"]
        lines.append(
            f"| {r['puzzle']} | {r['status']} | {pp['total_decimal_digits']} | "
            f"`{pp['x_y_over_2_256'][:24]}…` | `{pp['x_y_over_p'][:24]}…` |"
        )

    lines.extend([
        "",
        "Full stitched strings and all lenses: `puzzles/puzzle_NNN.json`",
        "",
        "Rebuild: `python build_the_real_decimal.py`",
        "",
    ])
    (OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "README.md").write_text(
        "\n".join([
            "# The Real Decimal",
            "",
            "Corrected fractional / packet silhouette for **everything** in the briefcase.",
            "",
            "| Path | Contents |",
            "|------|----------|",
            "| `MANIFEST.json` | counts + lens rules |",
            "| `index.md` | human index |",
            "| `globals/constants.json` | p, N, G, β, Λ, … |",
            "| `puzzles/puzzle_NNN.json` | per-puzzle packets + coordinates + RSZ + scalar |",
            "",
            "```text",
            "python build_the_real_decimal.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"The Real Decimal: {len(with_pub)} packets, digits {manifest['counts']}")
    p135 = next(r for r in with_pub if r["puzzle"] == 135)
    print(f"P135 digits={p135['primary_packet']['total_decimal_digits']}")
    print(f"P135 x.y/2^256={p135['primary_packet']['x_y_over_2_256'][:48]}")
    print(f"P135 x.y/p={p135['primary_packet']['x_y_over_p'][:48]}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
