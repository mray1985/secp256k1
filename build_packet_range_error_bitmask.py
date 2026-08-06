#!/usr/bin/env python3
"""
Packet / coordinate-derived range_error_bitmask scan.

Point-derived rulers (not blunt range anchors):
  expected = L + floor(frac(signal) · width)

Compare entropy to range-only baseline ≈ 6.3.

Writes ONLY under ARCHIVE/briefcase/misalignments/
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "misalignments"

RANGE_ONLY_BASELINE_ENTROPY = 6.3
HINGE = Decimal("0.58496250072115618145373894394781650876")
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240


def frac(x: Decimal) -> Decimal:
    return x - x.to_integral_value(rounding="ROUND_FLOOR")


def set_bits(x: int) -> list[int]:
    x = abs(x)
    bits = []
    i = 0
    while x:
        if x & 1:
            bits.append(i)
        x >>= 1
        i += 1
    return bits


def landing(lo: int, width: int, hi: int, t: Decimal) -> int:
    """L + floor(t * width), clamped to [lo, hi]. t in [0,1] preferred."""
    if t < 0:
        t = Decimal(0)
    if t > 1:
        t = Decimal(1)
    exp = lo + int(t * Decimal(width))
    if exp > hi:
        exp = hi
    if exp < lo:
        exp = lo
    return exp


def signals(px: int, py: int) -> dict[str, Decimal]:
    """Unit-interval signals from public coordinates."""
    pmy = (p - py) % p
    packet = Decimal(f"{px}.{pmy}")
    packet_p = packet / Decimal(p)
    px_over_p = Decimal(px) / Decimal(p)
    py_over_p = Decimal(py) / Decimal(p)
    pmy_over_p = Decimal(pmy) / Decimal(p)

    # (Px * Gx^-1 mod p) / p
    gx_ratio = Decimal((px * inv(GX, p)) % p) / Decimal(p)

    # β slot index: which of {Px/β², Px/β, Px} — pubkey is always slot 3 (index 2)
    # Still record for completeness; expect weak.
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    # slot fingerprint: use (Px mod 3) is wrong; use which y-branch + slot
    # Use fractional position of px2/p as a continuous β-related signal instead
    beta_slot_frac = Decimal(2) / Decimal(3)  # pubkey always slot 3
    px2_over_p = Decimal(px2) / Decimal(p)
    px1_over_p = Decimal(px1) / Decimal(p)

    return {
        "packet_width": frac(packet_p),  # packet_p already in (0,1)
        "packet_p_raw": packet_p,
        "packet_defect_width": frac(packet_p * Decimal(DELTA)),
        "packet_N_shadow": frac(packet_p * Decimal(N)),
        "packet_B4_width": frac(packet_p * Decimal(pow((1 << 32) + 977, 4))),
        "x_ratio_width": px_over_p,
        "y_ratio_width": py_over_p,
        "pmy_ratio_width": pmy_over_p,
        "gx_ratio_width": gx_ratio,
        "beta_slot_width": beta_slot_frac,
        "px1_ratio_width": px1_over_p,
        "px2_ratio_width": px2_over_p,
        "hinge_control": HINGE,  # not point-derived; baseline control
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    per_ruler: dict[str, list[dict]] = defaultdict(list)
    ruler_names: list[str] = []

    for n in range(1, 161):
        e = catalog[n]
        if not e.solved or not e.public_key or e.private_key <= 0:
            continue
        d = e.private_key
        lo, hi = e.range_min, e.range_max
        width = hi - lo + 1
        px, py = pubkey_xy(e.public_key)
        sigs = signals(px, py)
        if not ruler_names:
            ruler_names = [k for k in sigs if k != "packet_p_raw"]

        for rname in ruler_names:
            t = sigs[rname]
            expected = landing(lo, width, hi, t)
            err = d - expected
            bits = set_bits(err)
            rel = [b - (n - 1) for b in bits]
            per_ruler[rname].append({
                "puzzle": n,
                "d": str(d),
                "signal": format(t, "f"),
                "expected": str(expected),
                "error": str(err),
                "error_hex": hex(abs(err)),
                "bits": bits,
                "relative_bits_msb": rel,
                "popcount": len(bits),
                "binary_sum": " + ".join(f"2^{b}" for b in reversed(bits)) if bits else "0",
                "normalized_error": format(Decimal(err) / Decimal(width), "f"),
                "sign": 0 if err == 0 else (1 if err > 0 else -1),
            })

    rankings = []
    for rname in ruler_names:
        rows = per_ruler[rname]
        total = len(rows)
        pattern_counts = Counter(tuple(r["relative_bits_msb"]) for r in rows)
        top = pattern_counts.most_common(5)
        ent = 0.0
        for _, c in pattern_counts.items():
            p_i = c / total
            ent -= p_i * math.log2(p_i)
        best_pat, best_c = top[0] if top else ((), 0)
        shared = sum(c for _, c in pattern_counts.items() if c >= 2)

        # transfer reconstruct
        matches = 0
        for r in rows:
            n = r["puzzle"]
            recon = 0
            for rel in best_pat:
                bit = (n - 1) + rel
                if bit >= 0:
                    recon |= 1 << bit
            if abs(int(r["error"])) == recon:
                matches += 1

        beats_baseline = ent < RANGE_ONLY_BASELINE_ENTROPY - 0.3
        if matches / total > 0.5:
            verdict = "STRONG"
        elif best_c >= 5 and beats_baseline:
            verdict = "PROMISING"
        elif best_c >= 2 or (beats_baseline and best_c >= 2):
            verdict = "WEAK"
        else:
            verdict = "REJECT"

        rankings.append({
            "ruler": rname,
            "entropy": ent,
            "baseline_entropy": RANGE_ONLY_BASELINE_ENTROPY,
            "beats_baseline": beats_baseline,
            "unique_patterns": len(pattern_counts),
            "best_pattern_count": best_c,
            "best_pattern_relative_msb": list(best_pat),
            "puzzles_in_shared_patterns": shared,
            "transfer_reconstruct": matches,
            "puzzles_matched": matches,
            "n_solved": total,
            "match_rate": matches / total,
            "mean_popcount": sum(r["popcount"] for r in rows) / total,
            "top_patterns": [
                {"relative_bits_msb": list(pat), "count": c}
                for pat, c in top
            ],
            "verdict": verdict,
        })

    rankings.sort(key=lambda r: (r["entropy"], -r["best_pattern_count"]))

    # P135 candidates only for STRONG rulers
    e135 = catalog[135]
    lo, hi = e135.range_min, e135.range_max
    width = hi - lo + 1
    px135, py135 = pubkey_xy(e135.public_key)
    sig135 = signals(px135, py135)
    p135_candidates = []
    for r in rankings:
        if r["verdict"] != "STRONG":
            continue
        rname = r["ruler"]
        expected = landing(lo, width, hi, sig135[rname])
        pat = r["best_pattern_relative_msb"]
        recon = 0
        for rel in pat:
            bit = (135 - 1) + rel
            if bit >= 0:
                recon |= 1 << bit
        for sign in (1, -1):
            cand = expected + sign * recon
            if lo <= cand <= hi:
                p135_candidates.append({
                    "ruler": rname,
                    "expected": str(expected),
                    "mask": str(recon),
                    "sign": sign,
                    "candidate_d": str(cand),
                    "must_verify": "[d]G == P135",
                })

    strong = [r for r in rankings if r["verdict"] == "STRONG"]
    promising = [r for r in rankings if r["verdict"] == "PROMISING"]

    payload = {
        "exhibit": "packet_range_error_bitmask",
        "location": "ARCHIVE/briefcase/misalignments/",
        "range_only_baseline_entropy": RANGE_ONLY_BASELINE_ENTROPY,
        "rankings": rankings,
        "P135_candidates": p135_candidates,
        "summary": {
            "strong": [r["ruler"] for r in strong],
            "promising": [r["ruler"] for r in promising],
            "best_ruler": rankings[0]["ruler"] if rankings else None,
            "best_entropy": rankings[0]["entropy"] if rankings else None,
            "any_beats_baseline": any(r["beats_baseline"] for r in rankings),
        },
        "per_ruler": {k: v for k, v in per_ruler.items()},
        "final_truth": "[candidate_d]G == P135",
    }

    (OUT / "packet_range_error_bitmask.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# packet_range_error_bitmask",
        "",
        "Point-derived rulers: `expected = L + floor(frac(signal) · width)`",
        "",
        f"Range-only baseline entropy ≈ **{RANGE_ONLY_BASELINE_ENTROPY}**",
        "",
        "Thresholds: STRONG >50% reconstruct · PROMISING count≥5 & entropy≪6.3 · WEAK 2–3 · REJECT",
        "",
        "## Rankings",
        "",
        "| ruler | entropy | best_pattern_count | transfer_reconstruct | puzzles_matched | beats_6.3 | verdict |",
        "|-------|---------|--------------------|--------------------|-----------------|-----------|---------|",
    ]
    for r in rankings:
        lines.append(
            f"| `{r['ruler']}` | {r['entropy']:.3f} | {r['best_pattern_count']} | "
            f"{r['transfer_reconstruct']} | {r['puzzles_matched']}/{r['n_solved']} | "
            f"{r['beats_baseline']} | **{r['verdict']}** |"
        )

    lines.extend(["", "## Top patterns", ""])
    for r in rankings:
        lines.append(f"### `{r['ruler']}` — {r['verdict']}")
        lines.append("")
        for pat in r["top_patterns"][:3]:
            lines.append(f"- count **{pat['count']}**: `{pat['relative_bits_msb']}`")
        lines.append("")

    lines.append("## P135 candidates")
    lines.append("")
    if p135_candidates:
        for c in p135_candidates:
            lines.append(
                f"- `{c['ruler']}` sign={c['sign']}: `{c['candidate_d']}` "
                f"(must `[d]G == P135`)"
            )
    else:
        lines.append("_None — no STRONG transferable mask._")

    lines.extend([
        "",
        "## Ruling",
        "",
        f"Best entropy: `{payload['summary']['best_entropy']:.3f}` "
        f"on `{payload['summary']['best_ruler']}` "
        f"(baseline {RANGE_ONLY_BASELINE_ENTROPY}).",
        "",
        f"Beats baseline? **{payload['summary']['any_beats_baseline']}**",
        "",
        "Judge Popcorn: **the range fence alone is not the sky. "
        "Telescope on Px, Py, packet, defect, β — only [d]G is sunrise.**",
        "",
    ])

    (OUT / "packet_range_error_bitmask.md").write_text("\n".join(lines), encoding="utf-8")

    # README update
    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/misalignments",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `p1_baseline_misalignments.*` | P1 as origin |",
            "| `range_error_bitmask.*` | range-only rulers (baseline entropy ≈ 6.3) |",
            "| `packet_range_error_bitmask.*` | point-derived rulers vs baseline |",
            "",
            "```text",
            "python build_p1_baseline_misalignments.py",
            "python build_range_error_bitmask.py",
            "python build_packet_range_error_bitmask.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"baseline={RANGE_ONLY_BASELINE_ENTROPY}")
    for r in rankings:
        print(
            f"  {r['verdict']:10} {r['ruler']:22} ent={r['entropy']:.3f} "
            f"best={r['best_pattern_count']} recon={r['transfer_reconstruct']}/{r['n_solved']}"
        )
    print(f"wrote {OUT / 'packet_range_error_bitmask.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
