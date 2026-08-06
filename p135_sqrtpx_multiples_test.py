#!/usr/bin/env python3
"""Test sqrt(Px) multiple candidates against P135 pubkey."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from bucket_slice_search import band_midpoint, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

CANDIDATES = Path(r"C:\Users\mitch\Downloads\P135_sqrtPx_multiples_227_to_453(1).txt")
REPORT = ROOT / "ARCHIVE" / "p135_sqrtpx_multiples_test.txt"


def parse_candidates(path: Path) -> list[tuple[int, int]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\d+):\s*(\d+)\s*$", line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2))))
    return rows


def main() -> int:
    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    rows = parse_candidates(CANDIDATES)
    lines = [
        "P135 sqrt(Px) multiples m=227..453 EC test",
        f"candidates: {len(rows)}",
        f"band [{lo}, {hi})",
        f"mid (halfway): {mid}",
        f"upper half: d >= {mid}",
        "",
    ]

    hits = []
    in_band = above_mid = 0
    for m, d in rows:
        ok_band = lo <= d < hi
        ok_mid = d >= mid
        if ok_band:
            in_band += 1
        if ok_mid:
            above_mid += 1
        ec = verify_candidate(d, px, py) if ok_band else False
        frac = (d - lo) / lo if ok_band else 0
        flag = "EC_HIT" if ec else ""
        if ec:
            hits.append((m, d))
        lines.append(
            f"m={m:3d} d_tail...{str(d)[-8:]} band={ok_band} upper_half={ok_mid} "
            f"frac={frac:.6f} {flag}"
        )

    lines.extend(
        [
            "",
            f"in_band: {in_band}/{len(rows)}",
            f"upper_half: {above_mid}/{len(rows)}",
            f"EC hits: {len(hits)}",
        ]
    )
    if hits:
        for m, d in hits:
            lines.append(f"  HIT m={m} d={d} hex={hex(d)}")

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
