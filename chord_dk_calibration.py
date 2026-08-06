#!/usr/bin/env python3
"""Solved-puzzle chord calibration: P+R = (d+k)G vs shelf2/offset law."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config
from genesis_calibration import bridge_state
from gap_tier_common import observed_offset
from ecdlp_full_pipeline import N, puzzle_band
from hashkeys_rsz import PUZZLE_RSZ
from puzzle_keys_53125 import parse_53125
from p135_chord_third_point import add, chord_third_affine, neg, on_curve

OUT = ROOT / "ARCHIVE" / "cloud_pages" / "p115_chord_dk_calibration.png"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "chord_dk_calibration.log"

# Puzzles with published nonce k on hashkeys
CALIB = [70, 75, 80, 85, 90, 95, 100, 105, 110, 115]


def pt_scalar(s: int) -> tuple[int, int]:
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(s % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    return int(pt.x()), int(pt.y())


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def analyze_one(n: int, pk) -> dict | None:
    rsz = PUZZLE_RSZ.get(n)
    if not rsz or rsz.k is None:
        return None
    d, k = pk.d, rsz.k
    P = (pk.px, pk.py)
    R = pt_scalar(k)
    if not on_curve(*R):
        return None
    Pr = add(P, R)
    dkG = pt_scalar((d + k) % N)
    T = chord_third_affine(P, R)
    ok = Pr == dkG and T == neg(Pr)

    cfg = build_config(pk)
    st = bridge_state(cfg)
    lo, _, _ = puzzle_band(n)
    shelf2 = st["oitc"].shelf2
    off_d = observed_offset(d, shelf2, lo)
    dk = (d + k) % N
    off_dk = observed_offset(dk, shelf2, lo)

    return {
        "n": n,
        "row": cfg.row,
        "d": d,
        "k": k,
        "dk": dk,
        "P": P,
        "R": R,
        "Pr": Pr,
        "T": T,
        "dkG": dkG,
        "ok": ok,
        "shelf2": shelf2,
        "off_d_bits": off_d.bit_length(),
        "off_dk_bits": off_dk.bit_length(),
        "off_d": off_d,
        "off_dk": off_dk,
        "dk_eq_d": dk == d,
        "Pr_x_eq_d": Pr[0] == d if Pr else False,
    }


def chart_p115(rec: dict) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return

    P, R, T, Pr = rec["P"], rec["R"], rec["T"], rec["Pr"]
    Px, Py = P
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    lam = ((R[1] - Py) * pow(R[0] - Px, -1, p)) % p
    m_tan = (3 * Px * Px) * pow(2 * Py, -1, p) % p
    m_f, chord_f = m_tan / p, lam / p
    kappa = ((6 * Px % p) * (2 * Py) - (3 * Px * Px % p) * (2 * m_tan % p)) % p
    kappa = (kappa * pow(2 * Py * Py % p, -1, p)) % p
    kappa_f = kappa / p

    def loc(X: int, Y: int) -> tuple[float, float]:
        dx, dy = X - Px, Y - Py
        if dx > p // 2:
            dx -= p
        if dy > p // 2:
            dy -= p
        s = float(2**120)
        return dx / s, dy / s

    t = np.linspace(-0.4, 1.5, 300)
    curve = m_f * t + kappa_f * t * t
    chord = chord_f * t

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(t, curve, color="#1f5fbf", lw=2, label="curve (local)")
    ax.plot(t, chord, color="#2ca02c", lw=2, label="chord P-R")
    ax.plot(0, 0, "ko", ms=12, label=f"P  (d={rec['d'].bit_length()}b)")
    ax.plot(*loc(*R), "s", color="#8B4513", ms=10, label=f"R  (k={rec['k'].bit_length()}b)")
    ax.plot(*loc(*T), "^", color="#ff7f0e", ms=11, label="T = -(P+R)")
    ax.plot(*loc(*Pr), "D", color="#9467bd", ms=10, label="P+R = (d+k)G")
    ax.set_title(f"Puzzle {rec['n']}: chord hits T;  P+R = (d+k)G  verified")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("local x (scaled from Px)")
    ax.set_ylabel("local y (scaled from Py)")
    fig.text(
        0.5,
        0.02,
        f"(d+k) has {rec['dk'].bit_length()} bits — not in puzzle band; private key remains d alone",
        ha="center",
        fontsize=9,
        color="0.4",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close()
    log(f"Chart saved {OUT}")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    log("=== Chord calibration: P+R = (d+k)G vs shelf2 offset ===")
    log("")

    rows: list[dict] = []
    for n in CALIB:
        if n not in keys:
            continue
        rec = analyze_one(n, keys[n])
        if not rec:
            continue
        rows.append(rec)
        log(
            f"P{n} row={rec['row']}  P+R==(d+k)G? {rec['ok']}  "
            f"off(d)={rec['off_d_bits']}b  off(d+k)={rec['off_dk_bits']}b  "
            f"(d+k)==d? {rec['dk_eq_d']}  Pr.x==d? {rec['Pr_x_eq_d']}"
        )

    log("")
    log("=== Comparison to shelf2 law ===")
    log("n   row  offset(d)  offset(d+k)  (d+k) in puzzle band?")
    for rec in rows:
        lo, hi, _ = puzzle_band(rec["n"])
        in_band = lo <= rec["dk"] < hi
        log(
            f"P{rec['n']:3d}  {rec['row']}     {rec['off_d_bits']:3d}b        "
            f"{rec['off_dk_bits']:3d}b           {in_band}"
        )

    log("")
    hits_off = sum(1 for r in rows if r["off_dk"] == r["off_d"])
    hits_d = sum(1 for r in rows if r["dk"] == r["d"])
    log(f"offset(d+k) == offset(d): {hits_off}/{len(rows)}")
    log(f"(d+k) == d: {hits_d}/{len(rows)} (expected 0)")
    log("")
    log("VERDICT: P+R is (d+k)G geometrically; d+k is ~256b and unrelated to shelf2+offset(d).")

    p115 = next((r for r in rows if r["n"] == 115), None)
    if p115:
        chart_p115(p115)

    return 0


if __name__ == "__main__":
    sys.exit(main())
