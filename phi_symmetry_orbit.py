#!/usr/bin/env python3
"""
Phi-space symmetries of the transported group law F.

  F(C_n, C_m) = C_{(n+m) mod N}   via encode(decode(Cn)+decode(Cm))
  (naive decimal combines are CLOSED — not retested here)

Targets:
  1) Exact negation transform Phi(-P) from Phi(P)
  2) GLV sixfold orbit in Phi-space
  3) Candidate T_lambda: C_n -> C_(lambda*n)
  4) Equivariance: F(T(Cn), T(Cm)) == T(F(Cn, Cm))

Report: exact match, formula, cost, decode required?, cheaper than EC add?
"""
from __future__ import annotations

import csv
import time
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_SYMMETRY_ORBIT.txt")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
# secp256k1 GLV
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
# LAMBDA^2 mod N (since LAMBDA^3 = 1)
LAMBDA2 = (LAMBDA * LAMBDA) % N

G = SECP256k1.generator


def modinv(a: int, m: int = P) -> int:
    return pow(a % m, -1, m)


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def decode(c: Fraction) -> tuple[int, int]:
    cp = c * P
    x = int(cp)
    y = int((cp - x) * P)
    return x, y


def encode(x: int, y: int) -> Fraction:
    return phi(x % P, y % P)


def ec_add(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int]:
    if x1 == x2:
        if (y1 + y2) % P == 0:
            raise ValueError("infinity")
        lam = (3 * x1 * x1) * modinv(2 * y1) % P
    else:
        lam = (y2 - y1) * modinv((x2 - x1) % P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3


def ec_neg(x: int, y: int) -> tuple[int, int]:
    return x, (-y) % P


def ec_psi(x: int, y: int) -> tuple[int, int]:
    """GLV endomorphism: (x,y) -> (beta*x, y)."""
    return (BETA * x) % P, y


def phi_of_scalar(n: int) -> Fraction:
    n = n % N
    if n == 0:
        raise ValueError("infinity has no affine Phi")
    pt = n * G
    return phi(int(pt.x()), int(pt.y()))


def F(ca: Fraction, cb: Fraction) -> Fraction:
    x1, y1 = decode(ca)
    x2, y2 = decode(cb)
    x3, y3 = ec_add(x1, y1, x2, y2)
    return encode(x3, y3)


# --- candidate transforms on C (may decode) ---

def T_neg_exact(c: Fraction) -> Fraction:
    """Cheap exact: decode y only (or x,y), flip y -> p-y, re-encode.
    Formula: Phi(-P)=(x*p + (p-y))/p^2 = C + (p-2y)/p^2
    """
    x, y = decode(c)
    return encode(x, (-y) % P)


def T_neg_from_residual(c: Fraction) -> Fraction:
    """Same math via residual R = (p-2y)/p^2."""
    x, y = decode(c)
    return c + Fraction(P - 2 * y, P * P)


def T_lambda_psi(c: Fraction) -> Fraction:
    """Exact GLV on points: decode, (beta*x,y), encode. NOT a C-only formula."""
    x, y = decode(c)
    return encode(*ec_psi(x, y))


def T_lambda2_psi(c: Fraction) -> Fraction:
    x, y = decode(c)
    x2, y2 = ec_psi(x, y)
    return encode(*ec_psi(x2, y2))


def T_neg_lambda(c: Fraction) -> Fraction:
    return T_neg_exact(T_lambda_psi(c))


def T_neg_lambda2(c: Fraction) -> Fraction:
    return T_neg_exact(T_lambda2_psi(c))


# Cheap C-only candidates for T_lambda (expected to fail; document)
def T_lambda_naive_mod1(c: Fraction) -> Fraction:
    return (c * Fraction(LAMBDA, 1)) % 1  # nonsense scale


def load_solved() -> list[tuple[int, int]]:
    rows = []
    with KEYS.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            puzz = int(row["puzzle"])
            key = int(row["private_key"])
            if 1 <= key < N:
                rows.append((puzz, key))
    return rows


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phi symmetries: negation + GLV orbit + equivariance of F")
    w("=" * 88)
    w(f"  LAMBDA = {LAMBDA:064x}")
    w(f"  LAMBDA2 = {LAMBDA2:064x}")
    w(f"  BETA    = {BETA:064x}")
    w(f"  check LAMBDA^3 == 1 mod N: {(LAMBDA*LAMBDA*LAMBDA)%N == 1}")
    w(f"  check BETA^3 == 1 mod p:   {(BETA*BETA*BETA)%P == 1}")
    w()

    # Sanity: psi(G) == LAMBDA*G
    gx, gy = int(G.x()), int(G.y())
    px, py = ec_psi(gx, gy)
    lg = LAMBDA * G
    w(f"  psi(G)==LAMBDA*G: {px==int(lg.x()) and py==int(lg.y())}")
    w()

    solved = load_solved()
    # calibration / holdout by puzzle id
    cal = [(pz, k) for pz, k in solved if pz <= 100]
    hold = [(pz, k) for pz, k in solved if pz > 100]
    # also small walk scalars 1..64 for dense checks
    walk = list(range(1, 65))

    w("-" * 88)
    w("1) Exact negation in Phi-space")
    w("-" * 88)
    w("  Phi(-P) = (x*p + (p-y))/p^2")
    w("  Phi(-P) - Phi(P) = (p - 2y)/p^2")
    neg_ok = 0
    residual_ok = 0
    for n in walk:
        c = phi_of_scalar(n)
        c_neg = phi_of_scalar((-n) % N)
        t1 = T_neg_exact(c)
        t2 = T_neg_from_residual(c)
        x, y = decode(c)
        R = Fraction(P - 2 * y, P * P)
        if t1 == c_neg:
            neg_ok += 1
        if t2 == c_neg and (c_neg - c) == R:
            residual_ok += 1
    w(f"  walk 1..64: T_neg(C_n)==C_{{-n}}: {neg_ok}/64")
    w(f"  walk 1..64: residual formula exact: {residual_ok}/64")

    # cost: decode + one sub + encode vs full scalar mul
    t0 = time.perf_counter()
    for n in walk:
        T_neg_exact(phi_of_scalar(n))
    t_neg = time.perf_counter() - t0
    t0 = time.perf_counter()
    for n in walk:
        phi_of_scalar((-n) % N)  # full scalar path for -nG
    t_full = time.perf_counter() - t0
    w(f"  timing walk64: T_neg on known C ~ {t_neg*1000:.2f}ms  (includes phi_of_scalar get C)")
    w(f"  timing walk64: recompute (-n)G via scalar  ~ {t_full*1000:.2f}ms")
    w("  Arithmetic cost of T_neg given C: decode (2 mul/div by p) + y:=p-y + encode.")
    w("  Requires decode of y (hence x). Cheaper than EC add / scalar mul; not free on digits alone.")
    w()

    # Solved-key negation holdout
    neg_cal = neg_hold = 0
    for pz, k in cal:
        if T_neg_exact(phi_of_scalar(k)) == phi_of_scalar((-k) % N):
            neg_cal += 1
    for pz, k in hold:
        if T_neg_exact(phi_of_scalar(k)) == phi_of_scalar((-k) % N):
            neg_hold += 1
    w(f"  solved cal puzzles<=100: T_neg exact {neg_cal}/{len(cal)}")
    w(f"  solved holdout puzzles>100: T_neg exact {neg_hold}/{len(hold)}")
    w()

    w("-" * 88)
    w("2) GLV T_lambda via endomorphism psi (decode, beta*x, encode)")
    w("-" * 88)
    lam_ok = 0
    lam2_ok = 0
    for n in walk:
        c = phi_of_scalar(n)
        if T_lambda_psi(c) == phi_of_scalar((LAMBDA * n) % N):
            lam_ok += 1
        if T_lambda2_psi(c) == phi_of_scalar((LAMBDA2 * n) % N):
            lam2_ok += 1
    w(f"  walk: T_lambda_psi(C_n)==C_{{lambda n}}: {lam_ok}/64")
    w(f"  walk: T_lambda2_psi(C_n)==C_{{lambda2 n}}: {lam2_ok}/64")

    # Is there a C-only formula without beta*x? Probe: C' == f(C) with only rational ops on C
    # Check if C_lambda is a fixed fractional-linear transform of C: (aC+b)/(cC+d)
    # Fit on walk floats — only for reporting failure of cheap map
    import math

    pairs = []
    for n in walk:
        pairs.append((float(phi_of_scalar(n)), float(phi_of_scalar((LAMBDA * n) % N))))
    # If C' ~= a*C+b
    # lstsq 2-param
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    # normal eq
    sxx = sum(x * x for x in xs)
    sx = sum(xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sy = sum(ys)
    m = len(xs)
    det = sxx * m - sx * sx
    a = (sxy * m - sx * sy) / det if det else 0
    b = (sxx * sy - sx * sxy) / det if det else 0
    rmse = math.sqrt(sum((a * x + b - y) ** 2 for x, y in zip(xs, ys)) / m)
    w(f"  cheap probe C_lambda ~ a*C+b on walk: a={a:.6f} b={b:.6f} RMSE={rmse:.6f}")
    w("  (RMSE ~0.3 => no usable linear map on C alone)")

    lam_hold = 0
    for pz, k in hold:
        if T_lambda_psi(phi_of_scalar(k)) == phi_of_scalar((LAMBDA * k) % N):
            lam_hold += 1
    w(f"  solved holdout: T_lambda_psi exact {lam_hold}/{len(hold)}")
    w("  Cost: decode + 1 mul mod p (by BETA) + encode. Needs x. Cheaper than full scalar*LAMBDA.")
    w()

    w("-" * 88)
    w("3) Sixfold orbit Phi values (sample n=1,2,5,17)")
    w("-" * 88)
    labels = [
        ("n", lambda n: n % N, None),
        ("lambda n", lambda n: (LAMBDA * n) % N, T_lambda_psi),
        ("lambda2 n", lambda n: (LAMBDA2 * n) % N, T_lambda2_psi),
        ("-n", lambda n: (-n) % N, T_neg_exact),
        ("-lambda n", lambda n: (-LAMBDA * n) % N, T_neg_lambda),
        ("-lambda2 n", lambda n: (-LAMBDA2 * n) % N, T_neg_lambda2),
    ]
    for n in (1, 2, 5, 17):
        c0 = phi_of_scalar(n)
        w(f"  n={n}:")
        for name, scal, T in labels:
            c_true = phi_of_scalar(scal(n))
            if T is None:
                match = True
            else:
                match = T(c0) == c_true
            w(f"    {name:12s} C={float(c_true):.10f}  T_from_C_n_match={match}")
    w()

    w("-" * 88)
    w("4) Equivariance of F under T")
    w("-" * 88)
    w("  Need: F(T(Cn), T(Cm)) == T(F(Cn, Cm))")
    w("  Because (lambda n + lambda m)G = lambda(n+m)G etc.")

    def eq_test(T, name: str, pairs_nm: list[tuple[int, int]]) -> tuple[int, int]:
        ok = 0
        for n, m in pairs_nm:
            # avoid infinity
            if (n + m) % N == 0:
                continue
            cn, cm = phi_of_scalar(n), phi_of_scalar(m)
            try:
                left = F(T(cn), T(cm))
                right = T(F(cn, cm))
            except ValueError:
                continue
            if left == right:
                ok += 1
        return ok, len(pairs_nm)

    # dense small pairs
    pairs_nm = [(n, m) for n in range(1, 21) for m in range(1, 21)]
    # holdout pairs from solved keys (first 15 holdout keys as n, next as m cross sample)
    hold_keys = [k for _, k in hold[:20]]
    pairs_hold = []
    for i, n in enumerate(hold_keys):
        for m in hold_keys[i + 1 : i + 4]:
            if (n + m) % N != 0:
                pairs_hold.append((n, m))

    for T, name in [
        (T_neg_exact, "T_neg"),
        (T_lambda_psi, "T_lambda (psi)"),
        (T_lambda2_psi, "T_lambda2 (psi^2)"),
        (T_neg_lambda, "T_neg_lambda"),
        (T_neg_lambda2, "T_neg_lambda2"),
    ]:
        ok, tot = eq_test(T, name, pairs_nm)
        okh, toth = eq_test(T, name, pairs_hold) if pairs_hold else (0, 0)
        w(f"  {name:22s}  small pairs exact {ok}/{tot}  solved-holdout pairs {okh}/{toth}")

    w()
    w("-" * 88)
    w("5) Does equivariance need decode? Cost vs EC add")
    w("-" * 88)
    w("  All exact T_* above DECODE (x,y), apply field/endomorphism/neg, ENCODE.")
    w("  They are symmetries of F by construction of the group / GLV — expected 100%.")
    w("  They are NOT C-digit-only maps.")
    w("  vs full EC add: T_neg ~ flip y; T_lambda ~ 1 mul by BETA; EC add ~ inv + muls.")
    w("  So orbit moves are cheaper than general addition, but do not replace F.")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Negation: EXACT cheap relation in Phi via (p-2y)/p^2 after decode y.")
    w("  GLV: EXACT T_lambda = encode(beta*x, y); linear map on C alone FAILS.")
    w("  Equivariance F(T(a),T(b))=T(F(a,b)): HOLDS for neg/GLV orbit transforms.")
    w("  These are real symmetries of transported F — still require (x,y) layers.")
    w("  No C-only (no-decode) T_lambda found; naive C-linear probe dead.")
    w("  Useful structure: sixfold orbit is easy in Phi once decoded; addition F still EC.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
