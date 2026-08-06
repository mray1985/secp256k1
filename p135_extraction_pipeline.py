#!/usr/bin/env python3
"""
Puzzle 135 extraction verifier.

This script keeps the "closer to private key extraction" work honest:
it turns patterns into filters, then verifies candidates with dG == P.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    32670510020758816978083085130507043184471273380659243275938904335757337482424,
)

P135_POINT = (
    9210836494447108270027136741376870869791784014198948301625976867708124077590,
    46351506704828816385393879789131775975171267756561783641521771795450741674800,
)

P135_LOW = 1 << 134
P135_HIGH_EXCLUSIVE = 1 << 135
HALF_FIELD_MINUS_ONE = (P - 1) // 2
INTEGER_RE = re.compile(r"\b\d{20,}\b")


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(a: tuple[int, int] | None, b: tuple[int, int] | None) -> tuple[int, int] | None:
    if a is None:
        return b
    if b is None:
        return a

    x1, y1 = a
    x2, y2 = b

    if x1 == x2 and (y1 + y2) % P == 0:
        return None

    if a == b:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, P) % P
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, P) % P

    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3


def scalar_mult(k: int, point: tuple[int, int] = G) -> tuple[int, int] | None:
    k %= N
    result = None
    addend: tuple[int, int] | None = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def on_curve(point: tuple[int, int]) -> bool:
    x, y = point
    return (y * y - x * x * x - 7) % P == 0


def factor_small(n: int, limit: int = 100_000) -> tuple[list[tuple[int, int]], int]:
    factors: list[tuple[int, int]] = []
    d = 2
    while d <= limit and d * d <= n:
        count = 0
        while n % d == 0:
            n //= d
            count += 1
        if count:
            factors.append((d, count))
        d += 1 if d == 2 else 2
    return factors, n


def extract_band_candidates(paths: list[Path]) -> dict[int, list[str]]:
    candidates: dict[int, list[str]] = {}
    for path in paths:
        if not path.is_file() or path.suffix.lower() in {".zip", ".xlsx"}:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for match in INTEGER_RE.finditer(text):
            value = int(match.group(0))
            if P135_LOW <= value < P135_HIGH_EXCLUSIVE:
                candidates.setdefault(value, []).append(str(path))
    return candidates


def recover_d_from_signature(r: int, s: int, z: int, k: int) -> int:
    return ((s * k - z) * inv_mod(r, N)) % N


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, help="Files/directories to scan for P135-sized integers")
    parser.add_argument("--sig", nargs=4, metavar=("R", "S", "Z", "K"), help="Recover d from known ECDSA k")
    args = parser.parse_args()

    x, y = P135_POINT
    c = (pow(x, 3, P) + 7) % P

    print("P135 public point")
    print(f"  on_curve: {on_curve(P135_POINT)}")
    print(f"  y^2 == x^3+7 mod p: {(y * y) % P == c}")
    print(f"  range: [{P135_LOW}, {P135_HIGH_EXCLUSIVE})")
    print()

    print("(p-1)/2 coordinate fingerprints")
    print(f"  M = {HALF_FIELD_MINUS_ONE}")
    small_factors, remainder = factor_small(HALF_FIELD_MINUS_ONE)
    print(f"  small factors found: {small_factors}")
    print(f"  remaining cofactor: {remainder}")
    print(f"  x^3 mod M: {pow(x, 3, HALF_FIELD_MINUS_ONE)}")
    print(f"  y^2 mod M: {pow(y, 2, HALF_FIELD_MINUS_ONE)}")
    print("  expected Wolfram root branches: cube=27, square=8")
    print()

    if args.sig:
        r, s, z, k = (int(v, 0) for v in args.sig)
        d = recover_d_from_signature(r, s, z, k)
        print("Known-k ECDSA recovery")
        print(f"  d = {d}")
        print(f"  d in P135 band: {P135_LOW <= d < P135_HIGH_EXCLUSIVE}")
        print(f"  dG matches P135: {scalar_mult(d) == P135_POINT}")
        print()

    scan_paths: list[Path] = []
    for path in args.paths:
        if path.is_dir():
            scan_paths.extend(p for p in path.rglob("*") if p.is_file())
        else:
            scan_paths.append(path)

    if scan_paths:
        candidates = extract_band_candidates(scan_paths)
        print("Candidate scan")
        print(f"  files scanned: {len(scan_paths)}")
        print(f"  unique P135-band integers: {len(candidates)}")
        hits = []
        for idx, d in enumerate(sorted(candidates), start=1):
            if scalar_mult(d) == P135_POINT:
                hits.append((d, candidates[d]))
            if idx % 100 == 0:
                print(f"  checked {idx}/{len(candidates)}", end="\r")
        if candidates:
            print(" " * 40, end="\r")
        print(f"  exact dG hits: {len(hits)}")
        for d, sources in hits:
            print(f"  HIT d={d} sources={sources[:3]}")
        if not hits and candidates:
            sample = sorted(candidates)[:5]
            print(f"  first candidates checked: {sample}")
            print("  verdict: candidates are filters/leads only; none extract P135 d.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
