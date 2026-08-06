#!/usr/bin/env python3
"""
Full-range study: how EC coordinates behave as |d - (-d)| = |2d - N| varies.

Not a singularity at N/2 — sample across the whole scalar circle.
"""
from __future__ import annotations

import hashlib
import statistics

from ecdsa import SECP256k1, SigningKey

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
HALF = N // 2


def pt(d: int) -> tuple[int, int]:
    d %= N
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    return int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")


def gap(d: int) -> int:
    return abs(2 * (d % N) - N)


def main() -> None:
    # Uniform sample over [1, N/2] — gap is symmetric, so half covers all widths
    # Use 512 points spaced evenly in scalar space
    M = 256
    rows: list[dict] = []

    print("=" * 80)
    print(f"FULL SWEEP: {M} scalars evenly spaced in [1, N/2]")
    print("gap = |2d - N|  (max at d~0, min at d~N/2)")
    print("=" * 80)

    for i in range(M):
        # d from ~N/(2M) up to N/2
        d = 1 + (HALF * i) // (M - 1)
        if d == 0:
            d = 1
        P = pt(d)
        Q = pt(N - d)
        g = gap(d)
        rows.append(
            {
                "d": d,
                "gap": g,
                "gap_frac": g / N,  # 1.0 = max width, ~0 = min
                "x": P[0],
                "y": P[1],
                "x_bits": P[0].bit_length(),
                "x_same": P[0] == Q[0],
                "y_flip": (P[1] + Q[1]) % p == 0,
                "y_parity": P[1] % 2,
                # how "close" are the two points as affine coords?
                # x-distance is always 0; y-distance is |2y| or min(y, p-y)*2 style
                "y_chord": min(P[1], p - P[1]),  # distance of y from 0 or p (near axis)
            }
        )

    # Invariants across ALL samples
    all_x_same = all(r["x_same"] for r in rows)
    all_y_flip = all(r["y_flip"] for r in rows)
    print(f"Invariant x(d)==x(-d) for all {M}: {all_x_same}")
    print(f"Invariant y(-d)==-y(d) for all {M}: {all_y_flip}")
    print()

    # Bucket by gap fraction (width classes)
    buckets = [
        ("gap 0.9-1.0 (widest)", 0.9, 1.01),
        ("gap 0.7-0.9", 0.7, 0.9),
        ("gap 0.5-0.7", 0.5, 0.7),
        ("gap 0.3-0.5", 0.3, 0.5),
        ("gap 0.1-0.3", 0.1, 0.3),
        ("gap 0.01-0.1", 0.01, 0.1),
        ("gap 0-0.01 (narrowest)", 0.0, 0.01),
    ]

    print(f"{'bucket':<28} {'n':>4} {'mean_xbits':>10} {'std_xbits':>10} {'mean_ychord_bits':>16}")
    print("-" * 80)
    for name, lo, hi in buckets:
        sub = [r for r in rows if lo <= r["gap_frac"] < hi]
        if not sub:
            print(f"{name:<28} {0:4d}")
            continue
        xb = [r["x_bits"] for r in sub]
        yb = [r["y_chord"].bit_length() for r in sub]
        print(
            f"{name:<28} {len(sub):4d} {statistics.mean(xb):10.2f} "
            f"{statistics.pstdev(xb) if len(sub)>1 else 0:10.2f} {statistics.mean(yb):16.2f}"
        )

    print()
    print("=" * 80)
    print("CORRELATION: gap_frac vs x_bits / y_chord (Pearson-ish via ranks)")
    print("=" * 80)
    # simple correlation
    def corr(xs: list[float], ys: list[float]) -> float:
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        denx = sum((a - mx) ** 2 for a in xs) ** 0.5
        deny = sum((b - my) ** 2 for b in ys) ** 0.5
        return num / (denx * deny) if denx and deny else 0.0

    gf = [r["gap_frac"] for r in rows]
    xb = [float(r["x_bits"]) for r in rows]
    yc = [float(r["y_chord"].bit_length()) for r in rows]
    xf = [r["x"] / p for r in rows]  # x as fraction of field
    print(f"  corr(gap_frac, x_bits)     = {corr(gf, xb):+.4f}")
    print(f"  corr(gap_frac, x/p)        = {corr(gf, xf):+.4f}")
    print(f"  corr(gap_frac, y_chord_bits)= {corr(gf, yc):+.4f}")
    print("  (near 0 => no linear relationship across the full range)")

    print()
    print("=" * 80)
    print("POINT PAIR GEOMETRY (always, every d)")
    print("=" * 80)
    print("  P  = d·G  = (x,  y)")
    print("  P' = (-d)·G = (x, -y)")
    print("  Euclidean chord length in affine plane ~ |2y| (same x)")
    print("  As |y|->0, chord shrinks — but that is y near 0, NOT d near N/2")
    print()

    # When does y-chord get small? Independent of gap?
    small_y = sorted(rows, key=lambda r: r["y_chord"])[:10]
    print("10 smallest y-chords (points nearest x-axis):")
    print(f"  {'gap_frac':>10} {'y_chord_bits':>14} {'x_bits':>8}")
    for r in small_y:
        print(f"  {r['gap_frac']:10.6f} {r['y_chord'].bit_length():14d} {r['x_bits']:8d}")

    print()
    print("=" * 80)
    print("COORDINATE ± PAIRS (your 134 screenshots) across objects")
    print("=" * 80)
    objs = {
        "Px3": 9210836494447108270027136741376870869791784014198948301625976867708124077590,
        "Px2": 54715131853151445691733189261594605794679177894602772031317532630299444965014,
        "Px1": 51866120889717641461810659005716431188799022756838843706514074509901265629059,
        "rx3": 26000218878731561428273279366182192513989009817816850365013828370091835863739,
        "rx2": 90653255469745952335985143920649543885181555095025199315947044135806663628368,
        "rx1": 114930704126154877082883546730544079307369404418439078397954295509919169851219,
        "Gx3": 85340279321737800624759429340272274763154997815782306132637707972559913914315,
        "Gx2": 55066263022277343669578718895168534326250603453777594175500187360389116729240,
        "Gx1": 91177636130617246552803821781935006617134368061721227770777272682868638699771,
        "Nr1": 4295241207732992648834070171909958737418321088245693014740872866482121928576,
        "Nr2": 20843592559837250438751770916128405230237688095804012051917246139229375937393,
    }
    print(f"  {'obj':<6} {'v_bits':>7} {'|2v-N|/N':>10} {'width':>8}")
    for name, v in objs.items():
        v %= N
        g = abs(2 * v - N)
        frac = g / N
        width = "narrow" if frac < 0.1 else ("mid" if frac < 0.5 else "wide")
        print(f"  {name:<6} {v.bit_length():7d} {frac:10.6f} {width:>8}")

    print()
    print("=" * 80)
    print("CONCLUSION (full range, not singularity)")
    print("=" * 80)
    print("1. For EVERY d: x(d)=x(-d), y flips. No exception in the sweep.")
    print("2. Scalar gap |2d-N| runs full range 0..N; x_bits stays ~256 everywhere.")
    print("3. No correlation: gap width does not drive x size or y-chord.")
    print("4. Points get 'closer' in the plane only when y~0 (near x-axis),")
    print("   which is independent of d being near N/2.")
    print("5. Your 134 pairs {v,-v} are residue sign-pairs; their widths vary")
    print("   by object, but that is not private-key d/-d geometry.")


if __name__ == "__main__":
    main()
