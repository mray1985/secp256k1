#!/usr/bin/env python3
"""Decode poetic genesis-block overlay from user message."""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Coinbase script prefix from genesis block.txt hex dump (lines 4-5)
PREFIX = bytes.fromhex(
    "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa"
    "4b1e5e4a29ab5f49ffff001d1dac2b7c"
)
TIMES = (
    b"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
)
PUB = bytes.fromhex(
    "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb6"
    "49f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5fac"
)

USER_FRAGMENTS = [
    ("***·j-1y<4", "coinbase extra-nonce / pushdata noise"),
    ("gv.a", "bytes 67 76 8f 61 at script offset"),
    ("SQ2:9 / Q2:", "bytes 51 32 3a (ASCII Q2:)"),
    ("K.^J)+_I", "bytes 4b 1e 5e 4a 29 ab 5f 49"),
    ("The Times 03/Jan/2009", "genesis headline (Satoshi message)"),
    ("bailout for banks", "end of genesis headline"),
    ("CA.gSyubUH", "start of uncompressed pubkey push in coinbase"),
    ("ybae.abJI0K?LI816U", "pubkey body fragment"),
    ("ND/8", "tail marker (katakana D slash 8 in source)"),
]

DAI_LINES = [
    ("至必辛西辛彰語苦癸參第年經堂", 1),
    ("第要要第深者", 2),
    ("收第第第学第第第第第第据", 8),
    ("一票收收第第第", 3),
]


def ascii_runs(data: bytes) -> list[str]:
    runs: list[str] = []
    cur = ""
    for b in data:
        if 32 <= b < 127:
            cur += chr(b)
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = ""
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def main() -> None:
    raw = (PREFIX + TIMES + PUB).decode("latin-1", errors="replace")
    print("=" * 72)
    print("GENESIS COINBASE — POETIC INSTRUCTION DECODE")
    print("=" * 72)
    print()
    print("Readable ASCII runs in coinbase PREFIX:")
    for r in ascii_runs(PREFIX):
        print(f"  {r!r}")
    print()
    print("Hex prefix:", PREFIX.hex())
    print()

    print("User fragment -> genesis anchor:")
    for frag, note in USER_FRAGMENTS:
        key = frag.replace("***·", "").replace("SQ2:9", "Q2:")
        hit = key[:4] in raw or key[:6] in raw or key in raw
        print(f"  {frag:30s}  hit={hit}  ({note})")
    print()

    print("第 (dai = No./ordinal) counts - NOT puzzle numbers, mnemonic overlay:")
    total = 0
    for line, _ in DAI_LINES:
        n = line.count("第")
        total += n
        print(f"  {line}")
        print(f"    -> {n} x 第")
    print(f"  total 第 = {total}")
    print()

    print("Chinese header (from genesisblockdown.txt):")
    print("  系至必辛西辛彰語苦癸參第年經堂")
    print("  = homophone overlay on coinbase bytes, NOT a scalar recipe")
    print()

    print("Satoshi message (literal instruction):")
    print(f"  {TIMES.decode()}")
    print()

    print("Genesis pubkey X:")
    print(f"  {hex(int.from_bytes(PUB[1:33], 'big'))}")
    print()

    print("=" * 72)
    print("OPERATIONAL READ (for your ECDLP frame)")
    print("=" * 72)
    print("""
1. LITERAL LAYER - The Times headline is the real genesis coinbase text.
   ASCII blobs (gv.a, Q2:, K.^J)+_I, CA.gSyubUH…) are raw script bytes,
   not separate formulas.

2. 第 LAYER - Repeated 第 = 'No./edition' counters in the Japanese/Chinese
   gloss (1st year, 1st school year, 1st vote). Do NOT read as puzzle #135.

3. TAIL ンD/8中時三正十手司物 - Your notes map this to 'D/8' + place names.
   If used at all: test scalar ops *after* the 127-double chain (step127),
   not as a standalone key.

4. ECDLP LINK - Genesis block is calibration anchor #0, not puzzle 135/160.
   Bridge frame still applies: only d·G == P certifies a hit.

5. POST-127 BIT OPS - Your prior note 'DA, D, DA' after 127 doubles = bits 101
   on the scalar tail starting at step127 = 41512357110303327057832403173916941977504.
""")


if __name__ == "__main__":
    main()
