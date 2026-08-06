#!/usr/bin/env python3
"""Factoradic of public coords truncated to n bits vs private d ladder."""
from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_TRUNC_PUB_PRIV.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_trunc_pub_priv.csv")

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F


def to_factoradic(n: int) -> list[int]:
    n = abs(int(n))
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def lead_info(digs: list[int]) -> tuple[int, int, float, int]:
    if not digs:
        return 0, 0, 0.0, 0
    mk = len(digs) - 1
    a = digs[mk]
    return mk, a, (a / mk if mk else 1.0), sum(1 for x in digs if x)


def pub_xy(d: int) -> tuple[int, int]:
    sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    return int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def trunc(val: int, bits: int) -> int:
    if bits <= 0:
        return 0
    return val & ((1 << bits) - 1)


def main() -> None:
    puzzles: list[tuple[int, int]] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            if n > 70:
                continue
            puzzles.append((n, d))

    rows = []
    for n, d in puzzles:
        px, py = pub_xy(d)
        lower = d - (1 << (n - 1))
        # same bit-width as puzzle band
        variants = {
            "d": d,
            "lower": lower if lower > 0 else 0,
            "Px_mod_2n": trunc(px, n),
            "Py_mod_2n": trunc(py, n),
            "Px_mod_2nm1": trunc(px, n - 1),  # same width as lower bits
            "Py_mod_2nm1": trunc(py, n - 1),
            "Px_hi_n": px >> (px.bit_length() - n) if px.bit_length() >= n else px,
            "Py_hi_n": py >> (py.bit_length() - n) if py.bit_length() >= n else py,
            "Px_mod_N_lo_n": trunc(px % N, n),
            "map_p_to_n_Px_lo": trunc((N * px) // p, n),
        }
        info = {"n": n}
        for name, val in variants.items():
            mk, a, frac, nnz = lead_info(to_factoradic(val))
            info[name] = {
                "val": val,
                "bits": val.bit_length() if val else 0,
                "max_k": mk,
                "lead_a": a,
                "frac": frac,
                "nnz": nnz,
            }
        rows.append(info)

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("TRUNCATED PUBLIC COORDS vs d  (same bit-width as puzzle n)")
    w("=" * 88)
    w()
    w("Px_mod_2n = Px & (2^n - 1)     low n bits of pubkey x")
    w("Px_hi_n   = top n bits of Px   high slice")
    w("lower     = d - 2^(n-1)        private payload")
    w()

    w(
        f"{'n':>3} {'d_k':>4} {'d_f':>5} {'PxLo_k':>6} {'PxLo_f':>6} "
        f"{'PxHi_k':>6} {'PxHi_f':>6} {'low_k':>5} {'low_f':>5}"
    )
    w("-" * 88)
    for r in rows:
        w(
            f"{r['n']:3d} {r['d']['max_k']:4d} {r['d']['frac']:5.2f} "
            f"{r['Px_mod_2n']['max_k']:6d} {r['Px_mod_2n']['frac']:6.2f} "
            f"{r['Px_hi_n']['max_k']:6d} {r['Px_hi_n']['frac']:6.2f} "
            f"{r['lower']['max_k']:5d} {r['lower']['frac']:5.2f}"
        )

    w()
    w("=" * 88)
    w("CORRELATIONS")
    w("=" * 88)

    def col(key: str, field: str) -> list[float]:
        return [float(r[key][field]) for r in rows]

    pairs = [
        ("d", "Px_mod_2n", "max_k"),
        ("d", "Px_mod_2n", "frac"),
        ("d", "Px_hi_n", "max_k"),
        ("d", "Px_hi_n", "frac"),
        ("d", "Py_mod_2n", "frac"),
        ("lower", "Px_mod_2n", "max_k"),
        ("lower", "Px_mod_2n", "frac"),
        ("lower", "Px_mod_2nm1", "frac"),
        ("lower", "Px_hi_n", "frac"),
        ("lower", "Py_mod_2nm1", "frac"),
        ("lower", "map_p_to_n_Px_lo", "frac"),
        ("d", "Px_mod_N_lo_n", "frac"),
        ("d", "Py_mod_2n", "max_k"),
    ]
    for a, b, field in pairs:
        c = pearson(col(a, field), col(b, field))
        w(f"  corr({a}.{field:6s}, {b}.{field:6s}) = {c:+.3f}")

    # also corr with n
    ns = [float(r["n"]) for r in rows]
    w(f"  corr(d.max_k     , n           ) = {pearson(col('d','max_k'), ns):+.3f}")
    w(f"  corr(PxLo.max_k  , n           ) = {pearson(col('Px_mod_2n','max_k'), ns):+.3f}")
    w(f"  corr(PxHi.max_k  , n           ) = {pearson(col('Px_hi_n','max_k'), ns):+.3f}")

    w()
    w("=" * 88)
    w("SAME-SCALE COINCIDENCE")
    w("=" * 88)
    same_k_lo = sum(1 for r in rows if r["d"]["max_k"] == r["Px_mod_2n"]["max_k"])
    same_k_hi = sum(1 for r in rows if r["d"]["max_k"] == r["Px_hi_n"]["max_k"])
    same_k_low_payload = sum(
        1 for r in rows if r["lower"]["max_k"] == r["Px_mod_2nm1"]["max_k"]
    )
    close_frac_lo = sum(
        1 for r in rows if abs(r["d"]["frac"] - r["Px_mod_2n"]["frac"]) < 0.1
    )
    close_frac_hi = sum(
        1 for r in rows if abs(r["d"]["frac"] - r["Px_hi_n"]["frac"]) < 0.1
    )
    close_frac_payload = sum(
        1 for r in rows if abs(r["lower"]["frac"] - r["Px_mod_2nm1"]["frac"]) < 0.1
    )
    exact_lo = sum(1 for r in rows if r["d"]["val"] == r["Px_mod_2n"]["val"])
    exact_hi = sum(1 for r in rows if r["d"]["val"] == r["Px_hi_n"]["val"])
    exact_payload = sum(
        1 for r in rows if r["lower"]["val"] == r["Px_mod_2nm1"]["val"]
    )

    w(f"  d.max_k == Px_lo_n.max_k:           {same_k_lo}/{len(rows)}")
    w(f"  d.max_k == Px_hi_n.max_k:           {same_k_hi}/{len(rows)}")
    w(f"  lower.max_k == Px_lo_(n-1).max_k:   {same_k_low_payload}/{len(rows)}")
    w(f"  |d.frac - Px_lo.frac|<0.1:          {close_frac_lo}/{len(rows)}")
    w(f"  |d.frac - Px_hi.frac|<0.1:          {close_frac_hi}/{len(rows)}")
    w(f"  |lower.frac - Px_lo_(n-1).frac|<0.1:{close_frac_payload}/{len(rows)}")
    w(f"  d == Px_lo_n (exact):               {exact_lo}/{len(rows)}")
    w(f"  d == Px_hi_n (exact):               {exact_hi}/{len(rows)}")
    w(f"  lower == Px_lo_(n-1) (exact):       {exact_payload}/{len(rows)}")

    # leading frac bars side by side for a few
    w()
    w("=" * 88)
    w("SIDEWAYS: d.frac vs Px_lo.frac vs Px_hi.frac  (# = position)")
    w("=" * 88)
    for r in rows:
        def bar(frac: float) -> str:
            width = 20
            pos = min(width, int(round(frac * width)))
            return "." * pos + "#" + "." * (width - pos)

        w(
            f"{r['n']:3d} d|{bar(r['d']['frac'])}| "
            f"lo|{bar(r['Px_mod_2n']['frac'])}| "
            f"hi|{bar(r['Px_hi_n']['frac'])}| "
            f"pay|{bar(r['lower']['frac'])}|"
        )

    w()
    w("=" * 88)
    w("READOUT")
    w("=" * 88)
    w("  Truncation forces Px/Py onto the same bit-width as d.")
    w("  If a structural link existed, lead_frac / max_k would correlate.")
    w("  Check the corr table and coincidence counts above.")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "puzzle",
            "d_max_k",
            "d_frac",
            "lower_max_k",
            "lower_frac",
            "Px_lo_max_k",
            "Px_lo_frac",
            "Px_hi_max_k",
            "Px_hi_frac",
            "Py_lo_frac",
            "Px_lo_nm1_frac",
            "map_lo_frac",
        ]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            wr.writerow(
                {
                    "puzzle": r["n"],
                    "d_max_k": r["d"]["max_k"],
                    "d_frac": f"{r['d']['frac']:.6f}",
                    "lower_max_k": r["lower"]["max_k"],
                    "lower_frac": f"{r['lower']['frac']:.6f}",
                    "Px_lo_max_k": r["Px_mod_2n"]["max_k"],
                    "Px_lo_frac": f"{r['Px_mod_2n']['frac']:.6f}",
                    "Px_hi_max_k": r["Px_hi_n"]["max_k"],
                    "Px_hi_frac": f"{r['Px_hi_n']['frac']:.6f}",
                    "Py_lo_frac": f"{r['Py_mod_2n']['frac']:.6f}",
                    "Px_lo_nm1_frac": f"{r['Px_mod_2nm1']['frac']:.6f}",
                    "map_lo_frac": f"{r['map_p_to_n_Px_lo']['frac']:.6f}",
                }
            )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
