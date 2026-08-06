#!/usr/bin/env python3
"""
Chord P -> R on secp256k1: third curve intersection and group-law point P+R.

Line through P and R meets the curve at {P, R, T} with T = -(P+R) in affine coords.
Reflect T over x-axis to get P+R (EC group law).

Charts + scalar-frame check: m = d*k^-1 mod N when k known (solved puzzles).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "cloud_pages" / "p135_chord_third_point.png"
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_chord_third_point.log"

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
a, b = 0, 7

Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
Rx = 26000218878731561428273279366182192513989009817816850365013828370091835863739
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644

INF = None  # point at infinity


def inv(x: int, mod: int = p) -> int:
    return pow(x, -1, mod)


def on_curve(x: int, y: int) -> bool:
    return (pow(y, 2, p) - pow(x, 3, p) - 7) % p == 0


def neg(P: tuple[int, int] | None) -> tuple[int, int] | None:
    if P is None:
        return None
    x, y = P
    return (x, (-y) % p)


def add(P: tuple[int, int] | None, Q: tuple[int, int] | None) -> tuple[int, int] | None:
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return None
        # tangent doubling
        lam = (3 * x1 * x1 + a) * inv(2 * y1) % p
    else:
        lam = (y2 - y1) * inv(x2 - x1) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def chord_third_affine(P: tuple[int, int], Q: tuple[int, int]) -> tuple[int, int]:
    """Third intersection of line PQ with curve (before y-reflection). T with P+Q = -T."""
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        raise ValueError("vertical chord")
    lam = (y2 - y1) * inv(x2 - x1) % p
    # y = lam*(x - x1) + y1  =>  y^2 = x^3 + 7
    # third root x3 = lam^2 - x1 - x2
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x3 - x1) + y1) % p
    return (x3, y3)


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def ec_scalar_base(x: int, y: int) -> bool:
    try:
        from ecdsa import SECP256k1, SigningKey
    except ImportError:
        return False
    for d in range(1, 4):  # not used
        pass
    return True


def verify_point(label: str, d: int, ex: int, ey: int) -> bool:
    try:
        from ecdsa import SECP256k1, SigningKey

        sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1)
        pub = sk.get_verifying_key().to_string()
        px = int.from_bytes(pub[1:33], "big")
        py = int.from_bytes(pub[33:65], "big")
        ok = px == ex and py == ey
        log(f"  {label}: d*G match? {ok}")
        return ok
    except ImportError:
        log(f"  {label}: (no ecdsa)")
        return False


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    P = (Px, Py)
    R = (Rx, Ry)
    assert on_curve(*P) and on_curve(*R)

    T = chord_third_affine(P, R)
    PplusR = add(P, R)
    T_expected = neg(PplusR) if PplusR else None

    log("=== Chord P -> R: third intersection + P+R ===")
    log(f"P  = ({Px}, ...)")
    log(f"R  = ({Rx}, ...)")
    log(f"T  = third intersection on chord (affine) = ({T[0]}, {T[1]})")
    log(f"P+R = {PplusR}")
    log(f"-(P+R) == T? {T_expected == T}")
    log(f"T on curve? {on_curve(*T)}")
    if PplusR:
        log(f"P+R on curve? {on_curve(*PplusR)}")
        log(f"P+R x bits = {PplusR[0].bit_length()}")

    lam_chord = (Ry - Py) * inv(Rx - Px) % p
    log(f"chord slope = {lam_chord} ({lam_chord.bit_length()} bits)")
    log("")

    # Chart: project to 2D using local coords from P for curve patch + chord + points
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        log("matplotlib missing")
        return 0

    m_tan = (3 * Px * Px) * inv(2 * Py) % p
    m_f = m_tan / p
    chord_f = lam_chord / p
    fpp = (6 * Px) % p
    kappa = (fpp * (2 * Py) - (3 * Px * Px % p) * (2 * m_tan % p)) % p
    kappa = (kappa * inv(2 * Py * Py % p)) % p
    kappa_f = kappa / p

    def to_local(X: int, Y: int) -> tuple[float, float]:
        dx = X - Px
        if dx > p // 2:
            dx -= p
        dy = Y - Py
        if dy > p // 2:
            dy -= p
        # normalize for display
        scale = float(2**125)
        return dx / scale, dy / scale

    t = np.linspace(-0.5, 1.8, 400)
    curve_y = m_f * t + kappa_f * t * t
    chord_y = chord_f * t

    p_loc = (0.0, 0.0)
    r_loc = to_local(Rx, Ry)
    t_loc = to_local(T[0], T[1])
    s_loc = to_local(PplusR[0], PplusR[1]) if PplusR else (float("nan"), float("nan"))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    for ax, xlim, title in [
        (axes[0], (-0.15, 0.35), "Chord P→R through third point T = -(P+R)"),
        (axes[1], (-0.02, 0.02), "Zoom at P"),
    ]:
        mask = (t >= xlim[0]) & (t <= xlim[1])
        tt = t[mask]
        ax.plot(tt, curve_y[mask], color="#1f5fbf", lw=2, label="curve (local)")
        ax.plot(tt, chord_y[mask], color="#2ca02c", lw=2, label="chord P–R")
        ax.plot(*p_loc, "ko", ms=12, label="P", zorder=5)
        ax.plot(*r_loc, "s", color="#8B4513", ms=9, label="R", zorder=5)
        ax.plot(*t_loc, "^", color="#ff7f0e", ms=11, label="T = 3rd hit", zorder=5)
        if PplusR:
            ax.plot(*s_loc, "D", color="#9467bd", ms=9, label="P+R", zorder=5)
        ax.axhline(0, color="0.85", lw=0.5)
        ax.axvline(0, color="0.85", lw=0.5)
        ax.set_xlabel("local x (scaled Δ from Px)")
        ax.set_ylabel("local y (scaled Δ from Py)")
        ax.set_title(title)
        ax.legend(fontsize=7, loc="upper left")
        ax.grid(True, alpha=0.25)

    fig.suptitle("P135: chord intersection → group law  P + R = −T", fontsize=12, y=1.02)
    fig.text(
        0.5,
        0.01,
        "ECDSA: P = d·G, R = k·G  ⇒  P+R = (d+k)·G  (not d). Third point T is geometric; key still needs discrete log.",
        ha="center",
        fontsize=9,
        color="0.35",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160, bbox_inches="tight")
    plt.close()
    log(f"Chart saved {OUT}")

    # P135 band check: is (P+R).x related to d? no without knowing d+k
    lo, hi = 2**134, 2**135
    if PplusR:
        dx, dy = PplusR
        in_band = lo <= dx < hi
        log(f"(P+R).x in puzzle band? {in_band}  bits={dx.bit_length()}")
        verify_point("test d=(P+R).x", dx, Px, Py)  # expect false

    log("")
    log("=== Meaning ===")
    log("Chord through P and R hits curve again at T; reflect T over x-axis -> P+R.")
    log("This is the group law, not the private key. d satisfies d·G=P, not (P+R).x=d.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
