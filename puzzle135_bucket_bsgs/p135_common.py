"""P135 target pubkey, checksum bucket bounds, EC helpers."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from bucket_slice_search import bucket_bounds, checksum_u32, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

PUZZLE = 135
H160_RECORD = 25  # 20-byte h160 + 5-byte r
M_DEFAULT = 1 << 35

SOLVED_PATH = ROOT / "PUZZLE135_SOLVED.txt"


def load_target() -> tuple[int, int, bytes, int, int]:
    rsz = PUZZLE_RSZ[PUZZLE]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    comp = (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big")
    h160 = hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()
    chk = checksum_u32(px, py)
    return px, py, h160, chk, int(rsz.pub_compressed[2:], 16)


def load_bucket_slice(mode: str = "upper_half") -> tuple[int, int, int, str]:
    lo, hi, _ = puzzle_band(PUZZLE)
    px, py, _, chk, _ = load_target()
    return bucket_bounds(lo, hi, mode=mode, chk_u32=chk)


def inv_mod(a: int, m: int) -> int:
    return pow(a % m, -1, m)


def point_add(p1: tuple[int, int] | None, p2: tuple[int, int] | None) -> tuple[int, int] | None:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, P) % P
    else:
        lam = (y2 - y1) * inv_mod(x2 - x1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def point_neg(p: tuple[int, int]) -> tuple[int, int]:
    x, y = p
    return (x, (-y) % P)


def scalar_mult(k: int, point: tuple[int, int] = G) -> tuple[int, int] | None:
    k %= N
    if k == 0:
        return None
    result = None
    addend: tuple[int, int] | None = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def pubkey_h160(point: tuple[int, int]) -> bytes:
    x, y = point
    pk = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(pk).digest()).digest()


def save_hit(
    d: int,
    *,
    source: str,
    j: int = 0,
    r: int = 0,
    m: int = 0,
    hit_path: Path | None = None,
) -> None:
    px, py, h160, chk, _ = load_target()
    ok = verify_candidate(d, px, py, chk)
    text = (
        f"PUZZLE 135 SOLVED\n"
        f"source={source}\n"
        f"d={d}\n"
        f"hex={hex(d)}\n"
        f"h160={h160.hex()}\n"
        f"checksum=0x{chk:08x}\n"
        f"j={j} r={r} M={m}\n"
        f"ec_verify={ok}\n"
    )
    SOLVED_PATH.write_text(text, encoding="utf-8")
    if hit_path:
        hit_path.parent.mkdir(parents=True, exist_ok=True)
        hit_path.write_text(text, encoding="utf-8")
    print(text, flush=True)
