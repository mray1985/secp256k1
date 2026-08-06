#!/usr/bin/env python3
"""
Lead-window sweep: corr(d_frac, Px_lead(m)_frac) over many definitions of "lead".

Px_lead(m) = floor(Px / 2^(L-m))  where L = bit_length(Px) (or 256 if preferred)
We use L = max(Px.bit_length(), m) so top-m bits are well-defined.

Sweeps:
  1) fixed m in {8,16,24,32,40,48,56,64,72,80,96,112,128,160,192,224,256}
  2) offset: m = n - c for c = 0..20
  3) proportional: m = floor(alpha * n) for alpha in {0.25,0.5,0.75,1.0}
     also m = 8..n for each puzzle then aggregate (per-m across puzzles with n>=m)

Outputs per window: r, frac_close(|dF-pF|<0.1), MAE, permutation p
"""
from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_LEAD_WINDOW_SWEEP.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_lead_window_sweep.csv")
RIDGE_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_lead_window_ridge.csv")

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PERM_TRIALS = 500
RNG = random.Random(13570)


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
    sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1, hashfunc=hashlib.sha256)
    return int.from_bytes(sk.get_verifying_key().to_string()[:32], "big")


def px_lead(px: int, m: int, width: int = 256) -> int:
    """Top m bits of a width-bit view of px (zero-padded on the left if needed)."""
    if m <= 0:
        return 0
    if m >= width:
        return px & ((1 << width) - 1) if px.bit_length() > width else px
    # interpret px as width-bit integer
    return px >> (width - m)


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def mae(xs: list[float], ys: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(xs, ys)) / len(xs)


def close_rate(xs: list[float], ys: list[float], tol: float = 0.1) -> float:
    return sum(1 for a, b in zip(xs, ys) if abs(a - b) < tol) / len(xs)


def perm_p(xs: list[float], ys: list[float], observed: float, trials: int = PERM_TRIALS) -> float:
    """Two-sided permutation p for |r| under shuffling ys."""
    if len(xs) < 3:
        return 1.0
    count = 0
    y = list(ys)
    thr = abs(observed)
    for _ in range(trials):
        RNG.shuffle(y)
        if abs(pearson(xs, y)) >= thr:
            count += 1
    return (count + 1) / (trials + 1)


@dataclass
class SweepRow:
    family: str
    param: str
    n_used: int
    r: float
    close01: float
    mae: float
    p_perm: float


def metrics(d_fracs: list[float], p_fracs: list[float]) -> tuple[float, float, float, float]:
    r = pearson(d_fracs, p_fracs)
    return r, close_rate(d_fracs, p_fracs), mae(d_fracs, p_fracs), perm_p(d_fracs, p_fracs, r)


def main() -> None:
    puzzles: list[tuple[int, int, int, float]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            px = pub_x(d)
            puzzles.append((n, d, px, lead_frac(d)))

    results: list[SweepRow] = []
    ridge_rows: list[dict] = []

    # --- Family 1: fixed m ---
    fixed_ms = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 96, 112, 128, 160, 192, 224, 256]
    print("Family 1: fixed m ...")
    for m in fixed_ms:
        # only puzzles with n >= something? For fixed m, use all puzzles;
        # lead of Px is independent of n, but d_frac depends on full d.
        dF = [df for _, _, _, df in puzzles]
        pF = [lead_frac(px_lead(px, m)) for _, _, px, _ in puzzles]
        r, c01, merr, pv = metrics(dF, pF)
        results.append(SweepRow("fixed", f"m={m}", len(puzzles), r, c01, merr, pv))

    # --- Family 2: offset m = n - c ---
    print("Family 2: m = n - c ...")
    for c in range(0, 21):
        dF, pF = [], []
        for n, d, px, df in puzzles:
            m = n - c
            if m < 8:
                continue
            dF.append(df)
            pF.append(lead_frac(px_lead(px, m)))
        if len(dF) < 10:
            continue
        r, c01, merr, pv = metrics(dF, pF)
        results.append(SweepRow("offset", f"c={c} (m=n-c)", len(dF), r, c01, merr, pv))

    # --- Family 3: proportional m = floor(alpha * n) ---
    print("Family 3: m = floor(alpha*n) ...")
    for alpha in (0.25, 0.35, 0.5, 0.6, 0.75, 0.85, 1.0):
        dF, pF = [], []
        for n, d, px, df in puzzles:
            m = max(8, int(alpha * n))
            if m > 256:
                m = 256
            dF.append(df)
            pF.append(lead_frac(px_lead(px, m)))
        r, c01, merr, pv = metrics(dF, pF)
        results.append(
            SweepRow("proportional", f"alpha={alpha}", len(dF), r, c01, merr, pv)
        )

    # --- Family 4: dense ridge for m = 8..70 using puzzles with n >= m ---
    # For each fixed m, restrict to puzzles n>=m (so m is a meaningful "lead width"
    # relative to puzzle size for offset-like interpretation), AND also all-n version.
    print("Family 4: dense m ridge (n>=m subset) ...")
    for m in range(8, 71):
        dF, pF = [], []
        for n, d, px, df in puzzles:
            if n < m:
                continue
            dF.append(df)
            pF.append(lead_frac(px_lead(px, m)))
        if len(dF) < 10:
            continue
        r, c01, merr, pv = metrics(dF, pF)
        results.append(SweepRow("ridge_n_ge_m", f"m={m}", len(dF), r, c01, merr, pv))
        ridge_rows.append(
            {
                "m": m,
                "n_used": len(dF),
                "r": f"{r:.6f}",
                "close01": f"{c01:.4f}",
                "mae": f"{merr:.6f}",
                "p_perm": f"{pv:.4f}",
            }
        )

    # --- Family 5: dense m on ALL puzzles (fixed lead, ignore n) ---
    print("Family 5: dense m all puzzles ...")
    for m in list(range(8, 129, 2)) + [160, 192, 224, 256]:
        dF = [df for _, _, _, df in puzzles]
        pF = [lead_frac(px_lead(px, m)) for _, _, px, _ in puzzles]
        r, c01, merr, pv = metrics(dF, pF)
        results.append(SweepRow("ridge_all", f"m={m}", len(dF), r, c01, merr, pv))

    # Hold-out: train on 1..50, test 51..70 for best candidates
    print("Hold-out check on top candidates ...")
    train = [(n, d, px, df) for n, d, px, df in puzzles if n <= 50]
    test = [(n, d, px, df) for n, d, px, df in puzzles if n >= 51]

    def eval_window(family_param_m: int, subset: list) -> tuple[float, float, float]:
        dF = [df for _, _, _, df in subset]
        pF = [lead_frac(px_lead(px, family_param_m)) for _, _, px, _ in subset]
        r = pearson(dF, pF)
        return r, close_rate(dF, pF), mae(dF, pF)

    # Report
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("LEAD WINDOW SWEEP — corr(d_frac, Px_lead(m)_frac)")
    w("=" * 88)
    w(f"Puzzles 1-70 | permutation trials={PERM_TRIALS} | width view=256 bits")
    w()

    def show_family(name: str) -> None:
        sub = [r for r in results if r.family == name]
        if not sub:
            return
        w("-" * 88)
        w(f"FAMILY: {name}")
        w(f"{'param':<22} {'N':>4} {'r':>8} {'close01':>8} {'MAE':>8} {'p_perm':>8}")
        w("-" * 88)
        for r in sub:
            w(
                f"{r.param:<22} {r.n_used:4d} {r.r:+8.3f} {r.close01:8.3f} "
                f"{r.mae:8.4f} {r.p_perm:8.4f}"
            )
        w()

    for fam in ("fixed", "offset", "proportional", "ridge_n_ge_m", "ridge_all"):
        show_family(fam)

    # Best overall by |r|, then stability note from ridge
    ranked = sorted(results, key=lambda r: abs(r.r), reverse=True)
    w("=" * 88)
    w("TOP 15 BY |r|")
    w("=" * 88)
    for r in ranked[:15]:
        w(
            f"  {r.family:<14} {r.param:<22} r={r.r:+.3f}  close={r.close01:.3f}  "
            f"MAE={r.mae:.4f}  p={r.p_perm:.4f}  N={r.n_used}"
        )

    # Stability ridge: look at ridge_n_ge_m neighbors
    w()
    w("=" * 88)
    w("RIDGE STABILITY (ridge_n_ge_m): local |r| neighborhood")
    w("=" * 88)
    ridge = [r for r in results if r.family == "ridge_n_ge_m"]
    ridge_by_m = {int(r.param.split("=")[1]): r for r in ridge}
    # find peaks
    peaks = []
    for m, r in ridge_by_m.items():
        neighbors = [ridge_by_m[m + dm].r for dm in (-2, -1, 1, 2) if m + dm in ridge_by_m]
        if not neighbors:
            continue
        if abs(r.r) >= max(abs(x) for x in neighbors):
            peaks.append((m, r))
    w("Local |r| peaks (vs +/-2 neighbors):")
    for m, r in peaks:
        neigh = " ".join(
            f"{m+dm}:{ridge_by_m[m+dm].r:+.3f}"
            for dm in range(-2, 3)
            if m + dm in ridge_by_m
        )
        w(f"  m={m}: r={r.r:+.3f}  close={r.close01:.3f}  p={r.p_perm:.4f}  | {neigh}")

    # Hold-out for best fixed / best offset / best proportional / m=n
    w()
    w("=" * 88)
    w("HOLD-OUT (train n=1..50, test n=51..70)")
    w("=" * 88)
    candidates = [
        ("m=n (c=0)", 0, "offset"),
        ("m=64 fixed", 64, "fixed"),
        ("m=48 fixed", 48, "fixed"),
        ("m=32 fixed", 32, "fixed"),
        ("m=80 fixed", 80, "fixed"),
        ("m=96 fixed", 96, "fixed"),
    ]
    # pick best ridge m
    if ridge:
        best_ridge = max(ridge, key=lambda r: abs(r.r))
        bm = int(best_ridge.param.split("=")[1])
        candidates.append((f"best_ridge m={bm}", bm, "ridge"))

    for label, m, kind in candidates:
        if kind == "offset":
            # c=0 => m=n per puzzle
            def fracs(subset, c=m):
                dF, pF = [], []
                for n, d, px, df in subset:
                    mm = n - c
                    if mm < 8:
                        continue
                    dF.append(df)
                    pF.append(lead_frac(px_lead(px, mm)))
                return dF, pF

            dF_tr, pF_tr = fracs(train)
            dF_te, pF_te = fracs(test)
        else:
            dF_tr = [df for _, _, _, df in train]
            pF_tr = [lead_frac(px_lead(px, m)) for _, _, px, _ in train]
            dF_te = [df for _, _, _, df in test]
            pF_te = [lead_frac(px_lead(px, m)) for _, _, px, _ in test]
        if len(dF_tr) < 10 or len(dF_te) < 5:
            w(f"  {label}: insufficient samples")
            continue
        r_tr = pearson(dF_tr, pF_tr)
        r_te = pearson(dF_te, pF_te)
        c_te = close_rate(dF_te, pF_te)
        w(f"  {label:<22} train_r={r_tr:+.3f}  test_r={r_te:+.3f}  test_close={c_te:.3f}")

    w()
    w("=" * 88)
    w("GO-TO CRITERIA")
    w("=" * 88)
    # score: high |r|, low p, and for ridge check neighbor mean |r|
    go = []
    for r in results:
        if r.p_perm > 0.05:
            continue
        if abs(r.r) < 0.4:
            continue
        stable = True
        if r.family == "ridge_n_ge_m":
            m = int(r.param.split("=")[1])
            neigh = [
                abs(ridge_by_m[m + dm].r)
                for dm in (-1, 1)
                if m + dm in ridge_by_m
            ]
            if neigh and abs(r.r) - sum(neigh) / len(neigh) > 0.15:
                stable = False  # spike vs neighbors
        go.append((r, stable))

    w("Candidates with |r|>=0.4 and p_perm<=0.05:")
    for r, stable in sorted(go, key=lambda t: abs(t[0].r), reverse=True)[:20]:
        tag = "STABLE" if stable else "SPIKE?"
        w(
            f"  [{tag}] {r.family} {r.param}: r={r.r:+.3f} close={r.close01:.3f} "
            f"MAE={r.mae:.4f} p={r.p_perm:.4f}"
        )

    w()
    w("Interpretation:")
    w("  - A STABLE ridge = neighboring m keep similar r (relation survives redefinition).")
    w("  - A SPIKE = isolated max; treat as selection noise until hold-out agrees.")
    w("  - m=n (c=0) is one point on this surface; sweep finds if better windows exist.")

    # write CSVs
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = ["family", "param", "n_used", "r", "close01", "mae", "p_perm"]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in results:
            wr.writerow(
                {
                    "family": r.family,
                    "param": r.param,
                    "n_used": r.n_used,
                    "r": f"{r.r:.6f}",
                    "close01": f"{r.close01:.6f}",
                    "mae": f"{r.mae:.6f}",
                    "p_perm": f"{r.p_perm:.6f}",
                }
            )
    with RIDGE_OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(
            f, fieldnames=["m", "n_used", "r", "close01", "mae", "p_perm"]
        )
        wr.writeheader()
        wr.writerows(ridge_rows)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")
    w(f"Wrote {RIDGE_OUT}")


if __name__ == "__main__":
    main()
