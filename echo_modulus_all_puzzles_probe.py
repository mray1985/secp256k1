#!/usr/bin/env python3
"""Echo-modulus mirror for all puzzles: exponent = height/256, height = puzzle number n.

m = int( C^(n/256) )  where C = (x^3+7) mod p
Residues mod m: x, x^-1, y, y^-1, C, C^-1
Band: [2^(n-1), 2^n - 1]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1, SigningKey
from hashkeys_rsz import N as CURVE_ORDER, PUZZLE_RSZ, p, y_roots_from_x
from puzzle_keys_53125 import parse_53125

getcontext().prec = 300

P = p
OUT_JSON = ROOT / "echo_modulus_all_puzzles_report.json"
OUT_TXT = ROOT / "echo_modulus_all_puzzles_report.txt"

X_SIDE = ("x_mod_m", "x_inv_mod_m", "C_inv_mod_m")
Y_SIDE = ("y_mod_m", "y_inv_mod_m", "C_mod_m")
ALL_RESIDUES = X_SIDE + Y_SIDE


@dataclass
class ResidueRow:
    name: str
    value: int | None
    in_band: bool
    ec_match: bool | None  # None if not tested
    equals_known_d: bool | None


def pubkey_xy(n: int, keys: dict) -> tuple[int, int, str] | None:
    if n in keys and keys[n].px:
        return keys[n].px, keys[n].py, "53125"
    if n in PUZZLE_RSZ:
        pub = PUZZLE_RSZ[n].pub_compressed
        px = int(pub[2:], 16)
        yp, yn = y_roots_from_x(px)
        py = yp if pub.startswith("02") else yn
        return px, py, "RSZ"
    return None


def modinv_safe(v: int, m: int) -> int | None:
    if m <= 1:
        return None
    try:
        return pow(v, -1, m)
    except ValueError:
        return None


def verify_pubkey(d: int, px: int, py: int) -> bool:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    return pt.x() == px and pt.y() == py


def puzzle_band(n: int) -> tuple[int, int]:
    lo = 1 << (n - 1)
    hi = (1 << n) - 1
    return lo, hi


def process_puzzle(n: int, keys: dict) -> dict | None:
    xy = pubkey_xy(n, keys)
    if xy is None:
        return None
    px, py, src = xy
    c = (pow(px, 3, P) + 7) % P
    exp = Decimal(n) / Decimal(256)
    echo_dec = Decimal(c) ** exp
    m = int(echo_dec)

    lo, hi = puzzle_band(n)
    known_d = keys[n].d if n in keys and keys[n].d > 0 else None
    solved = known_d is not None

    raw = {
        "x_mod_m": px % m if m > 0 else None,
        "x_inv_mod_m": modinv_safe(px, m),
        "y_mod_m": py % m if m > 0 else None,
        "y_inv_mod_m": modinv_safe(py, m),
        "C_mod_m": c % m if m > 0 else None,
        "C_inv_mod_m": modinv_safe(c, m),
    }

    residues: dict[str, dict] = {}
    in_band_names: list[str] = []
    ec_hits: list[str] = []
    d_hits: list[str] = []

    for name in ALL_RESIDUES:
        val = raw[name]
        if val is None:
            residues[name] = {
                "value": None,
                "in_band": False,
                "ec_match": None,
                "equals_known_d": None,
            }
            continue
        in_band = lo <= val <= hi
        if in_band:
            in_band_names.append(name)
        ec_match = None
        equals_d = None
        if in_band:
            ec_match = verify_pubkey(val, px, py)
            if ec_match:
                ec_hits.append(name)
            if solved:
                equals_d = val == known_d
                if equals_d:
                    d_hits.append(name)
        residues[name] = {
            "value": val,
            "in_band": in_band,
            "ec_match": ec_match,
            "equals_known_d": equals_d,
        }

    x_side_in = sum(1 for k in X_SIDE if residues[k]["in_band"])
    y_side_in = sum(1 for k in Y_SIDE if residues[k]["in_band"])

    return {
        "puzzle": n,
        "height": n,
        "exponent": f"{n}/256",
        "pubkey_source": src,
        "solved": solved,
        "known_d": known_d,
        "px": px,
        "py": py,
        "C": c,
        "echo_m": m,
        "echo_decimal_tail": format(echo_dec, ".20f"),
        "band_lo": lo,
        "band_hi": hi,
        "residues": residues,
        "in_band": in_band_names,
        "x_side_in_band_count": x_side_in,
        "y_side_in_band_count": y_side_in,
        "x_side_dominates": x_side_in > y_side_in,
        "x_side_only_pattern": x_side_in >= 1 and y_side_in == 0,
        "p135_style_pattern": x_side_in >= 3 and y_side_in == 0,
        "ec_match_residues": ec_hits,
        "equals_known_d_residues": d_hits,
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    x_dom = sum(1 for r in rows if r["x_side_dominates"])
    x_only = sum(1 for r in rows if r["x_side_only_pattern"])
    p135_style = sum(1 for r in rows if r["p135_style_pattern"])
    any_ec = sum(1 for r in rows if r["ec_match_residues"])
    any_d = sum(1 for r in rows if r["equals_known_d_residues"])

    per_residue_band = {k: 0 for k in ALL_RESIDUES}
    for r in rows:
        for k in ALL_RESIDUES:
            if r["residues"][k]["in_band"]:
                per_residue_band[k] += 1

    solved_rows = [r for r in rows if r["solved"]]
    unsolved_rows = [r for r in rows if not r["solved"]]

    return {
        "puzzle_count": n,
        "solved_count": len(solved_rows),
        "unsolved_count": len(unsolved_rows),
        "x_side_dominates_count": x_dom,
        "x_side_dominates_rate": round(x_dom / n, 4) if n else 0,
        "x_side_only_pattern_count": x_only,
        "p135_style_pattern_count": p135_style,
        "any_ec_match_count": any_ec,
        "any_equals_known_d_count": any_d,
        "per_residue_in_band": per_residue_band,
        "solved_any_equals_d": [
            {
                "puzzle": r["puzzle"],
                "hits": r["equals_known_d_residues"],
            }
            for r in solved_rows
            if r["equals_known_d_residues"]
        ],
    }


def format_txt(rows: list[dict], summary: dict) -> str:
    lines = [
        "ECHO MODULUS ALL-PUZZLES REPORT",
        "  m = int( C^(n/256) ),  C = (x^3+7) mod p,  n = puzzle height (bit width)",
        f"  puzzles processed: {summary['puzzle_count']}",
        "",
        "AGGREGATE",
        f"  x-side dominates (x hits > y hits): {summary['x_side_dominates_count']}/{summary['puzzle_count']}",
        f"  x-side only (>=1 x-hit, 0 y-hit):   {summary['x_side_only_pattern_count']}/{summary['puzzle_count']}",
        f"  P135-style (3 x-side in band, 0 y): {summary['p135_style_pattern_count']}/{summary['puzzle_count']}",
        f"  any EC match (in-band d*G=P):       {summary['any_ec_match_count']}",
        f"  any residue == known d (solved):  {summary['any_equals_known_d_count']}",
        "",
        "Per-residue in-band counts:",
    ]
    for k, v in summary["per_residue_in_band"].items():
        lines.append(f"  {k:14s} {v}")

    lines += ["", "PER PUZZLE", ""]
    for r in rows:
        flags = []
        if r["p135_style_pattern"]:
            flags.append("P135-style")
        elif r["x_side_only_pattern"]:
            flags.append("x-only")
        if r["ec_match_residues"]:
            flags.append(f"EC-HIT:{','.join(r['ec_match_residues'])}")
        if r["equals_known_d_residues"]:
            flags.append(f"D-HIT:{','.join(r['equals_known_d_residues'])}")
        flag_s = " | ".join(flags) if flags else "-"
        lines.append(
            f"P{r['puzzle']:3d}  m={r['echo_m']}  "
            f"x={r['x_side_in_band_count']} y={r['y_side_in_band_count']}  "
            f"in_band={','.join(r['in_band']) or 'none'}  {flag_s}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    keys = parse_53125()
    puzzle_nums = sorted(set(keys) | set(PUZZLE_RSZ))

    rows: list[dict] = []
    skipped: list[int] = []
    for n in puzzle_nums:
        row = process_puzzle(n, keys)
        if row is None:
            skipped.append(n)
        else:
            rows.append(row)

    summary = summarize(rows)
    report = {
        "model": {
            "echo": "m = int( C^(n/256) )",
            "C": "(x^3 + 7) mod p",
            "n": "puzzle height = puzzle number (bit width of d band)",
            "band": "[2^(n-1), 2^n - 1]",
            "x_side": list(X_SIDE),
            "y_side": list(Y_SIDE),
        },
        "summary": summary,
        "skipped_no_pubkey": skipped,
        "puzzles": rows,
    }

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    OUT_TXT.write_text(format_txt(rows, summary), encoding="utf-8")

    print(format_txt(rows, summary))
    print(f"JSON: {OUT_JSON}")
    print(f"TXT:  {OUT_TXT}")


if __name__ == "__main__":
    main()
