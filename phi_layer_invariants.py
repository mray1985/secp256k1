#!/usr/bin/env python3
"""
Phi layer invariants: split C = X + Fine with

  X    = x/p          (coarse)
  Fine = y/p^2        (fine)
  C    = X + Fine

Ask: what is invariant / cheap under T_neg, T_lambda, F — without full EC add?
No naive C+C / C*C branches.
"""
from __future__ import annotations

import csv
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_LAYER_INVARIANTS.txt")
KEYS = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72
BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
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


def split_layers(c: Fraction) -> tuple[Fraction, Fraction, int, int]:
    """Return (X, Fine, x, y) with C = X + Fine, X=x/p, Fine=y/p^2."""
    x, y = decode(c)
    X = Fraction(x, P)
    Fine = Fraction(y, P * P)
    return X, Fine, x, y


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


def phi_of_scalar(n: int) -> Fraction:
    n = n % N
    if n == 0:
        raise ValueError("infinity")
    pt = n * G
    return phi(int(pt.x()), int(pt.y()))


def F(ca: Fraction, cb: Fraction) -> Fraction:
    return encode(*ec_add(*decode(ca), *decode(cb)))


def load_solved() -> list[tuple[int, int]]:
    """Return (puzzle_n, scalar) excluding 135."""
    rows: list[tuple[int, int]] = []
    with KEYS.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pn = int(r.get("puzzle") or r.get("n") or r.get("bits") or 0)
            raw = r.get("private_key") or r.get("d") or r.get("key") or ""
            raw = raw.strip()
            if not raw or pn == 135:
                continue
            d = int(raw, 16) if raw.lower().startswith("0x") or any(
                c in raw.lower() for c in "abcdef"
            ) else int(raw)
            if d % N == 0:
                continue
            rows.append((pn, d % N))
    return rows


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("Phi layer invariants: X = x/p, Fine = y/p^2, C = X + Fine")
    w("=" * 88)
    w()
    w("  Goal: find cheap layer rules / invariants under T_neg, T_lambda, F")
    w("  without paying a full EC addition for F itself.")
    w()

    # sanity on walk
    walk_ns = list(range(1, 65))
    walk_C = {n: phi_of_scalar(n) for n in walk_ns}

    # --- 1) Negation on layers ---
    w("-" * 88)
    w("1) Negation on layers")
    w("-" * 88)
    w("  Exact: x' = x, y' = p-y")
    w("  => X' = X  (coarse invariant)")
    w("  => Fine' = (p-y)/p^2 = 1/p - Fine")
    w("  => C' = C + 1/p - 2*Fine")
    w()

    x_inv = fine_rule = c_from_layers = 0
    for n in walk_ns:
        c = walk_C[n]
        X, Fine, x, y = split_layers(c)
        c_neg = walk_C.get((N - n) % N) if n != 0 else None
        # compute -nG via encode
        c_neg = encode(x, (-y) % P)
        Xn, Fn, xn, yn = split_layers(c_neg)
        if Xn == X:
            x_inv += 1
        if Fn == Fraction(1, P) - Fine:
            fine_rule += 1
        if c_neg == c + Fraction(1, P) - 2 * Fine:
            c_from_layers += 1

    w(f"  walk 1..64: X'==X:                    {x_inv}/64")
    w(f"  walk 1..64: Fine'==1/p - Fine:        {fine_rule}/64")
    w(f"  walk 1..64: C'==C + 1/p - 2*Fine:     {c_from_layers}/64")
    w("  Cost: split Fine from C (decode y) + one sub; NO field inv, NO EC add.")
    w("  Requires Fine (hence y). Digits-only without split: no (float hides Fine).")
    w()

    # --- 2) GLV on layers ---
    w("-" * 88)
    w("2) GLV T_lambda on layers")
    w("-" * 88)
    w("  psi: (x,y)->(beta*x mod p, y)")
    w("  => Fine' = Fine  (fine layer INVARIANT)")
    w("  => X' = (beta*x mod p)/p   NOT equal to (beta*X) mod 1 in general")
    w("     (wrap when beta*x >= p)")
    w()

    fine_inv = x_wrap_formula = cheap_mod1 = 0
    wraps = 0
    for n in walk_ns:
        c = walk_C[n]
        X, Fine, x, y = split_layers(c)
        x2 = (BETA * x) % P
        c2 = encode(x2, y)
        X2, F2, _, _ = split_layers(c2)
        if F2 == Fine:
            fine_inv += 1
        # exact wrap formula
        prod = BETA * x
        q, r = divmod(prod, P)
        if X2 == Fraction(r, P) and q == prod // P:
            x_wrap_formula += 1
        if q > 0:
            wraps += 1
        # naive: (beta * X) mod 1
        naive = Fraction((BETA * x) % P, P)  # this IS exact X2 — wait
        # (beta * X) as rational without mod: BETA * x / P, then fractional part
        raw = Fraction(BETA * x, P)
        frac_part = raw - int(raw)  # {beta*x / p} = (beta*x mod p)/p when we take floor correctly
        # int(raw) for Fraction truncates toward 0; for positive OK
        if frac_part == X2:
            cheap_mod1 += 1

    w(f"  walk 1..64: Fine'==Fine:                         {fine_inv}/64")
    w(f"  walk 1..64: X'==(beta*x mod p)/p exact:          {x_wrap_formula}/64")
    w(f"  walk 1..64: X'=={{beta*x/p}} (frac of beta*X*p?): {cheap_mod1}/64")
    w(f"  walk 1..64: times beta*x wrapped (>=1*p):        {wraps}/64")
    w("  So Fine is GLV-invariant. Coarse needs one mul-mod-p (decode x).")
    w("  Still cheaper than scalar*LAMBDA; not a C-digit multiply.")
    w()

    # lambda^2: Fine still invariant (y unchanged through psi^2)
    fine_inv2 = 0
    for n in walk_ns:
        c = walk_C[n]
        _, Fine, x, y = split_layers(c)
        x2 = (BETA * BETA * x) % P
        _, F2, _, _ = split_layers(encode(x2, y))
        if F2 == Fine:
            fine_inv2 += 1
    w(f"  walk 1..64: Fine invariant under psi^2:          {fine_inv2}/64")
    w()

    # --- 3) What F does to layers ---
    w("-" * 88)
    w("3) Addition F on layers — any cheap invariant?")
    w("-" * 88)
    w("  Test candidates that do NOT run full EC add (compare to true F):")
    w("    a) Fine_out == Fine_n + Fine_m          (fine sum)")
    w("    b) Fine_out == Fine_n + Fine_m - k/p^2  (carry probe, k small)")
    w("    c) X_out == (X_n + X_m) mod 1           (coarse mod-1)")
    w("    d) Fine_out == Fine_n  or  Fine_m       (preserve one fine)")
    w("    e) X_out == X_n  (coarse of one input)")
    w()

    pairs = [(a, b) for a in range(1, 21) for b in range(a + 1, 21)]
    # avoid a+b == 0 mod N (impossible for small) and doubles that hit weird — all fine
    stats = {
        "fine_sum": 0,
        "fine_sum_pm1": 0,
        "fine_sum_pm2": 0,
        "X_mod1": 0,
        "fine_eq_n": 0,
        "fine_eq_m": 0,
        "X_eq_n": 0,
        "X_eq_m": 0,
        "fine_sum_abs_err_lt_2": 0,
    }
    abs_err_fine: list[int] = []  # in units of 1/p^2 i.e. integer |y3 - (y1+y2)| kinda

    for a, b in pairs:
        ca, cb = walk_C[a], walk_C[b]
        Xa, Fa, xa, ya = split_layers(ca)
        Xb, Fb, xb, yb = split_layers(cb)
        cout = F(ca, cb)
        Xo, Fo, xo, yo = split_layers(cout)

        if Fo == Fa + Fb:
            stats["fine_sum"] += 1
        # Fine_n + Fine_m = (ya+yb)/p^2; may exceed 1/p so not even a valid Fine
        # measure integer residual on y: yo vs (ya+yb) mod something — not group
        dy = yo - (ya + yb)
        abs_err_fine.append(abs(dy))
        if Fo == Fa + Fb or Fo == Fa + Fb - Fraction(1, P * P) or Fo == Fa + Fb + Fraction(
            1, P * P
        ):
            stats["fine_sum_pm1"] += 1
        if any(Fo == Fa + Fb + Fraction(k, P * P) for k in (-2, -1, 0, 1, 2)):
            stats["fine_sum_pm2"] += 1
        if abs(dy) <= 2:
            stats["fine_sum_abs_err_lt_2"] += 1

        Xsum = Xa + Xb
        Xsum_mod = Xsum - int(Xsum)  # {Xa+Xb} for positive
        if Xo == Xsum_mod:
            stats["X_mod1"] += 1
        if Fo == Fa:
            stats["fine_eq_n"] += 1
        if Fo == Fb:
            stats["fine_eq_m"] += 1
        if Xo == Xa:
            stats["X_eq_n"] += 1
        if Xo == Xb:
            stats["X_eq_m"] += 1

    npairs = len(pairs)
    w(f"  pairs tested (a,b in 1..20, a<b): {npairs}")
    for k, v in stats.items():
        w(f"    exact {k}: {v}/{npairs}")
    if abs_err_fine:
        abs_err_fine.sort()
        med = abs_err_fine[len(abs_err_fine) // 2]
        w(f"  |yo - (ya+yb)| median={med}  (field ints; ~p/2 if random)")
        w(f"  |yo - (ya+yb)| min={abs_err_fine[0]} max={abs_err_fine[-1]}")
    w()
    w("  If F had a layer-additive structure, fine_sum or X_mod1 would hit >>0.")
    w("  Expect ~0 — addition mixes layers through slope/inv.")
    w()

    # --- 4) Orbit: Fine shared across {n, λn, λ²n}; X shared across {±} ---
    w("-" * 88)
    w("4) Sixfold orbit — which layer is shared?")
    w("-" * 88)
    sample = [1, 2, 5, 17, 31, 63]
    for n in sample:
        c = walk_C[n]
        X, Fine, x, y = split_layers(c)
        orbit = {
            "n": (x, y),
            "lam": ((BETA * x) % P, y),
            "lam2": ((BETA * BETA * x) % P, y),
            "-n": (x, (-y) % P),
            "-lam": ((BETA * x) % P, (-y) % P),
            "-lam2": ((BETA * BETA * x) % P, (-y) % P),
        }
        fines = {k: Fraction(yy, P * P) for k, (_, yy) in orbit.items()}
        Xs = {k: Fraction(xx, P) for k, (xx, _) in orbit.items()}
        # Fine equal within {n,lam,lam2} and within {-n,-lam,-lam2}
        g1 = fines["n"] == fines["lam"] == fines["lam2"]
        g2 = fines["-n"] == fines["-lam"] == fines["-lam2"]
        # and Fine(-) = 1/p - Fine(+)
        neg_link = fines["-n"] == Fraction(1, P) - fines["n"]
        # X equal within {n,-n}, {lam,-lam}, {lam2,-lam2}
        x_pairs = (
            Xs["n"] == Xs["-n"]
            and Xs["lam"] == Xs["-lam"]
            and Xs["lam2"] == Xs["-lam2"]
        )
        w(
            f"  n={n}: Fine shared on +orbit={g1} -orbit={g2}  "
            f"Fine(-)=1/p-Fine(+)={neg_link}  X shared on ±pairs={x_pairs}"
        )
    w()

    # --- 5) Equivariance at layer level (sanity; uses decode T) ---
    w("-" * 88)
    w("5) Layer reading of equivariance (sanity)")
    w("-" * 88)
    w("  Under T_lambda: Fine(F(Ta,Tb)) == Fine(F(a,b))  because psi preserves y")
    w("  and psi is a homomorphism: psi(P+Q)=psi(P)+psi(Q).")
    w()

    eq_fine = eq_X_fail_ok = 0
    eq_pairs = [(i, j) for i in range(1, 11) for j in range(i + 1, 11)]
    for a, b in eq_pairs:
        ca, cb = walk_C[a], walk_C[b]
        _, Fa, xa, ya = split_layers(ca)
        _, Fb, xb, yb = split_layers(cb)
        # T_lambda
        ta = encode((BETA * xa) % P, ya)
        tb = encode((BETA * xb) % P, yb)
        fout = F(ca, cb)
        ft = F(ta, tb)
        _, Fo, _, _ = split_layers(fout)
        _, Fot, xot, yot = split_layers(ft)
        # psi(fout) should equal ft
        xo, yo = decode(fout)
        if ft == encode((BETA * xo) % P, yo):
            eq_X_fail_ok += 1  # full equivariance
        if Fot == Fo:  # Fine of sum == Fine of T-sum? Only if y unchanged by psi on sum
            # psi preserves y of the SUM point, so Fine(psi(P+Q))=Fine(P+Q)
            # Fine(F(Ta,Tb))=Fine(psi(P)+psi(Q))=Fine(psi(P+Q))=Fine(P+Q)
            if Fot == Fo:
                eq_fine += 1

    w(f"  pairs: Fine(F(Ta,Tb))==Fine(F(a,b)): {eq_fine}/{len(eq_pairs)}")
    w(f"  pairs: F(Ta,Tb)==T(F(a,b)) full:     {eq_X_fail_ok}/{len(eq_pairs)}")
    w()

    # --- 6) Solved-key holdout for layer rules ---
    w("-" * 88)
    w("6) Solved-key holdout (puzzles>100, skip 135)")
    w("-" * 88)
    solved = load_solved()
    hold = [(pn, d) for pn, d in solved if pn > 100]
    cal = [(pn, d) for pn, d in solved if pn <= 100]
    w(f"  cal n<=100: {len(cal)}  holdout: {len(hold)}")

    def check_neg_layers(ds: list[tuple[int, int]]) -> tuple[int, int, int]:
        ok_x = ok_f = ok_c = 0
        for _, d in ds:
            c = phi_of_scalar(d)
            X, Fine, x, y = split_layers(c)
            cn = encode(x, (-y) % P)
            Xn, Fn, _, _ = split_layers(cn)
            if Xn == X:
                ok_x += 1
            if Fn == Fraction(1, P) - Fine:
                ok_f += 1
            if cn == c + Fraction(1, P) - 2 * Fine:
                ok_c += 1
        return ok_x, ok_f, ok_c

    def check_glv_fine(ds: list[tuple[int, int]]) -> int:
        ok = 0
        for _, d in ds:
            c = phi_of_scalar(d)
            _, Fine, x, y = split_layers(c)
            _, F2, _, _ = split_layers(encode((BETA * x) % P, y))
            if F2 == Fine:
                ok += 1
        return ok

    hx, hf, hc = check_neg_layers(hold)
    w(f"  holdout T_neg: X'==X {hx}/{len(hold)}  Fine'=1/p-Fine {hf}/{len(hold)}  "
      f"C formula {hc}/{len(hold)}")
    w(f"  holdout T_lambda: Fine'==Fine {check_glv_fine(hold)}/{len(hold)}")

    # F layer cheap rules on a few holdout pairs
    if len(hold) >= 2:
        hpairs = []
        for i in range(min(4, len(hold))):
            for j in range(i + 1, min(4, len(hold))):
                hpairs.append((hold[i][1], hold[j][1]))
        fs = xm = 0
        for da, db in hpairs:
            ca, cb = phi_of_scalar(da), phi_of_scalar(db)
            Xa, Fa, _, _ = split_layers(ca)
            Xb, Fb, _, _ = split_layers(cb)
            Xo, Fo, _, _ = split_layers(F(ca, cb))
            if Fo == Fa + Fb:
                fs += 1
            Xs = Xa + Xb
            if Xo == Xs - int(Xs):
                xm += 1
        w(f"  holdout pairs F: Fine_sum exact {fs}/{len(hpairs)}  X_mod1 exact {xm}/{len(hpairs)}")
    w()

    # --- verdict ---
    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  YES — visible layer structure, but only for ORBIT symmetries:")
    w("    • Negation: X invariant; Fine -> 1/p - Fine; C -> C + 1/p - 2*Fine")
    w("    • GLV:      Fine invariant; X -> (beta*x mod p)/p")
    w("  NO  — addition F has no cheap layer rule (fine sum / X mod-1 ~ 0 exact).")
    w("  Split makes orbit moves transparent; F still needs full EC (slope + inv).")
    w("  Decode cost to read layers: 2 mul by p (same as before).")
    w("  Cheaper than EC add: yes for T_neg / T_lambda; no substitute for F.")
    w()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
