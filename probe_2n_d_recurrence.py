#!/usr/bin/env python3
"""Probe 2^n * d_n vs next puzzle / nearest puzzle d."""

from __future__ import annotations

import re
from pathlib import Path

from puzzle_catalog import load_catalog

ROOT = Path(__file__).resolve().parent
TDAD_TXT = ROOT / "02_Research" / "notes" / "double_and_add.txt"
PATTERN_TXT = ROOT / "02_Research" / "notes" / "thePattern.txt"

T71 = 1411488254391826260559
T72 = 3041466034261123517719


def load_tdad() -> dict[int, int]:
    out: dict[int, int] = {}
    if not TDAD_TXT.exists():
        return out
    for line in TDAD_TXT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"puzzle\s+(\d+):\s*(.*)", line.strip(), re.I)
        if not m:
            continue
        rest = m.group(2).strip()
        if not rest:
            continue
        val_s = rest.split("=")[0].strip().replace("\t", "")
        if val_s and val_s[0].isdigit():
            out[int(m.group(1))] = int(val_s)
    return out


def nearest_puzzle(val: int, table: dict[int, int]) -> tuple[int, int, int]:
    n, d = min(table.items(), key=lambda x: abs(x[1] - val))
    return n, d, val - d


def main() -> int:
    cat = load_catalog()
    solved = {n: cat[n].private_key for n in range(1, 161) if cat[n].solved and cat[n].private_key > 0}
    tdad = load_tdad()
    extra = {71: T71, 72: T72}
    all_d = {**solved, **extra}

    print(f"solved={len(solved)} tdad={len(tdad)}")

    print("\n=== A: 2^k * d_n closest to d_{n+1} (best k per n) ===")
    print("n   k   exact  diff_bits  d_n_bits  d_next_bits")
    for n in range(1, 100):
        if n not in solved or (n + 1) not in solved:
            continue
        d, dnext = solved[n], solved[n + 1]
        best_k, best_diff = 0, abs(d - dnext)
        for k in range(0, 90):
            diff = abs((d << k) - dnext)
            if diff < best_diff:
                best_diff = diff
                best_k = k
        print(
            f"{n:3d} {best_k:3d}  {str((d << best_k) == dnext):5s}  "
            f"{best_diff.bit_length():3d}       {d.bit_length():3d}       {dnext.bit_length():3d}"
        )

    print("\n=== B: fixed k=32 : 2^32 * d_n vs d_{n+1} and nearest puzzle d ===")
    print("n   2^32*d bits  nearest  diff_bits  d_{n+1} diff_bits  delta sign")
    for n in sorted(set(list(range(1, 101)) + [105, 110, 115, 120, 125, 130])):
        if n not in all_d:
            continue
        d = all_d[n]
        val = d << 32
        nn, nd, delta = nearest_puzzle(val, all_d)
        dnext = all_d.get(n + 1)
        dnext_diff = abs(val - dnext) if dnext is not None else None
        print(
            f"{n:3d} {val.bit_length():3d}          P{nn:3d}   "
            f"{abs(delta).bit_length():3d}          "
            f"{(dnext_diff.bit_length() if dnext_diff is not None else 0):3d}           "
            f"{'+' if delta >= 0 else '-'}"
        )

    print("\n=== C: 2^n * d_n = d_{n+1} exact? (scan n as shift amount = puzzle index?) ===")
    hits = 0
    for n in range(1, 100):
        if n not in solved or (n + 1) not in solved:
            continue
        d, dnext = solved[n], solved[n + 1]
        for k in (n, n - 1, 32, 31, 33, d.bit_length(), dnext.bit_length()):
            if k < 0:
                continue
            if (d << k) == dnext:
                print(f"EXACT n={n} k={k}")
                hits += 1
    print(f"exact hits in C: {hits}")

    print("\n=== D: next_puzzle - 2^32*d or 2^32*d - drop 32 ===")
    for n in range(1, 75):
        if n not in solved or (n + 1) not in solved:
            continue
        d, dnext = solved[n], solved[n + 1]
        val = d << 32
        print(
            f"n={n:2d}  dnext-(2^32*d)={dnext - val}  "
            f"(2^32*d)-32={val - 32}  nearest? diff_to_dnext={(val - 32) - dnext}"
        )

    print("\n=== E: P71/P72 — 2^32 * d_70 vs T_71, nearest puzzle ===")
    for base_n, target_n, label in ((70, 71, "T71"), (71, 72, "T72")):
        if base_n not in all_d:
            continue
        d = all_d[base_n]
        val = d << 32
        tgt = all_d.get(target_n)
        nn, nd, delta = nearest_puzzle(val, all_d)
        tgt_diff = abs(val - tgt) if tgt else None
        print(
            f"{label}: 2^32*d_{base_n} bits={val.bit_length()}  "
            f"nearest P{nn} diff={delta}  "
            f"target P{target_n} diff={tgt - val if tgt else None}  "
            f"drop32 diff={(val - 32) - tgt if tgt else None}"
        )

    print("\n=== F: index lock — nearest puzzle to 2^32*d_n is P_{n+32}? ===")
    hits = total = 0
    for n in sorted(all_d):
        m = n + 32
        if m not in all_d:
            continue
        total += 1
        val = all_d[n] << 32
        nearest_n, nearest_d, _ = nearest_puzzle(val, all_d)
        ok = nearest_n == m
        if ok:
            hits += 1
        if 35 <= n <= 45 or 65 <= n <= 72:
            delta = val - all_d[m]
            print(
                f"n={n} nearest=P{nearest_n} expect P{m} ok={ok} "
                f"delta_bits={abs(delta).bit_length()}"
            )
    print(f"index lock hits: {hits}/{total}")

    print("\n=== G: 2^32*d_n - drop vs d_{n+32} (drop=0,32) ===")
    for n in sorted(all_d):
        m = n + 32
        if m not in all_d:
            continue
        val = all_d[n] << 32
        tgt = all_d[m]
        for drop in (0, 32):
            diff = (val - drop) - tgt
            if 35 <= n <= 45 or 65 <= n <= 72:
                print(
                    f"n={n} drop={drop} diff={diff} "
                    f"abs_bits={abs(diff).bit_length()}"
                )

    print("\n=== H: double lane 2*d_n vs d_{n+1} ===")
    for n in range(38, 45):
        if n not in all_d or (n + 1) not in all_d:
            continue
        d, d1 = all_d[n], all_d[n + 1]
        diff = 2 * d - d1
        print(f"n={n} (2d-dnext) bits={abs(diff).bit_length()} ratio={2 * d / d1:.8f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
