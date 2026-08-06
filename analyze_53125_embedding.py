#!/usr/bin/env python3
"""Analyze the 53125 spatial embedding: private key hex within x/y coords."""
from __future__ import annotations
import sys, re, itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from puzzle_keys_53125 import parse_53125
from hashkeys_rsz import PUZZLE_RSZ

pkeys = parse_53125()
puzzle_d: dict[int, int] = {}
puzzle_px: dict[int, int] = {}
puzzle_py: dict[int, int] = {}
for n, rec in pkeys.items():
    puzzle_d[n] = rec.d
    puzzle_px[n] = rec.px
    puzzle_py[n] = rec.py

for n, rsz in PUZZLE_RSZ.items():
    if n not in puzzle_px:
        raw = bytes.fromhex(rsz.pub_compressed)
        puzzle_px[n] = int.from_bytes(raw[1:], "big")

def fmt_hex(v: int, pad: int = 64) -> str:
    return format(v, "x").zfill(pad)

def find_embedding(n: int) -> None:
    """Check if private key hex digits appear in x and y hex strings."""
    if n not in puzzle_d:
        return
    d = puzzle_d[n]
    d_hex = format(d, "x")
    px = puzzle_px.get(n, 0)
    if not px:
        return
    py = puzzle_py.get(n, 0)
    px_hex = fmt_hex(px)
    py_hex = fmt_hex(py)
    
    # Try to find d_hex substring in px_hex or py_hex
    in_px = d_hex in px_hex
    in_py = d_hex in py_hex
    in_both = d_hex in px_hex or d_hex in py_hex
    
    # Check if d_hex digits are scattered in x/y at consistent offsets
    # For each digit position in d_hex, find where it appears in px_hex and py_hex
    positions_x = []
    positions_y = []
    for i, ch in enumerate(d_hex):
        # find first occurrence in px that we haven't used
        try:
            px_pos = px_hex.index(ch)
            positions_x.append(px_pos)
        except ValueError:
            positions_x.append(-1)
        try:
            py_pos = py_hex.index(ch)
            positions_y.append(py_pos)
        except ValueError:
            positions_y.append(-1)
    
    # Check if positions are monotonic (increasing)
    mono_x = all(a <= b for a, b in zip(positions_x, positions_x[1:]) if a >= 0 and b >= 0)
    mono_y = all(a <= b for a, b in zip(positions_y, positions_y[1:]) if a >= 0 and b >= 0)
    
    print(f"P{n:3d} d={d_hex}")
    print(f"     bits={d.bit_length()} in_px={in_px} in_py={in_py} mono_x={mono_x} mono_y={mono_y}")
    if n >= 60:
        print(f"     px_hex[:20]={px_hex[:20]}...")
        print(f"     py_hex[:20]={py_hex[:20]}...")

def check_page_relationship():
    """Analyze the 'page' concept from 53125.txt."""
    print("\n" + "=" * 80)
    print("PAGE RELATIONSHIP FROM 53125.TXT")
    print("=" * 80)
    
    # Known pages from 53125.txt (parsed manually):
    pages = {
        100: 14470353894822108305672986386,
        105: 484720502415300761779808819874,
        110: 18170768302566452875795674315863,
        115: 524402053842897536071227906073783,
        120: 15322391680683005559008517510312739,
        125: 627509161962375741762900164621920358,
        # P130 has two values - use first
        # P130 values unclear
    }
    
    for n, page in sorted(pages.items()):
        d = puzzle_d.get(n, 0)
        if d:
            ratio = d / page
            diff = d - page * 60
            print(f"P{n:3d}: d={d}  page={page}")
            print(f"       d/page = {ratio:.6f}")
            print(f"       d = 60*page + {diff}")
            print(f"       d mod 60 = {d % 60}")
            print(f"       page mod (d unique) = {(page * 60) % d}")

def find_page_p135():
    """Try to derive 'page' for P135 from the available data in 53125.txt."""

    px_hex = "145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16"
    px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    
    # Numbers from 53125.txt near P135 section
    # 145261182339667120712099431353032309608116  (could this be page?)
    num1 = 145261182339667120712099431353032309608116
    # DCAEFCEFFBBFEEAAFBBDDE = 266790037955370537520446942
    hex1 = 0xDCAEFCEFFBBFEEAAFBBDDE
    dec1 = 266790037955370537520446942
    
    print(f"\nP135 numbers from 53125.txt:")
    print(f"  num1 = {num1}")
    print(f"  hex1 = {hex1} = {dec1}")
    print(f"  px   = {px}")
    
    # Try dividing by 60 (if page * 60 ≈ d)
    print(f"\n  num1/60 = {num1 // 60} (remainder {num1 % 60})")
    print(f"  px/60   = {px // 60} (remainder {px % 60})")
    
    # Check if these numbers relate to the ladder digits
    # Ladder from y²: 23643 = result - 2^256
    ladder_y2 = [23643, 11775, 5864, 2920, 1454, 724, 360, 179, 89, 44, 22, 11, 5, 2, 1]
    prod_y2 = 1
    for v in ladder_y2:
        prod_y2 *= v
    print(f"\n  y² ladder product = {prod_y2}")
    
    # Ladder from x (line 81):
    ladder_x = [20589, 10254, 5107, 2543, 1266, 630, 314, 156, 77, 38, 19, 9, 4, 2, 1]
    prod_x = 1
    for v in ladder_x:
        prod_x *= v
    print(f"  x ladder product  = {prod_x}")
    
    # The ladder products factor as given in 53125.txt
    # x: 2^10 · 3^8 · 7^2 · 19^2 · 3607916095265246771435 = 428775246700352655224805257333760
    from math import prod
    x_prod_check = 2**10 * 3**8 * 7**2 * 19**2 * 3607916095265246771435
    print(f"  x ladder product (from factors) = {x_prod_check}")
    print(f"  match = {prod_x == x_prod_check}")
    
    # y²: 2^16 · 3^5 · 5^5 · 11^3 · 46263936511604342147 = 3064480517684782529255557324800000
    y2_prod_check = 2**16 * 3**5 * 5**5 * 11**3 * 46263936511604342147
    print(f"  y² ladder product (from factors) = {y2_prod_check}")
    print(f"  match = {prod_y2 == y2_prod_check}")
    
    # Check if ladder product relates to px
    print(f"\n  px / x_ladder_prod = {px / prod_x:.3f}")
    print(f"  px % x_ladder_prod = {px % prod_x}")

if __name__ == "__main__":
    # Analyze hex embedding for known puzzles
    print("=" * 80)
    print("HEX EMBEDDING ANALYSIS")
    print("=" * 80)
    selected = [7, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]
    for n in selected:
        find_embedding(n)
    
    check_page_relationship()
    find_page_p135()
