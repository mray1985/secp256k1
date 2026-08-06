#!/usr/bin/env python3
"""
range_error_bitmask / misalignment fingerprint scan.

For each solved puzzle and each ruler:
  error = actual_d - expected_landing
  decompose |error| into set bits
  normalize bit positions by puzzle size
  rank rulers by repeated relative bit patterns

Writes ONLY under ARCHIVE/briefcase/misalignments/
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import DELTA, N, p
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "misalignments"

B = (1 << 32) + 977
B4 = pow(B, 4)
HINGE = Decimal("0.58496250072115618145373894394781650876")
# log2(3)/2 ≈ 0.792481... sometimes used; keep hinge as primary


def set_bits(x: int) -> list[int]:
    if x < 0:
        x = -x
    bits = []
    i = 0
    while x:
        if x & 1:
            bits.append(i)
        x >>= 1
        i += 1
    return bits


def bit_fingerprint(err: int) -> dict:
    ab = abs(err)
    bits = set_bits(ab)
    return {
        "error": str(err),
        "error_abs": str(ab),
        "error_hex": hex(ab),
        "sign": 0 if err == 0 else (1 if err > 0 else -1),
        "bits": bits,
        "popcount": len(bits),
        "highest_bit": bits[-1] if bits else None,
        "lowest_bit": bits[0] if bits else None,
        "binary_sum": " + ".join(f"2^{b}" for b in reversed(bits)) if bits else "0",
    }


def rulers_for(n: int, lo: int, hi: int) -> dict[str, int]:
    """Named expected landings inside [lo, hi]."""
    width = hi - lo  # hi is exclusive in catalog? check catalog
    # catalog range_max is inclusive end of [2^{n-1}, 2^n) so hi = 2^n - 1 typically
    # load_catalog uses range_max from csv as int
    span = hi - lo + 1 if hi >= lo else 1
    mid = lo + (hi - lo) // 2
    hinge = int(Decimal(lo) + Decimal(span) * HINGE)
    if hinge > hi:
        hinge = hi
    if hinge < lo:
        hinge = lo
    # pure power hinge: 2^(n-1+HINGE)
    power_hinge = int(Decimal(2) ** (Decimal(n - 1) + HINGE))
    power_hinge = min(max(power_hinge, lo), hi)
    log_mid = int(Decimal(2) ** (Decimal(n) - Decimal("0.5")))
    log_mid = min(max(log_mid, lo), hi)
    quarter = lo + (hi - lo) // 4
    three_q = lo + 3 * (hi - lo) // 4
    return {
        "lower_anchor": lo,
        "upper_anchor": hi,
        "midpoint": mid,
        "hinge_58496_range": hinge,
        "hinge_58496_power": power_hinge,
        "log_midpoint": log_mid,
        "quarter": quarter,
        "three_quarter": three_q,
    }


def relative_bits(bits: list[int], n: int) -> list[int]:
    """Bit positions relative to range MSB (n-1)."""
    return [b - (n - 1) for b in bits]


def relative_bits_from_n(bits: list[int], n: int) -> list[int]:
    return [b - n for b in bits]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    ruler_names: list[str] = []
    per_ruler_rows: dict[str, list[dict]] = defaultdict(list)

    for n in range(1, 161):
        e = catalog[n]
        if not e.solved or e.private_key <= 0:
            continue
        d = e.private_key
        lo, hi = e.range_min, e.range_max
        # catalog range_max for puzzle n is typically 2^n - 1
        preds = rulers_for(n, lo, hi)
        if not ruler_names:
            ruler_names = list(preds.keys())

        width = hi - lo + 1
        for rname, expected in preds.items():
            err = d - expected
            fp = bit_fingerprint(err)
            rel = relative_bits(fp["bits"], n)
            rel_n = relative_bits_from_n(fp["bits"], n)
            row = {
                "puzzle": n,
                "d": str(d),
                "d_hex": hex(d),
                "range_lo": str(lo),
                "range_hi": str(hi),
                "expected": str(expected),
                "expected_hex": hex(expected),
                "error": fp["error"],
                "error_hex": fp["error_hex"],
                "sign": fp["sign"],
                "bits": fp["bits"],
                "binary_sum": fp["binary_sum"],
                "popcount": fp["popcount"],
                "highest_bit": fp["highest_bit"],
                "lowest_bit": fp["lowest_bit"],
                "relative_bits_msb": rel,  # bit - (n-1)
                "relative_bits_n": rel_n,  # bit - n
                "normalized_error": format(Decimal(err) / Decimal(width), "f"),
                "error_over_2_n_minus_1": format(Decimal(err) / Decimal(1 << (n - 1)), "f"),
                "error_mod_B": err % B,
                "error_mod_DELTA": err % DELTA if DELTA else None,
                "error_mod_B4": err % B4,
                "error_mod_N": err % N,
            }
            per_ruler_rows[rname].append(row)

    # rank rulers by structure of relative bit patterns
    rankings = []
    for rname in ruler_names:
        rows = per_ruler_rows[rname]
        # pattern key: frozenset or tuple of relative_bits_msb
        pattern_counts = Counter(tuple(r["relative_bits_msb"]) for r in rows)
        # also pattern ignoring sign-only differences — use abs error bits only (already abs in bits)
        # most common pattern
        top = pattern_counts.most_common(5)
        # entropy of pattern distribution
        total = len(rows)
        ent = 0.0
        for _, c in pattern_counts.items():
            p_i = c / total
            ent -= p_i * math.log2(p_i)
        # how often relative pattern is shared by >=2 puzzles
        shared = sum(c for _, c in pattern_counts.items() if c >= 2)
        # mean popcount
        mean_pop = sum(r["popcount"] for r in rows) / total
        # check for pure shift: relative pattern identical for many
        best_pat, best_c = top[0] if top else ((), 0)
        rankings.append({
            "ruler": rname,
            "n_solved": total,
            "unique_patterns": len(pattern_counts),
            "pattern_entropy_bits": ent,
            "puzzles_in_shared_patterns": shared,
            "best_pattern_relative_msb": list(best_pat),
            "best_pattern_count": best_c,
            "mean_popcount": mean_pop,
            "top_patterns": [
                {"relative_bits_msb": list(pat), "count": c, "binary": " + ".join(
                    f"2^(n-1{('+'+str(b)) if b>=0 else str(b)})" for b in reversed(pat)
                ) if pat else "0"}
                for pat, c in top
            ],
        })

    rankings.sort(key=lambda r: (r["pattern_entropy_bits"], -r["best_pattern_count"]))

    # Case A vs B verdict
    best = rankings[0] if rankings else None
    if best and best["best_pattern_count"] >= 5 and best["pattern_entropy_bits"] < 4:
        case = "B_structured"
        case_note = (
            "Repeated relative bit patterns — possible shifted_mask(n). "
            "Candidate: expected_landing(n) + reconstruct(mask, n), then [d]G verify."
        )
    elif best and best["best_pattern_count"] >= 3:
        case = "B_weak_structure"
        case_note = "Some repeated patterns; not yet a clean global mask."
    else:
        case = "A_random_looking"
        case_note = (
            "High pattern entropy — ruler errors look identity-specific, not a transferable bitmask."
        )

    # Build candidate formula check: for best ruler, if best pattern is common,
    # try reconstruct error from relative bits and see match rate
    transfer_test = None
    if best and best["best_pattern_count"] >= 2:
        rname = best["ruler"]
        pat = best["best_pattern_relative_msb"]
        rows = per_ruler_rows[rname]
        matches = 0
        for r in rows:
            n = r["puzzle"]
            recon = 0
            for rel in pat:
                bit = (n - 1) + rel
                if bit >= 0:
                    recon |= 1 << bit
            # error may be signed
            if abs(int(r["error"])) == recon or int(r["error"]) == recon or int(r["error"]) == -recon:
                matches += 1
        transfer_test = {
            "ruler": rname,
            "pattern_relative_msb": pat,
            "exact_recon_matches": matches,
            "n_solved": len(rows),
            "match_rate": matches / len(rows),
        }

    # P135 public-side: we cannot do error_d without d, but we can list ruler landings
    e135 = catalog[135]
    p135_landings = rulers_for(135, e135.range_min, e135.range_max)
    p135_candidates = {}
    if transfer_test and transfer_test["match_rate"] > 0.5:
        pat = transfer_test["pattern_relative_msb"]
        for rname, expected in p135_landings.items():
            recon = 0
            for rel in pat:
                bit = (135 - 1) + rel
                if bit >= 0:
                    recon |= 1 << bit
            for sign in (1, -1):
                cand = expected + sign * recon
                if e135.range_min <= cand <= e135.range_max:
                    p135_candidates.setdefault(rname, []).append({
                        "candidate_d": str(cand),
                        "sign": sign,
                        "mask": str(recon),
                        "note": "MUST verify [d]G == P135 — not done here as auto-claim",
                    })

    payload = {
        "exhibit": "range_error_bitmask",
        "location": "ARCHIVE/briefcase/misalignments/",
        "case": case,
        "case_note": case_note,
        "rulers": ruler_names,
        "rankings": rankings,
        "transfer_test": transfer_test,
        "P135_ruler_landings": {k: str(v) for k, v in p135_landings.items()},
        "P135_candidates_if_mask_transfers": p135_candidates,
        "per_ruler": {k: v for k, v in per_ruler_rows.items()},
        "final_truth": "[candidate_d]G == P135 public key",
    }

    (OUT / "range_error_bitmask.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    # markdown report
    lines = [
        "# range_error_bitmask — misalignment fingerprints",
        "",
        "For each solved puzzle and each ruler:",
        "",
        "```text",
        "error_n = actual_d - expected_landing",
        "error_n = Σ 2^i  (set bits)",
        "relative_bits = bit - (n-1)",
        "```",
        "",
        f"**Case:** `{case}`",
        "",
        case_note,
        "",
        "## Ruler rankings (lower entropy = more structure)",
        "",
        "| Rank | Ruler | Entropy | Unique patterns | Best pattern count | Mean popcount |",
        "|------|-------|---------|-----------------|--------------------|---------------|",
    ]
    for i, r in enumerate(rankings, 1):
        lines.append(
            f"| {i} | `{r['ruler']}` | {r['pattern_entropy_bits']:.3f} | "
            f"{r['unique_patterns']} | {r['best_pattern_count']} | {r['mean_popcount']:.2f} |"
        )

    lines.extend(["", "## Top patterns per ruler", ""])
    for r in rankings:
        lines.append(f"### `{r['ruler']}`")
        lines.append("")
        for pat in r["top_patterns"][:3]:
            lines.append(
                f"- count **{pat['count']}**: `{pat['relative_bits_msb']}` → {pat['binary']}"
            )
        lines.append("")

    if transfer_test:
        lines.append("## Transfer test (reconstruct mask from relative bits)")
        lines.append("")
        lines.append(f"- ruler: `{transfer_test['ruler']}`")
        lines.append(f"- pattern: `{transfer_test['pattern_relative_msb']}`")
        lines.append(
            f"- exact matches: **{transfer_test['exact_recon_matches']}** / "
            f"{transfer_test['n_solved']} "
            f"({100*transfer_test['match_rate']:.1f}%)"
        )
        lines.append("")

    lines.append("## Sample rows (best ruler, first 15 solved)")
    lines.append("")
    best_name = rankings[0]["ruler"]
    lines.append(f"Ruler: `{best_name}`")
    lines.append("")
    lines.append("| P | expected | error bits | relative_msb | popcount | norm_err |")
    lines.append("|---|----------|------------|--------------|----------|----------|")
    for r in per_ruler_rows[best_name][:15]:
        lines.append(
            f"| {r['puzzle']} | `{r['expected'][:20]}…` | `{r['bits']}` | "
            f"`{r['relative_bits_msb']}` | {r['popcount']} | `{r['normalized_error'][:12]}` |"
        )

    lines.extend([
        "",
        "## P135 ruler landings (no d — candidates only if mask transfers)",
        "",
    ])
    for k, v in p135_landings.items():
        lines.append(f"- **{k}:** `{v}`")
    if p135_candidates:
        lines.append("")
        lines.append("Candidate d values (require `[d]G == P135`):")
        for rname, cands in p135_candidates.items():
            for c in cands:
                lines.append(f"- `{rname}` sign={c['sign']}: `{c['candidate_d']}`")
    else:
        lines.append("")
        lines.append("_No auto candidates — mask does not transfer cleanly enough._")

    lines.extend([
        "",
        "## Ruling",
        "",
        "```text",
        "Case A: random-looking offsets → ruler not predictive",
        "Case B: structured offsets → error_n = shifted_mask(n)",
        "         candidate_d = expected_landing + shifted_mask(135)",
        "         truth: [candidate_d]G == P135",
        "```",
        "",
        f"This scan: **{case}**.",
        "",
        "Judge Popcorn: **binary fingerprints are constellations. "
        "Only [d]G is sunrise.**",
        "",
    ])

    (OUT / "range_error_bitmask.md").write_text("\n".join(lines), encoding="utf-8")

    # update README
    readme = OUT / "README.md"
    readme.write_text(
        "\n".join([
            "# briefcase/misalignments",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `p1_baseline_misalignments.*` | P1 as origin deltas |",
            "| `range_error_bitmask.*` | ruler errors as binary fingerprints |",
            "",
            "```text",
            "python build_p1_baseline_misalignments.py",
            "python build_range_error_bitmask.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"case={case}")
    print(f"best_ruler={best['ruler'] if best else None} entropy={best['pattern_entropy_bits'] if best else None}")
    if transfer_test:
        print(
            f"transfer {transfer_test['ruler']}: "
            f"{transfer_test['exact_recon_matches']}/{transfer_test['n_solved']}"
        )
    for r in rankings[:3]:
        print(
            f"  {r['ruler']}: ent={r['pattern_entropy_bits']:.2f} "
            f"best_count={r['best_pattern_count']} pat={r['best_pattern_relative_msb'][:8]}..."
        )
    print(f"wrote {OUT / 'range_error_bitmask.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
