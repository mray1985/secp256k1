#!/usr/bin/env python3
"""Lead sweep with BOTH width definitions: 256-window vs native bit_length."""
from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_LEAD_SWEEP_BOTH_DEFS.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_lead_sweep_both_defs.csv")

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PERM = 400
RNG = random.Random(42)


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


def lead_256(px: int, m: int) -> int:
    m = max(1, min(m, 256))
    return px >> (256 - m)


def lead_native(px: int, m: int) -> int:
    L = max(px.bit_length(), m)
    return px >> (L - m)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def close01(xs, ys):
    return sum(1 for a, b in zip(xs, ys) if abs(a - b) < 0.1) / len(xs)


def mae(xs, ys):
    return sum(abs(a - b) for a, b in zip(xs, ys)) / len(xs)


def perm_p(xs, ys, obs):
    y = list(ys)
    thr = abs(obs)
    c = 0
    for _ in range(PERM):
        RNG.shuffle(y)
        if abs(pearson(xs, y)) >= thr:
            c += 1
    return (c + 1) / (PERM + 1)


def main() -> None:
    puzzles = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            puzzles.append((n, d, pub_x(d), lead_frac(d)))

    rows = []
    lines = []

    def w(s=""):
        lines.append(s)
        print(s)

    w("=" * 88)
    w("LEAD SWEEP — two definitions of Px_lead(m)")
    w("=" * 88)
    w("  def256:    floor(Px / 2^(256-m))     [your formula]")
    w("  defNative: floor(Px / 2^(L-m)), L=bit_length(Px)  [earlier 0.61 cut]")
    w()

    # m=n both defs
    dF = [df for *_, df in puzzles]
    p256 = [lead_frac(lead_256(px, n)) for n, _, px, _ in puzzles]
    pNat = [lead_frac(lead_native(px, n)) for n, _, px, _ in puzzles]
    for name, pF in (("def256 m=n", p256), ("defNative m=n", pNat)):
        r = pearson(dF, pF)
        w(f"{name}: r={r:+.3f} close={close01(dF,pF):.3f} MAE={mae(dF,pF):.4f} p={perm_p(dF,pF,r):.4f}")
    w()

    # dense ridge both defs, all puzzles for fixed m; and n>=m subset
    w(f"{'def':<10} {'family':<12} {'param':<14} {'N':>4} {'r':>7} {'close':>7} {'MAE':>7} {'p':>7}")
    w("-" * 88)

    for defname, leadfn in (("def256", lead_256), ("defNative", lead_native)):
        # fixed
        for m in [32, 40, 48, 56, 64, 80, 96, 128, 160, 192, 256]:
            pF = [lead_frac(leadfn(px, m)) for _, _, px, _ in puzzles]
            r = pearson(dF, pF)
            row = dict(
                definition=defname,
                family="fixed",
                param=f"m={m}",
                n_used=70,
                r=r,
                close=close01(dF, pF),
                mae=mae(dF, pF),
                p=perm_p(dF, pF, r),
            )
            rows.append(row)
            w(
                f"{defname:<10} {'fixed':<12} {row['param']:<14} {70:4d} {r:+7.3f} "
                f"{row['close']:7.3f} {row['mae']:7.4f} {row['p']:7.4f}"
            )

        # offset c
        for c in range(0, 16):
            dFs, pFs = [], []
            for n, d, px, df in puzzles:
                m = n - c
                if m < 8:
                    continue
                dFs.append(df)
                pFs.append(lead_frac(leadfn(px, m)))
            if len(dFs) < 15:
                continue
            r = pearson(dFs, pFs)
            row = dict(
                definition=defname,
                family="offset",
                param=f"c={c}",
                n_used=len(dFs),
                r=r,
                close=close01(dFs, pFs),
                mae=mae(dFs, pFs),
                p=perm_p(dFs, pFs, r),
            )
            rows.append(row)
            w(
                f"{defname:<10} {'offset':<12} {row['param']:<14} {len(dFs):4d} {r:+7.3f} "
                f"{row['close']:7.3f} {row['mae']:7.4f} {row['p']:7.4f}"
            )

        # proportional
        for alpha in (0.5, 0.75, 1.0):
            pF = [
                lead_frac(leadfn(px, max(8, int(alpha * n))))
                for n, _, px, _ in puzzles
            ]
            r = pearson(dF, pF)
            row = dict(
                definition=defname,
                family="proportional",
                param=f"a={alpha}",
                n_used=70,
                r=r,
                close=close01(dF, pF),
                mae=mae(dF, pF),
                p=perm_p(dF, pF, r),
            )
            rows.append(row)
            w(
                f"{defname:<10} {'proportional':<12} {row['param']:<14} {70:4d} {r:+7.3f} "
                f"{row['close']:7.3f} {row['mae']:7.4f} {row['p']:7.4f}"
            )

        # ridge n>=m for m=20..60
        for m in range(20, 61):
            dFs, pFs = [], []
            for n, d, px, df in puzzles:
                if n < m:
                    continue
                dFs.append(df)
                pFs.append(lead_frac(leadfn(px, m)))
            if len(dFs) < 12:
                continue
            r = pearson(dFs, pFs)
            row = dict(
                definition=defname,
                family="ridge_n_ge_m",
                param=f"m={m}",
                n_used=len(dFs),
                r=r,
                close=close01(dFs, pFs),
                mae=mae(dFs, pFs),
                p=perm_p(dFs, pFs, r),
            )
            rows.append(row)

    w()
    w("=" * 88)
    w("TOP 12 BY |r| PER DEFINITION")
    w("=" * 88)
    for defname in ("def256", "defNative"):
        w(f"--- {defname} ---")
        sub = [r for r in rows if r["definition"] == defname]
        for r in sorted(sub, key=lambda x: abs(x["r"]), reverse=True)[:12]:
            w(
                f"  {r['family']:<14} {r['param']:<10} N={r['n_used']:<3} "
                f"r={r['r']:+.3f} close={r['close']:.3f} MAE={r['mae']:.4f} p={r['p']:.4f}"
            )

    # stability for defNative ridge
    w()
    w("=" * 88)
    w("RIDGE NEIGHBORHOOD (defNative, n>=m)")
    w("=" * 88)
    ridge = {
        int(r["param"].split("=")[1]): r
        for r in rows
        if r["definition"] == "defNative" and r["family"] == "ridge_n_ge_m"
    }
    for m in sorted(ridge):
        if m % 2:
            continue
        r = ridge[m]
        neigh = " ".join(
            f"{m+dm}:{ridge[m+dm]['r']:+.2f}"
            for dm in range(-2, 3)
            if m + dm in ridge
        )
        w(f"  m={m:2d} r={r['r']:+.3f} close={r['close']:.3f} p={r['p']:.3f} | {neigh}")

    # holdout defNative m=n
    w()
    w("=" * 88)
    w("HOLD-OUT defNative")
    w("=" * 88)
    for label, maker in [
        ("m=n", lambda n, px: lead_native(px, n)),
        ("m=64", lambda n, px: lead_native(px, 64)),
        ("m=48", lambda n, px: lead_native(px, 48)),
        ("m=floor(0.75n)", lambda n, px: lead_native(px, max(8, int(0.75 * n)))),
    ]:
        for split, subset in (("train1-50", [t for t in puzzles if t[0] <= 50]),
                              ("test51-70", [t for t in puzzles if t[0] >= 51])):
            dFs = [df for *_, df in subset]
            pFs = [lead_frac(maker(n, px)) for n, _, px, _ in subset]
            w(f"  {label:<16} {split}: r={pearson(dFs,pFs):+.3f} close={close01(dFs,pFs):.3f}")

    w()
    w("VERDICT:")
    w("  defNative m=n recovers ~0.61; def256 m=n is ~0.19.")
    w("  'How much lead' depends on WIDTH DEFINITION, not only m.")
    w("  Look for STABLE ridge under defNative; spikes under n>=m need hold-out.")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = ["definition", "family", "param", "n_used", "r", "close", "mae", "p"]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            wr.writerow(
                {
                    **{k: r[k] for k in ("definition", "family", "param", "n_used")},
                    "r": f"{r['r']:.6f}",
                    "close": f"{r['close']:.6f}",
                    "mae": f"{r['mae']:.6f}",
                    "p": f"{r['p']:.6f}",
                }
            )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
