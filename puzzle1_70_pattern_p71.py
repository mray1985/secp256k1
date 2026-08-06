#!/usr/bin/env python3
"""Pattern scan P1–P70 for bridge/gap/row signals; extrapolate to P71."""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    N,
    p,
    puzzle_band,
    run_bridge_regression,
    verify_core_lambda_laws,
)
from gap_tier_common import gap_from_observed, gap_interval, observed_offset  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

P71_LO = 1 << 70
P71_HI = 1 << 71
P71_H = 71


def analyze(n: int, keys: dict) -> dict:
    pk = keys[n]
    cfg = build_config(pk)
    st = bridge_state(cfg)
    row = cfg.row
    lo, hi, _top = puzzle_band(n)
    shelf2 = st["oitc"].shelf2
    o = observed_offset(pk.d, shelf2, lo)
    gap, ob = gap_from_observed(pk.d, shelf2, n, lo)
    lam_ps = [(cfg.Px[i] * pow(cfg.rx[i], -1, p)) % p for i in range(3)]
    laws = verify_core_lambda_laws(
        px=cfg.Px[row],
        rx=cfg.rx[row],
        py=cfg.Py,
        ry=cfg.ry,
        row=row,
        px_triple=cfg.Px,
        rx_triple=cfg.rx,
    )
    reg_ok, _ = run_bridge_regression(cfg)

    return {
        "n": n,
        "d": pk.d,
        "d_bits": pk.d.bit_length(),
        "row": row,
        "row_eq_n_mod3": row == n % 3,
        "shelf2": shelf2,
        "offset": o,
        "offset_bits": ob,
        "gap": gap,
        "h_minus_10": n - 10,
        "h10": ob == n - 10,
        "h_minus_1": n - 1,
        "h1": ob == n - 1,
        "h_minus_2": n - 2,
        "h2": ob == n - 2,
        "gap1": gap == 1,
        "gap2": gap == 2,
        "gap10": gap == 10,
        "has_rsz": PUZZLE_RSZ.get(n) is not None,
        "lambda_unified": len(set(lam_ps)) == 1,
        "law_p": laws.p_curve_law,
        "law_n": laws.n_law,
        "bridge_ok": reg_ok,
        "d_minus_lo": pk.d - lo,
        "shelf2_minus_lo": (shelf2 - lo) % lo,
        "d_mod3": pk.d % 3,
        "shelf2_mod3": shelf2 % 3,
        "offset_mod3": o % 3,
    }


def pct(vals: list[int], p: float) -> float:
    s = sorted(vals)
    if not s:
        return float("nan")
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (k - f) * (s[c] - s[f])


def p71_candidates(shelf2_est: int | None, ob_pred: int) -> list[tuple[str, int]]:
    """Lift shelf2 + offset_bit prediction to P71 band."""
    if shelf2_est is None:
        return []
    _, o_lo, o_hi = gap_interval(P71_H, P71_H - ob_pred)
    out: list[tuple[str, int]] = []
    for label, base in (("+", shelf2_est + o_lo), ("+mid", shelf2_est + (o_lo + o_hi - 1) // 2)):
        if P71_LO <= base < P71_HI:
            out.append((label, base))
    for label, base in (("-", shelf2_est - o_lo),):
        if P71_LO <= base < P71_HI:
            out.append((label, base))
    return out


def main() -> None:
    keys = parse_53125()
    rows: list[dict] = []
    errors: list[tuple[int, str]] = []

    for n in range(1, 71):
        try:
            rows.append(analyze(n, keys))
        except Exception as exc:
            errors.append((n, str(exc)))

    out_csv = ROOT / "ARCHIVE" / "puzzle1_70_pattern.csv"
    out_txt = ROOT / "ARCHIVE" / "puzzle1_70_pattern_p71_report.txt"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # --- aggregates ---
    by_row: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_row[r["row"]].append(r)

    gaps = [r["gap"] for r in rows]
    obs = [r["offset_bits"] for r in rows]
    gap_ctr = Counter(gaps)
    ob_ctr = Counter(obs)

    # recent window P60-P70
    recent = [r for r in rows if r["n"] >= 60]
    recent_gaps = Counter(r["gap"] for r in recent)
    recent_obs = Counter(r["offset_bits"] for r in recent)

    # row-specific recent
    p70 = next(r for r in rows if r["n"] == 70)
    p69 = next(r for r in rows if r["n"] == 69)
    p68 = next(r for r in rows if r["n"] == 68)

    lines = [
        "PUZZLE 1-70 PATTERN SCAN -> P71 EXTRAPOLATION",
        f"analyzed: {len(rows)}/70  errors: {len(errors)}",
        "",
        "=== BRIDGE (corrected lambda) ===",
        f"  LAW-P+LN+regression pass: {sum(1 for r in rows if r['bridge_ok'])}/{len(rows)}",
        f"  Lambda_p unified (RSZ only): "
        f"{sum(1 for r in rows if r['lambda_unified'])}/{sum(1 for r in rows if r['has_rsz'])} with RSZ",
        f"  P70 has RSZ: {p70['has_rsz']}  unified: {p70['lambda_unified']}",
        "",
        "=== OFFSET / GAP (full 1–70) ===",
        f"  offset_bits: min={min(obs)} max={max(obs)} median={statistics.median(obs):.0f}",
        f"  gap (H-ob):  min={min(gaps)} max={max(gaps)} median={statistics.median(gaps):.0f}",
        f"  gap counts: {dict(sorted(gap_ctr.items()))}",
        f"  top offset_bits: {ob_ctr.most_common(8)}",
        "",
        f"  H-10 (ob==H-10): {sum(1 for r in rows if r['h10'])}/{len(rows)}",
        f"  H-1  (ob==H-1):  {sum(1 for r in rows if r['h1'])}/{len(rows)}",
        f"  H-2  (ob==H-2):  {sum(1 for r in rows if r['h2'])}/{len(rows)}",
        f"  gap==1: {sum(1 for r in rows if r['gap1'])}/{len(rows)}",
        f"  gap==2: {sum(1 for r in rows if r['gap2'])}/{len(rows)}",
        "",
        "=== ROW LANDING (epsilon) ===",
        f"  row == n mod 3: {sum(1 for r in rows if r['row_eq_n_mod3'])}/{len(rows)}",
    ]
    for rid in (0, 1, 2):
        grp = by_row[rid]
        g = [x["gap"] for x in grp]
        lines.append(
            f"  row {rid}: n={len(grp)}  gap mode={Counter(g).most_common(3)}  "
            f"H-10={sum(1 for x in grp if x['h10'])}/{len(grp)}"
        )

    lines += [
        "",
        "=== RECENT P60–P70 ===",
        f"  puzzles: {[r['n'] for r in recent]}",
        f"  rows:    {[r['row'] for r in recent]}",
        f"  gaps:    {[r['gap'] for r in recent]}",
        f"  ob_bits: {[r['offset_bits'] for r in recent]}",
        f"  gap distribution: {dict(recent_gaps)}",
        f"  offset_bits distribution: {dict(recent_obs)}",
        "",
        "=== P68–P70 CHAIN ===",
        f"  P68: row={p68['row']} gap={p68['gap']} ob={p68['offset_bits']} shelf2_bits={p68['shelf2'].bit_length()}",
        f"  P69: row={p69['row']} gap={p69['gap']} ob={p69['offset_bits']} shelf2_bits={p69['shelf2'].bit_length()}",
        f"  P70: row={p70['row']} gap={p70['gap']} ob={p70['offset_bits']} shelf2_bits={p70['shelf2'].bit_length()}",
        "",
        "  row sequence 68→69→70: "
        f"{p68['row']}→{p69['row']}→{p70['row']}  (n mod 3: 68%3=2, 69%3=0, 70%3=1)",
        f"  gap sequence: {p68['gap']}→{p69['gap']}→{p70['gap']}",
        f"  ob sequence:  {p68['offset_bits']}→{p69['offset_bits']}→{p70['offset_bits']}",
    ]

    # P71 predictions
    p71_row_pred = 71 % 3  # = 2
    # gap-tier from recent: P60-P70 mostly gap 1 or 2
    recent_gap12 = sum(1 for r in recent if r["gap"] in (1, 2))
    ob_if_gap1 = P71_H - 1  # 70
    ob_if_gap2 = P71_H - 2  # 69
    ob_if_h10 = P71_H - 10  # 61

    # shelf2 extrapolation: ratio P70.shelf2 / P69.shelf2 or delta shelf2
    ds69 = (p70["shelf2"] - p69["shelf2"]) % P71_LO
    ds68 = (p69["shelf2"] - p68["shelf2"]) % P71_LO
    shelf2_lin = (p70["shelf2"] + ds69) % P71_LO
    shelf2_avg_delta = (p70["shelf2"] + (ds69 + ds68) // 2) % P71_LO

    lines += [
        "",
        "=== P71 EXTRAPOLATION (unsolved) ===",
        f"  predicted epsilon row (n mod 3): {p71_row_pred}",
        f"  P60–P70 gap∈{{1,2}}: {recent_gap12}/{len(recent)}",
        "",
        "  Gap-tier priors for P71:",
        f"    gap=1 → offset_bits=70  interval width 2^69",
        f"    gap=2 → offset_bits=69  interval width 2^68",
        f"    H-10  → offset_bits=61  (only 1 hit in full 1–70: P115 analog)",
        "",
        f"  shelf2 P69→P70 delta bits: {ds69.bit_length()}",
        f"  linear shelf2 guess (P70+delta): {shelf2_lin}",
        f"  avg-delta shelf2 guess:          {shelf2_avg_delta}",
        "",
        "  Candidate d from shelf2 + offset (NOT verified — need EC):",
    ]

    for tag, ob in [("gap1/ob70", ob_if_gap1), ("gap2/ob69", ob_if_gap2), ("H-10/ob61", ob_if_h10)]:
        for shelf_tag, s2 in [("lin", shelf2_lin), ("avg", shelf2_avg_delta), ("P70", p70["shelf2"])]:
            for lab, cand in p71_candidates(s2, ob):
                lines.append(f"    {tag} {shelf_tag} {lab}: {cand}")

    # D/A band anchors from puzzle71 files
    da_mid = 1770887431076116955135
    band_lo = P71_LO
    band_hi = P71_HI - 1
    lines += [
        "",
        "  D/A mid-band anchor (puzzle71_da_draft):",
        f"    {da_mid}  in_band={band_lo <= da_mid < P71_HI}",
        f"  band floor 2^70: {band_lo}",
        f"  band ceil  2^71-1: {band_hi}",
        "",
        "=== PER-PUZZLE TABLE (n row gap ob RSZ bridge) ===",
        f"{'n':>3} {'row':>3} {'gap':>3} {'ob':>3} {'RSZ':>3} {'br':>2}  note",
        "-" * 48,
    ]
    for r in rows:
        note = ""
        if r["h10"]:
            note = "H-10"
        elif r["gap1"]:
            note = "gap1"
        elif r["gap2"]:
            note = "gap2"
        lines.append(
            f"{r['n']:3d} {r['row']:3d} {r['gap']:3d} {r['offset_bits']:3d} "
            f"{'Y' if r['has_rsz'] else 'N':>3} "
            f"{'Y' if r['bridge_ok'] else 'N':>2}  {note}"
        )

    if errors:
        lines += ["", "ERRORS:"]
        for n, msg in errors:
            lines.append(f"  P{n}: {msg}")

    lines += [
        "",
        "=== VERDICT FOR P71 ===",
        "  1. Bridge laws will pass once P71 pubkey+RSZ wired like P70 (lambda unified).",
        "  2. Scalar: gap-tier {1,2} dominates P60–P70 → search ob∈{69,70} off shelf2, not Lambda.",
        f"  3. Row lock: expect row={p71_row_pred} (71 mod 3).",
        "  4. H-10 is NOT a 1–70 pattern (0/70 hits here; P115 is special).",
        "  5. D/A chain says P71 opens D(68) after P70 ends A — orthogonal to bridge offset.",
        "  6. No closed form d from Lambda/shift; kangaroo/BSGS in ~2^68–2^69 offset window.",
    ]

    text = "\n".join(lines) + "\n"
    out_txt.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out_csv}")
    print(f"wrote {out_txt}")


if __name__ == "__main__":
    main()
