#!/usr/bin/env python3
"""
Exhaustive fractional relation search: log2(d)/log2(N) vs hash160 / SHA256 / address buckets.

Bitcoin pipeline per puzzle:
  d -> P -> SHA256(compressed pubkey) -> RIPEMD160 = hash160 (20 B)
  payload = 0x00 || hash160 || SHA256d(payload)[0:4]  (25 B) -> Base58 address

Buckets: version byte, each hash160 byte, each checksum byte, each sha256 byte,
         address payload int/frac, per-byte /255 normalizations.
"""

from __future__ import annotations

import hashlib
import itertools
import math
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    N,
    p,
    pubkey_from_scalar,
    puzzle_band,
    y_even,
    y_roots,
)
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "log2_d_hash160_bucket_search.txt"
CSV_OUT = ARCHIVE / "log2_d_hash160_bucket_search.csv"

getcontext().prec = 50
LOG2_N = float(Decimal(N).ln() / Decimal(2).ln())
LOG2_P = float(Decimal(p).ln() / Decimal(2).ln())
LOG2_7 = math.log2(7)


@dataclass
class PuzzleCrypto:
    n: int
    d: int
    px: int
    py: int
    lo: int
    hi: int
    y_d: float  # log2(d)/log2(N)
    frac_d: float  # (d-lo)/lo
    log_pos: float  # log2(d)-(n-1)
    comp: bytes
    sha: bytes
    h160: bytes
    version: int
    checksum: bytes
    payload: bytes
    addr: str


def hash160_pipeline(x: int, y: int) -> tuple[bytes, bytes, bytes, bytes, bytes]:
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    comp = pref + x.to_bytes(32, "big")
    sha = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    payload = vh + chk
    return comp, sha, h160, chk, payload


def base58_encode(payload: bytes) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(payload, "big")
    result = ""
    while n:
        n, r = divmod(n, 58)
        result = alphabet[r] + result
    for byte in payload:
        if byte == 0:
            result = "1" + result
        else:
            break
    return result


def build_row(n: int, d: int, px: int, py: int) -> PuzzleCrypto:
    lo, hi, _ = puzzle_band(n)
    comp, sha, h160, chk, payload = hash160_pipeline(px, py)
    y_d = math.log2(d) / LOG2_N if d > 0 else 0.0
    frac_d = (d - lo) / lo if lo else 0.0
    return PuzzleCrypto(
        n=n,
        d=d,
        px=px,
        py=py,
        lo=lo,
        hi=hi,
        y_d=y_d,
        frac_d=frac_d,
        log_pos=math.log2(d) - (n - 1) if d > 0 else 0.0,
        comp=comp,
        sha=sha,
        h160=h160,
        version=0,
        checksum=chk,
        payload=payload,
        addr=base58_encode(payload),
    )


def bucket_features(row: PuzzleCrypto) -> dict[str, float]:
    f: dict[str, float] = {}
    f["n/256"] = row.n / 256.0
    f["n/(128+log2(7))"] = row.n / (128.0 + LOG2_7)
    f["(n-1)/256"] = (row.n - 1) / 256.0
    h160_int = int.from_bytes(row.h160, "big")
    sha_int = int.from_bytes(row.sha, "big")
    pay_int = int.from_bytes(row.payload, "big")
    if h160_int > 0:
        f["log2(h160)/log2(N)"] = math.log2(h160_int) / LOG2_N
    if sha_int > 0:
        f["log2(sha256)/log2(N)"] = math.log2(sha_int) / LOG2_N
    if pay_int > 0:
        f["log2(payload)/log2(N)"] = math.log2(pay_int) / LOG2_N
    f["h160/2^160"] = h160_int / (2**160)
    f["sha/2^256"] = sha_int / (2**256)
    f["payload/2^200"] = pay_int / (2**200)
    f["h160 mod lo / lo"] = (h160_int % row.lo) / row.lo if row.lo else 0.0
    f["d mod lo / lo"] = (row.d % row.lo) / row.lo if row.lo else 0.0
    f["sum(h160)/5100"] = sum(row.h160) / (20 * 255.0)
    f["sum(sha)/8160"] = sum(row.sha) / (32 * 255.0)
    f["sum(chk)/1020"] = sum(row.checksum) / (4 * 255.0)
    chk_int = int.from_bytes(row.checksum, "big")
    f["chk/2^32"] = chk_int / (2**32)
    for i, b in enumerate(row.h160):
        f[f"h160[{i:02d}]/255"] = b / 255.0
    for i, b in enumerate(row.sha):
        f[f"sha[{i:02d}]/255"] = b / 255.0
    for i, b in enumerate(row.checksum):
        f[f"chk[{i}]/255"] = b / 255.0
    # address char buckets (first 4 base58 as ord/123)
    for i, ch in enumerate(row.addr[:8]):
        f[f"addr[{i}]/58"] = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".index(ch) / 58.0
    return f


def eval_combo(rows: list[PuzzleCrypto], target: str, expr: str, pred_fn) -> tuple[float, float]:
    """Return (mean_abs_err, std_err) for y_d - pred across rows."""
    errs = []
    for r in rows:
        feats = bucket_features(r)
        try:
            pred = pred_fn(feats, r)
        except Exception:
            return 999.0, 999.0
        errs.append(r.y_d - pred)
    if not errs:
        return 999.0, 999.0
    mean_abs = sum(abs(e) for e in errs) / len(errs)
    mu = sum(errs) / len(errs)
    var = sum((e - mu) ** 2 for e in errs) / len(errs)
    return mean_abs, math.sqrt(var)


def main() -> int:
    keys = parse_53125()
    rows: list[PuzzleCrypto] = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        lo, hi, _ = puzzle_band(n)
        if not (lo <= pk.d < hi):
            continue
        rows.append(build_row(n, pk.d, pk.px, pk.py))

    lines = [
        "LOG2(d)/LOG2(N) vs HASH160 / SHA256 / ADDRESS BUCKET SEARCH",
        f"solved puzzles in band: {len(rows)}",
        f"log2(N) = {LOG2_N:.12f}",
        "",
    ]

    # --- single feature correlation ---
    feats_all: dict[str, list[float]] = {}
    y_vals = [r.y_d for r in rows]
    for r in rows:
        for k, v in bucket_features(r).items():
            feats_all.setdefault(k, []).append(v)

    corrs: list[tuple[float, str]] = []
    for k, xs in feats_all.items():
        if len(xs) != len(rows):
            continue
        mx = sum(xs) / len(xs)
        my = sum(y_vals) / len(y_vals)
        num = sum((xs[i] - mx) * (y_vals[i] - my) for i in range(len(rows)))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in y_vals))
        if dx < 1e-15 or dy < 1e-15:
            continue
        corrs.append((num / (dx * dy), k))
    corrs.sort(key=lambda t: -abs(t[0]))

    lines.append("=== top |correlation| single bucket vs log2(d)/log2(N) ===")
    for c, k in corrs[:25]:
        lines.append(f"  r={c:+.4f}  {k}")
    lines.append("")

    # --- constant difference y_d - feat (low std = invariant) ---
    inv: list[tuple[float, float, str]] = []
    for k, xs in feats_all.items():
        if len(xs) != len(rows):
            continue
        diffs = [rows[i].y_d - xs[i] for i in range(len(rows))]
        mu = sum(diffs) / len(diffs)
        std = math.sqrt(sum((d - mu) ** 2 for d in diffs) / len(diffs))
        inv.append((std, mu, k))
    inv.sort()

    lines.append("=== best invariant: y_d - bucket (low std) ===")
    for std, mu, k in inv[:30]:
        lines.append(f"  std={std:.6f}  mean_diff={mu:+.6f}  {k}")
    lines.append("")

    # --- pairwise sums/diffs of buckets ---
    pair_inv: list[tuple[float, str]] = []
    top_keys = [k for _, _, k in inv[:40]]
    for a, b in itertools.combinations(top_keys, 2):
        diffs = []
        for i, r in enumerate(rows):
            fa = bucket_features(r)[a]
            fb = bucket_features(r)[b]
            for name, pred in [
                (f"y - ({a} + {b})", fa + fb),
                (f"y - ({a} - {b})", fa - fb),
                (f"y - ({a}*{b})", fa * fb if fa * fb < 10 else None),
            ]:
                if pred is None:
                    continue
                diffs.append((name, r.y_d - pred))
        # skip heavy; test sum only
        diffs2 = [r.y_d - (bucket_features(r)[a] + bucket_features(r)[b]) for r in rows]
        mu = sum(diffs2) / len(diffs2)
        std = math.sqrt(sum((d - mu) ** 2 for d in diffs2) / len(diffs2))
        if std < 0.15:
            pair_inv.append((std, f"y - ({a}+{b}) std={std:.5f} mean={mu:+.5f}"))

    pair_inv.sort()
    lines.append("=== pairwise bucket sums (std < 0.15) ===")
    for std, msg in pair_inv[:20]:
        lines.append(f"  {msg}")
    if not pair_inv:
        lines.append("  (none under 0.15 std)")
    lines.append("")

    # --- exact checks ---
    lines.append("=== exact relations on solved set ===")
    exact = {
        "y_d == frac_d": sum(1 for r in rows if abs(r.y_d - r.frac_d) < 1e-9),
        "y_d == log_pos/256": sum(1 for r in rows if abs(r.y_d - r.log_pos / 256) < 0.01),
        "y_d == n/256": sum(1 for r in rows if abs(r.y_d - r.n / 256) < 0.01),
        "frac_d == h160 mod lo / lo": sum(
            1
            for r in rows
            if abs(r.frac_d - (int.from_bytes(r.h160, "big") % r.lo) / r.lo) < 1e-6
        ),
    }
    for k, v in exact.items():
        lines.append(f"  {k}: {v}/{len(rows)}")
    lines.append("")

    # --- P135 prediction from top invariants ---
    lines.append("=== P135 predictions (unsolved) ===")
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    want_even = rsz.pub_compressed.startswith("02")
    y_pos, y_neg = y_roots(px)
    py = y_pos if (y_pos % 2 == 0) == want_even else y_neg
    lo135, hi135, _ = puzzle_band(135)
    prow = build_row(135, 0, px, py)
    pf = bucket_features(prow)

    lines.append(f"  P135 addr: {prow.addr}")
    lines.append(f"  h160: {prow.h160.hex()}")
    lines.append(f"  checksum: {prow.checksum.hex()}")
    lines.append("")

    hits: list[str] = []
    for std, mu, k in inv[:15]:
        pred_y = pf[k] + mu  # y_d ≈ bucket + mean_diff inverted: pred = bucket, err = y-bucket
        # reconstruct d from y_d ≈ log2(d)/LOG2_N -> d = 2^(y_d * LOG2_N)
        # also band map: frac ≈ y_d for small? use frac = pred_y * LO2_N / log2(N) no
        # y_d = log2(d)/LOG2_N  => log2(d) = y_d * LOG2_N  => d = 2^(y_d * LOG2_N)
        y_pred = pf[k] + mu  # if invariant is y_d - bucket = mu, then y_d = bucket + mu
        d_est = int(2 ** (y_pred * LOG2_N))
        d_frac = int(lo135 * (1 + pf[k]))  # direct bucket as frac
        d_inv = int(2 ** ((pf[k] + mu) * LOG2_N))
        for tag, d_c in [
            (f"2^(y_pred*log2N) inv {k}", d_inv),
            (f"lo*(1+bucket) {k}", d_frac),
        ]:
            if lo135 <= d_c < hi135:
                try:
                    gx, gy = pubkey_from_scalar(d_c)
                    ok = gx == px and gy == py
                    lines.append(
                        f"  {tag}: d_bits={d_c.bit_length()} ec={ok} tail...{str(d_c)[-6:]}"
                    )
                    if ok:
                        hits.append(f"{tag} d={d_c}")
                except Exception:
                    pass

    # best correlation predictor: linear y = a*feat + b for top feat
    if corrs:
        best_k = corrs[0][1]
        xs = [bucket_features(r)[best_k] for r in rows]
        ys = y_vals
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        varx = sum((x - mx) ** 2 for x in xs)
        if varx > 0:
            a = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(rows))) / varx
            b = my - a * mx
            y135 = a * pf[best_k] + b
            d135 = int(2 ** (y135 * LOG2_N))
            lines.append(
                f"  linear {best_k}: a={a:.6f} b={b:.6f} -> d135 bits={d135.bit_length()} "
                f"band={lo135 <= d135 < hi135}"
            )
            if lo135 <= d135 < hi135:
                gx, gy = pubkey_from_scalar(d135)
                ok = gx == px and gy == py
                lines.append(f"    EC={ok}")
                if ok:
                    hits.append(f"linear {best_k} d={d135}")

    lines.append("")
    lines.append("=== VERDICT ===")
    if hits:
        lines.append(f"  EC HITS: {len(hits)}")
        for h in hits:
            lines.append(f"    {h}")
    else:
        lines.append("  No P135 EC hit from bucket invariants.")
        lines.append(f"  Best single-bucket invariant std: {inv[0][0]:.6f} ({inv[0][2]})")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")

    with CSV_OUT.open("w", encoding="utf-8") as f:
        f.write("n,y_d,frac_d,log_pos,h160_hex,checksum,address\n")
        for r in rows:
            f.write(
                f"{r.n},{r.y_d:.12f},{r.frac_d:.12f},{r.log_pos:.12f},"
                f"{r.h160.hex()},{r.checksum.hex()},{r.addr}\n"
            )

    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
