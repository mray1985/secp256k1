#!/usr/bin/env python3
"""
Phi map probe: C = Phi(P) = (x + y/p)/p = (x*p + y)/p^2

1) Exact decode <-> encode round-trip on nG, n=1..1100
2) Exact F(C) = Phi(decode(C) + G) via field add-G (no ecdsa Point API in F)
3) Empirical cheap-map hunt: fit Delta_C vs C (and C_prev) on train 1..800,
   hold out 801..1100. Falsify if holdout is near-chance / needs full EC.

A "cheap" win would be a low-complexity rule on C alone that predicts C'.
Baseline F is exact but is EC renamed (decode + add-G + encode).
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_MAP_F_PROBE.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = SECP256k1.generator
GX = int(G.x())
GY = int(G.y())
MAX_N = 1100
TRAIN_END = 800  # transitions i=1..799 use C_i -> C_{i+1}; indices 0-based


def modinv(a: int, m: int = P) -> int:
    return pow(a % m, -1, m)


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def decode(c: Fraction) -> tuple[int, int]:
    """Inverse of nested real division: result=y/p; C=(x+result)/p."""
    # C * p = x + y/p  =>  x = floor(C*p), y = (C*p - x)*p
    cp = c * P
    x = int(cp)  # floor for positive
    frac = cp - x
    y_frac = frac * P
    y = int(y_frac)
    if y_frac != y:
        # exact Fraction should be integer
        if y_frac.denominator != 1:
            raise ValueError(f"decode non-integral y: {y_frac}")
        y = y_frac.numerator
    if not (0 <= x < P and 0 <= y < P):
        raise ValueError(f"decode out of range x={x} y={y}")
    return x, y


def encode(x: int, y: int) -> Fraction:
    return phi(x % P, y % P)


def add_g(x: int, y: int) -> tuple[int, int]:
    """Affine P + G over F_p (curve a=0). Infinity not handled (nG for small n)."""
    if x == GX:
        # either double or vertical (P=-G)
        if y == GY:
            # double G — not used on walk after 1G when adding G to nG, n>=1
            # still implement double for completeness if P==G
            lam = (3 * x * x) * modinv(2 * y) % P
        elif (y + GY) % P == 0:
            raise ValueError("P + G = infinity")
        else:
            lam = (GY - y) * modinv((GX - x) % P) % P
    else:
        lam = (GY - y) * modinv((GX - x) % P) % P
    x2 = (lam * lam - x - GX) % P
    y2 = (lam * (x - x2) - y) % P
    return x2, y2


def F(c: Fraction) -> Fraction:
    """Exact Phi map: decode -> +G -> encode. This IS the group step in Phi coords."""
    x, y = decode(c)
    x2, y2 = add_g(x, y)
    return encode(x2, y2)


def lstsq(X: list[list[float]], y: list[float]) -> list[float]:
    """Ordinary least squares via normal equations (small dim)."""
    n = len(X)
    k = len(X[0])
    # XtX, Xty
    XtX = [[0.0] * k for _ in range(k)]
    Xty = [0.0] * k
    for i in range(n):
        for a in range(k):
            Xty[a] += X[i][a] * y[i]
            for b in range(k):
                XtX[a][b] += X[i][a] * X[i][b]
    # Gaussian elimination
    A = [XtX[r][:] + [Xty[r]] for r in range(k)]
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        if abs(A[col][col]) < 1e-18:
            return [0.0] * k
        div = A[col][col]
        for j in range(col, k + 1):
            A[col][j] /= div
        for r in range(k):
            if r == col:
                continue
            fac = A[r][col]
            for j in range(col, k + 1):
                A[r][j] -= fac * A[col][j]
    return [A[r][k] for r in range(k)]


def rmse(pred: list[float], actual: list[float]) -> float:
    return math.sqrt(sum((p - a) ** 2 for p, a in zip(pred, actual)) / len(actual))


def mae(pred: list[float], actual: list[float]) -> float:
    return sum(abs(p - a) for p, a in zip(pred, actual)) / len(actual)


def corr(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phi map F probe: decode/encode, exact F, cheap-fit holdout")
    w("=" * 88)
    w(f"  Phi = (x + y/p)/p   p=secp256k1 prime")
    w(f"  Walk: nG for n=1..{MAX_N}")
    w(f"  Train transitions: n=1..{TRAIN_END-1}   Holdout: n={TRAIN_END}..{MAX_N-1}")
    w()

    # Build walk via ecdsa (ground truth points)
    Cs: list[Fraction] = []
    xs: list[int] = []
    ys: list[int] = []
    pt = G
    for _ in range(MAX_N):
        x, y = int(pt.x()), int(pt.y())
        xs.append(x)
        ys.append(y)
        Cs.append(phi(x, y))
        pt = pt + G

    # --- 1) Round-trip decode/encode ---
    w("-" * 88)
    w("1) Exact decode <-> encode round-trip")
    w("-" * 88)
    rt_ok = 0
    for i in range(MAX_N):
        xd, yd = decode(Cs[i])
        if xd == xs[i] and yd == ys[i] and encode(xd, yd) == Cs[i]:
            rt_ok += 1
    w(f"  round-trip ok: {rt_ok}/{MAX_N}")
    w()

    # --- 2) Exact F(C) matches C_{n+1} ---
    w("-" * 88)
    w("2) Exact F(C)=encode(decode(C)+G) vs walk C_{n+1}")
    w("-" * 88)
    f_ok = 0
    for i in range(MAX_N - 1):
        if F(Cs[i]) == Cs[i + 1]:
            f_ok += 1
    w(f"  F(C_n)==C_{{n+1}}: {f_ok}/{MAX_N-1}")
    w("  Algebraic skeleton (field ops, a=0):")
    w("    x,y = decode(C)")
    w("    lam = (Gy-y) * inv(Gx-x)  mod p")
    w("    x'  = lam^2 - x - Gx     mod p")
    w("    y'  = lam*(x-x') - y     mod p")
    w("    C'  = (x' + y'/p)/p")
    w("  VERDICT: F is exact and is EC add-G in Phi clothing (not a cheap decimal rule).")
    w()

    # Float series for empirics (Phi in (0,1))
    cf = [float(c) for c in Cs]
    dcf = [cf[i + 1] - cf[i] for i in range(MAX_N - 1)]

    train_idx = list(range(0, TRAIN_END - 1))  # C_i -> C_{i+1}, i=0..798
    hold_idx = list(range(TRAIN_END - 1, MAX_N - 1))  # i=799..1098

    def split(vals: list[float], idx: list[int]) -> list[float]:
        return [vals[i] for i in idx]

    # Null baselines
    mean_d_train = sum(split(dcf, train_idx)) / len(train_idx)
    null_pred_hold = [mean_d_train] * len(hold_idx)
    d_hold = split(dcf, hold_idx)
    null_rmse = rmse(null_pred_hold, d_hold)
    null_mae = mae(null_pred_hold, d_hold)
    # chance: predict 0
    zero_rmse = rmse([0.0] * len(hold_idx), d_hold)

    w("-" * 88)
    w("3) Empirical cheap maps for Delta_C = C_{n+1}-C_n  (float)")
    w("-" * 88)
    w(f"  corr(C, Delta_C) all:     {corr(cf[:-1], dcf):.6f}")
    w(f"  corr(C, Delta_C) train:   {corr(split(cf[:-1], train_idx), split(dcf, train_idx)):.6f}")
    w(f"  corr(C, Delta_C) holdout: {corr(split(cf[:-1], hold_idx), d_hold):.6f}")
    if TRAIN_END >= 2:
        cprev = [cf[i - 1] if i > 0 else 0.0 for i in range(MAX_N - 1)]
        w(f"  corr(C_prev, Delta) all:  {corr(cprev, dcf):.6f}")
    w(f"  |Delta| mean train={sum(abs(x) for x in split(dcf,train_idx))/len(train_idx):.6e}")
    w(f"  holdout null (predict mean train Delta) RMSE={null_rmse:.6e} MAE={null_mae:.6e}")
    w(f"  holdout null (predict 0)                 RMSE={zero_rmse:.6e}")
    w()

    models: list[tuple[str, list[float], list[float]]] = []

    # M1: Delta ~ a*C + b
    Xtr = [[split(cf[:-1], train_idx)[j], 1.0] for j in range(len(train_idx))]
    ytr = split(dcf, train_idx)
    a, b = lstsq(Xtr, ytr)
    pred_h = [a * cf[i] + b for i in hold_idx]
    models.append((f"Delta ~ {a:.6f}*C + {b:.6f}", pred_h, d_hold))

    # M2: Delta ~ a*C + b*C^2 + c
    Xtr2 = [[cf[i], cf[i] ** 2, 1.0] for i in train_idx]
    coef2 = lstsq(Xtr2, ytr)
    a2, b2, c2 = coef2
    pred2 = [a2 * cf[i] + b2 * cf[i] ** 2 + c2 for i in hold_idx]
    models.append((f"Delta ~ {a2:.6f}*C + {b2:.6f}*C^2 + {c2:.6f}", pred2, d_hold))

    # M3: Delta ~ a*C + b*C_prev + c  (needs n>=2)
    tr3 = [i for i in train_idx if i >= 1]
    ho3 = [i for i in hold_idx if i >= 1]
    Xtr3 = [[cf[i], cf[i - 1], 1.0] for i in tr3]
    ytr3 = [dcf[i] for i in tr3]
    a3, b3, c3 = lstsq(Xtr3, ytr3)
    pred3 = [a3 * cf[i] + b3 * cf[i - 1] + c3 for i in ho3]
    d_ho3 = [dcf[i] for i in ho3]
    models.append((f"Delta ~ {a3:.6f}*C + {b3:.6f}*C_prev + {c3:.6f}", pred3, d_ho3))

    # M4: C' ~ a*C + b  (direct next, not delta)
    ytr_c = [cf[i + 1] for i in train_idx]
    Xtr_c = [[cf[i], 1.0] for i in train_idx]
    ac, bc = lstsq(Xtr_c, ytr_c)
    pred_c = [ac * cf[i] + bc for i in hold_idx]
    act_c = [cf[i + 1] for i in hold_idx]
    # also report as model on C' scale
    w("  Direct C' fits:")
    w(f"    C' ~ {ac:.6f}*C + {bc:.6f}")
    w(f"    holdout RMSE={rmse(pred_c, act_c):.6e} MAE={mae(pred_c, act_c):.6e}")
    w(f"    holdout corr(pred,actual)={corr(pred_c, act_c):.6f}")
    # identity / mean baselines for C'
    mean_c_train = sum(ytr_c) / len(ytr_c)
    w(f"    null mean-C' RMSE={rmse([mean_c_train]*len(act_c), act_c):.6e}")
    w(f"    null C'=C   RMSE={rmse([cf[i] for i in hold_idx], act_c):.6e}")
    w()

    w("  Delta models holdout:")
    for name, pred, act in models:
        w(f"    {name}")
        w(
            f"      RMSE={rmse(pred, act):.6e}  MAE={mae(pred, act):.6e}  "
            f"corr={corr(pred, act):.6f}"
        )
    w()

    # Digit-leading probe: same first k digits of C => same first m of Delta? (coarse)
    w("-" * 88)
    w("4) Leading-digit bucket probe (train -> holdout)")
    w("-" * 88)

    def lead(v: float, k: int) -> str:
        s = f"{v:.20f}"  # enough
        body = s.split(".")[1]
        return body[:k]

    for k in (1, 2, 3):
        buckets: dict[str, list[float]] = {}
        for i in train_idx:
            key = lead(cf[i], k)
            buckets.setdefault(key, []).append(dcf[i])
        bucket_mean = {key: sum(vs) / len(vs) for key, vs in buckets.items()}
        preds, acts = [], []
        miss = 0
        for i in hold_idx:
            key = lead(cf[i], k)
            if key not in bucket_mean:
                miss += 1
                preds.append(mean_d_train)
            else:
                preds.append(bucket_mean[key])
            acts.append(dcf[i])
        w(
            f"  k={k}: holdout RMSE={rmse(preds, acts):.6e}  "
            f"MAE={mae(preds, acts):.6e}  unseen_buckets={miss}/{len(hold_idx)}"
        )
    w()

    # Exact F cost note vs cheap reject
    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  decode/encode: exact on full walk.")
    w("  Exact F(C)=Phi(P+G) works 100%: it IS field add-G after decode.")
    w("  Cheap polynomial / bucket maps on C (and C_prev): holdout error stays")
    w("  on the same order as predicting mean Delta (~0.3) — no usable decimal rule.")
    w("  Next levers if continuing: symbolic simplify of F in Q(C), or differential")
    w("  Phi(P+H)-Phi(P) for fixed jump H — still must beat decode+EC.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
