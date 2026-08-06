#!/usr/bin/env python3
"""
Within-n stratified permutation null for high-slice factoradic phase coupling.

Claim under test:
  factoradic lead fraction(d) partially tracks
  factoradic lead fraction(floor(Px / 2^(L-n)))

Decisive nulls (preserve bit-width / factorial height / sample composition;
destroy pairing):
  S1  block shuffle of d within consecutive n-blocks of size B
  S2  nearby-n restricted shuffle (|n_i - n_j| <= W)
  S3  residualized: remove linear n trend, then global shuffle of d residuals
  S4  same as S1/S2 but for LOW slice (contrast)

Reports one-sided:
  P(r_null >= r_obs) and P(H_null >= H_obs)
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import statistics
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_HIGH_SLICE_STRATIFIED_NULL.txt")
JSON_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_high_slice_stratified_null.json")
LEDGER = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\LEDGER_HIGH_SLICE_FACTORADIC_PHASE_COUPLING.md")

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
TRIALS = 5000
RNG = random.Random(20260711)
THRESH = 0.1


def to_factoradic(n: int) -> list[int]:
    n = abs(int(n))
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def lead_frac(n: int) -> float:
    digs = to_factoradic(n)
    if not digs:
        return 0.0
    mk = len(digs) - 1
    a = digs[mk]
    return a / mk if mk else 1.0


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


def hit_count(xs: list[float], ys: list[float], thr: float = THRESH) -> int:
    return sum(1 for a, b in zip(xs, ys) if abs(a - b) < thr)


def residualize(xs: list[float], ns: list[float]) -> list[float]:
    n = len(xs)
    mx = sum(xs) / n
    mn = sum(ns) / n
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
    """Restricted Fisher-Yates: swap i only with j where |n_i - n_j| <= width."""
    out = list(vals)
    m = len(out)
    for i in range(m - 1, 0, -1):
        candidates = [j for j in range(0, i + 1) if abs(ns[j] - ns[i]) <= width]
        j = candidates[rng.randrange(len(candidates))]
        out[i], out[j] = out[j], out[i]
    return out


def one_sided(samples: list[float], real: float, ge: bool = True) -> dict:
    if ge:
        cnt = sum(1 for s in samples if s >= real)
    else:
        cnt = sum(1 for s in samples if s <= real)
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
    d_fracs = [lead_frac(d) for _, d, _ in puzzles]
    px_hi_fracs = [lead_frac(lead_native(px, n)) for n, _, px in puzzles]
    px_lo_fracs = [lead_frac(trunc_lo(px, n)) for n, _, px in puzzles]

    r_hi = pearson(d_fracs, px_hi_fracs)
    r_lo = pearson(d_fracs, px_lo_fracs)
    H_hi = hit_count(d_fracs, px_hi_fracs)
    H_lo = hit_count(d_fracs, px_lo_fracs)

    d_res = residualize(d_fracs, ns_f)
    hi_res = residualize(px_hi_fracs, ns_f)
    lo_res = residualize(px_lo_fracs, ns_f)
    r_hi_res = pearson(d_res, hi_res)
    r_lo_res = pearson(d_res, lo_res)

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("STRATIFIED WITHIN-n PERMUTATION NULL")
    w("High-slice factoradic phase coupling")
    w("=" * 88)
    w(f"N puzzles = {len(puzzles)} (1..70); each n unique => exact-n strata size 1")
    w(f"Trials = {TRIALS}; seed = 20260711; close threshold = {THRESH}")
    w()
    w("OBSERVED (true pairing)")
    w(f"  corr(d_frac, Px_hi_frac) = {r_hi:+.6f}")
    w(f"  corr(d_frac, Px_lo_frac) = {r_lo:+.6f}")
    w(f"  H_hi = |d_frac - Px_hi_frac| < {THRESH}: {H_hi}/{len(puzzles)} ({H_hi/len(puzzles):.4f})")
    w(f"  H_lo = |d_frac - Px_lo_frac| < {THRESH}: {H_lo}/{len(puzzles)} ({H_lo/len(puzzles):.4f})")
    w(f"  residualized corr hi = {r_hi_res:+.6f}")
    w(f"  residualized corr lo = {r_lo_res:+.6f}")
    w()

    results: dict = {
        "n": len(puzzles),
        "observed": {
            "r_hi": r_hi,
            "r_lo": r_lo,
            "H_hi": H_hi,
            "H_lo": H_lo,
            "r_hi_residual": r_hi_res,
            "r_lo_residual": r_lo_res,
        },
        "nulls": {},
    }

    configs = [
        ("S1_block5", "block", 5),
        ("S1_block10", "block", 10),
        ("S2_near5", "near", 5),
        ("S2_near10", "near", 10),
        ("S2_near15", "near", 15),
        ("global", "global", 0),
    ]

    for name, mode, param in configs:
        r_hi_s: list[float] = []
        r_lo_s: list[float] = []
        H_hi_s: list[int] = []
        H_lo_s: list[int] = []
        for _ in range(TRIALS):
            if mode == "block":
                d_s = block_shuffle(d_fracs, param, RNG)
            elif mode == "near":
                d_s = nearby_shuffle(d_fracs, ns, param, RNG)
            else:
                d_s = list(d_fracs)
                RNG.shuffle(d_s)
            r_hi_s.append(pearson(d_s, px_hi_fracs))
            r_lo_s.append(pearson(d_s, px_lo_fracs))
            H_hi_s.append(hit_count(d_s, px_hi_fracs))
            H_lo_s.append(hit_count(d_s, px_lo_fracs))

        sr = one_sided(r_hi_s, r_hi, ge=True)
        sH = one_sided([float(x) for x in H_hi_s], float(H_hi), ge=True)
        sr_lo = one_sided(r_lo_s, r_lo, ge=True)
        sH_lo = one_sided([float(x) for x in H_lo_s], float(H_lo), ge=True)
        # also: how often null hi exceeds null lo by the observed gap
        gap_obs = r_hi - r_lo
        gap_s = [a - b for a, b in zip(r_hi_s, r_lo_s)]
        s_gap = one_sided(gap_s, gap_obs, ge=True)
        Hgap_obs = H_hi - H_lo
        Hgap_s = [a - b for a, b in zip(H_hi_s, H_lo_s)]
        s_Hgap = one_sided([float(x) for x in Hgap_s], float(Hgap_obs), ge=True)

        results["nulls"][name] = {
            "mode": mode,
            "param": param,
            "r_hi": sr,
            "H_hi": sH,
            "r_lo": sr_lo,
            "H_lo": sH_lo,
            "gap_r": s_gap,
            "gap_H": s_Hgap,
        }

        w("-" * 88)
        w(f"NULL {name}  ({mode}, param={param})")
        w(
            f"  r_hi: mean={sr['mean']:+.4f}  p95={sr['p95']:+.4f}  "
            f"P(r>={r_hi:.3f})={sr['p']:.4f}  ({sr['n_extreme']}/{sr['n_trials']})"
        )
        w(
            f"  H_hi: mean={sH['mean']:.2f}  p95={sH['p95']:.1f}  "
            f"P(H>={H_hi})={sH['p']:.4f}  ({sH['n_extreme']}/{sH['n_trials']})"
        )
        w(
            f"  r_lo: mean={sr_lo['mean']:+.4f}  P(r>={r_lo:.3f})={sr_lo['p']:.4f}"
        )
        w(
            f"  gap r_hi-r_lo: obs={gap_obs:+.4f}  null_mean={s_gap['mean']:+.4f}  "
            f"P(gap>=obs)={s_gap['p']:.4f}"
        )
        w(
            f"  gap H_hi-H_lo: obs={Hgap_obs:+d}  null_mean={s_Hgap['mean']:+.2f}  "
            f"P(gap>=obs)={s_Hgap['p']:.4f}"
        )

    # residualized shuffle (destroy pairing after n-trend removed)
    w()
    w("-" * 88)
    w("NULL S3_residual_global  (OLS-remove n from both, then shuffle d residuals)")
    r_res_s: list[float] = []
    for _ in range(TRIALS):
        d_s = list(d_res)
        RNG.shuffle(d_s)
        r_res_s.append(pearson(d_s, hi_res))
    s_res = one_sided(r_res_s, r_hi_res, ge=True)
    results["nulls"]["S3_residual_global"] = {"r_hi_residual": s_res}
    w(f"  residual real r_hi = {r_hi_res:+.6f}")
    w(
        f"  null mean={s_res['mean']:+.4f}  p95={s_res['p95']:+.4f}  "
        f"P(r_res>={r_hi_res:.3f})={s_res['p']:.4f}  ({s_res['n_extreme']}/{s_res['n_trials']})"
    )

    # primary decisive numbers (prefer nearby-10 as user "nearby n")
    primary = results["nulls"]["S2_near10"]
    p_r = primary["r_hi"]["p"]
    p_H = primary["H_hi"]["p"]
    p_gap = primary["gap_r"]["p"]

    w()
    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w(f"  Primary null (nearby |dn|<=10):")
    w(f"    P(r_null >= {r_hi:.3f}) = {p_r:.4f}")
    w(f"    P(H_null >= {H_hi})     = {p_H:.4f}")
    w(f"    P(gap_r  >= {r_hi-r_lo:.3f}) = {p_gap:.4f}")
    if p_r < 0.01 and p_H < 0.01:
        verdict = "PAIRING-DEPENDENT SIGNAL"
        detail = "Stratified nulls reject chance; promote as tested coupling (still not an inversion)."
    elif p_r < 0.05 or p_H < 0.05 or p_gap < 0.05:
        verdict = "WEAK / MARGINAL"
        detail = "Some stratified tests borderline; do not treat as recoverable private-key info."
    else:
        verdict = "NULL under stratified pairing destruction"
        detail = (
            "Observed hi>lo asymmetry is real descriptively, but does not survive "
            "within-n / nearby-n / residualized permutation. Not pairing evidence."
        )
    w(f"  STATUS: {verdict}")
    w(f"  {detail}")

    results["verdict"] = verdict
    results["primary_null"] = "S2_near10"
    results["primary_p"] = {"r": p_r, "H": p_H, "gap_r": p_gap}

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    JSON_OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Ledger entry
    LEDGER.write_text(
        f"""# LEDGER — High-slice factoradic phase coupling

**Status:** **{verdict}**

**Date:** 2026-07-11  
**Artifacts:** `factoradic_high_slice_stratified_null.py`,  
`logs/FACTORADIC_HIGH_SLICE_STRATIFIED_NULL.txt`,  
`logs/factoradic_high_slice_stratified_null.json`  
**Related:** `factoradic_trunc_pub_priv.py`, `factoradic_native_lead_null.py`,  
`logs/FACTORADIC_EVIDENCE_DIGEST.md`

## Compact claim

\[
\text{{factoradic lead fraction}}(d)
\quad\\text{{partially tracks}}\\quad
\text{{factoradic lead fraction}}\\!\\left(\\left\\lfloor Px/2^{{L-n}}\\right\\rfloor\\right).
\]

Native high slice: \(L=\\mathrm{{bitlength}}(Px)\), retain exactly \(n\) leading bits.

## Observed (puzzles 1–70, true pairing)

| metric | high slice | low slice |
|--------|----------:|----------:|
| \(r = \\mathrm{{corr}}(d_\\mathrm{{frac}}, \\cdot)\) | **{r_hi:+.3f}** | {r_lo:+.3f} |
| \(H = \\#\\|\\Delta\\mathrm{{frac}}\\|<0.1\) | **{H_hi}/70** ({H_hi/70:.1%}) | {H_lo}/70 ({H_lo/70:.1%}) |
| residualized \(r\) (linear \(n\) removed) | {r_hi_res:+.3f} | {r_lo_res:+.3f} |

Bit-width alone cannot explain the hi/lo gap: both slices have width \(n\).

## Why `max_k` alignment is bookkeeping

\(d\), \(Px_\\mathrm{{hi}}\), \(Px_\\mathrm{{lo}}\) all live in \([0,2^n)\), so they share the same
largest factorial index. That is **not** elliptic-curve leakage.

## Decisive null: stratified within-\(n\) permutation

Exact-\(n\) strata have size 1 (one puzzle per height). Nulls therefore use
**nearby-\(n\)** / **block** stratification, plus residualized global shuffle.

Primary null: shuffle \(d_\\mathrm{{frac}}\) among puzzles with \(|n_i-n_j|\\le 10\),
keeping each puzzle's \((n, Px_\\mathrm{{hi/lo}})\) fixed.

| test | \(P\) (one-sided) |
|------|------------------:|
| \(P(r_\\mathrm{{null}}\\ge {r_hi:.3f})\) | **{p_r:.4f}** |
| \(P(H_\\mathrm{{null}}\\ge {H_hi})\) | **{p_H:.4f}** |
| \(P((r_\\mathrm{{hi}}-r_\\mathrm{{lo}})_\\mathrm{{null}}\\ge {r_hi-r_lo:.3f})\) | **{p_gap:.4f}** |

Full table (all strata / residual): see `FACTORADIC_HIGH_SLICE_STRATIFIED_NULL.txt`.

## Ruling

```text
Real observed coupling (hi vs lo descriptive gap): YES
Explained by common width alone:                  NO (gap exists)
Survives stratified pairing destruction:          {"YES" if p_r < 0.01 and p_H < 0.01 else "NO"}
Evidence of recoverable private-key information:  NOT YET / NO
```

**Ledger name:** High-slice factoradic phase coupling

**Promotion posture:** tested **partial descriptive invariant** of the solved cohort
under the native \(m=n\) lead definition — **not** an inversion formula, and
**{"pairing-dependent under nearby-n null" if p_r < 0.01 else "not pairing-dependent under nearby-n null"}**.

Prior unstratified / random-width nulls in `FACTORADIC_EVIDENCE_DIGEST.md`
already showed mean \(r\\sim 0.48\)–\(0.53\) with \(p\\approx 0.14\)–\(0.24\). This entry
adds the stratified test the digest warned was required.
""",
        encoding="utf-8",
    )

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {JSON_OUT}")
    w(f"Wrote {LEDGER}")


if __name__ == "__main__":
    main()
