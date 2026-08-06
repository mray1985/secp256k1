"""
SECP256k1 Band-Wrap Toolkit (single file)

What this script DOES (safely & mathematically):

1) Load secp256k1 parameters
2) Accept a known public key (Px, Py)
3) Verify the point is on the curve
4) Wrap a scalar IF you have it (optional)
5) Wrap a PUBLIC POINT using a chosen scale factor
6) Report bit-bands and sanity metrics

This does NOT:
- Guess private keys
- Perform discrete-log solving
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict

from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point


# =========================
# Curve globals
# =========================
curve = SECP256k1.curve
G = SECP256k1.generator
n = SECP256k1.order
p = curve.p()


# =========================
# Helpers / metrics
# =========================
def detect_band(N: int) -> int:
    """Return floor(log2(N)) = bit_length - 1"""
    if N <= 0:
        raise ValueError("detect_band expects N > 0")
    return N.bit_length() - 1


def bit_density(N: int) -> int:
    """Popcount (number of 1-bits)"""
    return bin(N).count("1")


def fmt(N: int) -> str:
    return f"{N:,}"


# =========================
# Scalar band-wrap (requires N)
# =========================
def band_wrap_scalar(N: int, target_exp: int) -> Tuple[int, int, int]:
    """
    Wrap scalar N into lower band near 2^target_exp

        s     = N >> target_exp
        s_inv = s^{-1} mod n
        Nw    = N * s_inv mod n
    """
    if N <= 0:
        raise ValueError("N must be positive")
    if target_exp < 0:
        raise ValueError("target_exp must be >= 0")

    s = N >> target_exp
    if s == 0:
        raise ValueError("Shift too large, s became 0")

    if s % n == 0:
        raise ValueError("s not invertible mod n")

    s_inv = pow(s, -1, n)
    Nw = (N * s_inv) % n

    if Nw == 0:
        raise ValueError("Wrapped scalar became 0")

    return Nw, s_inv, s


# =========================
# Point-only wrap (NO private key required)
# =========================
def wrap_point_with_scale(P: Point, s: int) -> Tuple[Point, int]:
    """
    Wrap a public key using chosen scale s:

        s_inv = s^{-1} mod n
        Pw    = s_inv * P
    """
    if s <= 0:
        raise ValueError("s must be positive")
    if s % n == 0:
        raise ValueError("s not invertible mod n")

    s_inv = pow(s, -1, n)
    Pw = s_inv * P
    return Pw, s_inv


# =========================
# Lift helper (optional)
# =========================
def lift_scalar(Nw: int, s: int) -> int:
    return (Nw * s) % n


# =========================
# MAIN
# =========================
def main():
    print("\nSECP256k1 Band-Wrap Toolkit\n")

    # ============================================================
    # PUZZLE 160 PUBLIC KEY (THIS IS WHERE Px, Py GO)
    # ============================================================
    Px = 101616124637840542991531253248586524020213215258338643076214814468447630501491
    Py = 88132823371574229813684435207239348220522140366126834573803505878170136640646

    P = Point(curve, Px, Py)

    # Sanity check
    if not curve.contains_point(P.x(), P.y()):
        raise ValueError("ERROR: Px,Py is NOT on secp256k1 curve")

    print("✔ Puzzle 160 public key loaded")
    print("Px =", Px)
    print("Py =", Py)
    print("Public key band (x): 2^", detect_band(Px))
    print("Public key band (y): 2^", detect_band(Py))

    # ============================================================
    # POINT-ONLY BAND WRAP (no private scalar used)
    # ============================================================
    target_exp = 2
    s = 1 << target_exp

    Pw, s_inv = wrap_point_with_scale(P, s)

    print("\n--- Point-only wrap ---")
    print("Target band: ~2^", target_exp)
    print("Scale s:", s)
    print("s_inv mod n:", s_inv)
    print("Wrapped Px:", Pw.x())
    print("Wrapped Py:", Pw.y())
    print("Wrapped band (x): 2^", detect_band(Pw.x()))
    print("Wrapped band (y): 2^", detect_band(Pw.y()))

    # ============================================================
    # OPTIONAL DEMO: scalar wrap (example only)
    # ============================================================
    print("\n--- Scalar demo (example only) ---")
    N_demo = (1 << 159) + 123456789
    Nw, s_inv_demo, s_demo = band_wrap_scalar(N_demo, 90)

    print("Original scalar band: 2^", detect_band(N_demo))
    print("Wrapped scalar band : 2^", detect_band(Nw))
    print("Lift check:",
          "OK" if lift_scalar(Nw, s_demo) == N_demo % n else "FAIL")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
