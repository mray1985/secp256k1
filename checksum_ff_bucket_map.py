#!/usr/bin/env python3
"""
Checksum bucket map: 00000000 .. FFFFFFFF (4 bytes) as fraction of full range.

Also: N as 32 bytes split into 8 x 4-byte lanes; band size / 2^32 keys per bucket.
"""

from __future__ import annotations

import hashlib
import math
import sys
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "checksum_ff_bucket_map.txt"

CHK_MAX = 0xFFFFFFFF  # 4-byte appended checksum ceiling
EIGHT_BUCKETS = 8


def checksum_u32(px: int, py: int) -> int:
    comp = (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big")
    sha = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    vh = b"\x00" + h160
    return int.from_bytes(hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4], "big")


def main() -> int:
    getcontext().prec = 50
    log2_n = float(Decimal(N).ln() / Decimal(2).ln())

    keys = parse_53125()
    rows = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        lo, hi, _ = puzzle_band(n)
        if not (lo <= pk.d < hi):
            continue
        chk = checksum_u32(pk.px, pk.py)
        d = pk.d
        frac_d = (d - lo) / lo
        log_pos = math.log2(d) - (n - 1)
        chk_frac = chk / CHK_MAX  # map 00000000..FFFFFFFF -> 0..1
        bucket8 = chk >> 29  # top 3 bits -> 8 buckets (0..7)
        rows.append(
            {
                "n": n,
                "d": d,
                "lo": lo,
                "hi": hi,
                "chk": chk,
                "chk_hex": f"{chk:08x}",
                "chk_frac": chk_frac,
                "frac_d": frac_d,
                "log_pos": log_pos,
                "bucket8": bucket8,
                "band_w": hi - lo,
            }
        )

    lines = [
        "CHECKSUM FFFFFFFF BUCKET MAP",
        "",
        f"N bits = {N.bit_length()}  (32 bytes)",
        f"N / 2^32 = {N // (CHK_MAX + 1)}  (4-byte lanes that fit in N)",
        f"32 bytes / 8 = 4 bytes per mega-lane (checksum width)",
        f"checksum range: 0x00000000 .. 0xFFFFFFFF  ({CHK_MAX + 1} buckets)",
        "",
    ]

    # correlation chk_frac vs band position
    xs = [r["chk_frac"] for r in rows]
    ys = [r["frac_d"] for r in rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    r_frac = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(rows))) / (dx * dy) if dx and dy else 0

    ys2 = [r["log_pos"] for r in rows]
    my2 = sum(ys2) / len(ys2)
    dy2 = math.sqrt(sum((y - my2) ** 2 for y in ys2))
    r_log = sum((xs[i] - mx) * (ys2[i] - my2) for i in range(len(rows))) / (dx * dy2) if dx and dy2 else 0

    lines.append("=== map checksum / FFFFFFFF vs private key position in band ===")
    lines.append(f"  corr(chk/FFFF, frac_d):     {r_frac:+.4f}")
    lines.append(f"  corr(chk/FFFF, log_pos):   {r_log:+.4f}")
    diffs = [r["frac_d"] - r["chk_frac"] for r in rows]
    mu = sum(diffs) / len(diffs)
    std = math.sqrt(sum((d - mu) ** 2 for d in diffs) / len(diffs))
    lines.append(f"  frac_d - chk/FFFF: mean={mu:+.5f} std={std:.5f}")
    lines.append("")

    # keys per bucket estimate: band_width / 2^32
    lines.append("=== how many d keys share one checksum bucket (uniform estimate) ===")
    lines.append("  band_width / 2^32 = 2^(n-1) / 2^32 = 2^(n-33)")
    for n in (65, 100, 130, 135):
        lo, hi, _ = puzzle_band(n)
        w = hi - lo
        est = w // (CHK_MAX + 1)
        log2_est = (n - 1) - 32
        lines.append(f"  P{n}: band~2^{n-1}  ~2^{log2_est} keys per checksum bucket  ({est:.2e} int)")
    lines.append("")

    # 8-bucket partition (N/8 bytes idea -> 8 lanes)
    lines.append("=== 8-bucket partition (top 3 bits of checksum) ===")
    c8 = Counter(r["bucket8"] for r in rows)
    for b in range(EIGHT_BUCKETS):
        cnt = c8.get(b, 0)
        lo_b = (b * (CHK_MAX + 1)) // EIGHT_BUCKETS
        hi_b = ((b + 1) * (CHK_MAX + 1) - 1) // EIGHT_BUCKETS
        lines.append(
            f"  bucket {b}: count={cnt:2d}  chk range 0x{lo_b:08x}..0x{hi_b:08x}"
        )
    lines.append("")

    # N byte lanes: byte k of N as bucket label vs puzzle
    n_bytes = N.to_bytes(32, "big")
    lines.append("=== N split into 8 x 4-byte lanes (32/8 bytes) ===")
    for lane in range(8):
        chunk = int.from_bytes(n_bytes[lane * 4 : lane * 4 + 4], "big")
        lines.append(f"  lane {lane}: 0x{chunk:08x}  dec ...{str(chunk)[-6:]}")
    lines.append("")

    # compare checksum to N lane
    lines.append("=== checksum vs N lane (same 4-byte width) ===")
    for lane in range(8):
        n_chunk = int.from_bytes(n_bytes[lane * 4 : lane * 4 + 4], "big")
        ratios = [r["chk"] / n_chunk if n_chunk else 0 for r in rows]
        fracs = [r["chk"] / CHK_MAX for r in rows]
        # corr chk with n_chunk mod? 
        diffs = [r["chk"] - (n_chunk % (CHK_MAX + 1)) for r in rows]
        std = math.sqrt(sum((d - sum(diffs) / len(diffs)) ** 2 for d in diffs) / len(diffs))
        lines.append(f"  lane {lane}: std(chk - (N_lane mod 2^32)) = {std:.2e}")

    lines.append("")
    lines.append("=== P135 ===")
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo135, hi135, _ = puzzle_band(135)
    chk = checksum_u32(px, py)
    cf = chk / CHK_MAX
    b8 = chk >> 29
    lines.append(f"  checksum: 0x{chk:08x}  frac={cf:.8f}  bucket8={b8}")
    lines.append(f"  bucket8 range: 0x{(b8*(CHK_MAX+1)//8):08x} .. 0x{(((b8+1)*(CHK_MAX+1)-1)//8):08x}")
    keys_in_bucket = (hi135 - lo135) // EIGHT_BUCKETS
    lines.append(f"  P135 band / 8 buckets ~ {keys_in_bucket:.2e} keys per coarse bucket")
    keys_in_chk = (hi135 - lo135) // (CHK_MAX + 1)
    lines.append(f"  P135 band / 2^32 checksum buckets ~ 2^{134-32} = 2^102 keys each")
    lines.append("")
    lines.append("  d estimate from chk/FFFF map:")
    for tag, f in [("frac=chk/FFFF", cf), ("frac=chk/FFFF mean-adjusted", cf + mu)]:
        d = int(lo135 * (1 + f % 1))
        if lo135 <= d < hi135:
            gx, gy = pubkey_from_scalar(d)
            ok = gx == px and gy == py
            lines.append(f"    {tag}: d tail ...{str(d)[-6:]} ec={ok}")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
