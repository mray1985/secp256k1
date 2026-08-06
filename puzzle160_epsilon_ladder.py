#!/usr/bin/env python3
"""Puzzle 160 — eps ladder on m = 2^96 + eps·2^57.

Model:  N + 1 = m · x
        m(eps) = 2^96 + eps · 2^57     (eps = 0 … 2^39 − 1)
        x(eps) = (N+1) / m(eps)        partner d in [2^159, 2^160)

Two related ladders:
  Eps ladder (last-digit ticks on m): uniform +2^57 per +0.000…001.
  Positional k-ladder (96.000…000k): alternating d steps 2^57 / 2^56
    (2^57 = 2·2^56); odd k→k+1 uses 2^57, even k→k+1 uses 2^56.

Positional partner (N-anchor, k ≥ 1):
  d_k = floor((N+1)/2^96) - (2^56-1) - floor(k/2)*2^57 - floor((k-1)/2)*2^56
P-anchor: d_k(P) = d_k(N) + 5_457_912_602  (constant across k; see newfound.txt)

Legacy 2^95 leg (--base 95): step 2^61.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from multiprocessing import Pool, cpu_count
from pathlib import Path

from probe_height96 import N, scalar_mul, trace_mult

NP1 = N + 1
STEP_57 = 2**57  # 144115188075855872 — eps tick / odd positional step
STEP_56 = 2**56  # 72057594037927936  — even positional step (= STEP_57 // 2)
STEP_96 = STEP_57  # alias for eps-ladder scans
STEP_95 = 2**61  # legacy complement leg
OFFSET_96 = 2**56 - 1  # 72057594037927935 — anchors .000…0001 to d-band
P_SHIFT = 5_457_912_602  # d_k(P) - d_k(N), constant for all k
ANCHOR_N = N
ANCHOR_P = N + 432_420_386_565_659_900_747_238_600_676_621_316_326
D_BASE = (N + 1) // (2**96)  # floor((N+1)/2^96); equals floor(N/2^96) at this scale
D_LO = 2**159  # puzzle 160: d in [2^159, 2^160)
D_HI = 2**160

P160 = (
    101616124637840542991531253248586524020213215258338643076214814468447630501491,
    88132823371574229813684435207239348220522140366126834573803505878170136640646,
)
G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)

OUT_TXT = Path(__file__).resolve().parent / "puzzle160_epsilon_ladder_report.txt"
OUT_JSON = Path(__file__).resolve().parent / "puzzle160_epsilon_ladder.json"

# Refuse huge brute scans unless explicitly opted in (549B eps grid = days, no hits in 1M probe).
MAX_EPS_SPAN_DEFAULT = 1_000_000
PROGRESS_EVERY_CHUNKS = 20


@dataclass
class Row:
    eps: int
    m: int
    d: int
    rem: int
    d_bits: int
    d_in_p160_band: bool
    exact_div: bool
    d_g_match: bool
    trace_closure: bool
    trace_p160_xy: bool


def step_for_base(base_exp: int) -> int:
    return STEP_96 if base_exp == 96 else STEP_95


def ladder_params(base_exp: int) -> tuple[int, int, int, int]:
    base = 2**base_exp
    step = step_for_base(base_exp)
    m_hi = base * 2 - 1
    max_eps = (m_hi - base) // step + 1
    return base, step, m_hi, max_eps


def m_from_eps(eps: int, base: int, step: int) -> int:
    return base + eps * step


def step_k_to_next(k: int) -> int:
    """Positional ladder: delta d when advancing k → k+1."""
    return STEP_57 if k % 2 == 1 else STEP_56


def d_from_k(k: int, anchor: str = "n") -> int:
    """Partner d for positional label 96.000…000k (k ≥ 1). anchor: 'n' or 'p'."""
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    d = D_BASE - OFFSET_96 - (k // 2) * STEP_57 - ((k - 1) // 2) * STEP_56
    if anchor == "p":
        d += P_SHIFT
    elif anchor != "n":
        raise ValueError(f"anchor must be 'n' or 'p', got {anchor!r}")
    return d


def anchor_for(leg: str) -> int:
    return ANCHOR_N if leg == "n" else ANCHOR_P


def decode_positional_decimal(s: str, anchor: str = "n") -> tuple[int, int, int, int | None]:
    """Parse 96.000…000k → (k, m_fixed, d_pred, step_from_prev).

    Positional d uses alternating 2^57 / 2^56 steps (not uniform 2^57).
    """
    s = s.strip()
    if "." not in s:
        raise ValueError(f"expected 96.000…000k form, got {s!r}")
    whole, frac = s.split(".", 1)
    if int(whole) != 96:
        raise ValueError(f"expected base 96, got {whole!r}")
    k = int(frac)  # trailing digit value: 1, 2, …
    m = 2**96
    d = d_from_k(k, anchor)
    prev_step = step_k_to_next(k - 1) if k > 1 else None
    return k, m, d, prev_step


def format_ladder_row(k: int, leg: str) -> str:
    frac = f"2^96.{frac_label(k)}"
    return f"{frac}  anchor={anchor_for(leg)}  d={d_from_k(k, leg)}"


def frac_label(k: int) -> str:
    return ("0" * 31 + str(k))[-32:]


def check_d_g(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    return scalar_mul(d, G) == P160


def trace_flags(m: int) -> tuple[bool, bool]:
    shell = scalar_mul(m, P160)
    if shell is None:
        return False, False
    tr = trace_mult(NP1, shell)
    ex, ey = tr[-1][3], tr[-1][4]
    sx, sy = shell
    return (sx == ex and sy == ey), (ex == P160[0] and ey == P160[1])


def enrich(eps: int, base: int, step: int, do_trace: bool) -> Row:
    m = m_from_eps(eps, base, step)
    rem = NP1 % m
    d = NP1 // m
    exact = rem == 0
    return Row(
        eps=eps,
        m=m,
        d=d,
        rem=rem,
        d_bits=d.bit_length(),
        d_in_p160_band=D_LO <= d < D_HI,
        exact_div=exact,
        d_g_match=check_d_g(d) if exact else False,
        trace_closure=trace_flags(m)[0] if do_trace else False,
        trace_p160_xy=trace_flags(m)[1] if do_trace else False,
    )


def _divisor_chunk(args: tuple[int, int, int, int]) -> list[tuple[int, int, int]]:
    eps_lo, eps_hi, base, step = args
    hits = []
    for eps in range(eps_lo, eps_hi + 1):
        m = base + eps * step
        if NP1 % m == 0:
            hits.append((eps, m, NP1 // m))
    return hits


def scan_divisors(
    base: int, step: int, eps_lo: int, eps_hi: int, workers: int, chunk: int, progress: bool = True
) -> list[tuple[int, int, int]]:
    jobs = []
    pos = eps_lo
    while pos <= eps_hi:
        end = min(pos + chunk - 1, eps_hi)
        jobs.append((pos, end, base, step))
        pos = end + 1

    raw: list[tuple[int, int, int]] = []
    done = 0
    t0 = time.time()

    def _collect(part: list[tuple[int, int, int]]) -> None:
        nonlocal done
        raw.extend(part)
        done += 1
        if progress and done % PROGRESS_EVERY_CHUNKS == 0:
            pct = 100.0 * done / len(jobs)
            print(f"  divisor scan {done}/{len(jobs)} chunks ({pct:.2f}%)  hits={len(raw)}  {time.time()-t0:.0f}s", flush=True)

    if workers <= 1:
        for job in jobs:
            _collect(_divisor_chunk(job))
    else:
        with Pool(workers) as pool:
            for part in pool.imap_unordered(_divisor_chunk, jobs, chunksize=1):
                _collect(part)
    if progress:
        print(f"  divisor scan done: {len(jobs)} chunks  hits={len(raw)}  {time.time()-t0:.1f}s", flush=True)
    return sorted(raw, key=lambda x: x[0])


def scan_remainder_band(
    base: int, step: int, eps_lo: int, eps_hi: int, max_rem: int, workers: int, chunk: int
) -> list[int]:
    def _chunk(args: tuple[int, int, int, int, int]) -> list[int]:
        lo, hi, b, st, cap = args
        out = []
        for eps in range(lo, hi + 1):
            m = b + eps * st
            if NP1 % m < cap:
                out.append(eps)
        return out

    jobs = []
    pos = eps_lo
    while pos <= eps_hi:
        end = min(pos + chunk - 1, eps_hi)
        jobs.append((pos, end, base, step, max_rem))
        pos = end + 1

    eps_list: list[int] = []
    if workers <= 1:
        for job in jobs:
            eps_list.extend(_chunk(job))
    else:
        with Pool(workers) as pool:
            for part in pool.imap_unordered(_chunk, jobs, chunksize=1):
                eps_list.extend(part)
    return eps_list


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=int, default=96, choices=(95, 96), help="m base: 2^96 (puzzle leg) or 2^95 (legacy)")
    ap.add_argument("--eps-lo", type=int, default=0)
    ap.add_argument("--eps-hi", type=int, default=None)
    ap.add_argument("--divisors-only", action="store_true", help="fast NP1 %% m == 0 scan")
    ap.add_argument("--small-rem", type=int, default=0, help="list ε with remainder < this")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--decode", type=str, default=None, help='positional decimal e.g. 96.0000000000000000000000000000001')
    ap.add_argument("--anchor", choices=("n", "p", "both"), default="n", help="N-anchor or P-anchor for --decode/--ladder")
    ap.add_argument("--ladder", type=int, default=0, metavar="K", help="print positional k=1..K (N and/or P per --anchor)")
    ap.add_argument("--spot", type=int, nargs="*", help="spot-check eps values")
    ap.add_argument("--allow-full-scan", action="store_true", help="allow eps span > 1M (549B-point grid; very slow)")
    ap.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    ap.add_argument("--chunk", type=int, default=500_000)
    args = ap.parse_args()

    base, step, m_hi, max_eps = ladder_params(args.base)
    eps_hi = args.eps_hi if args.eps_hi is not None else min(max_eps - 1, args.eps_lo + MAX_EPS_SPAN_DEFAULT - 1)
    span = eps_hi - args.eps_lo + 1

    if span > MAX_EPS_SPAN_DEFAULT and not args.allow_full_scan:
        print(
            f"Refusing scan: eps span {span:,} exceeds default cap {MAX_EPS_SPAN_DEFAULT:,}.\n"
            f"  Use --eps-hi to set a smaller window, or --allow-full-scan to run the full grid.\n"
            f"  Positional ladder (fast): --ladder 5 --anchor both\n"
            f"  Single decode: --decode 96.000...0001 --anchor both"
        )
        return 2

    lines = [
        f"Puzzle 160 eps-ladder  base=2^{args.base}  step=2^{step.bit_length()-1}={step}",
        f"m band [2^{args.base}, 2^{args.base+1})  eps in [0, {max_eps - 1}]  ({max_eps:,} points)",
        f"d partner target [2^159, 2^160)  NP1 bits={NP1.bit_length()}",
        "",
    ]

    if args.decode:
        legs = ("n", "p") if args.anchor == "both" else (args.anchor,)
        digits = args.decode.replace(".", "")
        lines.append(f"decode {args.decode!r}  len={len(args.decode)}  digits={len(digits)}")
        lines.append(f"  positional steps: odd k→k+1 = 2^57 ({STEP_57}), even = 2^56 ({STEP_56})")
        lines.append(f"  2^57 = 2 * 2^56")
        for leg in legs:
            k, m, d, prev_step = decode_positional_decimal(args.decode, leg)
            r = Row(
                eps=k,
                m=m,
                d=d,
                rem=NP1 % m,
                d_bits=d.bit_length(),
                d_in_p160_band=D_LO <= d < D_HI,
                exact_div=(NP1 % m == 0),
                d_g_match=check_d_g(d),
                trace_closure=trace_flags(m)[0] if args.trace else False,
                trace_p160_xy=trace_flags(m)[1] if args.trace else False,
            )
            leg_label = "N" if leg == "n" else "P"
            lines.append(f"  [{leg_label}] anchor={anchor_for(leg)}")
            lines.append(
                f"  [{leg_label}] k={k}  m=2^96={m}  step_prev={prev_step}  "
                f"d={d} ({r.d_bits}b) rem={r.rem} band={r.d_in_p160_band} "
                f"dG={r.d_g_match} closure={r.trace_closure} Pxy={r.trace_p160_xy}"
            )
            if leg == "p":
                d_n = d_from_k(k, "n")
                lines.append(f"  d(P)-d(N)={d - d_n}  (expect {P_SHIFT})")
        print("\n".join(lines))
        return 0

    if args.ladder > 0:
        legs = ("n", "p") if args.anchor == "both" else (args.anchor,)
        lines.append(f"Positional ladder k=1..{args.ladder}  anchor={args.anchor}")
        lines.append(f"  steps alternate 2^57 / 2^56; P_SHIFT={P_SHIFT}")
        for leg in legs:
            leg_label = "N" if leg == "n" else "P"
            lines.append(f"  --- {leg_label}-anchor ---")
            prev_d = None
            for k in range(1, args.ladder + 1):
                d = d_from_k(k, leg)
                delta = prev_d - d if prev_d is not None else None
                hit = check_d_g(d)
                lines.append(
                    f"  k={k}  {frac_label(k)}  d={d}  delta={delta}  "
                    f"band={D_LO <= d < D_HI}  dG={hit}"
                )
                prev_d = d
        print("\n".join(lines))
        return 0

    if args.spot is not None and len(args.spot) > 0:
        for eps in args.spot:
            r = enrich(eps, base, step, args.trace)
            lines.append(
                f"eps={r.eps} m={r.m} d={r.d} ({r.d_bits}b) rem={r.rem} "
                f"band={r.d_in_p160_band} exact={r.exact_div} dG={r.d_g_match} "
                f"closure={r.trace_closure} Pxy={r.trace_p160_xy}"
            )
        print("\n".join(lines))
        return 0

    t0 = time.time()
    solution = None

    if args.divisors_only:
        lines.append(f"Divisor scan eps=[{args.eps_lo},{eps_hi}] workers={args.workers}")
        divs = scan_divisors(base, step, args.eps_lo, eps_hi, args.workers, args.chunk, progress=True)
        lines.append(f"exact m|(N+1) hits: {len(divs)}  ({time.time()-t0:.1f}s)")
        for eps, m, d in divs[:50]:
            r = enrich(eps, base, step, do_trace=True)
            lines.append(
                f"  eps={eps} m={m} d={d} hex={hex(d)} dG={r.d_g_match} "
                f"closure={r.trace_closure} Pxy={r.trace_p160_xy}"
            )
            if r.d_g_match:
                solution = r
        if not divs:
            lines.append("  (none in range)")

    if args.small_rem > 0:
        lines.append("")
        lines.append(f"Small remainder scan rem < {args.small_rem}")
        t1 = time.time()
        eps_small = scan_remainder_band(
            base, step, args.eps_lo, eps_hi, args.small_rem, args.workers, args.chunk
        )
        lines.append(f"  {len(eps_small):,} eps in {time.time()-t1:.1f}s — showing top 20 by eps")
        shown = []
        for eps in eps_small[:500]:
            r = enrich(eps, base, step, False)
            shown.append((r.rem, r))
        shown.sort(key=lambda x: x[0])
        for _, r in shown[:20]:
            lines.append(f"  eps={r.eps} rem={r.rem} d={r.d} ({r.d_bits}b) band={r.d_in_p160_band}")

    if not args.divisors_only and args.small_rem <= 0:
        # sample head/tail + anchor-nearest on grid
        anchor = 0x1564DE685E4BB400000000000
        near = (anchor - base) // step
        for label, eps in [
            ("eps=0", 0),
            ("eps=1", 1),
            ("eps=2^38", max_eps // 2),
            ("eps=max", max_eps - 1),
            ("anchor floor", max(0, near)),
            ("anchor ceil", min(max_eps - 1, near + 1)),
        ]:
            if args.eps_lo <= eps <= eps_hi:
                r = enrich(eps, base, step, args.trace)
                lines.append(
                    f"{label}: m={r.m} d_bits={r.d_bits} rem={r.rem} "
                    f"band={r.d_in_p160_band} closure={r.trace_closure} Pxy={r.trace_p160_xy}"
                )

    lines.append("")
    if solution:
        lines.append("=== SOLUTION ===")
        lines.append(f"eps={solution.eps} d={solution.d} hex={hex(solution.d)}")
    else:
        lines.append("No d*G == P_160 from this pass.")

    if args.base == 95:
        lines.append("")
        lines.append("Note: --base 95 uses step 2^61; d is ~161-bit. Default --base 96 is puzzle leg.")

    report = "\n".join(lines)
    OUT_TXT.write_text(report, encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"base": args.base, "report": report, "solution": asdict(solution) if solution else None}, indent=2),
        encoding="utf-8",
    )
    print(report)
    print(f"\nWrote {OUT_TXT}")
    return 0 if solution else 1


if __name__ == "__main__":
    raise SystemExit(main())
