#!/usr/bin/env python3
"""
P160 subdue scan: linear ±1..10000 and power ±2^n from pubkey/shelf anchors.

Treats Px, Py, shelf2, etc. as scalar seeds (heuristic), maps into puzzle band,
checks d*G == P160.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    PuzzleConfig,
    apply_puzzle_defaults,
    band_representative,
    puzzle_band,
    pubkey_from_scalar,
)
from genesis_calibration import bridge_state  # noqa: E402
from p160_shoot_report import parse_complement_manifest  # noqa: E402


def in_band(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def lift_to_band(raw: int, lo: int, hi: int) -> int:
    return band_representative(raw, lo, hi)


def generate_candidates(anchor: int, lo: int, hi: int, linear: int, max_pow: int) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(tag: str, raw: int) -> None:
        d = raw if in_band(raw, lo, hi) else lift_to_band(raw, lo, hi)
        if d in seen:
            return
        seen.add(d)
        out.append((tag, d))

    for k in range(-linear, linear + 1):
        add(f"lin{k:+d}", anchor + k)

    for n in range(1, max_pow + 1):
        step = 1 << n
        add(f"-2^{n}", anchor - step)
        add(f"+2^{n}", anchor + step)

    return out


def main() -> None:
    linear = 10_000
    max_pow = 158
    puzzle_n = 160

    cfg = PuzzleConfig(puzzle_num=puzzle_n)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(puzzle_n)
    row = cfg.row
    px, py = cfg.Px[row], cfg.Py
    shelf2 = st["oitc"].shelf2
    mid = 3 * (1 << (puzzle_n - 2))

    manifest = parse_complement_manifest(
        ROOT / "puzzle160_keyhunt_bsgs" / "complement_exports" / "complement_manifest.txt"
    )
    comp_centers = [r["center"] for r in sorted(manifest, key=lambda r: r["center"])[:5]]

    anchors: list[tuple[str, int]] = [
        ("Px", px),
        ("Py", py),
        ("shelf2", shelf2),
        ("1.5x_floor", mid),
    ]
    for i, c in enumerate(comp_centers):
        anchors.append((f"comp_{i}", c))

    t0 = time.time()
    tested = 0
    hit: tuple[str, int] | None = None
    nearest: tuple[int, str, int, int] | None = None  # dist, tag, d, pub_x

    lines = [
        "P160 SUBDUE SCAN",
        f"linear offsets: [{-linear}, +{linear}]",
        f"power offsets: ±2^n for n=1..{max_pow}",
        f"target Px row{row}: {px}",
        f"target Py: {py}",
        f"band lo={lo}",
        "",
        "ANCHORS:",
    ]
    for name, a in anchors:
        lines.append(f"  {name}: {a}")

    lines.append("")
    lines.append("SCANNING...")

    for aname, anchor in anchors:
        for tag, d in generate_candidates(anchor, lo, hi, linear, max_pow):
            tested += 1
            pub_x, pub_y = pubkey_from_scalar(d)
            if pub_x == px and pub_y == py:
                hit = (f"{aname}:{tag}", d)
                break
            dist = abs(pub_x - px)
            if nearest is None or dist < nearest[0]:
                nearest = (dist, f"{aname}:{tag}", d, pub_x)
        if hit:
            break

    elapsed = time.time() - t0
    lines.append(f"tested={tested:,}  elapsed={elapsed:.2f}s  rate={tested/max(elapsed,1e-9):,.0f}/s")
    lines.append("")

    if hit:
        tag, d = hit
        lines.append(f"HIT  {tag}  d={d}  hex={hex(d)}")
    else:
        lines.append("NO EC HIT in this subdue grid.")
        if nearest:
            dist, tag, d, pub_x = nearest
            lines.append(f"nearest pubkey-x miss: {tag}  d={d}")
            lines.append(f"  pub_x={pub_x}")
            lines.append(f"  |pub_x - Px| = {dist}")

    lines += [
        "",
        "NOTE:",
        "  (Px,Py) +/- small int here means scalar anchors Px+k, Py+k — not invalid",
        "  coordinate tuple arithmetic. Valid curve neighbors are P +/- k*G (separate mode).",
        "  Power ladder ±2^n from each anchor maps out-of-band values back into band via LO wrap.",
    ]

    out_txt = ROOT / "ARCHIVE" / "p160_subdue_scan_report.txt"
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {out_txt}")


if __name__ == "__main__":
    main()
