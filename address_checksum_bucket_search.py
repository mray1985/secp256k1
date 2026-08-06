#!/usr/bin/env python3
"""
Bucket search: 4-byte checksum (and 8-byte tail) appended to P2PKH address payload.

Payload hex: 00 || hash160 (20B) || checksum (4B)  => 25 bytes = 50 hex chars
Tail-8 hex = last 8 bytes = last 16 hex chars (hash160[-4:] || checksum)
Checksum hex = 8 hex chars (4 bytes appended to 00||hash160)
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
REPORT = ARCHIVE / "address_checksum_bucket_search.txt"

getcontext().prec = 50
LOG2_N = float(Decimal(N).ln() / Decimal(2).ln())


def address_parts(px: int, py: int) -> dict[str, str | int | bytes]:
    comp = (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big")
    sha = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    ph = payload.hex()
    return {
        "h160": h160,
        "checksum": chk,
        "payload": payload,
        "payload_hex": ph,
        "checksum_hex": chk.hex(),  # 8 hex = 4 bytes appended
        "tail8_hex": ph[-16:],  # last 8 bytes: h160[-4] + checksum
        "tail4_hex": ph[-8:],  # checksum only as address tail
        "h160_tail8_hex": h160[-8:].hex(),
        "chk_u32": int.from_bytes(chk, "big"),
        "tail8_u64": int.from_bytes(payload[-8:], "big"),
    }


def ec_hit(d: int, px: int, py: int) -> bool:
    gx, gy = pubkey_from_scalar(d)
    return gx == px and gy == py


def main() -> int:
    keys = parse_53125()
    rows = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        lo, hi, _ = puzzle_band(n)
        if not (lo <= pk.d < hi):
            continue
        ap = address_parts(pk.px, pk.py)
        d = pk.d
        rows.append(
            {
                "n": n,
                "d": d,
                "lo": lo,
                "log_pos": math.log2(d) - (n - 1),
                "frac_d": (d - lo) / lo,
                "y_d": math.log2(d) / LOG2_N,
                "d_hex_head8": format(d, "x")[:8],
                "d_hex_tail8": format(d, "x")[-8:],
                **ap,
            }
        )

    lines = [
        "ADDRESS CHECKSUM / TAIL HEX BUCKET SEARCH",
        f"puzzles: {len(rows)}",
        "",
        "Buckets:",
        "  checksum_hex  = 4 appended bytes (8 hex chars)",
        "  tail8_hex     = last 8 payload bytes (16 hex chars)",
        "  h160_tail8_hex = last 4 bytes of hash160 (8 hex chars)",
        "",
    ]

    # exact hex substring relations
    lines.append("=== d_hex substring in checksum / tail hex ===")
    checks = [
        ("d_hex[:2] in checksum_hex", lambda r: r["d_hex_head8"][:2] in r["checksum_hex"]),
        ("d_hex[:4] in checksum_hex", lambda r: r["d_hex_head8"][:4] in r["checksum_hex"]),
        ("d_hex[:8] in checksum_hex", lambda r: r["d_hex_head8"] in r["checksum_hex"]),
        ("d_hex[-8:] in checksum_hex", lambda r: r["d_hex_tail8"] in r["checksum_hex"]),
        ("d_hex[:4] in tail8_hex", lambda r: r["d_hex_head8"][:4] in r["tail8_hex"]),
        ("d_hex[:8] in tail8_hex", lambda r: r["d_hex_head8"] in r["tail8_hex"]),
        ("checksum_hex in d_hex", lambda r: r["checksum_hex"] in format(r["d"], "x")),
        ("tail8_hex in d_hex", lambda r: r["tail8_hex"] in format(r["d"], "x")),
    ]
    for name, fn in checks:
        hit = sum(1 for r in rows if fn(r))
        lines.append(f"  {name}: {hit}/{len(rows)}")
    lines.append("")

    # fractional buckets from hex bytes
    def byte_fracs(hexstr: str) -> list[float]:
        return [int(hexstr[i : i + 2], 16) / 255.0 for i in range(0, len(hexstr), 2)]

    lines.append("=== checksum byte buckets vs log_pos (correlation) ===")
    corrs = []
    for bi in range(4):
        xs = [int(r["checksum_hex"][bi * 2 : bi * 2 + 2], 16) / 255.0 for r in rows]
        ys = [r["log_pos"] for r in rows]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        r = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(rows))) / (dx * dy) if dx and dy else 0
        corrs.append((abs(r), r, f"checksum_byte[{bi}]/255"))
    corrs.sort(reverse=True)
    for _, r, k in corrs:
        lines.append(f"  r={r:+.4f}  {k}")

    lines.append("")
    lines.append("=== tail8 byte buckets vs log_pos (top |r|) ===")
    corrs8 = []
    for bi in range(8):
        hx = [r["tail8_hex"][bi * 2 : bi * 2 + 2] for r in rows]
        xs = [int(h, 16) / 255.0 for h in hx]
        ys = [r["log_pos"] for r in rows]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        r = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(rows))) / (dx * dy) if dx and dy else 0
        corrs8.append((abs(r), r, f"tail8_byte[{bi}]/255", hx[0][:2] if hx else ""))
    corrs8.sort(reverse=True)
    for _, r, k, _ in corrs8[:8]:
        lines.append(f"  r={r:+.4f}  {k}")

    # invariant: log_pos - f(checksum bytes)
    lines.append("")
    lines.append("=== invariants log_pos - bucket (low std) ===")
    inv = []
    for bi in range(4):
        k = f"chk_b{bi}/255"
        xs = [int(r["checksum_hex"][bi * 2 : bi * 2 + 2], 16) / 255.0 for r in rows]
        diffs = [rows[i]["log_pos"] - xs[i] for i in range(len(rows))]
        mu = sum(diffs) / len(diffs)
        std = math.sqrt(sum((d - mu) ** 2 for d in diffs) / len(diffs))
        inv.append((std, mu, k))
    for bi in range(8):
        k = f"tail8_b{bi}/255"
        xs = [int(r["tail8_hex"][bi * 2 : bi * 2 + 2], 16) / 255.0 for r in rows]
        diffs = [rows[i]["log_pos"] - xs[i] for i in range(len(rows))]
        mu = sum(diffs) / len(diffs)
        std = math.sqrt(sum((d - mu) ** 2 for d in diffs) / len(diffs))
        inv.append((std, mu, k))
    inv.sort()
    for std, mu, k in inv[:12]:
        lines.append(f"  std={std:.5f} mean={mu:+.5f}  {k}")

    # uniqueness / bucketing power
    lines.append("")
    lines.append("=== bucket cardinality (partition power) ===")
    for field in ("checksum_hex", "tail8_hex", "h160_tail8_hex"):
        c = Counter(r[field] for r in rows)
        lines.append(f"  {field}: {len(c)} distinct / {len(rows)} puzzles")
        if len(c) <= 10:
            for val, cnt in c.most_common():
                lines.append(f"    {val}: {cnt}")

    # P135
    lines.append("")
    lines.append("=== P135 buckets (constraint candidates) ===")
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo135, hi135, _ = puzzle_band(135)
    ap = address_parts(px, py)
    lines.append(f"  checksum_hex: {ap['checksum_hex']}")
    lines.append(f"  tail8_hex:    {ap['tail8_hex']}")
    lines.append(f"  payload tail: ...{ap['payload_hex'][-16:]}")
    chk_fracs = byte_fracs(ap["checksum_hex"])
    lines.append(f"  checksum byte fracs /255: {[round(x,4) for x in chk_fracs]}")
    tail_fracs = byte_fracs(ap["tail8_hex"])
    lines.append(f"  tail8 byte fracs /255:    {[round(x,4) for x in tail_fracs]}")

    hits = []
    lines.append("")
    lines.append("  d candidates from best invariant (chk_b0/255):")
    best_std, best_mu, best_k = inv[0]
    bi = int(best_k.split("b")[1].split("/")[0]) if "chk_b" in best_k or "tail8_b" in best_k else 0
    if "chk_b" in best_k:
        pred_frac = chk_fracs[bi] + best_mu
    else:
        pred_frac = tail_fracs[bi] + best_mu
    pred_frac %= 1.0
    for tag, d_est in [
        ("lo*(1+frac)", int(lo135 * (1 + pred_frac))),
        ("lo*2^frac", int(lo135 * (2**pred_frac))),
    ]:
        if lo135 <= d_est < hi135:
            ok = ec_hit(d_est, px, py)
            lines.append(f"    {tag}: bits={d_est.bit_length()} ec={ok} tail...{str(d_est)[-6:]}")
            if ok:
                hits.append(d_est)

    lines.append("")
    lines.append(f"VERDICT: P135 EC hits from checksum bucket = {len(hits)}")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
