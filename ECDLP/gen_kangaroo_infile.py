#!/usr/bin/env python3
"""Build JeanLucPons Kangaroo inFiles from ECDLP pipeline shelf2 anchors.

Puzzle n: d in [2^(n-1), 2^n).  Kangaroo v2.x is limited to ~125-bit intervals.

Outputs under kangaroo_infiles/:
  p{n}_shelf2_125bit.txt       — [shelf2, shelf2 + 2^125 - 1] capped at TOP
  p{n}_band_lo_125bit.txt      — [LO, LO + 2^125 - 1] (band floor window)
  p{n}_meta.txt                — human-readable notes + run commands

Usage:
  python gen_kangaroo_infile.py --puzzle 135
  python gen_kangaroo_infile.py --puzzle 160
  python gen_kangaroo_infile.py --puzzle 135 160
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ecdlp_full_pipeline import (
    N,
    P115_HEIGHT_MINUS_OFFSET_BITS,
    PuzzleConfig,
    apply_puzzle_defaults,
    compute_order_in_the_court,
    delta,
    puzzle_band,
    verify_n_y_compression,
    y_even,
)

KANGAROO_MAX_BITS = 125
OUT_DIR = Path(__file__).resolve().parent / "kangaroo_infiles"
P160_OFFICIAL_PUB = (
    Path(__file__).resolve().parent.parent
    / "puzzle160_keyhunt_bsgs"
    / "P160_compressed.pub"
)
KANGAROO_EXE = Path(__file__).resolve().parent.parent / "Kangaroo" / "Kangaroo.exe"


def compressed_pubkey(x: int, y: int) -> str:
    prefix = "02" if y % 2 == 0 else "03"
    return prefix + format(x, "064x")


def puzzle_pubkey(cfg: PuzzleConfig) -> tuple[str, int, int, str]:
    """Return (compressed_hex, px, py, source_note)."""
    if cfg.puzzle_num == 160 and P160_OFFICIAL_PUB.is_file():
        line = P160_OFFICIAL_PUB.read_text(encoding="ascii").strip().splitlines()[0].strip()
        return line, 0, 0, f"official puzzle 160 ({P160_OFFICIAL_PUB.name})"
    row = cfg.row
    px, py = cfg.Px[row], cfg.Py
    assert py is not None
    return (
        compressed_pubkey(px, py),
        px,
        py,
        f"bridge Px{row + 1} even-y",
    )


def compute_shelf2(cfg: PuzzleConfig) -> int:
    lo = cfg.lo
    px, rx, py = cfg.Px, cfg.rx, cfg.Py
    assert py is not None and cfg.ry is not None
    qx = [(rx[i] * delta) % N for i in range(3)]
    qx_scaled = [(px[i] * delta) % N for i in range(3)]
    lambda_ns = [(qx_scaled[i] * pow(qx[i], -1, N)) % N for i in range(3)]
    n_yc = verify_n_y_compression(px_triple=px, rx_triple=rx, py=py, ry=cfg.ry)
    py1 = y_even(px[0])
    ry1 = y_even(rx[0])
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(ry1 * delta) % N,
        qx_scaled=qx_scaled,
        qy_scaled=(py1 * delta) % N,
        lambda_ns=lambda_ns,
        lam_y_n=n_yc.lambda_y_n,
    )
    return oitc.shelf2


def write_infile(path: Path, start: int, end: int, pubkey: str) -> None:
    if start > end:
        raise ValueError(f"invalid range start={start} > end={end}")
    path.write_text(
        f"{start:x}\n{end:x}\n{pubkey}\n",
        encoding="ascii",
    )


def generate_for_puzzle(puzzle_num: int) -> list[Path]:
    cfg = PuzzleConfig(puzzle_num=puzzle_num)
    apply_puzzle_defaults(cfg)
    lo, hi, top = puzzle_band(puzzle_num)
    shelf2 = compute_shelf2(cfg)
    pub, px, py, pub_src = puzzle_pubkey(cfg)
    expect_off_bits = puzzle_num - P115_HEIGHT_MINUS_OFFSET_BITS

    win = (1 << KANGAROO_MAX_BITS) - 1
    shelf2_end = min(shelf2 + win, top)
    lo_end = min(lo + win, top)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    pfx = OUT_DIR / f"p{puzzle_num}"
    f1 = Path(f"{pfx}_shelf2_125bit.txt")
    write_infile(f1, shelf2, shelf2_end, pub)
    written.append(f1)

    f2 = Path(f"{pfx}_band_lo_125bit.txt")
    write_infile(f2, lo, lo_end, pub)
    written.append(f2)

    meta = Path(f"{pfx}_meta.txt")
    meta.write_text(
        f"Puzzle {puzzle_num} Kangaroo inFiles\n"
        f"{'=' * 60}\n"
        f"Band (half-open): d in [2^{puzzle_num - 1}, 2^{puzzle_num})\n"
        f"  LO  = {lo}\n"
        f"  HI  = {hi}\n"
        f"  TOP = {top}  (HI - 1, inclusive ceiling)\n"
        f"\n"
        f"Pubkey ({pub_src}):\n"
        f"  {pub}\n"
        f"\n"
        f"Bridge shelf2 anchor (v0 d2 track):\n"
        f"  {shelf2}\n"
        f"  hex {shelf2:x}\n"
        f"\n"
        f"P115 offset pattern: expect ~{expect_off_bits}-bit offset from shelf2 to d\n"
        f"Kangaroo limit: max ~{KANGAROO_MAX_BITS}-bit interval per run\n"
        f"\n"
        f"Generated ranges (inclusive end, Kangaroo format):\n"
        f"  {f1.name}\n"
        f"    [{shelf2:x}, {shelf2_end:x}]  width_bits~{((shelf2_end - shelf2 + 1).bit_length())}\n"
        f"  {f2.name}\n"
        f"    [{lo:x}, {lo_end:x}]  width_bits~{((lo_end - lo + 1).bit_length())}\n"
        f"\n"
        f"Full band ({puzzle_num}-bit wide) — use KeyHunt BSGS for puzzle 160, not Kangaroo:\n"
        f"  ..\\puzzle160_keyhunt_bsgs\\run_p160_bsgs_7m.bat\n"
        f"\n"
        f"Windows CPU run (from repo Kangaroo folder):\n"
        f"  cd ..\\Kangaroo\n"
        f"  .\\Kangaroo.exe -t 4 -d 22 -w p{puzzle_num}.work -wi 300 -o p{puzzle_num}_result.txt "
        f"..\\ECDLP\\kangaroo_infiles\\{f1.name}\n"
        f"\n"
        f"WSL:\n"
        f"  cd /mnt/c/Users/mitch/Desktop/secp256k1/Kangaroo\n"
        f"  ./kangaroo -t 4 -d 22 -w p{puzzle_num}.work -wi 300 -o p{puzzle_num}_result.txt "
        f"../ECDLP/kangaroo_infiles/{f1.name}\n",
        encoding="utf-8",
    )
    written.append(meta)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Kangaroo inFiles from pipeline shelf2")
    ap.add_argument("puzzles", type=int, nargs="*", default=[135, 160])
    args = ap.parse_args()

    all_files: list[Path] = []
    for n in args.puzzles:
        try:
            files = generate_for_puzzle(n)
            all_files.extend(files)
            print(f"Puzzle {n}: wrote {len(files)} files to {OUT_DIR}")
            for f in files:
                print(f"  {f.name}")
        except Exception as exc:
            print(f"Puzzle {n}: FAILED — {exc}", file=sys.stderr)
            return 1

    print(f"\nKangaroo.exe: {KANGAROO_EXE}  exists={KANGAROO_EXE.is_file()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
