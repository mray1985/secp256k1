#!/usr/bin/env python3
"""Correlate factoradic of public coordinates (Px, Py) with factoradic of d."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_PUB_PRIV_CORRELATION.txt")
CSV_OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\factoradic_pub_priv.csv")

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


def lead_info(digs: list[int]) -> tuple[int, int, float]:
    if not digs:
        return 0, 0, 0.0
    mk = len(digs) - 1
    a = digs[mk]
    return mk, a, (a / mk if mk else 1.0)


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
        objs = {
            "d": d,
            "lower": lower if lower > 0 else 0,
            "Px": px,
            "Py": py,
            "negPy": (p - py) % p,
            "Px_mod_N": px % N,
            "Py_mod_N": py % N,
        }
        info = {}
        for name, val in objs.items():
            digs = to_factoradic(val)
            mk, a, frac = lead_info(digs)
            info[name] = {
                "val": val,
                "bits": val.bit_length() if val else 0,
                "max_k": mk,
                "lead_a": a,
                "lead_frac": frac,
                "nnz": sum(1 for x in digs if x),
                "digs": digs,
            }
        rows.append((n, info))

    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    w("=" * 88)
    w("FACTORADIC: private d  vs  public (Px, Py)   puzzles 1-70")
    w("=" * 88)
    w()
    w("For each puzzle: expand d and pubkey coords in factoradic, compare structure.")
    w()

    # Table
    w(f"{'n':>3} {'d_k':>4} {'d_f':>5} {'Px_k':>5} {'Px_f':>5} {'Py_k':>5} {'Py_f':>5} {'dk-Pxk':>7}")
    w("-" * 88)
    for n, info in rows:
        w(
            f"{n:3d} {info['d']['max_k']:4d} {info['d']['lead_frac']:5.2f} "
            f"{info['Px']['max_k']:5d} {info['Px']['lead_frac']:5.2f} "
            f"{info['Py']['max_k']:5d} {info['Py']['lead_frac']:5.2f} "
            f"{info['d']['max_k']-info['Px']['max_k']:7d}"
        )

    # Correlations
    w()
    w("=" * 88)
    w("CORRELATIONS (Pearson) across puzzles 1-70")
    w("=" * 88)
    series = {
        "d.max_k": [r[1]["d"]["max_k"] for r in rows],
        "d.frac": [r[1]["d"]["lead_frac"] for r in rows],
        "d.nnz": [r[1]["d"]["nnz"] for r in rows],
        "lower.max_k": [r[1]["lower"]["max_k"] for r in rows],
        "lower.frac": [r[1]["lower"]["lead_frac"] for r in rows],
        "Px.max_k": [r[1]["Px"]["max_k"] for r in rows],
        "Px.frac": [r[1]["Px"]["lead_frac"] for r in rows],
        "Px.nnz": [r[1]["Px"]["nnz"] for r in rows],
        "Py.max_k": [r[1]["Py"]["max_k"] for r in rows],
        "Py.frac": [r[1]["Py"]["lead_frac"] for r in rows],
        "PxN.max_k": [r[1]["Px_mod_N"]["max_k"] for r in rows],
        "PxN.frac": [r[1]["Px_mod_N"]["lead_frac"] for r in rows],
        "n": [r[0] for r in rows],
        "d.bits": [r[1]["d"]["bits"] for r in rows],
        "Px.bits": [r[1]["Px"]["bits"] for r in rows],
    }

    pairs = [
        ("d.max_k", "Px.max_k"),
        ("d.max_k", "Py.max_k"),
        ("d.frac", "Px.frac"),
        ("d.frac", "Py.frac"),
        ("d.nnz", "Px.nnz"),
        ("lower.frac", "Px.frac"),
        ("lower.max_k", "Px.max_k"),
        ("d.max_k", "n"),
        ("Px.max_k", "n"),
        ("Px.max_k", "Px.bits"),
        ("d.max_k", "d.bits"),
        ("d.frac", "PxN.frac"),
        ("Px.frac", "Py.frac"),
    ]
    for a, b in pairs:
        c = pearson(series[a], series[b])
        w(f"  corr({a:12s}, {b:12s}) = {c:+.3f}")

    # Digit overlap: same leading k?
    w()
    w("=" * 88)
    w("COINCIDENCE CHECKS")
    w("=" * 88)
    same_k = sum(1 for _, info in rows if info["d"]["max_k"] == info["Px"]["max_k"])
    same_frac_bin = sum(
        1
        for _, info in rows
        if abs(info["d"]["lead_frac"] - info["Px"]["lead_frac"]) < 0.1
    )
    w(f"  d.max_k == Px.max_k:     {same_k}/{len(rows)}")
    w(f"  |d.frac - Px.frac|<0.1:  {same_frac_bin}/{len(rows)}")

    # Px max_k is almost always ~58-59 for full-size field elements
    from collections import Counter

    px_ks = Counter(info["Px"]["max_k"] for _, info in rows)
    w(f"  Px.max_k distribution: {dict(sorted(px_ks.items()))}")
    py_ks = Counter(info["Py"]["max_k"] for _, info in rows)
    w(f"  Py.max_k distribution: {dict(sorted(py_ks.items()))}")

    # Framework fixed coords
    w()
    w("=" * 88)
    w("FRAMEWORK PUBLIC COORDS (Complexity_Simplified) factoradic")
    w("=" * 88)
    framework = {
        "Gx2": 55066263022277343669578718895168534326250603453777594175500187360389116729240,
        "Px3": 9210836494447108270027136741376870869791784014198948301625976867708124077590,
        "rx2": 90653255469745952335985143920649543885181555095025199315947044135806663628368,
        "Nr1": 4295241207732992648834070171909958737418321088245693014740872866482121928576,
        "omega2": 37718080363155996902926221483475020450927657555482586988616620542887997980018,
        "beta": 55594575648329892869085402983802832744385952214688224221778511981742606582254,
    }
    for name, val in framework.items():
        mk, a, frac = lead_info(to_factoradic(val))
        w(f"  {name:8s} bits={val.bit_length():3d}  max_k={mk:3d}  lead={a}*{mk}!  frac={frac:.3f}")

    w()
    w("=" * 88)
    w("READOUT")
    w("=" * 88)
    w("  Px/Py are ~256-bit field elements -> their max_k sits near ~58-59 always.")
    w("  d is n-bit -> max_k climbs with n (the sawtooth ladder).")
    w("  So d.max_k and Px.max_k are NOT the same song: one grows, one is flat.")
    w("  lead_frac(d) vs lead_frac(Px) correlation should be weak if independent.")
    w("  Strong corr(d.max_k, n) and corr(Px.max_k, Px.bits)~flat is the expected split:")
    w("    private scale ladder  vs  public full-field factorial height.")

    # CSV
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "puzzle",
            "d_max_k",
            "d_lead_frac",
            "d_nnz",
            "lower_max_k",
            "lower_lead_frac",
            "Px_max_k",
            "Px_lead_frac",
            "Px_nnz",
            "Py_max_k",
            "Py_lead_frac",
            "Px_bits",
            "Py_bits",
        ]
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for n, info in rows:
            wr.writerow(
                {
                    "puzzle": n,
                    "d_max_k": info["d"]["max_k"],
                    "d_lead_frac": f"{info['d']['lead_frac']:.6f}",
                    "d_nnz": info["d"]["nnz"],
                    "lower_max_k": info["lower"]["max_k"],
                    "lower_lead_frac": f"{info['lower']['lead_frac']:.6f}",
                    "Px_max_k": info["Px"]["max_k"],
                    "Px_lead_frac": f"{info['Px']['lead_frac']:.6f}",
                    "Px_nnz": info["Px"]["nnz"],
                    "Py_max_k": info["Py"]["max_k"],
                    "Py_lead_frac": f"{info['Py']['lead_frac']:.6f}",
                    "Px_bits": info["Px"]["bits"],
                    "Py_bits": info["Py"]["bits"],
                }
            )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    w()
    w(f"Wrote {OUT}")
    w(f"Wrote {CSV_OUT}")


if __name__ == "__main__":
    main()
