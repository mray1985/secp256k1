#!/usr/bin/env python3
"""Address payload vs h160: the 2^32 lane and decimal zero-tail structure."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

TWO32 = 4294967296
ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def h160_bytes(x: int, y: int) -> bytes:
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()


def payload_parts(h160: bytes) -> tuple[int, int, int]:
    """Return (payload_int, h160_int, checksum_int) for P2PKH version 0."""
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    return int.from_bytes(payload, "big"), int.from_bytes(h160, "big"), int.from_bytes(chk, "big")


def pubkey_h160(pub: str) -> bytes:
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    return h160_bytes(x, y)


def main() -> None:
    keys = parse_53125()
    lines: list[str] = [
        "Address / hash160 and the 2^32 lane",
        "=" * 60,
        "",
        "P2PKH payload (25 bytes) = 0x00 || hash160(20) || checksum(4)",
        "As integer:  payload_int = hash160_int * 2^32 + checksum_int",
        "So (payload_int - checksum_int) // hash160_int = 2^32 = 4294967296 EXACTLY",
        "",
    ]

    all_exact = True
    for n in sorted(keys):
        k = keys[n]
        if not k.px:
            continue
        h = h160_bytes(k.px, k.py)
        payload, hi, chk = payload_parts(h)
        q, rem = divmod(payload - chk, hi)
        exact = q == TWO32 and rem == 0
        all_exact &= exact
        if n <= 12 or n in (65, 70, 75, 115, 125, 135, 160):
            lines.append(
                f"P{n:3d}  payload//h160 quotient={q}  (exact 2^32? {exact})  "
                f"checksum={chk}  chk<2^32? {chk < TWO32}"
            )

    lines.append(f"\nall solved checked: quotient always 2^32? {all_exact}")
    lines.append("")

    # P160 unsolved
    pub = PUZZLE_RSZ[160].pub_compressed
    h = pubkey_h160(pub)
    payload, hi, chk = payload_parts(h)
    q = (payload - chk) // hi
    lines.append(f"P160  payload/h160 lane quotient = {q}  (2^32={q == TWO32})")
    lines.append(f"      checksum (low 32-bit lane) = {chk}")
    lines.append("")

    # Decimal zero-tail on h160 // 2^32 quotient
    lines.append("=== Decimal form: h160 = q * 2^32 + r (low lane) ===")
    lines.append("q = h160 // 2^32 is ~38-39 decimal digits; r is the 'small offset' lane")
    lines.append("")
    for n in [1, 32, 65, 70, 75, 115, 125, 135, 160]:
        if n == 160:
            h = pubkey_h160(pub)
        else:
            k = keys[n]
            if not k.px:
                continue
            h = h160_bytes(k.px, k.py)
        hi = int.from_bytes(h, "big")
        q, r = divmod(hi, TWO32)
        qs = str(q)
        trail = len(qs) - len(qs.rstrip("0"))
        lines.append(f"P{n:3d}  h160_dec_len={len(str(hi))}  q_len={len(qs)}  q_trail_zeros={trail}")
        lines.append(f"       h160 = {qs} * 2^32 + {r}")
        lines.append(f"       dec: {hi}")
        lines.append("")

    # Private key d in puzzle band: same 2^32 lane split
    lines.append("=== Private key d in band: (d - lo) = q * 2^32 + r ===")
    lines.append("(band width / 2^32 = 2^(n-33) buckets — checksum fine buckets)")
    lines.append("")
    for n in [65, 70, 75, 115, 125, 130, 135, 160]:
        lo, hi, _ = puzzle_band(n if n < 160 else 160)
        if n < 160:
            lo, hi, _ = puzzle_band(n)
            d = keys[n].d if n in keys else 0
        else:
            lo, hi, _ = puzzle_band(160)
            h = pubkey_h160(pub)
            d = int.from_bytes(h, "big")  # anchor only, not true d
            label = "h160(P160) anchor"
        if n < 160:
            d = keys[n].d
            label = f"true d"
        off = d - lo
        q, r = divmod(off, TWO32)
        buckets = (hi - lo) // TWO32
        lines.append(
            f"P{n:3d}  {label}  band_buckets~2^{(n-33) if n<160 else 127}  "
            f"(d-lo)//2^32={q}  rem={r}"
        )

    lines.append("")
    lines.append("=== Interpretation ===")
    lines.append(
        "The '4294967296 every time' is structural: checksum sits in the low 32-bit lane, "
        "so address_int = h160_int * 2^32 + checksum. Not a puzzle secret — encoding geometry."
    )
    lines.append(
        "The 'long zeros + small offset' in decimal is usually h160 = (big quotient) * 2^32 + "
        "(remainder under 4.3e9). Same lane split applies to d-lo in the puzzle band."
    )

    text = "\n".join(lines) + "\n"
    out = ROOT / "ARCHIVE" / "h160_address_two32_pattern.txt"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
