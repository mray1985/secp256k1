#!/usr/bin/env python3
"""
Puzzle-1 baseline misalignment scan.

P1 is d=1 → P=G. Every verified identity on P1 is the curve origin.
For each other pubkey puzzle, record the same quantities and the
delta from P1 — does a fixed "off by" from P1 explain the rest?

Writes ONLY under ARCHIVE/briefcase/misalignments/
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path
from statistics import mean, pstdev

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p, y_roots
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "misalignments"

B = (1 << 32) + 977
B4 = pow(B, 4)
CORRECTION = Decimal(DELTA) / Decimal(B4)
HINGE = 0.5849625007211562


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def measure(px: int, py: int, d: int | None, bits: int, lo: int, hi: int) -> dict:
    """Run verified k1 side-processes on one point."""
    pmy = (p - py) % p
    # primary branch = p-y (matches P135 packet exhibit)
    packet = Decimal(f"{px}.{pmy}")
    packet_p = packet / Decimal(p)
    floor_p = int(packet_p * Decimal(p))
    floor_n = int(packet_p * Decimal(N))
    floor_delta = int(packet_p * Decimal(DELTA))
    floor_b4 = int(packet_p * Decimal(B4))
    int_only = map_p_to_n(px)
    off_by = floor_n - int_only

    # β slots
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    beta_ok = (px2 * BETA) % p == px3

    # y^2 law
    on_curve = (pow(py, 2, p) - (pow(px, 3, p) + 7)) % p == 0

    row = {
        "bits": bits,
        "Px": str(px),
        "Py": str(py),
        "p_minus_y": str(pmy),
        "packet_p": format(packet_p, "f"),
        "floor_packet_p_times_p": str(floor_p),
        "floor_packet_p_times_N": str(floor_n),
        "floor_packet_p_times_DELTA": str(floor_delta),
        "floor_packet_p_times_B4": str(floor_b4),
        "map_p_to_n_Px": str(int_only),
        "off_by_map_p_to_n": off_by,
        "floor_ratio_DELTA_over_B4": (
            format(Decimal(floor_delta) / Decimal(floor_b4), "f") if floor_b4 else None
        ),
        "correction": format(CORRECTION, "f"),
        "ratio_minus_correction": (
            format(Decimal(floor_delta) / Decimal(floor_b4) - CORRECTION, "f")
            if floor_b4
            else None
        ),
        "Px1": str(px1),
        "Px2": str(px2),
        "Px3": str(px3),
        "beta_slot_ok": beta_ok,
        "on_curve": on_curve,
        "matches_Px_integer": floor_p == px,
        "range_lo": str(lo),
        "range_hi": str(hi),
    }

    # log2 embeddings
    row["log2_Px"] = math.log2(px) if px > 0 else None
    row["log2_packet_p"] = float(packet_p.ln() / Decimal(math.log(2)))
    row["frac_log2_Px"] = row["log2_Px"] - math.floor(row["log2_Px"]) if row["log2_Px"] else None
    row["dist_frac_log2_Px_to_hinge"] = (
        abs(row["frac_log2_Px"] - HINGE) if row["frac_log2_Px"] is not None else None
    )

    if d and d > 0:
        row["d"] = str(d)
        row["log2_d"] = math.log2(d)
        row["range_frac"] = (d - lo) / (hi - lo) if hi > lo else None
        row["d_minus_lo"] = str(d - lo)
        row["hi_minus_d"] = str(hi - d)
        row["frac_log2_d"] = row["log2_d"] - math.floor(row["log2_d"])
        row["dist_frac_log2_d_to_hinge"] = abs(row["frac_log2_d"] - HINGE)
    else:
        row["d"] = None

    return row


def delta_from_baseline(base: dict, row: dict) -> dict:
    """Numeric misalignments relative to P1."""
    out: dict = {}

    def isub(key: str) -> None:
        if key in base and key in row and base[key] is not None and row[key] is not None:
            try:
                out[f"d_{key}"] = str(int(row[key]) - int(base[key]))
            except (TypeError, ValueError):
                pass

    for key in (
        "floor_packet_p_times_p",
        "floor_packet_p_times_N",
        "floor_packet_p_times_DELTA",
        "floor_packet_p_times_B4",
        "map_p_to_n_Px",
        "Px",
        "Py",
        "p_minus_y",
        "Px1",
        "Px2",
        "Px3",
    ):
        isub(key)

    out["d_off_by_map_p_to_n"] = row["off_by_map_p_to_n"] - base["off_by_map_p_to_n"]
    out["d_log2_Px"] = (
        row["log2_Px"] - base["log2_Px"]
        if row["log2_Px"] is not None and base["log2_Px"] is not None
        else None
    )
    out["d_log2_packet_p"] = (
        row["log2_packet_p"] - base["log2_packet_p"]
        if row["log2_packet_p"] is not None and base["log2_packet_p"] is not None
        else None
    )
    out["d_packet_p"] = format(
        Decimal(row["packet_p"]) - Decimal(base["packet_p"]), "f"
    )

    # packet_p ratio (multiplicative misalignment from G)
    if Decimal(base["packet_p"]) != 0:
        out["packet_p_over_P1"] = format(
            Decimal(row["packet_p"]) / Decimal(base["packet_p"]), "f"
        )

    # floor_N / floor_N_P1
    b_n = int(base["floor_packet_p_times_N"])
    r_n = int(row["floor_packet_p_times_N"])
    if b_n:
        out["floor_N_over_P1"] = format(Decimal(r_n) / Decimal(b_n), "f")

    if row.get("d") and base.get("d"):
        out["d_log2_d"] = row["log2_d"] - base["log2_d"]  # = log2(d) since P1 d=1
        out["d_over_P1_d"] = row["d"]  # d/1 = d

    # Does off_by match P1? (binary misalignment flag)
    out["off_by_same_as_P1"] = row["off_by_map_p_to_n"] == base["off_by_map_p_to_n"]
    out["beta_ok"] = row["beta_slot_ok"]
    out["on_curve"] = row["on_curve"]
    out["shell_ratio_near_correction"] = (
        abs(Decimal(row["ratio_minus_correction"] or "1")) < Decimal("1e-8")
        if row.get("ratio_minus_correction")
        else False
    )
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    # P1 baseline
    e1 = catalog[1]
    px1, py1 = pubkey_xy(e1.public_key)
    base = measure(px1, py1, e1.private_key, 1, e1.range_min, e1.range_max)

    rows = []
    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            rows.append({
                "puzzle": n,
                "status": "no_pubkey",
                "baseline": "P1",
                "note": "cannot measure coordinate misalignment without Px,Py",
            })
            continue
        px, py = pubkey_xy(e.public_key)
        d = e.private_key if e.solved else None
        m = measure(px, py, d, n, e.range_min, e.range_max)
        delta = delta_from_baseline(base, m)
        rows.append({
            "puzzle": n,
            "status": "solved" if e.solved else "unsolved_pubkey",
            "baseline": "P1",
            "measure": m,
            "delta_from_P1": delta,
        })

    # summary: does P1 off_by predict others?
    with_pub = [r for r in rows if "delta_from_P1" in r]
    off_by_vals = [r["measure"]["off_by_map_p_to_n"] for r in with_pub]
    off_by_same = sum(1 for r in with_pub if r["delta_from_P1"]["off_by_same_as_P1"])
    beta_ok_n = sum(1 for r in with_pub if r["delta_from_P1"]["beta_ok"])
    shell_ok_n = sum(1 for r in with_pub if r["delta_from_P1"]["shell_ratio_near_correction"])

    # for solved: is d_log2_Px related to log2(d)?
    solved = [r for r in with_pub if r["status"] == "solved"]
    pairs = []
    for r in solved:
        if r["delta_from_P1"].get("d_log2_Px") is not None and r["measure"].get("log2_d"):
            pairs.append({
                "puzzle": r["puzzle"],
                "log2_d": r["measure"]["log2_d"],
                "d_log2_Px": r["delta_from_P1"]["d_log2_Px"],
                "diff": r["delta_from_P1"]["d_log2_Px"] - r["measure"]["log2_d"],
            })
    diffs = [p["diff"] for p in pairs]

    summary = {
        "baseline_puzzle": 1,
        "baseline_note": "P1 d=1 => P=G; P1 measures are the curve origin",
        "P1_measure": base,
        "n_with_pubkey": len(with_pub),
        "n_no_pubkey": sum(1 for r in rows if r.get("status") == "no_pubkey"),
        "off_by_map_p_to_n": {
            "P1": base["off_by_map_p_to_n"],
            "counts": {
                str(k): off_by_vals.count(k) for k in sorted(set(off_by_vals))
            },
            "same_as_P1": off_by_same,
            "different_from_P1": len(with_pub) - off_by_same,
            "ruling": (
                "off_by is only 0 or 1 (decimal floor nudge). "
                "P1's off_by does not encode a per-puzzle scalar offset."
            ),
        },
        "invariants_all_puzzles": {
            "beta_slot_ok": beta_ok_n,
            "shell_ratio_near_correction": shell_ok_n,
            "expected": len(with_pub),
        },
        "solved_d_log2_Px_minus_log2_d": {
            "n": len(diffs),
            "mean": mean(diffs) if diffs else None,
            "stdev": pstdev(diffs) if len(diffs) > 1 else None,
            "min": min(diffs) if diffs else None,
            "max": max(diffs) if diffs else None,
            "ruling": (
                "If stdev is large, log2(Px)-log2(Px_G) is not log2(d). "
                "P1 baseline does not give a fixed additive defect for d."
            ),
        },
        "quest_ruling": (
            "P1 is the origin (G). Invariants (beta, shell ratio, on_curve) hold for all. "
            "Variable misalignments (packet, floor_N, log2_Px) are point-specific fingerprints, "
            "not a single off-by that maps P1 -> every puzzle's d. "
            "Use P1 as null control: anything true for P1 and all puzzles is curve law; "
            "anything that varies is coordinate identity, not a universal range defect."
        ),
    }

    payload = {
        "exhibit": "p1_baseline_misalignments",
        "location": "ARCHIVE/briefcase/misalignments/",
        "summary": summary,
        "rows": rows,
    }
    (OUT / "p1_baseline_misalignments.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    # markdown
    lines = [
        "# P1 baseline misalignments",
        "",
        "Puzzle 1 is `d = 1` → `P = G`. Every verified side-process on P1 is the **curve origin**.",
        "Each other pubkey puzzle is measured the same way; `delta_from_P1` is the misalignment.",
        "",
        "## P1 origin",
        "",
        f"- off_by_map_p_to_n = `{base['off_by_map_p_to_n']}`",
        f"- packet_p = `{base['packet_p'][:40]}…`",
        f"- floor(packet·N) = `{base['floor_packet_p_times_N']}`",
        f"- map_p_to_n(Gx) = `{base['map_p_to_n_Px']}`",
        f"- beta_slot_ok = `{base['beta_slot_ok']}`",
        f"- shell floor_ratio − correction = `{base['ratio_minus_correction']}`",
        "",
        "## Does P1's off-by tell us every other puzzle?",
        "",
        f"- P1 off_by = `{base['off_by_map_p_to_n']}`",
        f"- same as P1: **{off_by_same}** / {len(with_pub)}",
        f"- different: **{len(with_pub) - off_by_same}** / {len(with_pub)}",
        f"- off_by value counts: `{summary['off_by_map_p_to_n']['counts']}`",
        "",
        "**No.** `off_by` is only a 0/1 floor nudge from the decimal packet, not a scalar defect.",
        "",
        "## Invariants (true for P1 and all pubkey puzzles)",
        "",
        f"- beta_slot_ok: {beta_ok_n}/{len(with_pub)}",
        f"- shell ratio ≈ correction: {shell_ok_n}/{len(with_pub)}",
        "",
        "These are **curve laws**, not per-puzzle offsets from P1.",
        "",
        "## Solved: is Δlog2(Px) from P1 equal to log2(d)?",
        "",
    ]
    if diffs:
        lines.append(
            f"- mean(Δlog2(Px) − log2(d)) = `{mean(diffs):.6f}`"
        )
        lines.append(
            f"- stdev = `{pstdev(diffs):.6f}`"
        )
        lines.append(
            f"- range = `[{min(diffs):.4f}, {max(diffs):.4f}]`"
        )
        lines.append("")
        lines.append(
            "Large spread ⇒ P1 does **not** give a fixed additive defect that yields d."
        )
    lines.extend([
        "",
        "## Sample deltas (solved)",
        "",
        "| P | d | off_by | Δoff_by vs P1 | Δlog2(Px) | log2(d) | Δlog2(Px)−log2(d) |",
        "|---|---|--------|---------------|-----------|---------|-------------------|",
    ])
    for r in solved[:20]:
        m, dlt = r["measure"], r["delta_from_P1"]
        diff = (
            dlt["d_log2_Px"] - m["log2_d"]
            if dlt.get("d_log2_Px") is not None
            else None
        )
        lines.append(
            f"| {r['puzzle']} | {m['d']} | {m['off_by_map_p_to_n']} | "
            f"{dlt['d_off_by_map_p_to_n']} | "
            f"{dlt['d_log2_Px']:.4f} | {m['log2_d']:.4f} | "
            f"{diff:.4f} |"
        )
    lines.extend([
        "",
        "## Ruling",
        "",
        summary["quest_ruling"],
        "",
        "Judge Popcorn: **P1 is the origin star, not a universal offset key. "
        "What matches P1 everywhere is law; what differs is identity.**",
        "",
    ])
    (OUT / "p1_baseline_misalignments.md").write_text("\n".join(lines), encoding="utf-8")

    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/misalignments",
            "",
            "Per-puzzle defects relative to verified secp256k1 side-processes.",
            "",
            "| File | Purpose |",
            "|------|---------|",
            "| `p1_baseline_misalignments.md` / `.json` | P1 as origin; deltas for all pubkey puzzles |",
            "",
            "Rebuild: `python build_p1_baseline_misalignments.py`",
            "",
        ]),
        encoding="utf-8",
    )

    print(f"P1 off_by={base['off_by_map_p_to_n']}")
    print(f"same_as_P1={off_by_same}/{len(with_pub)} different={len(with_pub)-off_by_same}")
    print(f"beta_ok={beta_ok_n}/{len(with_pub)} shell_ok={shell_ok_n}/{len(with_pub)}")
    if diffs:
        print(f"d_log2_Px - log2_d: mean={mean(diffs):.4f} stdev={pstdev(diffs):.4f}")
    print(f"wrote {OUT / 'p1_baseline_misalignments.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
