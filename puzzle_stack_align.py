#!/usr/bin/env python3
"""Visualize solved puzzle keys stacked with left-edge alignment."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

OUT = ROOT / "ARCHIVE" / "puzzle_stack_left_align.txt"


def main() -> int:
    keys = parse_53125()
    solved = sorted(n for n in keys if keys[n].d > 0)
    lines: list[str] = []

    lines.append("PUZZLE KEYS — LEFT-ALIGNED 64-HEX STACK (puzzles 1..130)")
    lines.append("=" * 80)
    lines.append("All rows start at column 0. Significant digits grow from the RIGHT.")
    lines.append("Leading-zero run shrinks ~1 hex digit per 4 puzzle heights.")
    lines.append("")

    for n in solved:
        h = format(keys[n].d, "064x")
        lz = len(h) - len(h.lstrip("0"))
        sig = h.lstrip("0") or "0"
        lines.append(f"P{n:3d} lz={lz:2d} |{h}|")

    lines.append("")
    lines.append("STRIPPED HEX — first significant digit aligned at column 0")
    lines.append("-" * 80)
    for n in solved:
        sig = format(keys[n].d, "x")
        lines.append(f"P{n:3d} {sig}")

    lines.append("")
    lines.append("BINARY in 135-bit frame — leftmost '1' column (= 135 - bit_length)")
    lines.append("-" * 80)
    W = 135
    for n in solved:
        bl = keys[n].d.bit_length()
        b = format(keys[n].d, f"0{bl}b").rjust(W, "0")
        col = b.index("1")
        lines.append(f"P{n:3d} col={col:3d} (135-{bl}={W-bl}) |{b[-24:]}|")

    lines.append("")
    lines.append("P135 band preview (not solved):")
    lines.append("  64-hex: 30 zeros + nibble 4|5|6|7 + ...")
    lines.append("  prophecy lane 6B (B~8): prefix 68...")
    lines.append("  leftmost-1 in 135-bit frame: col 0")

    text = "\n".join(lines)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text[:4000])
    if len(text) > 4000:
        print(f"\n... ({len(text)} chars total, wrote {OUT})")
    else:
        print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
