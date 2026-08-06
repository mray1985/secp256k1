#!/usr/bin/env python3
"""
Full decimal RIPEMD160 correlation sweep in P160 band [2^159, 2^160).

Samples d = LO + offset for offset in [0, N) and tests every practical
correlation vs band offset and vs P160 anchor hash160.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402

LO160 = 1 << 159
DEFAULT_N = 10_000


def hash160_compressed(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    x, y = pub[:32], pub[32:]
    comp = (b"\x02" if (y[-1] & 1) == 0 else b"\x03") + x
    h = hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()
    return int.from_bytes(h, "big")


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def spearman(xs: list[int | float], ys: list[int | float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")

    def ranks(vals: list[int | float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    return pearson(ranks(xs), ranks(ys))


def p160_hash160() -> int:
    comp = bytes.fromhex(load_catalog()[160].public_key)
    return int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest(), "big"
    )


def digit_string(h: int) -> str:
    return str(h)


def prefix_int(s: str, k: int) -> int:
    return int(s[:k])


def suffix_int(s: str, k: int) -> int:
    return int(s[-k:])


def middle_int(s: str, start: int, length: int) -> int:
    return int(s[start : start + length])


def prefix_match_len(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def suffix_match_len(a: str, b: str) -> int:
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


def digit_sum(s: str) -> int:
    return sum(int(c) for c in s)


def digital_root(s: str) -> int:
    x = digit_sum(s)
    while x >= 10:
        x = sum(int(c) for c in str(x))
    return x


def build_dataset(n: int, h_anchor: int) -> tuple[list[dict], str, int]:
    s_anchor = digit_string(h_anchor)
    width = len(s_anchor)
    rows: list[dict] = []
    for off in range(n):
        d = LO160 + off
        h = hash160_compressed(d)
        raw = digit_string(h)
        s = raw.rjust(width, "0")
        row: dict = {
            "offset": off,
            "d": d,
            "hash160": h,
            "s": s,
            "raw": raw,
            "ndigits": len(raw),
            "log_dist": math.log10(abs(h - h_anchor) + 1),
            "prefix_match": prefix_match_len(raw, s_anchor),
            "suffix_match": suffix_match_len(raw, s_anchor),
            "digit_sum": digit_sum(s),
            "digital_root": digital_root(s),
            "last_digit": int(s[-1]),
            "first_digit": int(s.lstrip("0")[0]) if h else 0,
        }
        rows.append(row)
    return rows, s_anchor, width


def corr_table(rows: list[dict], features: list[tuple[str, str]]) -> list[dict]:
    offsets = [float(r["offset"]) for r in rows]
    out = []
    for name, key in features:
        ys = [float(r[key]) for r in rows]
        r_p = pearson(offsets, ys)
        if all(isinstance(r[key], int) for r in rows):
            r_s = spearman([r["offset"] for r in rows], [r[key] for r in rows])
        else:
            r_s = spearman([r["offset"] for r in rows], ys)
        out.append({"feature": name, "pearson": r_p, "spearman": r_s, "abs_max": max(abs(r_p), abs(r_s))})
    return sorted(out, key=lambda x: -x["abs_max"])


def scan_prefix_suffix(rows: list[dict], s_anchor: str) -> dict:
    nd = len(s_anchor)
    pref_pearson = []
    suff_pearson = []
    for k in range(1, min(16, nd + 1)):
        pref = [prefix_int(r["s"], k) for r in rows]
        suff = [suffix_int(r["s"], k) for r in rows]
        offsets = [float(r["offset"]) for r in rows]
        pref_pearson.append({"k": k, "pearson": pearson(offsets, [float(x) for x in pref])})
        suff_pearson.append({"k": k, "pearson": pearson(offsets, [float(x) for x in suff])})

    # distance to P160 prefix/suffix as int
    pref_dist = []
    suff_dist = []
    for k in range(1, 16):
        pa = prefix_int(s_anchor, k)
        sa = suffix_int(s_anchor, k)
        pd = [abs(prefix_int(r["s"], k) - pa) for r in rows]
        sd = [abs(suffix_int(r["s"], k) - sa) for r in rows]
        offsets = [float(r["offset"]) for r in rows]
        pref_dist.append({"k": k, "pearson": pearson(offsets, [float(x) for x in pd])})
        suff_dist.append({"k": k, "pearson": pearson(offsets, [float(x) for x in sd])})

    return {
        "prefix_value_vs_offset": pref_pearson,
        "suffix_value_vs_offset": suff_pearson,
        "prefix_distance_to_P160": pref_dist,
        "suffix_distance_to_P160": suff_dist,
    }


def scan_digit_positions(rows: list[dict], s_anchor: str) -> list[dict]:
    """Per decimal position: digit value vs offset; match to P160 digit."""
    nd = len(s_anchor)
    offsets = [float(r["offset"]) for r in rows]
    out = []
    for pos in range(nd):
        vals = [int(r["raw"][pos]) if pos < len(r["raw"]) else 0 for r in rows]
        match = [
            1 if pos < len(r["raw"]) and r["raw"][pos] == s_anchor[pos] else 0 for r in rows
        ]
        out.append(
            {
                "pos": pos,
                "side": "left" if pos < nd // 2 else "right",
                "anchor_digit": int(s_anchor[pos]),
                "pearson_digit": pearson(offsets, [float(v) for v in vals]),
                "pearson_match": pearson(offsets, [float(m) for m in match]),
                "match_rate": sum(match) / len(match),
            }
        )
    return sorted(out, key=lambda x: -abs(x["pearson_digit"]))


def scan_middle_windows(rows: list[dict], s_anchor: str) -> list[dict]:
    nd = len(s_anchor)
    offsets = [float(r["offset"]) for r in rows]
    out = []
    for length in (3, 5, 7, 9):
        for start in range(0, nd - length + 1, max(1, length // 2)):
            seg_anchor = middle_int(s_anchor, start, length)
            vals = [middle_int(r["s"], start, length) for r in rows]
            dists = [abs(v - seg_anchor) for v in vals]
            out.append(
                {
                    "start": start,
                    "length": length,
                    "segment": s_anchor[start : start + length],
                    "pearson_value": pearson(offsets, [float(v) for v in vals]),
                    "pearson_dist": pearson(offsets, [float(d) for d in dists]),
                }
            )
    return sorted(out, key=lambda x: -abs(x["pearson_dist"]))[:25]


def mod_correlations(rows: list[dict]) -> list[dict]:
    offsets = [float(r["offset"]) for r in rows]
    mods = [10, 100, 1000, 10000, 100000, 1000000, 10**9, 10**12, 10**15]
    out = []
    for m in mods:
        vals = [r["hash160"] % m for r in rows]
        out.append({"mod": m, "pearson": pearson(offsets, [float(v) for v in vals])})
    return sorted(out, key=lambda x: -abs(x["pearson"]))


def lag_correlations(rows: list[dict]) -> dict:
    """Consecutive offset steps: does hash160 change predictably?"""
    dh = [rows[i + 1]["hash160"] - rows[i]["hash160"] for i in range(len(rows) - 1)]
    d_prefix = [rows[i + 1]["prefix_match"] - rows[i]["prefix_match"] for i in range(len(rows) - 1)]
    d_suffix = [rows[i + 1]["suffix_match"] - rows[i]["suffix_match"] for i in range(len(rows) - 1)]
    offs = [float(rows[i]["offset"]) for i in range(len(rows) - 1)]
    return {
        "pearson_offset_vs_delta_hash": pearson(offs, [float(x) for x in dh]),
        "pearson_offset_vs_delta_prefix_match": pearson(offs, [float(x) for x in d_prefix]),
        "pearson_offset_vs_delta_suffix_match": pearson(offs, [float(x) for x in d_suffix]),
        "mean_abs_delta_hash": sum(abs(x) for x in dh) / len(dh),
    }


def block_compare(rows: list[dict], block: int = 1000) -> list[dict]:
    n = len(rows)
    chunks = [rows[i : i + block] for i in range(0, n, block)]
    out = []
    for i, ch in enumerate(chunks):
        lo, hi = ch[0]["offset"], ch[-1]["offset"]
        mean_pm = sum(r["prefix_match"] for r in ch) / len(ch)
        mean_sm = sum(r["suffix_match"] for r in ch) / len(ch)
        mean_ld = sum(r["log_dist"] for r in ch) / len(ch)
        out.append(
            {
                "block": i + 1,
                "offset_lo": lo,
                "offset_hi": hi,
                "mean_prefix_match": mean_pm,
                "mean_suffix_match": mean_sm,
                "mean_log10_dist": mean_ld,
            }
        )
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=DEFAULT_N, help="sample size from band floor")
    args = ap.parse_args()

    h_anchor = p160_hash160()
    s_anchor = digit_string(h_anchor)
    print(f"P160 hash160 ({len(s_anchor)} digits): {h_anchor}")
    print(f"Sampling d = 2^159 + [0..{args.n - 1}]")
    print("Building dataset...", flush=True)

    rows, s_anchor, width = build_dataset(args.n, h_anchor)
    s_anchor = s_anchor.rjust(width, "0")

    base_features = [
        ("hash160 (full int)", "hash160"),
        ("log10 distance to P160", "log_dist"),
        ("prefix match length", "prefix_match"),
        ("suffix match length", "suffix_match"),
        ("digit sum", "digit_sum"),
        ("digital root", "digital_root"),
        ("first decimal digit", "first_digit"),
        ("last decimal digit", "last_digit"),
        ("decimal length", "ndigits"),
    ]

    top_base = corr_table(rows, base_features)
    ps = scan_prefix_suffix(rows, s_anchor)
    digits = scan_digit_positions(rows, s_anchor)
    middle = scan_middle_windows(rows, s_anchor)
    mods = mod_correlations(rows)
    lag = lag_correlations(rows)
    blocks = block_compare(rows)

    # top |r| overall
    all_ranked: list[tuple[str, float, float]] = []
    for t in top_base:
        all_ranked.append((t["feature"], t["pearson"], t["spearman"]))
    for t in ps["prefix_distance_to_P160"]:
        all_ranked.append((f"prefix_dist_k{t['k']}", t["pearson"], float("nan")))
    for t in ps["suffix_distance_to_P160"]:
        all_ranked.append((f"suffix_dist_k{t['k']}", t["pearson"], float("nan")))
    for t in digits[:10]:
        all_ranked.append((f"digit_pos{t['pos']}", t["pearson_digit"], t["pearson_match"]))
    for t in middle[:10]:
        all_ranked.append((f"mid[{t['start']}:{t['start']+t['length']}]", t["pearson_dist"], t["pearson_value"]))

    all_ranked.sort(key=lambda x: -max(abs(x[1]), abs(x[2]) if not math.isnan(x[2]) else 0))

    print()
    print("=== TOP 20 |correlation| with band offset (Pearson / Spearman) ===")
    for name, rp, rs in all_ranked[:20]:
        rs_s = f"{rs:+.5f}" if not math.isnan(rs) else "   n/a"
        print(f"  {name:32s}  P={rp:+.5f}  S={rs_s}")

    print()
    print("=== SIGNIFICANCE GATE (|r| > 0.05 on n={}) ===".format(args.n))
    sig = [x for x in all_ranked if max(abs(x[1]), abs(x[2]) if not math.isnan(x[2]) else 0) > 0.05]
    print(f"  features with |r|>0.05: {len(sig)} / {len(all_ranked)}")
    if not sig:
        print("  NONE — all correlations below noise floor")
    else:
        for name, rp, rs in sig[:15]:
            rs_s = f"{rs:+.5f}" if not math.isnan(rs) else "n/a"
            print(f"    {name}: P={rp:+.5f} S={rs_s}")

    print()
    print("=== PER-DECIMAL-DIGIT vs offset (top 10 |r|) ===")
    for t in sorted(digits, key=lambda x: -abs(x["pearson_digit"]))[:10]:
        print(
            f"  pos={t['pos']:2d} anchor={t['anchor_digit']} "
            f"P={t['pearson_digit']:+.5f} match_rate={t['match_rate']:.3f}"
        )

    print()
    print("=== PREFIX/SUFFIX distance to P160 (Pearson vs offset) ===")
    print("  prefix dist:", [f"k{t['k']}:{t['pearson']:+.4f}" for t in ps["prefix_distance_to_P160"][:8]])
    print("  suffix dist:", [f"k{t['k']}:{t['pearson']:+.4f}" for t in ps["suffix_distance_to_P160"][:8]])

    print()
    print("=== MOD hash160 % M vs offset ===")
    for t in mods:
        print(f"  mod {t['mod']:>12d}: r={t['pearson']:+.5f}")

    print()
    print("=== LAG / consecutive step ===")
    for k, v in lag.items():
        print(f"  {k}: {v}")

    print()
    print("=== 1000-block means (prefix/suffix match, log dist) ===")
    for b in blocks:
        print(
            f"  block {b['block']} off {b['offset_lo']:5d}-{b['offset_hi']:5d}: "
            f"pref_match={b['mean_prefix_match']:.3f} suff_match={b['mean_suffix_match']:.3f} "
            f"log_dist={b['mean_log10_dist']:.3f}"
        )

    # nearest full hash
    nearest = sorted(rows, key=lambda r: abs(r["hash160"] - h_anchor))[:5]
    print()
    print("=== NEAREST 5 full hash160 to P160 anchor ===")
    for r in nearest:
        print(f"  offset={r['offset']} prefix_match={r['prefix_match']}/{len(s_anchor)} dist={abs(r['hash160']-h_anchor)}")

    report = {
        "n": args.n,
        "p160_hash160": str(h_anchor),
        "ndigits": len(s_anchor),
        "top20": [{"name": a, "pearson": b, "spearman": c} for a, b, c in all_ranked[:20]],
        "significant_count": len(sig),
        "digit_positions": digits,
        "prefix_suffix": ps,
        "middle_windows": middle,
        "mod_correlations": mods,
        "lag": lag,
        "blocks": blocks,
        "nearest5": [
            {"offset": r["offset"], "prefix_match": r["prefix_match"], "hash160": str(r["hash160"])}
            for r in nearest
        ],
    }

    out_json = ROOT / "ARCHIVE" / "p160_band_full_rmd160_correlations.json"
    out_md = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal" / "p160_band_full_rmd160_correlations.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# P160 band — full RIPEMD160 decimal correlation sweep",
        "",
        f"Sample: `d = 2^159 + offset`, offset `0..{args.n - 1}`",
        f"P160 anchor ({len(s_anchor)} digits): `{h_anchor}`",
        "",
        "## Top correlations with band offset",
        "",
        "| feature | Pearson | Spearman |",
        "|---------|---------|----------|",
    ]
    for name, rp, rs in all_ranked[:25]:
        rs_s = f"{rs:+.5f}" if not math.isnan(rs) else "n/a"
        lines.append(f"| {name} | {rp:+.5f} | {rs_s} |")
    lines += [
        "",
        f"Features with |r|>0.05: **{len(sig)}**",
        "",
        "## Ruling",
        "",
    ]
    if len(sig) <= 3:
        lines.append("No material correlation between band offset and any decimal segment of hash160.")
        lines.append("P160 anchor alignment does not tighten as d walks the band floor.")
    else:
        lines.append("Weak correlations detected — inspect JSON for detail.")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
