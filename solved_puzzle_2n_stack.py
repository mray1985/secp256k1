#!/usr/bin/env python3
"""Stack solved puzzle d decompositions: vertical offset rows 2^(p-1-k)."""

from __future__ import annotations

from pathlib import Path

from puzzle_keys_53125 import parse_53125

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "solved_puzzle_2n_stack.txt"


def offsets_from_msb(p: int, d: int) -> set[int]:
    if d <= 0:
        return set()
    top = p - 1
    bits = [i for i in range(d.bit_length()) if d & (1 << i)]
    return {top - b for b in bits}


def main() -> int:
    keys = parse_53125()
    puzzles = sorted(keys)
    off_by_p = {p: offsets_from_msb(p, keys[p].d) for p in puzzles}
    max_off = max((max(s) for s in off_by_p.values() if s), default=0)
    solved_n = sum(1 for p in puzzles if keys[p].d > 0)

    out: list[str] = []
    out.append("SOLVED PUZZLE 2^n STACK (relative: row k = 2^(p-1-k))")
    out.append("# = bit set   . = clear   - = no private key in 53125")
    out.append("=" * 100)

    chunk = 20
    for c0 in range(0, len(puzzles), chunk):
        ps = puzzles[c0 : c0 + chunk]
        out.append("")
        out.append("Puzzle: " + ", ".join(str(p) for p in ps))
        hdr = " k\\P |" + "|".join(f"{p:>3}" for p in ps) + "| hits |"
        out.append(hdr)
        out.append("-" * len(hdr))
        for k in range(max_off + 1):
            cells = []
            for p in ps:
                d = keys[p].d
                if d <= 0:
                    cells.append("  -")
                elif k in off_by_p[p]:
                    cells.append("  #")
                else:
                    cells.append("  .")
            hits = sum(1 for p in puzzles if k in off_by_p.get(p, set()))
            out.append(f"{k:3d}  |" + "|".join(cells) + f"| {hits:4d} |")

    out.append("")
    out.append("ROW k LABELS (what each horizontal line means at puzzle p)")
    out.append("  k=0 -> 2^(p-1)     (MSB / band floor bit)")
    out.append("  k=1 -> 2^(p-2)")
    out.append("  k=a -> 2^(p-1-a)")
    out.append("")

    out.append("HIGH-RUN ROWS (offset k present in many puzzles)")
    for k in range(max_off + 1):
        hits = [p for p in puzzles if k in off_by_p.get(p, set())]
        if len(hits) >= 10:
            out.append(f"  k={k:3d}  hits={len(hits):2d}/{solved_n}  puzzles={hits[:25]}{'...' if len(hits)>25 else ''}")

    out.append("")
    out.append("ABSOLUTE BIT STACK P55-P85 (row n = 2^n globally)")
    ps = [p for p in puzzles if 55 <= p <= 85]
    if ps:
        hdr = "  n |" + "|".join(f"{p:>3}" for p in ps) + "|"
        out.append(hdr)
        out.append("-" * len(hdr))
        for n in range(84, 54, -1):
            cells = []
            for p in ps:
                d = keys[p].d
                if d <= 0:
                    cells.append("  -")
                elif d & (1 << n):
                    cells.append("  #")
                else:
                    cells.append("  .")
            out.append(f"{n:3d} |" + "|".join(cells) + "|")

    out.append("")
    out.append("SHARED OFFSET k BETWEEN p AND p+5 (n mod 5 lane stack)")
    for p in puzzles:
        q = p + 5
        if q not in keys or keys[p].d <= 0 or keys[q].d <= 0:
            continue
        shared = sorted(off_by_p[p] & off_by_p[q])
        if shared:
            out.append(f"  P{p:3d}+5=P{q:3d}  shared k={shared}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print("\n".join(out[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
