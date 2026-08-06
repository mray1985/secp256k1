#!/usr/bin/env python3
"""P160 attack brief: bridge + gap priors + complement windows (pubkey from RSZ)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import PuzzleConfig, apply_puzzle_defaults, p, run_bridge_regression, puzzle_band  # noqa: E402
from gap_tier_common import gap_interval  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from compare_family_mirror_batch import analyze_one  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402


def parse_complement_manifest(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("run_p160_comp_"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        script = parts[0]
        label = parts[1]
        span_txt = next((part for part in parts if part.startswith("span=")), None)
        range_txt = next(
            (
                part for part in parts
                if ":" in part and all(ch in "0123456789abcdef:" for ch in part.lower())
            ),
            None,
        )
        if span_txt is None or range_txt is None:
            continue
        lo_hex, hi_hex = range_txt.split(":")
        lo = int(lo_hex, 16)
        hi = int(hi_hex, 16)
        rows.append(
            {
                "script": script,
                "label": label,
                "span": int(span_txt.split("=")[1]),
                "lo": lo,
                "hi": hi,
                "center": (lo + hi) // 2,
            }
        )
    return rows


def main() -> None:
    cfg = PuzzleConfig(puzzle_num=160)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(160)
    rsz = PUZZLE_RSZ[160]
    r_pt = recover_r_point_from_sig(rsz.r)
    ok, msgs = run_bridge_regression(cfg)

    shelf2 = st["oitc"].shelf2
    lam_ps = [(cfg.Px[i] * pow(cfg.rx[i], -1, p)) % p for i in range(3)]
    target_mid = 3 * (1 << 158)
    target_f = math.log2(1.5)
    manifest = parse_complement_manifest(
        ROOT / "puzzle160_keyhunt_bsgs" / "complement_exports" / "complement_manifest.txt"
    )
    for row in manifest:
        row["log2_center"] = math.log2(row["center"])
        row["f_center"] = row["log2_center"] - 159
        row["f_distance"] = abs(row["f_center"] - target_f)
        row["mid_distance"] = abs(row["center"] - target_mid)
    ranked = sorted(manifest, key=lambda row: (row["f_distance"], row["mid_distance"]))

    # Neighbor solved puzzles with RSZ (offset calibration)
    keys = parse_53125()
    neighbors = []
    for n in (130, 135, 140, 145, 150, 155):
        if n in keys and keys[n].d:
            try:
                if n == 135:
                    c = PuzzleConfig(135)
                    apply_puzzle_defaults(c)
                    from genesis_calibration import bridge_state as bs

                    s = bs(c)
                    neighbors.append(
                        {
                            "n": n,
                            "row": c.row,
                            "shelf2_bits": s["oitc"].shelf2.bit_length(),
                            "note": "unsolved",
                        }
                    )
                else:
                    a = analyze_one(keys[n])
                    neighbors.append(a)
            except Exception:
                pass

    lines = [
        "PUZZLE 160 — SHOOT BRIEF",
        "=" * 72,
        "",
        "TARGET (from hashkeys RSZ — full pubkey, not hash160-only)",
        f"  compressed: {rsz.pub_compressed}",
        f"  Px (row {cfg.row}): {cfg.Px[cfg.row]}",
        f"  Py: {cfg.Py}",
        f"  band: [{lo}, {hi})",
        f"  1.5x-floor prior: {target_mid}",
        "",
        "SPEND (nonce R from signature r)",
        f"  r_sig: {hex(rsz.r)}",
        f"  R point: {r_pt}",
        f"  rx slot[2] (true kG_x): {cfg.rx[2]}",
        "",
        "BRIDGE (corrected lambda)",
        f"  regression: {'PASS' if ok else 'FAIL'}",
        f"  detail: {', '.join(msgs)}",
        f"  epsilon row: {cfg.row} (was hardcoded 0 — pubkey is row 1)",
        f"  Lambda_p unified: {len(set(lam_ps)) == 1}",
        f"  shelf2: {shelf2}",
        f"  shelf2 bits: {shelf2.bit_length()}",
        f"  shelf2 / floor = {shelf2 / lo:.6f}x",
        "",
        "GAP-TIER PRIORS (from P1–P70 + high puzzles)",
        "  gap=1 -> offset_bits=159  width 2^158",
        "  gap=2 -> offset_bits=158  width 2^157",
        f"  P115-style H-10 -> ob=150 bits (not seen in P1–P70)",
    ]
    for gap in (1, 2):
        ob, o_lo, o_hi = gap_interval(160, gap)
        for sign, base in (("+", shelf2 + o_lo), ("+", shelf2 + (o_lo + o_hi - 1) // 2)):
            if lo <= base < hi:
                lines.append(f"  gap{gap} {sign}o: d={base}")

    lines += [
        "",
        "COMPLEMENT m-LEG (N+1 partner, ~2^96)",
        "  D_BASE = floor((N+1)/2^96)",
        f"  {len(manifest)} KeyHunt windows in puzzle160_keyhunt_bsgs/complement_exports/",
        "",
        "RANKED COMPLEMENT WINDOWS (closest to 1.5x-floor prior)",
        "",
        "NEIGHBOR SOLVED (RSZ band)",
    ]
    for row in ranked[:8]:
        lines.insert(
            len(lines) - 2,
            f"  {row['script']:<34} f={row['f_center']:.4f}  "
            f"|df|={row['f_distance']:.4f}  center={row['center']}",
        )
    for nb in neighbors:
        if "offset_bits" in nb:
            lines.append(
                f"  P{nb['n']:3d} row={nb['row']} gap~{nb['n']-nb['offset_bits']} "
                f"ob={nb['offset_bits']} shelf2_bits={nb['shelf2'].bit_length()}"
            )
        else:
            lines.append(f"  P{nb['n']:3d} row={nb['row']} {nb.get('note','')}")

    lines += [
        "",
        "ATTACK VECTORS (ranked)",
        f"  1. Start with {ranked[0]['script']}, {ranked[1]['script']}, {ranked[2]['script']}",
        "  2. Then sweep the rest of the ranked complement windows",
        "  3. Keep shelf2/gap-tier as a secondary prior; avoid CPU scalar-by-scalar scroll",
        "",
        "GATE: d*G == P160  (x=Px row1, y=Py)",
        "=" * 72,
    ]

    out = ROOT / "ARCHIVE" / "p160_shoot_report.txt"
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
