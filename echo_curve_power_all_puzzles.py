#!/usr/bin/env python3
"""
Echo from EC curve value c = y^2 mod p = x^3+7 mod p, raised to puzzle exponent:

  exp(n) = (n - 1 + log2(3/2)) / 256
         = (n - 1 + 0.58496250072115618145373894394781650875981440769248106045575265) / 256

Puzzle 135 -> 134.584962.../256
Puzzle 130 -> 129.584962.../256

echo = integer part of c^exp(n)
Then modinv-echo residues mod echo for x, y, c.
"""

from __future__ import annotations

import json
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

getcontext().prec = 300

P = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16)
FRAC = Decimal("0.58496250072115618145373894394781650875981440769248106045575265")
OUT_TXT = ROOT / "ARCHIVE" / "echo_curve_power_all_puzzles.txt"
OUT_JSON = ROOT / "ARCHIVE" / "echo_curve_power_all_puzzles.json"


def exp_ratio(n: int) -> Decimal:
    return (Decimal(n - 1) + FRAC) / Decimal(256)


def pubkey_xy(n: int, keys: dict) -> tuple[int, int] | None:
    if n in keys and keys[n].px:
        return keys[n].px, keys[n].py
    if n not in PUZZLE_RSZ:
        return None
    pub = PUZZLE_RSZ[n].pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots(px)
    raw = bytes.fromhex(pub)
    py = yp if raw[0] == 2 else yn
    return px, py


def process(n: int, keys: dict) -> dict | None:
    xy = pubkey_xy(n, keys)
    if xy is None:
        return None
    px, py = xy
    c = (pow(px, 3, P) + 7) % P
    ratio = exp_ratio(n)
    echo_dec = Decimal(c) ** ratio
    echo = int(echo_dec)
    if echo <= 1:
        return None

    def modinv(v: int) -> int | None:
        try:
            return pow(v, -1, echo)
        except ValueError:
            return None

    x_mi = modinv(px)
    y_mi = modinv(py)
    c_mi = modinv(c)
    row = {
        "puzzle": n,
        "exp_num": float(n - 1) + float(FRAC),
        "exp": f"{n - 1}+{FRAC}/256",
        "x": px,
        "y": py,
        "c": c,
        "echo": echo,
        "echo_tail": str(echo_dec - int(echo_dec))[:20],
        "x_modinv_echo": x_mi,
        "y_modinv_echo": y_mi,
        "c_modinv_echo": c_mi,
        "x_mod_echo": px % echo,
        "y_mod_echo": py % echo,
        "c_mod_echo": c % echo,
        "known_d": keys[n].d if n in keys and keys[n].d > 0 else None,
    }
    lo, hi = 1 << (n - 1), (1 << n) - 1

    def band(v: int | None) -> bool | None:
        return lo <= v < hi if v is not None else None

    row["in_band"] = {
        "x_mod_echo": band(row["x_mod_echo"]),
        "y_mod_echo": band(row["y_mod_echo"]),
        "c_mod_echo": band(row["c_mod_echo"]),
        "x_modinv_echo": band(x_mi),
        "y_modinv_echo": band(y_mi),
        "c_modinv_echo": band(c_mi),
    }
    return row


def main() -> int:
    keys = parse_53125()
    puzzles = sorted(set(PUZZLE_RSZ) | {n for n in keys if keys[n].px})
    rows = []
    lines = [
        "ECHO CURVE POWER — all puzzles",
        f"c = y^2 mod p = x^3+7 mod p",
        f"exp(n) = (n-1 + log2(3/2)) / 256",
        f"FRAC = {FRAC}",
        "",
        f"{'P':>4} {'exp':>22} {'echo bits':>10} {'c mod echo in band':>18} {'y mod echo in band':>18}",
    ]

    for n in puzzles:
        r = process(n, keys)
        if r is None:
            continue
        rows.append(r)
        ib = r["in_band"]
        lines.append(
            f"P{n:>3} {r['exp_num']:>22.15f} {r['echo'].bit_length():>10} "
            f"{str(ib['c_mod_echo']):>18} {str(ib['y_mod_echo']):>18}"
        )

    # P135 detail block
    p135 = next((r for r in rows if r["puzzle"] == 135), None)
    if p135:
        lines.extend([
            "",
            "=== P135 DETAIL ===",
            f"c  = {p135['c']}",
            f"exp = {p135['exp_num']}",
            f"echo = {p135['echo']}",
            f"x modinv echo = {p135['x_modinv_echo']}",
            f"y modinv echo = {p135['y_modinv_echo']}",
            f"c modinv echo = {p135['c_modinv_echo']}",
            f"x mod echo    = {p135['x_mod_echo']}",
            f"y mod echo    = {p135['y_mod_echo']}",
            f"c mod echo    = {p135['c_mod_echo']}",
            "",
            "Compare old ratio 135/256:",
        ])
        c135 = p135["c"]
        old_echo = int(Decimal(c135) ** (Decimal(135) / Decimal(256)))
        lines.append(f"  old echo (135/256)     = {old_echo}")
        lines.append(f"  new echo (134.5849/256)= {p135['echo']}")

    text = "\n".join(lines) + "\n"
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text(text, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(text)
    print(f"wrote {OUT_TXT}")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
