#!/usr/bin/env python3
"""
P135 search: 8 hex-char chunks in an 8x8 grid (Px x Py chunk cross).

Each row i, col j:
  - replace chunk i with py_chunk[j]
  - replace chunk j with px_chunk[i]
  - chunk k = xor_hex(px_chunk[i], py_chunk[j]) for k==i
  - full row from px, one slot from py[j]
Also: kanga 8-chunk flip matrix from observed chunk values.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 1 << 134
TOP = (1 << 135) - 1
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
KANGA = ROOT / "135kanga_2p65_candidates.txt"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "hex_8x8_hunt.log"


def ec(d: int) -> bool:
    pt = d * G
    return pt.x() == PX and pt.y() == PY


def check(d: int) -> int | None:
    for c in (d, N - d):
        if LO <= c <= TOP and ec(c):
            return c
    return None


def chunks8(h64: str) -> list[str]:
    h = h64.lower().zfill(64)[-64:]
    return [h[i * 8 : (i + 1) * 8] for i in range(8)]


def xor_chunk(a: str, b: str) -> str:
    return "".join(f"{int(x, 16) ^ int(y, 16):x}" for x, y in zip(a, b))


def assemble(ch: list[str]) -> int:
    return int("".join(ch), 16)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def load_kanga_chunks() -> list[list[str]]:
    rows: list[list[str]] = []
    for line in KANGA.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip().lower()
        if not line or line.startswith("02") or len(line) < 64:
            continue
        if all(c in "0123456789abcdef" for c in line):
            rows.append(chunks8(line))
    return rows


def add_candidate(ch: list[str], tested: int, label: str) -> tuple[int | None, int]:
    d = assemble(ch)
    tested += 2
    hit = check(d)
    if hit:
        log(f"*** X MARKS THE SPOT d={hit} [{label}] hex={''.join(ch)} ***")
        return hit, tested
    return None, tested


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kanga-local", action="store_true", help="8x8 chunk swap on kanga bases")
    args = ap.parse_args()

    LOG.write_text("", encoding="utf-8")
    t0 = time.perf_counter()
    tested = 0
    px_c = chunks8(format(PX, "x"))
    py_c = chunks8(format(PY, "x"))

    log("Px chunks: " + " | ".join(px_c))
    log("Py chunks: " + " | ".join(py_c))

    # 8x8 cross: 64 primary transforms
    log("Phase A: 8x8 px/py chunk cross (64 grid)")
    for i in range(8):
        for j in range(8):
            # swap-style: slot i <- py[j]
            ch = px_c.copy()
            ch[i] = py_c[j]
            hit, tested = add_candidate(ch, tested, f"px+slot{i}<-py[{j}]")
            if hit:
                return 0

            ch = py_c.copy()
            ch[j] = px_c[i]
            hit, tested = add_candidate(ch, tested, f"py+slot{j}<-px[{i}]")
            if hit:
                return 0

            ch = px_c.copy()
            ch[i] = xor_chunk(px_c[i], py_c[j])
            hit, tested = add_candidate(ch, tested, f"px slot{i} xor py[{j}]")
            if hit:
                return 0

            # row i from px, col j inject at both i and j
            ch = px_c.copy()
            ch[i] = py_c[j]
            ch[j] = xor_chunk(px_c[i], py_c[j])
            hit, tested = add_candidate(ch, tested, f"px i={i} j={j} dual")
            if hit:
                return 0

    log(f"Phase A done tested={tested}")

    # 8x8 digit grid lift (single hex cells): row i col j -> priv chunk nibble map
    log("Phase B: 8x8 digit grid diagonals")
    px_digits = list(format(PX, "064x")[-64:])
    py_digits = list(format(PY, "064x")[-64:])
    for i in range(8):
        for j in range(8):
            # build 64-hex from grid[i][k]=px digit, grid[k][j]=py digit blend
            grid = [[px_digits[r * 8 + c] for c in range(8)] for r in range(8)]
            for k in range(8):
                grid[i][k] = py_digits[j * 8 + k]
                grid[k][j] = px_digits[i * 8 + k]
            flat = "".join("".join(row) for row in grid)
            ch = chunks8(flat)
            hit, tested = add_candidate(ch, tested, f"grid row{i} col{j}")
            if hit:
                return 0

    log(f"Phase B done tested={tested}")

    if args.kanga_local or True:
        log("Phase C: kanga 8x8 chunk substitution")
        kanga = load_kanga_chunks()
        # unique chunk values per slot
        slot_vals: list[set[str]] = [set() for _ in range(8)]
        for row in kanga:
            for k in range(8):
                slot_vals[k].add(row[k])
        for k in range(8):
            log(f"  slot {k} unique 8-hex chunks: {len(slot_vals[k])}")

        # 8x8: on first 200 kanga bases, try px[i]/py[j] at slots i,j
        for bi, base in enumerate(kanga):
            for i in range(8):
                for j in range(8):
                    ch = base.copy()
                    ch[i] = py_c[j]
                    hit, tested = add_candidate(ch, tested, f"kanga[{bi}] slot{i}<-py[{j}]")
                    if hit:
                        return 0
                    ch = base.copy()
                    ch[j] = px_c[i]
                    hit, tested = add_candidate(ch, tested, f"kanga[{bi}] slot{j}<-px[{i}]")
                    if hit:
                        return 0
            if bi and bi % 200 == 0:
                log(f"  kanga base {bi}/{len(kanga)} tested={tested}")

    elapsed = time.perf_counter() - t0
    log(f"DONE no hit tested={tested} elapsed={elapsed:.1f}s rate={tested/max(elapsed,1e-9):.0f}/s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
