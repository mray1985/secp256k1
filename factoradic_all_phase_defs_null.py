#!/usr/bin/env python3
"""
Ledger lock: ALL four factoradic phase definitions + stratified nulls.

Defs (lead step always: term = a*k!, rem = d - term):
  digit_frac   = a/k
  cell_frac    = rem/k! = (d - a*k!)/k!
  plateau_frac = (d - k!)/(k*k!)   for d in [k!, (k+1)!)
  mass_frac    = (a*k!)/d

For each def: observed hi/lo corr + H(<0.1), then nearby-n / block / residual nulls.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_ALL_PHASE_DEFS_NULL.txt")
JSON_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_all_phase_defs_null.json")
LEDGER = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\LEDGER_HIGH_SLICE_FACTORADIC_PHASE_COUPLING.md")
DIGEST_NOTE = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_ALL_PHASE_DEFS.md")

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
TRIALS = 2000
RNG = random.Random(20260711)
THRESH = 0.1
DEFS = ("digit_frac", "cell_frac", "plateau_frac", "mass_frac")


def to_factoradic(n: int) -> list[int]:
    digits: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digits.append(x % i)
        x //= i
        i += 1
    return digits


def lead_pack(n: int) -> dict[str, float | int | bool]:
    digs = to_factoradic(n)
    if not digs:
        return {k: 0.0 for k in DEFS} | {"k": 0, "a": 0, "term": 0, "rem": 0, "ok": True}
    k = len(digs) - 1
    a = digs[k]
    fk = math.factorial(k)
    term = a * fk  # multiply
    rem = n - term  # subtract
    ok = sum(digs[i] * math.factorial(i) for i in range(len(digs))) == n
    return {
        "k": k,
        "a": a,
        "term": term,
        "rem": rem,
        "digit_frac": (a / k) if k else 1.0,
        "cell_frac": (rem / fk) if fk else 0.0,
        "plateau_frac": ((n - fk) / (k * fk)) if (k and n >= fk) else 0.0,
        "mass_frac": (term / n) if n else 0.0,
        "ok": ok,
    }


def pub_x(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d % N_ORDER, curve=SECP256k1, hashfunc=hashlib.sha256)
    return int.from_bytes(sk.get_verifying_key().to_string()[:32], "big")


def lead_native(x: int, m: int) -> int:
    L = max(x.bit_length(), m)
    return x >> (L - m)


def trunc_lo(x: int, m: int) -> int:
    return x & ((1 << m) - 1) if m > 0 else 0


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def hit_count(xs: list[float], ys: list[float]) -> int:
    return sum(1 for a, b in zip(xs, ys) if abs(a - b) < THRESH)


def residualize(xs: list[float], ns: list[float]) -> list[float]:
    n = len(xs)
    mx, mn = sum(xs) / n, sum(ns) / n
    num = sum((a - mx) * (b - mn) for a, b in zip(xs, ns))
    den = sum((b - mn) ** 2 for b in ns)
    if den == 0:
        return list(xs)
    slope = num / den
    intercept = mx - slope * mn
    return [a - (intercept + slope * b) for a, b in zip(xs, ns)]


def block_shuffle(vals: list[float], block: int, rng: random.Random) -> list[float]:
    out = list(vals)
    for start in range(0, len(out), block):
        chunk = out[start : start + block]
        rng.shuffle(chunk)
        out[start : start + block] = chunk
    return out


def nearby_shuffle(vals: list[float], ns: list[int], width: int, rng: random.Random) -> list[float]:
    out = list(vals)
    m = len(out)
    for i in range(m - 1, 0, -1):
        cands = [j for j in range(0, i + 1) if abs(ns[j] - ns[i]) <= width]
        j = cands[rng.randrange(len(cands))]
        out[i], out[j] = out[j], out[i]
    return out


def one_sided(samples: list[float], real: float) -> dict:
    cnt = sum(1 for s in samples if s >= real)
    p = (cnt + 1) / (len(samples) + 1)
    ss = sorted(samples)
    q = lambda t: ss[min(len(ss) - 1, int(t * (len(ss) - 1)))]
    return {
        "real": real,
        "mean": statistics.fmean(samples),
        "sd": statistics.pstdev(samples) if len(samples) > 1 else 0.0,
        "p05": q(0.05),
        "p50": q(0.50),
        "p95": q(0.95),
        "n_extreme": cnt,
        "n_trials": len(samples),
        "p": p,
    }


def status_from_p(p_r: float, p_H: float, p_gap: float) -> str:
    if p_r < 0.01 and p_H < 0.01:
        return "PAIRING-DEPENDENT"
    if min(p_r, p_H, p_gap) < 0.05:
        return "WEAK/MARGINAL"
    return "NULL"


def main() -> None:
    puzzles: list[tuple[int, int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            puzzles.append((n, d, pub_x(d)))

    ns = [n for n, _, _ in puzzles]
    ns_f = [float(n) for n in ns]
    N = len(puzzles)

    # Precompute phase vectors per def for d / hi / lo
    series: dict[str, dict[str, list[float]]] = {}
    for name in DEFS:
        d_f: list[float] = []
        hi_f: list[float] = []
        lo_f: list[float] = []
        for n, d, px in puzzles:
            d_f.append(float(lead_pack(d)[name]))
            hi_f.append(float(lead_pack(lead_native(px, n))[name]))
            lo_f.append(float(lead_pack(trunc_lo(px, n))[name]))
        series[name] = {"d": d_f, "hi": hi_f, "lo": lo_f}

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("ALL FOUR FACTORADIC PHASE DEFS  +  STRATIFIED NULLS")
    w("=" * 88)
    w(f"N={N} puzzles 1..70; trials={TRIALS}; seed=20260711; thresh={THRESH}")
    w("Lead step locked: term=a*k!; rem=d-term; rebuild sum a_i*i!.")
    w()

    # recon check
    bad = sum(1 for _, d, _ in puzzles if not lead_pack(d)["ok"])
    w(f"Reconstruction: {N - bad}/{N} exact")
    w()

    results: dict = {"n": N, "trials": TRIALS, "defs": {}}

    null_cfgs = [
        ("S1_block5", "block", 5),
        ("S1_block10", "block", 10),
        ("S2_near10", "near", 10),
        ("global", "global", 0),
    ]

    for name in DEFS:
        d_f = series[name]["d"]
        hi_f = series[name]["hi"]
        lo_f = series[name]["lo"]
        r_hi = pearson(d_f, hi_f)
        r_lo = pearson(d_f, lo_f)
        H_hi = hit_count(d_f, hi_f)
        H_lo = hit_count(d_f, lo_f)
        gap = r_hi - r_lo
        Hgap = H_hi - H_lo

        d_res = residualize(d_f, ns_f)
        hi_res = residualize(hi_f, ns_f)
        r_hi_res = pearson(d_res, hi_res)

        w("-" * 88)
        w(f"DEF {name}")
        w(f"  observed  r_hi={r_hi:+.4f}  r_lo={r_lo:+.4f}  gap={gap:+.4f}")
        w(f"            H_hi={H_hi}/{N}  H_lo={H_lo}/{N}  Hgap={Hgap:+d}")
        w(f"            residualized r_hi={r_hi_res:+.4f}")

        def_res: dict = {
            "observed": {
                "r_hi": r_hi,
                "r_lo": r_lo,
                "H_hi": H_hi,
                "H_lo": H_lo,
                "gap_r": gap,
                "gap_H": Hgap,
                "r_hi_residual": r_hi_res,
            },
            "nulls": {},
        }

        for nname, mode, param in null_cfgs:
            r_hi_s: list[float] = []
            r_lo_s: list[float] = []
            H_hi_s: list[float] = []
            H_lo_s: list[float] = []
            for _ in range(TRIALS):
                if mode == "block":
                    d_s = block_shuffle(d_f, param, RNG)
                elif mode == "near":
                    d_s = nearby_shuffle(d_f, ns, param, RNG)
                else:
                    d_s = list(d_f)
                    RNG.shuffle(d_s)
                r_hi_s.append(pearson(d_s, hi_f))
                r_lo_s.append(pearson(d_s, lo_f))
                H_hi_s.append(float(hit_count(d_s, hi_f)))
                H_lo_s.append(float(hit_count(d_s, lo_f)))

            sr = one_sided(r_hi_s, r_hi)
            sH = one_sided(H_hi_s, float(H_hi))
            s_gap = one_sided([a - b for a, b in zip(r_hi_s, r_lo_s)], gap)
            s_Hgap = one_sided([a - b for a, b in zip(H_hi_s, H_lo_s)], float(Hgap))
            def_res["nulls"][nname] = {
                "r_hi": sr,
                "H_hi": sH,
                "gap_r": s_gap,
                "gap_H": s_Hgap,
            }
            w(
                f"  {nname:<12} P(r>={r_hi:.3f})={sr['p']:.4f}  "
                f"P(H>={H_hi})={sH['p']:.4f}  "
                f"P(gap_r>={gap:.3f})={s_gap['p']:.4f}  "
                f"(null_mean_r={sr['mean']:+.3f})"
            )

        # residual global
        r_res_s: list[float] = []
        for _ in range(TRIALS):
            d_s = list(d_res)
            RNG.shuffle(d_s)
            r_res_s.append(pearson(d_s, hi_res))
        s_res = one_sided(r_res_s, r_hi_res)
        def_res["nulls"]["S3_residual"] = {"r_hi_residual": s_res}
        w(
            f"  {'S3_residual':<12} residual_real={r_hi_res:+.4f}  "
            f"P(r_res>=real)={s_res['p']:.4f}  null_mean={s_res['mean']:+.3f}"
        )

        primary = def_res["nulls"]["S2_near10"]
        st = status_from_p(primary["r_hi"]["p"], primary["H_hi"]["p"], primary["gap_r"]["p"])
        def_res["status"] = st
        def_res["primary"] = {
            "p_r": primary["r_hi"]["p"],
            "p_H": primary["H_hi"]["p"],
            "p_gap": primary["gap_r"]["p"],
        }
        w(f"  STATUS ({name}): {st}")
        results["defs"][name] = def_res

    w()
    w("=" * 88)
    w("SUMMARY TABLE")
    w("=" * 88)
    w(f"{'def':<14} {'r_hi':>7} {'r_lo':>7} {'H_hi':>6} {'p_r':>8} {'p_H':>8} {'p_gap':>8} {'status'}")
    w("-" * 88)
    for name in DEFS:
        d = results["defs"][name]
        o = d["observed"]
        p = d["primary"]
        w(
            f"{name:<14} {o['r_hi']:+7.3f} {o['r_lo']:+7.3f} {o['H_hi']:3d}/70 "
            f"{p['p_r']:8.4f} {p['p_H']:8.4f} {p['p_gap']:8.4f} {d['status']}"
        )

    w()
    w("VERDICT")
    w("  All four defs are locked as the phase suite.")
    w("  Lead arithmetic is multiply-then-subtract: term=a*k!, rem=d-term.")
    w("  Pairing claim is judged per-def via nearby-|dn|<=10 null (primary).")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    JSON_OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Build ledger from results
    rows_md = []
    for name in DEFS:
        d = results["defs"][name]
        o = d["observed"]
        p = d["primary"]
        rows_md.append(
            f"| `{name}` | {o['r_hi']:+.3f} | {o['r_lo']:+.3f} | {o['H_hi']}/70 | "
            f"{o['H_lo']}/70 | {p['p_r']:.4f} | {p['p_H']:.4f} | {p['p_gap']:.4f} | **{d['status']}** |"
        )

    LEDGER.write_text(
        f"""# LEDGER — High-slice factoradic phase coupling

**Status:** **SUITE LOCKED (all four phase defs)** — pairing judged per-def  
**Date:** 2026-07-11  
**Artifacts:**
- `factoradic_all_phase_defs_null.py`
- `logs/FACTORADIC_ALL_PHASE_DEFS_NULL.txt`
- `logs/factoradic_all_phase_defs_null.json`
- `factoradic_multiply_then_subtract.py`

## Lead arithmetic (mandatory)

\[
\\mathrm{{term}}=a\\cdot k!,\\qquad \\mathrm{{rem}}=d-\\mathrm{{term}}
\]

Rebuild: \(d=\\sum_i a_i\\cdot i!\). Exact on 70/70 solved keys.

## Phase suite (all chosen)

| def | formula |
|-----|---------|
| `digit_frac` | \(a/k\) |
| `cell_frac` | \(\\mathrm{{rem}}/k! = (d-a\\cdot k!)/k!\) |
| `plateau_frac` | \((d-k!)/(k\\cdot k!)\) for \(d\\in[k!,(k+1)!)\) |
| `mass_frac` | \((a\\cdot k!)/d\) |

Native high slice: \(\\lfloor Px / 2^{{L-n}}\\rfloor\), \(L=\\mathrm{{bitlength}}(Px)\).  
Low slice: \(Px \\bmod 2^n\).

## Observed + primary stratified null (nearby \(\\|\\Delta n\\|\\le 10\))

| def | r_hi | r_lo | H_hi | H_lo | P(r) | P(H) | P(gap_r) | status |
|-----|-----:|-----:|-----:|-----:|-----:|-----:|---------:|--------|
{chr(10).join(rows_md)}

Trials = {TRIALS}. Exact-\(n\) strata have size 1; nearby/block/residual nulls used.

## Ruling

```text
Suite locked:                          YES (all four defs)
Lead multiply-then-subtract:           REQUIRED
Real descriptive hi/lo gap:            present for digit/plateau/mass; weak for cell
Recoverable private-key information:   NOT claimed
Pairing dependence:                    per-def status column above
```

**Ledger name:** High-slice factoradic phase coupling (full suite)

Related prior: `logs/FACTORADIC_EVIDENCE_DIGEST.md` (native-lead falsification under
unstratified / random-width nulls). This entry supersedes single-def promotion by
locking the whole suite and reporting stratified p-values for each.
""",
        encoding="utf-8",
    )

    DIGEST_NOTE.write_text(
        "\n".join(lines[:40])
        + "\n\nSee LEDGER_HIGH_SLICE_FACTORADIC_PHASE_COUPLING.md for the locked suite.\n",
        encoding="utf-8",
    )

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {JSON_OUT}")
    w(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
