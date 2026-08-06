#!/usr/bin/env python3
"""
DEAD END (negative result) — do not extend.

Packed U = x*10^78 + y, then unpack -> EC add -> repack, then study Delta-U,
is ordinary curve arithmetic in a trench coat. Empirically: all tested P+G,
2P, 2P+G packed deltas were unique; P135 neighborhood overlapped none of the
early walk. No reusable packed-decimal delta.

See instead: decimal_side_solved_triples.py
"""
raise SystemExit(
    "DEAD END: packed U / Delta-U branch closed. "
    "Use decimal_side_solved_triples.py"
)
