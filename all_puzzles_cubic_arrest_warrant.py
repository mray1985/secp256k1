#!/usr/bin/env python3
"""
Cubic-root lambda arrest warrant across all hashkeys RSZ puzzles.

Per puzzle (RSZ r,s,z + pubkey Px,Py):
  u_i^3 == r (mod N)  ->  lambda_i = Px * u_i^-1
  arrest: x_i = lambda_i * z * (s - r*lambda_i)^-1  (mod N)

Hit if x_i*G == P  and/or  x_i == known d  and/or  x_i in puzzle band.
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
    N,
    p,
    primitive_cube_root_of_unity,
    pubkey_from_scalar,
    puzzle_band,
    y_even,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ, PuzzleRSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "all_puzzles_cubic_arrest_warrant_report.txt"
CSV_OUT = ARCHIVE / "all_puzzles_cubic_arrest_warrant.csv"


@dataclass(frozen=True)
class Hit:
    puzzle: int
    branch: str
    lam_path: str
    x: int
    ec_hit: bool
    d_match: bool
    in_band: bool


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


def cube_roots_of_r(r: int) -> list[tuple[str, int]]:
    r %= N
    out: list[tuple[str, int]] = []
    if pow(r, (N - 1) // 3, N) == 1:
        u0 = pow(r, (N + 2) // 9, N)
        if pow(u0, 3, N) == r:
            w = primitive_cube_root_of_unity(N)
            if w:
                for j, u in enumerate([u0, (u0 * w) % N, (u0 * w * w) % N]):
                    out.append((f"cbrt_r_j{j}", u))
            else:
                out.append(("cbrt_r_j0", u0))
    r3 = pow(r, 3, N)
    if pow(r3, (N - 1) // 3, N) == 1:
        u0 = pow(r3, (N + 2) // 9, N)
        if pow(u0, 3, N) == r3:
            w = primitive_cube_root_of_unity(N)
            branches = [u0, (u0 * w) % N, (u0 * w * w) % N] if w else [u0]
            for j, u in enumerate(branches):
                tag = f"cbrt_r3_j{j}"
                if not any(u == v for _, v in out):
                    out.append((tag, u))
    if not any(u == r for _, u in out):
        out.append(("r_direct", r))
    return out


def lambda_paths(px: int, u: int) -> list[tuple[str, int]]:
    lam_n = (px * pow(u, -1, N)) % N
    lam_f = ((px * pow(u % p, -1, p)) % p) % N
    return [("Px/u mod N", lam_n), ("Px/u mod p", lam_f)]


def arrest_x(lam: int, r: int, s: int, z: int) -> int | None:
    d = (s - r * lam) % N
    if d == 0:
        return None
    k = (z * pow(d, -1, N)) % N
    return (lam * k) % N


def ec_match(x: int, px: int, py: int) -> bool:
    try:
        gx, gy = pubkey_from_scalar(x)
        return gx == px and gy == py
    except Exception:
        return False


def hunt_puzzle(n: int, rsz: PuzzleRSZ, keys: dict) -> tuple[list[Hit], list[str]]:
    px, py = pubkey_xy(rsz, keys)
    r, s, z = rsz.r, rsz.s, rsz.z
    d_known = keys[n].d if n in keys and keys[n].d else None
    lo, hi, _ = puzzle_band(n)
    detail: list[str] = [
        f"P{n}  Px...{str(px)[-3:]}  r...{str(r)[-3:]}  band_bits={n}",
    ]
    if d_known:
        detail.append(f"  known d bits={d_known.bit_length()}")

    hits: list[Hit] = []
    branches = cube_roots_of_r(r)
    detail.append(f"  branches={len(branches)}")

    for tag, u in branches:
        for lname, lam in lambda_paths(px, u):
            x = arrest_x(lam, r, s, z)
            if x is None:
                continue
            ec = ec_match(x, px, py)
            dm = d_known is not None and x == d_known
            ib = lo <= x < hi
            if ec or dm or ib:
                hits.append(Hit(n, tag, lname, x, ec, dm, ib))
                detail.append(
                    f"  HIT {tag} {lname}: ec={ec} d_match={dm} in_band={ib} x_bits={x.bit_length()}"
                )

    # control: Px/r no cube root
    lam0 = (px * pow(r, -1, N)) % N
    x0 = arrest_x(lam0, r, s, z)
    if x0 is not None:
        ec0 = ec_match(x0, px, py)
        dm0 = d_known is not None and x0 == d_known
        ib0 = lo <= x0 < hi
        if ec0 or dm0 or ib0:
            hits.append(Hit(n, "Px/r_control", "Px/r mod N", x0, ec0, dm0, ib0))
            detail.append(f"  HIT Px/r_control: ec={ec0} d_match={dm0} in_band={ib0}")

    if not hits:
        detail.append("  no hits")
    return hits, detail


def main() -> int:
    keys = parse_53125()
    puzzles = sorted(PUZZLE_RSZ.keys())
    all_hits: list[Hit] = []
    lines = [
        "ALL PUZZLES CUBIC ARREST WARRANT",
        f"puzzles={len(puzzles)}  N mod 9={N % 9}",
        "",
    ]

    for n in puzzles:
        rsz = PUZZLE_RSZ[n]
        hits, detail = hunt_puzzle(n, rsz, keys)
        all_hits.extend(hits)
        lines.extend(detail)
        lines.append("")

    ec_hits = [h for h in all_hits if h.ec_hit]
    d_hits = [h for h in all_hits if h.d_match]
    band_hits = [h for h in all_hits if h.in_band]

    lines.extend([
        "SUMMARY",
        f"  total candidate hits (ec|d|band): {len(all_hits)}",
        f"  EC hits: {len(ec_hits)}",
        f"  d_match hits: {len(d_hits)}",
        f"  in_band hits: {len(band_hits)}",
        "",
    ])
    for h in all_hits:
        lines.append(
            f"  P{h.puzzle} {h.branch} {h.lam_path} ec={h.ec_hit} d={h.d_match} band={h.in_band}"
        )

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["puzzle", "branch", "lam_path", "x", "ec_hit", "d_match", "in_band"])
        for h in all_hits:
            w.writerow([h.puzzle, h.branch, h.lam_path, h.x, h.ec_hit, h.d_match, h.in_band])

    print(text)
    print(f"wrote {REPORT}")
    print(f"wrote {CSV_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
