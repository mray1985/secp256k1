"""Shared Puzzle 71 target constants and hit reporting."""

from __future__ import annotations

import hashlib
from pathlib import Path

LO = 1 << 70
TOP = (1 << 71) - 1
M_FULL = 1 << 35
M_2P29 = 1 << 29
M_2P30 = 1 << 30
# Geometric mid of [2^70, 2^71): d = LO + 2^69
MID_R = 1 << 69
# 2^29 window centered on mid-band (avoid LO..0 sweep — long searches missed there)
START_R_MID_2P29 = MID_R - (M_2P29 // 2)
END_R_MID_2P29 = START_R_MID_2P29 + M_2P29
H160_RECORD = 25  # 20-byte hash160 + 5-byte big-endian r

TARGET_ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
TARGET_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")

SOLVED_PATH = Path(r"C:\Users\mitch\Desktop\secp256k1\PUZZLE71_SOLVED.txt")
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def hash160_to_address(h160: bytes) -> str:
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    n = int.from_bytes(payload, "big")
    result = ""
    while n:
        n, r = divmod(n, 58)
        result = ALPHABET[r] + result
    for byte in payload:
        if byte == 0:
            result = "1" + result
        else:
            break
    return result


def save_p71_hit(
    d: int,
    *,
    source: str,
    j: int = 0,
    r: int = 0,
    m: int = 0,
    hit_path: Path | None = None,
) -> str:
    addr = hash160_to_address(TARGET_H160)
    text = (
        f"PUZZLE 71 SOLVED\n"
        f"source={source}\n"
        f"d={d}\n"
        f"hex={hex(d)}\n"
        f"address={addr}\n"
        f"j={j} r={r} M={m}\n"
        f"expected_address={TARGET_ADDR}\n"
    )
    SOLVED_PATH.write_text(text, encoding="utf-8")
    if hit_path:
        hit_path.parent.mkdir(parents=True, exist_ok=True)
        hit_path.write_text(text, encoding="utf-8")
    print(text, flush=True)
    return text
