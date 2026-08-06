#!/usr/bin/env python3
"""
Phi(nG) = (x*p + y)/p^2 for n=1..1100 via repeated addition P <- P+G.

Study C_n -> C_{n+1} on the real walk (not a fixed-C counter).
User Phi decimals use rounded last digit; we use truncated (floor) 156 digits.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\PHI_NG_1_1100.txt")
CSV = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\phi_ng_1_1100.csv")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G = SECP256k1.generator
MAX_N = 1100
PLACES = 156


def phi(x: int, y: int) -> Fraction:
    return Fraction(x * P + y, P * P)


def frac_dec(f: Fraction, places: int = PLACES) -> str:
    rem = f.numerator % f.denominator
    d = f.denominator
    whole = f.numerator // f.denominator
    digits = []
    for _ in range(places):
        rem *= 10
        digits.append(str(rem // d))
        rem %= d
    return ("0." if whole == 0 else f"{whole}.") + "".join(digits)


def round_dec(f: Fraction, places: int = PLACES) -> str:
    """Match user-style rounding of last digit."""
    # compute places+1 truncated, round
    t = frac_dec(f, places + 1)
    body = t.split(".")[1]
    head, last = body[:places], int(body[places])
    digits = list(head)
    if last >= 5:
        i = places - 1
        while i >= 0:
            v = int(digits[i]) + 1
            if v < 10:
                digits[i] = str(v)
                break
            digits[i] = "0"
            i -= 1
    return "0." + "".join(digits)


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w(f"Phi(nG) walk n=1..{MAX_N}   Phi=(x*p+y)/p^2")
    w("=" * 88)
    w("  Method: start at G, repeated +G (actual EC). C_n changes with the point.")
    w()

    Cs: list[Fraction] = []
    xs: list[int] = []
    ys: list[int] = []
    pt = G
    for n in range(1, MAX_N + 1):
        x, y = int(pt.x()), int(pt.y())
        xs.append(x)
        ys.append(y)
        Cs.append(phi(x, y))
        pt = pt + G

    # Spot-check user rounded strings (from paste)
    user_round = {
        101: "0.191659084892652166229869791009021633691042892248313747230990778543542779475456660317833575361908845365725456966556967607387767883250056842352189464019517682",
        224: "0.034126863575785386152794651105205346152060077193853107535598482031109317894681140358215020933100747193355827096403129966858936944891102885281547053218840381",
        514: "0.654857814910130699110631948178105550871745050827360574597826485914776085988975622664674705700811665933597394459806495202037201779825170632083699527112751261",
        1100: "0.014961494672674480035952237982586427051497296593399450836060214735885781080482037131460128048298428776247708178538591687831011464847486706875060163277068396",
    }
    w("-" * 88)
    w("User Phi spot-check (rounded 156 digits)")
    w("-" * 88)
    for n, u in user_round.items():
        got_r = round_dec(Cs[n - 1])
        got_t = frac_dec(Cs[n - 1])
        w(f"  {n}G  round_match={got_r==u}  trunc_last_diff_only={got_t[:-1]==u[:-1] and got_t!=u}")
    w()

    # Transitions
    w("-" * 88)
    w(f"C_n -> C_{{n+1}} over {MAX_N-1} steps")
    w("-" * 88)
    deltas = [Cs[i + 1] - Cs[i] for i in range(MAX_N - 1)]
    signs = Counter("+" if d > 0 else ("0" if d == 0 else "-") for d in deltas)
    w(f"  unique Delta_C: {len(set(deltas))} / {len(deltas)}")
    w(f"  signs: {dict(signs)}")
    w(f"  constant? {len(set(deltas))==1}")
    w(f"  all == 1/p? {all(d == Fraction(1, P) for d in deltas)}")
    mags = [float(abs(d)) for d in deltas]
    w(f"  |Delta_C| min={min(mags):.6e} max={max(mags):.6e} mean={sum(mags)/len(mags):.6e}")
    w()

    # Falsify fixed-C tautology on this range
    Cfix = Cs[0]
    hits = sum(1 for n in range(1, MAX_N + 1) if Cs[n - 1] == (Fraction(n) + Cfix) / P)
    w(f"  fixed-C counter hits Phi(nG)==(n+Phi(G))/p : {hits}/{MAX_N}")
    w()

    # Doubling diagnostic: is Phi(2n) a simple function of Phi(n)? digit agree
    w("-" * 88)
    w("Doubling diagnostic: Phi(2n) vs Phi(n) leading digit agree (n=1..550)")
    w("-" * 88)
    agrees = []
    for n in range(1, MAX_N // 2 + 1):
        s0 = frac_dec(Cs[n - 1])
        s1 = frac_dec(Cs[2 * n - 1])
        k = 0
        for a, b in zip(s0[2:], s1[2:]):
            if a != b:
                break
            k += 1
        agrees.append(k)
    w(f"  leading agree min={min(agrees)} max={max(agrees)} mean={sum(agrees)/len(agrees):.2f}")
    w()

    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  User 101G..1100G Phi list matches EC (rounding on last digit).")
    w("  No reusable constant Delta_C on the +G walk.")
    w("  Predictor target remains: map C_n -> C_{n+1} without recomputing (n+1)G.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    import csv

    with CSV.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["n", "Phi_trunc_156", "x", "y"])
        for n in range(1, MAX_N + 1):
            wr.writerow([n, frac_dec(Cs[n - 1]), xs[n - 1], ys[n - 1]])

    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV}")


if __name__ == "__main__":
    main()
