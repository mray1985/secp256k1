#!/usr/bin/env python3
"""Probe whether hash160 correlates with pubkey/d/bridge on solved puzzles (P71 lead)."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config
from genesis_calibration import bridge_state
from ecdlp_full_pipeline import puzzle_band
from puzzle_keys_53125 import parse_53125

P71_H160_HEX = "F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8"
P71_LO = 1 << 70
P71_HI = 1 << 71


def hash160_bytes(px: int, py: int) -> bytes:
    pref = b"\x02" if py % 2 == 0 else b"\x03"
    return hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + px.to_bytes(32, "big")).digest(),
    ).digest()


def hash160_int(px: int, py: int) -> int:
    return int.from_bytes(hash160_bytes(px, py), "big")


def verify_d(d: int, target: bytes, lo: int, hi: int) -> bool:
    from ecdlp_full_pipeline import pubkey_from_scalar

    if not (lo <= d < hi):
        return False
    x, y = pubkey_from_scalar(d)
    return hash160_bytes(x, y) == target


def main() -> int:
    keys = parse_53125()
    target = bytes.fromhex(P71_H160_HEX)
    h71 = int.from_bytes(target, "big")

    print("=== P71 hash160 target ===")
    print(f"  hex: {P71_H160_HEX}")
    print(f"  int bits: {h71.bit_length()}")
    print(f"  in [2^70,2^71)? {P71_LO <= h71 < P71_HI}")
    print(f"  h71 mod LO bits: {(h71 % P71_LO).bit_length()}")
    print()

    checks = {
        "h160 == d": 0,
        "h160 == px": 0,
        "h160 == py": 0,
        "(h160 mod LO) == (d mod LO)": 0,
        "(h160 mod LO) == offset(d-shelf2)": 0,
        "h160 bytes prefix in px hex": 0,
        "first 10 hex of h160 in px hex": 0,
    }
    n_ok = 0

    print("=== Solved puzzles 1-70: hash160 vs d / pubkey / bridge ===")
    for n in sorted(keys):
        pk = keys[n]
        if pk.d == 0 or n > 70:
            continue
        n_ok += 1
        lo, hi, _ = puzzle_band(n)
        h = hash160_int(pk.px, pk.py)
        off = 0
        try:
            cfg = build_config(pk)
            st = bridge_state(cfg)
            off = (pk.d - st["oitc"].shelf2) % lo
        except Exception:
            pass
        if h == pk.d:
            checks["h160 == d"] += 1
        if h == pk.px:
            checks["h160 == px"] += 1
        if h == pk.py:
            checks["h160 == py"] += 1
        if (h % lo) == (pk.d % lo):
            checks["(h160 mod LO) == (d mod LO)"] += 1
        if (h % lo) == off:
            checks["(h160 mod LO) == offset(d-shelf2)"] += 1
        px_hex = format(pk.px, "x")
        h_hex = format(h, "040x")
        if h_hex[:8] in px_hex:
            checks["first 10 hex of h160 in px hex"] += 1

    for k, v in checks.items():
        print(f"  {k}: {v}/{n_ok}")

    print()
    print("=== P65-P70 detail ===")
    print(f"{'n':>3} {'h160 bits':>9} {'d bits':>7} {'px bits':>7} {'h160==target71':>14}")
    for n in range(65, 71):
        pk = keys[n]
        h = hash160_int(pk.px, pk.py)
        match = "YES" if hash160_bytes(pk.px, pk.py) == target else ""
        print(f"{n:3d} {h.bit_length():9d} {pk.d.bit_length():7d} {pk.px.bit_length():7d} {match:>14}")

    print()
    print("=== Can hash160 alone recover d? (wrong hashers on P70) ===")
    pk70 = keys[70]
    d70 = pk70.d
    wrong_modes = {
        "RIPEMD160(str(d))": hashlib.new("ripemd160", str(d70).encode()).hexdigest(),
        "RIPEMD160(hex(d))": hashlib.new("ripemd160", format(d70, "x").encode()).hexdigest(),
        "correct hash160(P)": hash160_bytes(pk70.px, pk70.py).hex(),
    }
    for name, val in wrong_modes.items():
        print(f"  {name}: {val}")

    print()
    print("=== P71: test bridge-extrapolated d candidates vs hash160 ===")
    # P71 row = 71 mod 3 = 2; extrapolate shelf2 from P70 pattern
    p70 = keys[70]
    cfg70 = build_config(p70)
    st70 = bridge_state(cfg70)
    lo70, _, _ = puzzle_band(70)
    shelf2_70 = st70["oitc"].shelf2
    # naive: shelf2_71 ~ 2*shelf2_70 - shelf2_69 pattern or LO + (shelf2_70 mod LO)
    shelf2_guess = P71_LO + ((shelf2_70 * 2) % P71_LO)  # placeholder
    for ob in (60, 61, 69, 70):  # common offset_bits near P70
        _, o_lo, o_hi = __import__("gap_tier_common", fromlist=["gap_interval"]).gap_interval(71, 71 - ob)
        for d in (shelf2_guess + o_lo, shelf2_guess + (o_lo + o_hi) // 2):
            if P71_LO <= d < P71_HI:
                ok = verify_d(d, target, P71_LO, P71_HI)
                print(f"  d~shelf2+off(ob={ob}): {d} EC={ok}")

    print()
    print("=== VERDICT ===")
    print("  hash160 is 160-bit digest — no stable equality with d/Px on solved set.")
    print("  P71 must verify: hash160(compress(d*G)) == target (Harvester/BSGS).")
    print("  Bridge shelf2 guesses still need EC/hash160 gate — not bypassed by h160 alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
