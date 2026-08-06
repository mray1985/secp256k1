#!/usr/bin/env python3
"""D/A ladder index flow per puzzle (first-appearance order, gaps from n-3 head)."""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_da_sequence import USER_DA, parse_da, format_da, build_chain, Tok


def chains_p1_70() -> dict[int, str]:
    chains = {n: USER_DA[n] for n in range(1, 21)}
    prev_end = parse_da(chains[20])[-1].op
    for n in range(21, 71):
        toks = build_chain(n, prev_end)
        if toks is None:
            raise RuntimeError(f"no chain P{n}")
        chains[n] = format_da(toks)
        prev_end = toks[-1].op
    return chains


def ladder(chain: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for t in parse_da(chain):
        if t.k not in seen:
            seen.add(t.k)
            out.append(t.k)
    return out


def gap_list(lad: list[int]) -> list[int]:
    return [lad[i] - lad[i + 1] for i in range(len(lad) - 1)]


def gap_str(lad: list[int]) -> str:
    return ",".join(str(g) for g in gap_list(lad))


def longest_minus1_streak(gaps: list[int]) -> int:
    run = best = 0
    for g in gaps:
        if g == 1:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


@dataclass
class LadderStats:
    n: int
    anchor: int
    lad: list[int]
    gaps: list[int]
    first_minus1: bool
    count_minus1: int
    streak_minus1: int

    @classmethod
    def from_chain(cls, n: int, chain: str) -> LadderStats:
        lad = ladder(chain)
        gaps = gap_list(lad)
        return cls(
            n=n,
            anchor=n - 3,
            lad=lad,
            gaps=gaps,
            first_minus1=bool(gaps and gaps[0] == 1),
            count_minus1=sum(1 for g in gaps if g == 1),
            streak_minus1=longest_minus1_streak(gaps),
        )


def head_block(chain: str, n: int) -> str:
    """First run at anchor k = n-3."""
    if n < 4:
        return chain
    k = n - 3
    m = re.match(rf"^((?:[DA]\({k}\))+)", chain)
    return m.group(1) if m else "?"


def p71_shift_p70(p70: str) -> str:
    toks = [Tok(t.op, t.k + 1) for t in parse_da(p70)]
    return format_da(toks)


def write_csv(rows: list[LadderStats], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "puzzle",
                "anchor_k",
                "num_indices",
                "first_minus1",
                "count_minus1",
                "max_streak_minus1",
                "ladder",
                "gaps",
            ]
        )
        for s in rows:
            w.writerow(
                [
                    s.n,
                    s.anchor,
                    len(s.lad),
                    int(s.first_minus1),
                    s.count_minus1,
                    s.streak_minus1,
                    " ".join(str(k) for k in s.lad),
                    gap_str(s.lad),
                ]
            )


def summary_lines(rows: list[LadderStats]) -> list[str]:
    first_yes = [s.n for s in rows if s.first_minus1]
    first_no = [s.n for s in rows if s.gaps and not s.first_minus1]
    single = [s.n for s in rows if len(s.lad) < 2]
    any_minus1 = [s.n for s in rows if s.count_minus1]
    zero_minus1 = [s.n for s in rows if not s.count_minus1]
    total_steps = sum(s.count_minus1 for s in rows)
    with_ladder = sum(1 for s in rows if len(s.lad) > 1)

    best = sorted(rows, key=lambda s: s.streak_minus1, reverse=True)[:5]
    best_lines = [
        f"  P{s.n:02d}: streak {s.streak_minus1}  ladder={s.lad}"
        for s in best
        if s.streak_minus1
    ]

    return [
        "=== MINUS-1 STEP SUMMARY (gap=1 in ladder, e.g. 47->46) ===",
        f"  Puzzles P4-P70: {len(rows)} total",
        f"  First step after head is -1: {len(first_yes)} / {len(rows)} ({100 * len(first_yes) / len(rows):.1f}%)",
        f"    YES: {', '.join(f'P{n}' for n in first_yes)}",
        f"  First step is NOT -1: {len(first_no)} (+ {len(single)} with no next index: P{single[0]}, P{single[1]})"
        if len(single) >= 2
        else f"  First step is NOT -1: {len(first_no)}",
        f"    NO:  {', '.join(f'P{n}' for n in first_no + single)}",
        f"  At least one -1 step anywhere: {len(any_minus1)} / {len(rows)}",
        f"  Zero -1 steps: {len(zero_minus1)} - {', '.join(f'P{n}' for n in zero_minus1)}",
        f"  Total -1 steps (all puzzles): {total_steps}",
        f"  Avg -1 steps per puzzle (ladder>1): {total_steps / with_ladder:.2f}",
        "",
        "=== LONGEST CONSECUTIVE -1 STREAKS ===",
        *best_lines,
    ]


def main() -> None:
    chains = chains_p1_70()
    stats = [LadderStats.from_chain(n, chains[n]) for n in range(4, 71)]
    p70 = chains[70]
    p71_hyp = p71_shift_p70(p70)

    lines = [
        "D/A LADDER FLOW — puzzle index order (first appearance in chain)",
        "  Head anchor k = n-3 for n>=4; chain alternates D/A on each k",
        "  A(k) weight 1xP_k, D(k) weight 2xP_k",
        "  gap=1 means -1 next (e.g. P47 -> P46)",
        "",
        "n   anchor  start  end   #idx  1st  #1  streak  ladder (high -> low)              gaps",
        "--- ------  -----  ----  ----  ---  --  ------  --------------------------------  ----------------",
    ]

    for s in stats:
        ch = chains[s.n]
        first, last = parse_da(ch)[0], parse_da(ch)[-1]
        fm = "Y" if s.first_minus1 else ("-" if len(s.lad) < 2 else "N")
        lines.append(
            f"P{s.n:<2d}  n-3={s.anchor:<2d}  {first.op}({first.k}){'':<{max(0, 6 - len(str(first.k)))}}"
            f"  {last.op}({last.k}){'':<{max(0, 4 - len(str(last.k)))}}"
            f"  {len(s.lad):<4d}  {fm:<3s}  {s.count_minus1:<2d}  {s.streak_minus1:<6d}  {s.lad}  [{gap_str(s.lad)}]"
        )

    lines += ["", *summary_lines(stats)]
    lines += [
        "",
        "=== P70 full (reference) ===",
        f"chain: {p70}",
        f"ladder: {ladder(p70)}",
        f"gaps:   [{gap_str(ladder(p70))}]",
        f"head:   {head_block(p70, 70)}",
        "",
        "=== P71 hypothesis (P70 indices +1, ends P2) ===",
        f"chain: {p71_hyp}",
        f"ladder: {ladder(p71_hyp)}",
        f"gaps:   [{gap_str(ladder(p71_hyp))}]",
        f"head:   {head_block(p71_hyp, 71) if len(ladder(p71_hyp)) else '?'}",
        "",
        "=== FLOW RULE (n >= 4) ===",
        "1. q = floor(P_n / P_{n-3})  — how many A/D units at the head anchor",
        "2. Head block at k=n-3, starting op = oppose(P_{n-1} last op)",
        "   P70 ended A(1) -> P71 head starts D(68)",
        "3. Tail decomposes remainder using k = (n-3)-1 down to 1",
        "4. Ladder indices descend from ~n-3 toward 1 (P71: toward 2)",
    ]

    txt_out = ROOT / "ARCHIVE" / "p71_da_ladder_flow.txt"
    csv_out = ROOT / "ARCHIVE" / "p71_da_ladder_minus1.csv"
    txt_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(stats, csv_out)
    print(f"wrote {txt_out}")
    print(f"wrote {csv_out}")
    print()
    print("\n".join(summary_lines(stats)))


if __name__ == "__main__":
    main()
