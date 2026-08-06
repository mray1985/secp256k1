#!/usr/bin/env python3
"""
Resolution 1/p and 1/p^2 — injectivity of floor Tax_k.

theorem / proof / verification.
Document: Resolution_Coarse_Fine_Lattice.md

Correction: collisions are at k=77 (coarse) and k=154 (fine), NOT at 78/155.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\RESOLUTION_LATTICE_VERIFY.txt")

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
P2 = P * P


def tax_floor_int(x: int, M: int, k_pow: int) -> int:
    """Return floor((x/M)*10^k) = floor(x * 10^k / M) as integer digit string value."""
    return (x * k_pow) // M


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(s)
        print(s)

    def block(title: str, theorem: str, proof: str) -> None:
        w()
        w("-" * 88)
        w(f"THEOREM: {title}")
        w(f"  Statement: {theorem}")
        w(f"  Proof:     {proof}")
        w("  Verification:")

    w("=" * 88)
    w("Coarse/Fine resolution: lattice 1/p and 1/p^2")
    w("=" * 88)

    # ------------------------------------------------------------------ bounds
    block(
        "Bounds on p and p^2",
        "10^77 < p < 10^78 and 10^154 < p^2 < 10^155.",
        "Direct integer comparison.",
    )
    assert 10**77 < P < 10**78
    assert 10**154 < P2 < 10**155
    w(f"    10^78 - p = {10**78 - P}")
    w(f"    p - 10^77 = {P - 10**77}")
    w(f"    10^155 - p^2 = {10**155 - P2}")
    w("    OK")

    # ------------------------------------------------------------------ C1
    block(
        "C1 Floor Tax_78 injective on {x/p}",
        "Tax_78(x/p) distinct for distinct x in 0..p-1.",
        "Min spacing 1/p; bin width 10^(-78); 10^78>p => 10^(-78)<1/p; "
        "no bin can hold two lattice points.",
    )
    assert 10**78 > P  # => bin width < spacing
    # Equivalent computational check: floor(x*10^78/p) unique for all x
    # Full scan of p is impossible; prove via spacing + spot-check + collision search failure
    K78 = 10**78
    # If collision of consecutive: floor(x*K/p)==floor((x+1)*K/p) iff (xK)%p + K < p
    # i.e. (xK)%p < p-K. But K=10^78 > p so p-K < 0, impossible.
    assert K78 > P
    assert P - K78 < 0
    w("    Consecutive collision criterion (xK)%p < p-K is impossible since p-K<0")
    w("    Hence no consecutive (hence no) collisions for Tax_78 - OK")

    # ------------------------------------------------------------------ C2
    block(
        "C2 Floor Tax_77 NOT injective",
        "Exists x with Tax_77(x/p)=Tax_77((x+1)/p).",
        "10^77<p => bin width 10^(-77)>1/p; consecutive residues can share a bin.",
    )
    K77 = 10**77
    assert K77 < P
    found = None
    # Search: (x*K77)%P < P-K77
    for x in range(0, 10000):
        r = (x * K77) % P
        if r < P - K77:
            f1 = (x * K77) // P
            f2 = ((x + 1) * K77) // P
            assert f1 == f2
            found = (x, x + 1, f1)
            break
    assert found is not None
    w(f"    Explicit collision: x={found[0]} and x={found[1]} share Tax_77 floor={found[2]}")
    w("    NOTE: this is k=77, NOT k=78 - OK")

    # ------------------------------------------------------------------ F1/F2
    block(
        "F1/F2 Fine channel Tax_155 injective; Tax_154 not",
        "Same lemma with delta=1/p^2.",
        "10^155>p^2>10^154.",
    )
    assert 10**155 > P2
    assert 10**154 < P2
    # consecutive collision for 154 possible: p^2 - 10^154 > 0
    K154 = 10**154
    K155 = 10**155
    assert P2 - K155 < 0
    w("    Tax_155: p^2-10^155<0 => no consecutive floor collisions - OK")
    found_f = None
    for y in range(0, 100000):
        r = (y * K154) % P2
        if r < P2 - K154:
            f1 = (y * K154) // P2
            f2 = ((y + 1) * K154) // P2
            if f1 == f2:
                found_f = (y, y + 1)
                break
    assert found_f is not None
    w(f"    Tax_154 explicit consecutive collision: y={found_f[0]},{found_f[1]} - OK")

    # ------------------------------------------------------------------ lattice primacy
    block(
        "Lattice primacy",
        "Coarse resolution 1/p; fine resolution 1/p^2. Decimals encode these lattices.",
        "Definitions; E=xp+y packages both without base 10.",
    )
    # E recovers (x,y)
    for x, y in ((0, 0), (1, 2), (P - 1, P - 1), (12345, 67890)):
        E = x * P + y
        assert E // P == x and E % P == y
    w("    E=xp+y recovers (x,y) - OK")
    w("    Decimal digit counts are encodings of bin-width vs lattice spacing - OK")

    w()
    w("=" * 88)
    w("VERDICT")
    w("=" * 88)
    w("  Floor Tax_78 IS injective (theorem: 10^78>p).")
    w("  Earlier collision example was Tax_77, not Tax_78.")
    w("  Prefer language: resolution 1/p and 1/p^2.")
    w("  ALL resolution-lattice checks PASSED.")
    w("=" * 88)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
