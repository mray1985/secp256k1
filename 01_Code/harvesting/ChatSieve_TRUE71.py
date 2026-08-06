#!/usr/bin/env python3
"""
ChatSieve_TRUE71.py
Current project version: lane/echo + Omega residue + ECC verification.

What this script does:
  1) Scores solved puzzle keys and Puzzle 135 against the D/8 lane system.
  2) Applies the current Omega/mod-9 candidate filter for Puzzle 135.
  3) Verifies candidates cryptographically with real secp256k1 point multiplication.
  4) Warns when a physics/intensity metric is effectively constant and not useful.

Proof rule:
  A candidate is only a private key if scalar_mult(d) == target public point.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path
import argparse
import csv
import re
from typing import Iterable, Optional

getcontext().prec = 110

# secp256k1 constants
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

# Puzzle 135 ECDSA/public data used in current work
PUZZLE135_HEIGHT = 135
PUZZLE135_X = int("145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16", 16)
PUZZLE135_Y_EVEN = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PUZZLE135_P = (PUZZLE135_X, PUZZLE135_Y_EVEN)
R135 = int("86bec9faea4892fd98d718bdfc770d0d11c3d6bfd4328f25fe9b06bfadb9650", 16)
S135 = int("224a322e81c044d341521f65fabdfa86d84673fb55ed7533862e37f7724931fa", 16)
Z135 = int("92886faaf53f90a5c03d6af773a726e75097179306b980e5d28772e612e00fc7", 16)
OMEGA_PLUS_RESIDUES = {1, 4, 7}

# Solved calibration keys used for lane drift comparison
SOLVED = {
    10: 514,  # optional puzzle-key calibration, not ground truth 714 lane demo
    70: 970436974005023690481,
    75: 22538323240989823823367,
    80: 1105520030589234487939456,
    85: 21090315766411506144426920,
    90: 868012190417726402719548863,
    100: 868221233689326498340379183142,
    110: 1090246098153987172547740458951748,
    120: 919343500840980333540511050618764323,
    125: 37650549717742544505774009877315221420,
    130: 1103873984953507439627945351144005829577,
}


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(P: Optional[tuple[int, int]], Q: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, p) % p
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mult(k: int, P: tuple[int, int] = G) -> Optional[tuple[int, int]]:
    k %= N
    result = None
    addend: Optional[tuple[int, int]] = P
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def log2_decimal(n: int) -> Decimal:
    if n <= 0:
        return Decimal("-Infinity")
    return Decimal(n).ln() / Decimal(2).ln()


def frac_power_int(n: int, numerator: int, denominator: int = 256) -> int:
    if n <= 0:
        return 0
    return int((Decimal(n).ln() * Decimal(numerator) / Decimal(denominator)).exp())


def puzzle_range(height: int) -> tuple[int, int, int, int, int]:
    lower = 1 << (height - 1)
    upper = (1 << height) - 1
    D = upper - lower + 1
    D8 = D // 8
    mid = lower + D // 2
    return lower, upper, D, D8, mid


def lanes_for_height(height: int) -> dict[str, int]:
    lower, upper, D, D8, mid = puzzle_range(height)
    return {
        "A_mid_minus_D8": mid - D8,
        "B_mid": mid,
        "C_mid_plus_D8": mid + D8,
    }


def classify_lane(height: int, d: int) -> tuple[str, int]:
    lanes = lanes_for_height(height)
    best = min(lanes.items(), key=lambda item: abs(d - item[1]))
    return best[0], d - best[1]


def omega_residue_135(d: int) -> int:
    # IMPORTANT: current rule uses ((r*d - z) mod N) % 9, not raw integer mod 9.
    return ((R135 * (d % N) - Z135) % N) % 9


def derived_k_135(d: int) -> int:
    return ((Z135 + R135 * (d % N)) * inv_mod(S135, N)) % N


def verify_candidate_135(d: int) -> dict[str, object]:
    lower, upper, *_ = puzzle_range(PUZZLE135_HEIGHT)
    P = scalar_mult(d)
    negP = scalar_mult(N - (d % N))
    residue = omega_residue_135(d)
    lane_name, lane_offset = classify_lane(PUZZLE135_HEIGHT, d)
    return {
        "d_dec": d,
        "d_hex": hex(d),
        "bit_length": d.bit_length(),
        "in_range": lower <= d <= upper,
        "omega_residue": residue,
        "omega_plus_ok": residue in OMEGA_PLUS_RESIDUES,
        "derived_k_hex": hex(derived_k_135(d)),
        "nearest_lane": lane_name,
        "lane_offset": lane_offset,
        "dG_x_match": P is not None and P[0] == PUZZLE135_X,
        "dG_full_match": P == PUZZLE135_P,
        "N_minus_d_full_match": negP == PUZZLE135_P,
    }


def read_candidate_file(path: Path) -> list[int]:
    """Accepts decimal or hex candidates anywhere in a text/CSV file."""
    text = path.read_text(errors="replace")
    vals: list[int] = []
    for token in re.findall(r"0x[0-9a-fA-F]+|\b[0-9a-fA-F]{32,64}\b|\b\d{20,}\b", text):
        try:
            if token.lower().startswith("0x"):
                vals.append(int(token, 16))
            elif any(c in "abcdefABCDEF" for c in token):
                vals.append(int(token, 16))
            else:
                vals.append(int(token, 10))
        except ValueError:
            pass
    # preserve order, remove duplicates
    out, seen = [], set()
    for v in vals:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


def lane_echo_report(height: int, priv: Optional[int] = None, pub: Optional[tuple[int, int]] = None) -> None:
    print("=" * 100)
    print(f"Puzzle height: {height}")
    lower, upper, D, D8, mid = puzzle_range(height)
    print(f"lower = {lower}")
    print(f"upper = {upper}")
    print(f"D     = {D}")
    print(f"D/8   = {D8}")
    print(f"mid   = {mid}")
    P = scalar_mult(priv) if priv is not None else pub
    if P is None:
        print("No public point available.")
        return
    x, y = P
    print(f"Public x = {x}")
    print(f"Public y = {y}")
    P8 = scalar_mult(8, P)
    PN8 = scalar_mult(N - 8, P)
    print("\n[N-8 REFLECTION CHECK]")
    print(f"8P.x      = {P8[0] if P8 else None}")
    print(f"(N-8)P.x  = {PN8[0] if PN8 else None}")
    print(f"same x?   = {P8 is not None and PN8 is not None and P8[0] == PN8[0]}")
    print(f"y sum=p?  = {P8 is not None and PN8 is not None and (P8[1] + PN8[1]) % p == 0}")
    curve_val = (pow(x, 3, p) + 7) % p
    x_echo = frac_power_int(x, height)
    y_echo = frac_power_int(y, height)
    c_echo = frac_power_int(curve_val, height)
    print("\n[ECHO VALUES]")
    print(f"x^(h/256)              = {x_echo}")
    print(f"y^(h/256)              = {y_echo}")
    print(f"(x^3+7 mod p)^(h/256) = {c_echo}")
    print("\n[LANE SCORE TABLE]")
    for name, lane in lanes_for_height(height).items():
        dx, dy, dc = abs(lane - x_echo), abs(lane - y_echo), abs(lane - c_echo)
        print("-" * 100)
        print(name)
        print(f"lane              = {lane}")
        print(f"|lane - x_echo|   = {dx}")
        print(f"|lane - y_echo|   = {dy}")
        print(f"|lane - curve|    = {dc}")
        if x_echo:
            print(f"lane / x_echo     = {Decimal(lane) / Decimal(x_echo)}")
        if y_echo:
            print(f"lane / y_echo     = {Decimal(lane) / Decimal(y_echo)}")
        print(f"log2 drift x      = {log2_decimal(lane) - log2_decimal(x_echo) if x_echo else 'N/A'}")
        print(f"log2 drift y      = {log2_decimal(lane) - log2_decimal(y_echo) if y_echo else 'N/A'}")
        if priv is not None:
            print(f"|lane - priv|     = {abs(lane - priv)}")
            print(f"lane / priv       = {Decimal(lane) / Decimal(priv)}")


def warn_constant_intensity(samples: list[float]) -> None:
    if not samples:
        return
    if max(samples) == min(samples):
        print("[warning] Field intensity is constant across sampled k values; it cannot rank candidates.")
        print("          Make sure the formula actually depends on k and is not underflowing to a constant.")


def main() -> None:
    parser = argparse.ArgumentParser(description="TRUE71 ChatSieve: lane/echo score + Omega filter + ECC verification")
    parser.add_argument("--candidates", type=Path, help="Optional text/CSV with decimal or hex candidates to verify against Puzzle 135")
    parser.add_argument("--csv", type=Path, help="Optional CSV output for candidate verification results")
    parser.add_argument("--no-lanes", action="store_true", help="Skip lane/echo report")
    args = parser.parse_args()

    if not args.no_lanes:
        for h in [70, 75, 80, 85, 90, 100, 110, 120, 125, 130]:
            lane_echo_report(h, priv=SOLVED[h])
        lane_echo_report(PUZZLE135_HEIGHT, pub=PUZZLE135_P)

    if args.candidates:
        candidates = read_candidate_file(args.candidates)
        print("\n" + "=" * 100)
        print(f"Candidate verification for Puzzle 135: {len(candidates)} unique candidates")
        rows = [verify_candidate_135(d) for d in candidates]
        survivors = [r for r in rows if r["omega_plus_ok"]]
        hits = [r for r in rows if r["dG_full_match"] or r["N_minus_d_full_match"]]
        print(f"Omega +1 phase survivors: {len(survivors)} / {len(rows)}")
        print(f"Cryptographic hits: {len(hits)}")
        for i, r in enumerate(rows, 1):
            print("-" * 100)
            print(f"#{i}: d={r['d_dec']}")
            print(f"hex={r['d_hex']}")
            print(f"in_range={r['in_range']} bitlen={r['bit_length']} omega9={r['omega_residue']} omega_ok={r['omega_plus_ok']}")
            print(f"lane={r['nearest_lane']} offset={r['lane_offset']}")
            print(f"dG.x_match={r['dG_x_match']} dG.full={r['dG_full_match']} (N-d)G.full={r['N_minus_d_full_match']}")
        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            with args.csv.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
                if rows:
                    writer.writeheader()
                    writer.writerows(rows)
            print(f"CSV written: {args.csv}")


if __name__ == "__main__":
    main()
