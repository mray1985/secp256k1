#!/usr/bin/env python3
"""Verify KeyHunt hit: d*G == P_160 and m=(N+1)/d in 2^96 complement band."""

from ecdsa import SECP256k1

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
TX = 0xE0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673
TY = 0xC2D9690945DD98F6E0E45D4A1F760C9E85ED5AE5FFEEDA74E121EE0D836A7C86
G = SECP256k1.generator

GX_PREFIX = str(G.x())[:3]  # 550 — G-prefix prune reference


def verify(d: int) -> None:
    p = d * G
    ok = p.x() == TX and p.y() == TY
    m = (N + 1) // d
    rem = (N + 1) % d
    print(f"d = {d}")
    print(f"hex = {hex(d)}")
    print(f"d*G == P_160: {ok}")
    print(f"(N+1) % d == 0: {rem == 0}")
    print(f"m = (N+1)//d = {m}  ({m.bit_length()} bits)")
    print(f"m in [2^96, 2^97): {2**96 <= m < 2**97}")
    print(f"m in [2^95, 2^96): {2**95 <= m < 2**96}")
    print(f"G-prefix (Gx first 3 dig): {GX_PREFIX}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python verify_p160_hit.py <d_decimal_or_0xhex>")
        sys.exit(1)
    s = sys.argv[1].strip()
    d = int(s, 16) if s.lower().startswith("0x") else int(s)
    verify(d)
