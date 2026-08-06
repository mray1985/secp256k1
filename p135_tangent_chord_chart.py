#!/usr/bin/env python3
"""
P135 local chart: Taylor zoom at P (tangent ∩ curve) + chord slope + Λ_p residues.

Raw integer Δx steps mod p jump at dx=1 (255-bit), so the geometric zoom uses
the second-order local expansion at P; bar chart uses true secp256k1 slopes.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "cloud_pages" / "p135_tangent_chord_zoom.png"

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
Rx = 26000218878731561428273279366182192513989009817816850365013828370091835863739
Ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644


def main() -> int:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("pip install matplotlib numpy")
        return 1

    m = (3 * pow(Px, 2, p) * pow(2 * Py, -1, p)) % p
    chord = ((Ry - Py) * pow(Rx - Px, -1, p)) % p
    lam_p = (Px * pow(Rx, -1, p)) % p

    # Second-order local shape at P: Δy ≈ m·Δx + κ·Δx²  (then scale for plot)
    # κ from implicit differentiation on y² = x³ + 7
    fpp = (6 * Px) % p
    ypp_num = (fpp * (2 * Py) - (3 * Px * Px % p) * (2 * m % p)) % p
    kappa = (ypp_num * pow(2 * Py * Py % p, -1, p)) % p
    kappa_f = kappa / p
    m_f = m / p
    chord_f = chord / p

    # Formal parameter t ∈ [-1,1] ↔ infinitesimal Δx
    t = np.linspace(-1.0, 1.0, 300)
    curve_local = m_f * t + kappa_f * t * t
    tangent_local = m_f * t
    chord_local = chord_f * t

    fig = plt.figure(figsize=(12, 6))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.35, wspace=0.25)

    ax_wide = fig.add_subplot(gs[0, 0])
    ax_zoom = fig.add_subplot(gs[0, 1])
    ax_bar = fig.add_subplot(gs[1, :])

    for ax, lo, hi, title in [
        (ax_wide, -1.0, 1.0, "Local chart at P135 (Taylor parameter t)"),
        (ax_zoom, -0.12, 0.12, "Zoom: tangent ∩ curve at P"),
    ]:
        mask = (t >= lo) & (t <= hi)
        tt = t[mask]
        ax.plot(tt, curve_local[mask], color="#1f5fbf", lw=2.5, label="curve (2nd order)")
        ax.plot(tt, tangent_local[mask], color="#d62728", lw=2, label="tangent")
        ax.plot(tt, chord_local[mask], color="#2ca02c", ls="--", lw=2, label="chord P→R")
        ax.plot(0, 0, "ko", ms=10, zorder=5)
        ax.axhline(0, color="0.85", lw=0.5)
        ax.axvline(0, color="0.85", lw=0.5)
        ax.set_xlabel("local parameter t  (proportional to uniformizer)")
        ax.set_ylabel("Δy  (scaled local coords)")
        ax.set_title(title)
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.25)

    ax_zoom.annotate(
        "order-1 contact\n(Silverman l/l′)",
        xy=(0, 0),
        xytext=(0.04, max(tangent_local[t <= 0.12]) * 0.4),
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color="0.35"),
    )

    ax_wide.text(
        0.02,
        0.97,
        "Note: integer Δx=1 already wraps mod p (255-bit jump).\n"
        "Zoom is in formal/local parameter, not raw coordinate steps.",
        transform=ax_wide.transAxes,
        va="top",
        fontsize=7.5,
        bbox=dict(boxstyle="round", facecolor="#fff8dc", alpha=0.9),
    )

    mod = 1 << 20
    names = ["tangent m", "chord P→R", "Λ_p = Px/rx"]
    vals = [m % mod, chord % mod, lam_p % mod]
    colors = ["#d62728", "#2ca02c", "#1f5fbf"]
    bars = ax_bar.bar(names, vals, color=colors, edgecolor="k", lw=0.5)
    ax_bar.set_ylabel(f"residue mod 2^20")
    ax_bar.set_title("True secp256k1 slopes — three distinct values (no intersection at this scale)")
    for bar, v in zip(bars, vals):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, v, f"{v:,}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("P135: zoom where tangent meets curve", fontsize=13, y=1.01)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Saved {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
