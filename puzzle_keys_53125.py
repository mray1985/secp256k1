#!/usr/bin/env python3
"""Parse solved puzzle keys + pub coords from 00_Projects/patent/53125.txt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH_53125 = ROOT / "00_Projects" / "patent" / "53125.txt"


@dataclass(frozen=True)
class PuzzleKey53125:
    n: int
    d: int
    px: int
    py: int


def parse_53125(path: Path = PATH_53125) -> dict[int, PuzzleKey53125]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[int, PuzzleKey53125] = {}
    # Match blocks: puzzle N ... priv dec ... x dec ... y dec
    blocks = re.split(r"(?i)(?:puzzle)\s+(\d+)\b", text)[1:]
    for i in range(0, len(blocks) - 1, 2):
        n = int(blocks[i])
        body = blocks[i + 1]
        m_d = re.search(r"priv\s+dec\s+(\d+)", body, re.I)
        m_x = re.search(r"x\s+dec\s+(\d+)", body, re.I)
        m_y = re.search(r"y\s*dec\s+(\d+)", body, re.I)
        if not (m_x and m_y):
            continue
        d = int(m_d.group(1)) if m_d else 0
        out[n] = PuzzleKey53125(n, d, int(m_x.group(1)), int(m_y.group(1)))
    return out


if __name__ == "__main__":
    keys = parse_53125()
    print(f"parsed {len(keys)} puzzles from {PATH_53125}")
    for n in sorted(keys)[:5]:
        print(n, keys[n].d)
