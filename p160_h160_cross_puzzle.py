#!/usr/bin/env python3
"""Test: is P160 private key = hash160(pubkey) from another puzzle?"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

P160 = 160
REPORT = ROOT / "ARCHIVE" / "p160_h160_cross_puzzle.txt"


def h160_from_compressed(pub_hex: str) -> tuple[int, bytes]:
    raw = bytes.fromhex(pub_hex)
    x = int(pub_hex[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    return int.from_bytes(digest, "big"), digest


def h160_from_xy(x: int, y: int) -> tuple[int, bytes]:
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    return int.from_bytes(digest, "big"), digest


def load_all_pubkeys() -> dict[int, str]:
    """puzzle_num -> compressed pubkey hex (source tag in value tuple via side dict)."""
    out: dict[int, str] = {}
    for n, row in parse_53125().items():
        if row.px and row.py:
            pref = "02" if row.py % 2 == 0 else "03"
            out[n] = pref + format(row.px, "064x")
    for n, rsz in PUZZLE_RSZ.items():
        if n not in out and rsz.pub_compressed:
            out[n] = rsz.pub_compressed
    p160_pub = ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
    if p160_pub.is_file():
        out[P160] = p160_pub.read_text(encoding="ascii").strip().splitlines()[0].strip()
    return out


def ec_match(d: int, target_pub: str) -> bool:
    tx = int(target_pub[2:], 16)
    x, y = pubkey_from_scalar(d)
    return x == tx and (target_pub[:2] == "02") == (y % 2 == 0)


def main() -> None:
    pubs = load_all_pubkeys()
    lo, hi, _ = puzzle_band(P160)
    p160_pub = pubs[P160]

    lines: list[str] = [
        "P160 d = hash160(another puzzle pubkey)?",
        f"P160 band [{lo}, {hi})  width 2^159",
        f"P160 pubkey {p160_pub}",
        "",
    ]

    # --- A) which h160 land in P160 band ---
    in_band: list[tuple[int, int, float]] = []
    for m in sorted(pubs):
        if m == P160:
            continue
        h_int, h_bytes = h160_from_compressed(pubs[m])
        if lo <= h_int < hi:
            bf = (h_int - lo) / (hi - lo)
            in_band.append((m, h_int, bf))

    lines.append(f"=== hash160 values in P160 band: {len(in_band)} / {len(pubs)-1} puzzles ===")
    for m, h_int, bf in in_band:
        hit = ec_match(h_int, p160_pub)
        lines.append(
            f"  P{m:3d}  h160={h_int.to_bytes(20, 'big').hex()}  "
            f"band_frac={bf:.6f}  d*G==P160? {'HIT' if hit else 'no'}"
        )
    lines.append("")

    # --- B) EC verify all in-band + nearby transforms ---
    transforms = [
        ("raw", lambda h: h),
        ("N-h", lambda h: (N - h) % N),
        ("h+2^159", lambda h: h + (1 << 159)),
        ("h|2^159", lambda h: h | (1 << 159)),
        ("h^2^159", lambda h: h ^ (1 << 159)),
    ]
    hits: list[str] = []
    for m in sorted(pubs):
        if m == P160:
            continue
        h_int, _ = h160_from_compressed(pubs[m])
        for tname, fn in transforms:
            cand = fn(h_int) % N
            if not (lo <= cand < hi):
                continue
            if ec_match(cand, p160_pub):
                hits.append(f"HIT P{m} {tname} d={cand}")

    lines.append(f"=== EC hits (with transforms): {len(hits)} ===")
    lines.extend(hits or ["  (none)"])
    lines.append("")

    # --- C) on solved keys: d_n == h160(m)? ---
    solved = {n: k.d for n, k in parse_53125().items() if k.d}
    d_eq_h: list[str] = []
    h_by_m: dict[int, int] = {}
    for m in sorted(pubs):
        h_by_m[m], _ = h160_from_compressed(pubs[m])

    for n in sorted(solved):
        d = solved[n]
        for m, h in h_by_m.items():
            if m == n:
                continue
            if d == h:
                d_eq_h.append(f"  P{n} d == h160(P{m})  d={d}")
            if d == (N - h) % N:
                d_eq_h.append(f"  P{n} d == N-h160(P{m})  d={d}")

    lines.append(f"=== solved d == another puzzle h160: {len(d_eq_h)} ===")
    lines.extend(d_eq_h or ["  (none on 53125 solved set)"])
    lines.append("")

    # --- D) P160's own h160 as d? ---
    h160_self, hb = h160_from_compressed(p160_pub)
    lines.append("=== P160 self-reference ===")
    lines.append(f"  h160(P160) = {hb.hex()}  bits={h160_self.bit_length()}")
    lines.append(f"  in band? {lo <= h160_self < hi}  band_frac={(h160_self-lo)/(hi-lo):.6f}")
    lines.append(f"  h160(P160)*G==P160? {ec_match(h160_self, p160_pub)}")
    lines.append("")

    # --- E) bit-magnitude summary ---
    lines.append("=== magnitude (log10) ===")
    import math

    for label, val in [
        ("d_lo", lo),
        ("d_hi~", hi - 1),
        ("h160(P160)", h160_self),
        ("h160(P135)", h_by_m.get(135, 0)),
        ("h160(P125)", h_by_m.get(125, 0)),
        ("h160(P70)", h_by_m.get(70, 0)),
    ]:
        if val:
            lines.append(f"  {label:14s} bits={val.bit_length():3d}  ~10^{math.log10(val):.2f}")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
