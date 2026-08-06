"""
SECP256k1 Band-Wrap Toolkit (single-file)

What this gives you in ONE script:
1) Wrap a scalar N from a high band down to a target band (e.g., 2^159 -> ~2^79)
2) Apply the exact same wrap to a public key point P = N*G
3) Detect / report bands (bit-length minus 1)
4) Batch wrap + basic clustering stats
5) Lift a wrapped scalar back up using the original scale factor
6) Bit-density (popcount) + quick sanity checks

Install:
    pip install ecdsa

Run:
    python band_wrap_toolkit.py
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point


# =========================
# Curve globals
# =========================
curve = SECP256k1.curve
G = SECP256k1.generator
n = SECP256k1.order


# =========================
# Helpers / metrics
# =========================
def detect_band(N: int) -> int:
    """Return band index ~ floor(log2(N)) for N>0 (i.e., bit_length-1)."""
    if N <= 0:
        raise ValueError("detect_band expects N > 0")
    return N.bit_length() - 1


def bit_density(N: int) -> int:
    """Count of 1-bits in N (popcount)."""
    if N < 0:
        raise ValueError("bit_density expects N >= 0")
    return bin(N).count("1")


def fmt_int(N: int, group: int = 3) -> str:
    """Human-friendly comma formatting for big ints."""
    return f"{N:,}"


# =========================
# Core band-wrap logic
# =========================
@dataclass
class WrapResult:
    original_scalar: int
    wrapped_scalar: int
    target_exp: int
    scale_s: int
    scale_inv: int
    original_band: int
    wrapped_band: int
    original_density: int
    wrapped_density: int


def band_wrap_scalar(N: int, target_exp: int) -> Tuple[int, int, int]:
    """
    Map scalar N into a lower band near 2^target_exp by:
        s     = N >> target_exp   (rough scale ~ N / 2^target_exp)
        s_inv = s^{-1} mod n
        Nw    = N * s_inv mod n

    Returns:
        (N_wrapped, s_inv, s)
    """
    if N <= 0:
        raise ValueError("N must be positive")
    if target_exp < 0:
        raise ValueError("target_exp must be >= 0")

    s = N >> target_exp
    if s == 0:
        raise ValueError(
            f"Shift too large: N >> {target_exp} became 0. "
            "Choose a smaller target_exp or a larger N."
        )

    # Ensure invertible modulo group order n
    if s % n == 0:
        raise ValueError("Scaling factor s is 0 mod n; not invertible")

    s_inv = pow(s, -1, n)
    N_wrapped = (N * s_inv) % n

    # Edge case: wrapped scalar could become 0 (very unlikely but possible mod n)
    if N_wrapped == 0:
        # 0 has no band. You can decide what you want here.
        raise ValueError("Wrapped scalar became 0 mod n; choose a different N or target_exp.")

    return N_wrapped, s_inv, s


def band_wrap_point(P: Point, s_inv: int) -> Point:
    """
    Apply same inverse-scalar wrap to an EC point:
        Pw = s_inv * P

    If P = N*G, then Pw = (N*s_inv)*G, aligned with wrapped scalar.
    """
    if not isinstance(P, Point):
        raise TypeError("P must be an ecdsa.ellipticcurve.Point")
    return s_inv * P


def lift_scalar(N_wrapped: int, s: int) -> int:
    """
    Lift a wrapped scalar back up using s:
        N_lift = N_wrapped * s mod n

    NOTE: This 'undoes' the wrap only up to mod n equivalence.
    """
    if N_wrapped <= 0:
        raise ValueError("N_wrapped must be positive")
    if s <= 0:
        raise ValueError("s must be positive")
    return (N_wrapped * s) % n


def wrap_report(N: int, target_exp: int, verify_point: bool = True) -> WrapResult:
    """
    Wrap scalar N and optionally verify point alignment:
        P = N*G
        Pw_by_point = s_inv*P
        Pw_by_scalar = Nw*G
        check Pw_by_point == Pw_by_scalar
    """
    Nw, s_inv, s = band_wrap_scalar(N, target_exp)

    if verify_point:
        P = N * G
        Pw1 = band_wrap_point(P, s_inv)
        Pw2 = Nw * G
        if Pw1 != Pw2:
            raise RuntimeError("Point wrap mismatch: s_inv*(N*G) != (Nw*G). Something is wrong.")

    return WrapResult(
        original_scalar=N,
        wrapped_scalar=Nw,
        target_exp=target_exp,
        scale_s=s,
        scale_inv=s_inv,
        original_band=detect_band(N),
        wrapped_band=detect_band(Nw),
        original_density=bit_density(N),
        wrapped_density=bit_density(Nw),
    )


# =========================
# Batch utilities + simple clustering
# =========================
def batch_wrap(scalars: List[int], target_exp: int, verify_point: bool = False) -> List[WrapResult]:
    results: List[WrapResult] = []
    for N in scalars:
        results.append(wrap_report(N, target_exp=target_exp, verify_point=verify_point))
    return results


def cluster_by_band(results: List[WrapResult]) -> Dict[int, int]:
    """
    Count how many wrapped scalars landed in each wrapped_band.
    """
    counts: Dict[int, int] = {}
    for r in results:
        counts[r.wrapped_band] = counts.get(r.wrapped_band, 0) + 1
    return counts


def cluster_by_density(results: List[WrapResult]) -> Dict[int, int]:
    """
    Count how many wrapped scalars have each popcount value.
    """
    counts: Dict[int, int] = {}
    for r in results:
        counts[r.wrapped_density] = counts.get(r.wrapped_density, 0) + 1
    return counts


# =========================
# Demo / Example usage
# =========================
def main():
    print("SECP256k1 Band-Wrap Toolkit\n")

    # --------------------------------------------------
    # Example: scalar in [2^159, 2^160)
    # --------------------------------------------------
    N = (1 << 159) + 123_456_789
    target_exp = 79  # aim for ~2^79..2^80 band

    print("=== Single wrap demo ===")
    r = wrap_report(N, target_exp=target_exp, verify_point=True)

    print(f"Original N:        {fmt_int(r.original_scalar)}")
    print(f"Original band:     2^{r.original_band} .. 2^{r.original_band + 1} - 1")
    print(f"Original popcount: {r.original_density}")

    print(f"\nTarget exp:        {r.target_exp}")
    print(f"Scale s = N>>exp:  {fmt_int(r.scale_s)}")
    print(f"Scale inv mod n:   {r.scale_inv}  (mod n)")

    print(f"\nWrapped Nw:        {fmt_int(r.wrapped_scalar)}")
    print(f"Wrapped band:      2^{r.wrapped_band} .. 2^{r.wrapped_band + 1} - 1")
    print(f"Wrapped popcount:  {r.wrapped_density}")

    # Lift back (mod n)
    lifted = lift_scalar(r.wrapped_scalar, r.scale_s)
    print("\nLift check (mod n):")
    print(f"Lifted (Nw*s mod n): {fmt_int(lifted)}")
    print(f"Original (N mod n):  {fmt_int(r.original_scalar % n)}")
    print("Match?              ", "YES" if lifted == (r.original_scalar % n) else "NO")

    # --------------------------------------------------
    # Batch demo: multiple nearby scalars
    # --------------------------------------------------
    print("\n=== Batch wrap demo ===")
    test_scalars = [
        (1 << 159) + 111,
        (1 << 159) + 222,
        (1 << 159) + 333,
        (1 << 159) + 444,
        (1 << 159) + 555,
    ]
    results = batch_wrap(test_scalars, target_exp=target_exp, verify_point=False)

    for i, rr in enumerate(results, 1):
        print(
            f"{i:02d}) N band 2^{rr.original_band} -> wrapped band 2^{rr.wrapped_band}, "
            f"popcount {rr.original_density}->{rr.wrapped_density}"
        )

    print("\nCluster (wrapped band -> count):", cluster_by_band(results))
    print("Cluster (wrapped popcount -> count):", cluster_by_density(results))

    # --------------------------------------------------
    # NOTE: Where to plug BSGS
    # --------------------------------------------------
    print(
        "\n=== Where BSGS plugs in ===\n"
        "If you can solve discrete log in the WRAPPED band:\n"
        "    Find k such that k*G == Pw\n"
        "then lift:\n"
        "    N ≡ k*s (mod n)\n"
        "The wrap is your 'fold' into a smaller search window.\n"
    )


if __name__ == "__main__":
    main()
