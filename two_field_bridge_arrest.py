#!/usr/bin/env python3
"""
Two-field bridge arrest warrant.

Field side:  Lambda = Px * denom^-1  (mod p)
Scalar side: lambda = Lambda mod N
Arrest:      x = lambda * z * (s - r*lambda)^-1  (mod N)

denom = rx_j (coordinate) and/or u_i (cubic root of signature r in Z_N).
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    DEFAULT_RX,
    N,
    P135_R_TRUE_X,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ, PuzzleRSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "two_field_bridge_arrest_report.txt"
CSV_OUT = ARCHIVE / "two_field_bridge_arrest.csv"


@dataclass(frozen=True)
class Hit:
    puzzle: int
    bridge: str
    px_slot: int
    denom_slot: int
    x: int
    ec: bool
    d_match: bool
    in_band: bool
    lam: int


def lam_field(px: int, denom: int) -> int:
    return ((px * pow(denom % p, -1, p)) % p) % N


def lam_scalar_noise(px: int, denom: int) -> int:
    """Wrong path: inverse mod N before ratio."""
    return (px * pow(denom, -1, N)) % N


def pubkey_xy(rsz: PuzzleRSZ, keys: dict) -> tuple[int, int]:
    pk = keys.get(rsz.puzzle_num)
    if pk and pk.px and pk.py:
        return pk.px, pk.py
    comp = rsz.pub_compressed
    px = int(comp[2:], 16)
    want_even = comp.startswith("02")
    y_pos, y_neg = y_roots(px)
    py = y_pos if (y_pos % 2 == 0) == want_even else y_neg
    return px, py


def cbrt_branches_r(r: int) -> list[tuple[str, int]]:
    r %= N
    if pow(r, (N - 1) // 3, N) != 1:
        return []
    u0 = pow(r, (N + 2) // 9, N)
    if pow(u0, 3, N) != r:
        return []
    w = primitive_cube_root_of_unity(N)
    if not w:
        return [("u0", u0)]
    return [(f"u{j}", u) for j, u in enumerate([u0, (u0 * w) % N, (u0 * w * w) % N])]


def arrest(lam: int, r: int, s: int, z: int) -> int | None:
    d = (s - r * lam) % N
    if d == 0:
        return None
    return (lam * z * pow(d, -1, N)) % N


def ec_ok(x: int, px: int, py: int) -> bool:
    try:
        gx, gy = pubkey_from_scalar(x)
        return gx == px and gy == py
    except Exception:
        return False


def hunt_p135_full() -> list[str]:
    rsz = PUZZLE_RSZ[135]
    px_pub, py = pubkey_xy(rsz, {})
    r, s, z = rsz.r, rsz.s, rsz.z
    lo, hi, _ = puzzle_band(135)
    lines = [
        "P135 TWO-FIELD BRIDGE GRID",
        f"pub Px tail ...{str(px_pub)[-3:]}  r tail ...{str(r)[-3:]}",
        "",
    ]

    hits: list[Hit] = []
    for pi, px in enumerate(DEFAULT_PX):
        for ri, rx in enumerate(DEFAULT_RX):
            lam = lam_field(px, rx)
            x = arrest(lam, r, s, z)
            if x is None:
                continue
            ec = ec_ok(x, px_pub, py)
            ib = lo <= x < hi
            if ec or ib:
                hits.append(Hit(135, "Px/rx field", pi, ri, x, ec, False, ib, lam))
            lines.append(
                f"  Px[{pi}]/rx[{ri}] field: lam_tail ...{str(lam)[-5:]} "
                f"x_bits={x.bit_length()} ec={ec} band={ib}"
            )

    lines.append("")
    lines.append("P135 cubic u_i as field denom (lambda = (Px*u_i^-1 mod p) mod N):")
    for ui, u in cbrt_branches_r(r):
        for pi, px in enumerate(DEFAULT_PX):
            lam = lam_field(px, u)
            x = arrest(lam, r, s, z)
            if x is None:
                continue
            ec = ec_ok(x, px_pub, py)
            ib = lo <= x < hi
            if ec or ib:
                hits.append(Hit(135, f"cbrt_{ui}", pi, -1, x, ec, False, ib, lam))
            lines.append(
                f"  Px[{pi}]/{ui} field: x_bits={x.bit_length()} ec={ec} band={ib} lam...{str(lam)[-3:]}"
            )

    lines.append("")
    lines.append(f"P135 hits: {len(hits)}")
    return lines, hits


def hunt_all_rsz() -> tuple[list[str], list[Hit]]:
    keys = parse_53125()
    all_hits: list[Hit] = []
    lines = ["", "ALL RSZ PUZZLES — field bridge Px_pub/r_sig", ""]

    for n in sorted(PUZZLE_RSZ.keys()):
        rsz = PUZZLE_RSZ[n]
        px, py = pubkey_xy(rsz, keys)
        r, s, z = rsz.r, rsz.s, rsz.z
        d_known = keys[n].d if n in keys and keys[n].d else None
        lo, hi, _ = puzzle_band(n)

        # canonical two-field: pubkey px / signature r
        lam_f = lam_field(px, r)
        lam_n = lam_scalar_noise(px, r)
        x_f = arrest(lam_f, r, s, z)
        x_n = arrest(lam_n, r, s, z) if lam_n else None

        d_f = d_known is not None and x_f == d_known if x_f else False
        d_n = d_known is not None and x_n == d_known if x_n else False
        ec_f = ec_ok(x_f, px, py) if x_f else False
        ec_n = ec_ok(x_n, px, py) if x_n else False

        if ec_f or d_f or (x_f and lo <= x_f < hi):
            all_hits.append(Hit(n, "field Px/r", 0, 0, x_f, ec_f, d_f, lo <= x_f < hi, lam_f))
        if ec_n or d_n or (x_n and lo <= x_n < hi):
            all_hits.append(Hit(n, "scalar Px/r noise", 0, 0, x_n, ec_n, d_n, lo <= x_n < hi, lam_n))

        if d_known and (d_f or d_n or ec_f or ec_n):
            lines.append(
                f"P{n} SOLVED field_d={d_f} scalar_d={d_n} field_ec={ec_f} scalar_ec={ec_n}"
            )

        # cubic branches on solved puzzles
        if d_known:
            for tag, u in cbrt_branches_r(r):
                lam = lam_field(px, u)
                x = arrest(lam, r, s, z)
                if x is None:
                    continue
                dm = x == d_known
                ec = ec_ok(x, px, py)
                if dm or ec:
                    all_hits.append(Hit(n, f"field Px/{tag}", 0, 0, x, ec, dm, lo <= x < hi, lam))
                    lines.append(f"  P{n} {tag} field bridge d_match={dm} ec={ec}")

    lines.append("")
    lines.append(f"Total hits: {len(all_hits)}")
    return lines, all_hits


def main() -> int:
    p135_lines, p135_hits = hunt_p135_full()
    all_lines, all_hits = hunt_all_rsz()
    hits = p135_hits + all_hits

    text = "\n".join(
        [
            "TWO-FIELD BRIDGE ARREST WARRANT",
            "lambda = (Px * denom^-1 mod p) mod N",
            "arrest x = lambda * z * (s - r*lambda)^-1 mod N",
            "",
        ]
        + p135_lines
        + all_lines
    )

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["puzzle", "bridge", "px_slot", "denom_slot", "lambda", "x", "ec", "d_match", "in_band"])
        for h in hits:
            w.writerow([h.puzzle, h.bridge, h.px_slot, h.denom_slot, h.lam, h.x, h.ec, h.d_match, h.in_band])

    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
