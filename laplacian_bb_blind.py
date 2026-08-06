#!/usr/bin/env python3
"""BB blind test — construct L from PUBLIC data only.

Allowed inputs per puzzle: Px, Py, r, s, z, p, N, Gx, puzzle index n,
range bounds [2^(n-1), 2^n - 1].

FORBIDDEN: true k, true d, nonce_hex, recover_k_from_d, z+r*d.

Tests: k ?= L/A, k ?= L/D, d ?= L/A, d ?= L/D (real divide + mod-N scaled).
Reports BLIND HITS ONLY on solved 53125 set (P65-P130 every 5th).
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hashkeys_rsz import N, PUZZLE_RSZ, p, y_roots_from_x  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FB10D4B8C

SOLVED = tuple(range(65, 131, 5))
OUT_DEFAULT = ROOT / "laplacian_bb_blind_report.txt"


@dataclass(frozen=True)
class PublicCtx:
    n: int
    px: int
    py: int
    r: int
    s: int
    z: int
    d_lo: int
    d_hi: int


def sec(x: float) -> float:
    c = math.cos(x)
    if abs(c) < 1e-18:
        raise ValueError("sec pole")
    return 1.0 / c


def laplacian_body(x: float) -> float:
    s = sec(x)
    return s * (2.0 * s * s - 1.0)


def cart_x_literal(px: int) -> float:
    return float(Decimal(px % p) / Decimal(p))


def cart_A(px: int, *, prec: int = 280) -> Decimal:
    getcontext().prec = prec
    x = cart_x_literal(px)
    body = laplacian_body(x)
    return Decimal(256) * Decimal(p) * Decimal(body)


def polar_D(px: int, py: int, *, prec: int = 280) -> Decimal:
    getcontext().prec = prec
    x = cart_x_literal(px)
    body = laplacian_body(x)
    r2 = px * px + py * py
    return Decimal(256) * Decimal(p) * Decimal(body) / Decimal(r2)


def pubkey_ctx(n: int, keys: dict) -> PublicCtx | None:
    rsz = PUZZLE_RSZ.get(n)
    if rsz is None:
        return None
    if n in keys:
        px, py = keys[n].px, keys[n].py
    else:
        pub = rsz.pub_compressed
        px = int(pub[2:], 16)
        yp, yn = y_roots_from_x(px)
        py = yp if pub.startswith("02") else yn
    return PublicCtx(
        n=n,
        px=px,
        py=py,
        r=rsz.r,
        s=rsz.s,
        z=rsz.z,
        d_lo=2 ** (n - 1),
        d_hi=2**n - 1,
    )


def mod(x: int) -> int:
    return x % N


def public_L_catalog(ctx: PublicCtx) -> list[tuple[str, int]]:
    """L built only from public fields — no k, no d."""
    px, py, r, s, z = ctx.px, ctx.py, ctx.r, ctx.s, ctx.z
    n, lo, hi = ctx.n, ctx.d_lo, ctx.d_hi
    items: list[tuple[str, int]] = []

    def add(name: str, val: int) -> None:
        items.append((name, val % N))

    # RSZ unary
    for name, v in (
        ("z", z),
        ("r", r),
        ("s", s),
        ("z+r", z + r),
        ("z-r", z - r),
        ("r+s", r + s),
        ("r-s", r - s),
        ("z*s", z * s),
        ("r*s", r * s),
        ("z*r", z * r),
        ("s*z", s * z),
    ):
        add(name, v)

    # pubkey
    add("Px", px)
    add("Py", py)
    add("Px+Py", px + py)
    add("Px-Py", px - py)
    add("Px*Py", px * py)
    add("Px^2", px * px)
    add("Py^2", py * py)

    # ECDSA-shaped but pubkey not d
    add("z+r*Px", z + r * px)
    add("z-r*Px", z - r * px)
    add("z+r*Py", z + r * py)
    add("z-r*Py", z - r * py)
    add("r*Px", r * px)
    add("r*Py", r * py)
    add("s*Px", s * px)
    add("s*Py", s * py)
    add("s*Px+z", s * px + z)
    add("s*Py+z", s * py + z)
    add("r*Px+z", r * px + z)
    add("r*Py+z", r * py + z)
    add("s*Px-r*Px", s * px - r * px)
    add("(z+r)*Px", (z + r) * px)
    add("(z-r)*Px", (z - r) * px)
    add("z*Px", z * px)
    add("z*Py", z * py)
    add("Px+z*s", px + z * s)
    add("Px+r*s", px + r * s)

    # generator + index + range (public constants)
    add("Gx", Gx)
    add("Gy", Gy)
    add("Gx+Px", Gx + px)
    add("Gx*Px", Gx * px)
    add("Gy+Py", Gy + py)
    add("n", n)
    add("2^(n-1)", lo)
    add("2^n-1", hi)
    add("lo+Px", lo + px)
    add("hi+Px", hi + px)
    add("lo*Px mod", lo * px)
    add("Px-lo", px - lo)
    add("hi-Px", hi - px)
    add("z+lo", z + lo)
    add("z+hi", z + hi)
    add("r+lo", r + lo)
    add("r*lo", r * lo)
    add("s*lo", s * lo)

    # field bridge
    add("Px mod p", px % p)
    add("Py mod p", py % p)
    add("Px+Py mod p", (px + py) % p)
    add("z+Px mod p", (z + px) % p)
    add("r+Px mod p", (r + px) % p)

    # curve template on pubkey x (public)
    add("Px^3+7", pow(px, 3, p) + 7)
    add("Py^2 mod p", pow(py, 2, p))

    return items


def mod_inv_scaled(num: int, den: Decimal, modulus: int, scale_exp: int) -> int | None:
    if den <= 0:
        return None
    scale = Decimal(10) ** scale_exp
    den_i = int((den * scale).to_integral_value())
    if den_i <= 0 or math.gcd(den_i, modulus) != 1:
        return None
    return (num * scale % modulus) * pow(den_i, -1, modulus) % modulus


def run_blind(*, prec: int = 280, out_path: Path = OUT_DEFAULT) -> str:
    keys = parse_53125()
    lines: list[str] = []
    w = lines.append

    w("=" * 72)
    w("BB BLIND TEST — public L only")
    w("  x = Px/p,  A = 256*p*sec(x)(2*sec^2(x)-1),  D = A/r^2")
    w("  FORBIDDEN: k, d, z+r*d, recover_k_from_d")
    w("=" * 72)

    k_hits: list[str] = []
    d_hits: list[str] = []
    k_mod_hits: list[str] = []
    d_mod_hits: list[str] = []

    for n in SOLVED:
        pk = keys.get(n)
        if not pk or not pk.d:
            continue
        ctx = pubkey_ctx(n, keys)
        if ctx is None:
            continue
        d_true = pk.d
        rsz = PUZZLE_RSZ[n]
        k_true = rsz.k
        if k_true is None:
            # ground truth for scoring only — never used to build L
            k_true = pow(rsz.s, -1, N) * (rsz.z + rsz.r * d_true) % N

        A = cart_A(ctx.px, prec=prec)
        D = polar_D(ctx.px, ctx.py, prec=prec)

        for lname, Lm in public_L_catalog(ctx):
            Ldec = Decimal(Lm)

            # real divide -> k
            kA = int(Ldec / A)
            if kA == k_true:
                k_hits.append(f"P{n} k=L/A L={lname}")
            kD = int(Ldec / D)
            if kD == k_true:
                k_hits.append(f"P{n} k=L/D L={lname}")

            # real divide -> d
            dA = int(Ldec / A)
            if dA == d_true:
                d_hits.append(f"P{n} d=L/A L={lname}")
            dD = int(Ldec / D)
            if dD == d_true:
                d_hits.append(f"P{n} d=L/D L={lname}")

            # k from L/A then derive d via ECDSA (still blind on k)
            if kA == k_true:
                d_der = (rsz.s * kA - rsz.z) * pow(rsz.r, -1, N) % N
                if d_der == d_true:
                    k_hits.append(f"P{n} k=L/A + ECDSA d L={lname}")

            # mod N scaled
            for se in (60, 80, 100, 120, 140, 160):
                ke = mod_inv_scaled(Lm, A, N, se)
                if ke is not None and ke == k_true:
                    k_mod_hits.append(f"P{n} k mod N L={lname} scale=10^{se} denom=A")
                ke = mod_inv_scaled(Lm, D, N, se)
                if ke is not None and ke == k_true:
                    k_mod_hits.append(f"P{n} k mod N L={lname} scale=10^{se} denom=D")
                de = mod_inv_scaled(Lm, A, N, se)
                if de is not None and de == d_true:
                    d_mod_hits.append(f"P{n} d mod N L={lname} scale=10^{se} denom=A")
                de = mod_inv_scaled(Lm, D, N, se)
                if de is not None and de == d_true:
                    d_mod_hits.append(f"P{n} d mod N L={lname} scale=10^{se} denom=D")

    w("\n--- BLIND HITS: k (real L/A or L/D) ---")
    if k_hits:
        for h in k_hits:
            w(f"  {h}")
    else:
        w("  (none)")

    w("\n--- BLIND HITS: d (real L/A or L/D) ---")
    if d_hits:
        for h in d_hits:
            w(f"  {h}")
    else:
        w("  (none)")

    w("\n--- BLIND HITS: k (mod N scaled) ---")
    if k_mod_hits:
        for h in k_mod_hits:
            w(f"  {h}")
    else:
        w("  (none)")

    w("\n--- BLIND HITS: d (mod N scaled) ---")
    if d_mod_hits:
        for h in d_mod_hits:
            w(f"  {h}")
    else:
        w("  (none)")

    w("\n--- STATUS ---")
    w("BB literal Px/p: algebra CONFIRMED (forward); blind ECDSA bridge FAILED.")
    w("Px/p vs 2*pi*Px/p changes sec-body sign (e.g. P80 +1.79 vs -1.01).")
    w("Label: PROMISING geometry / TEST algebra — not confirmed key leak.")

    w(f"\nCatalog size: {len(public_L_catalog(pubkey_ctx(80, keys)))} L formulas per puzzle")
    w(f"Puzzles tested: {len(SOLVED)}")

    # coordinate sign note
    w("\n--- P80 body sign (public geometry only) ---")
    ctx80 = pubkey_ctx(80, keys)
    if ctx80:
        x_lit = cart_x_literal(ctx80.px)
        body_lit = laplacian_body(x_lit)
        x_ang = float(Decimal(ctx80.px % p) / Decimal(p) * Decimal(2) * Decimal(str(math.pi)))
        body_ang = laplacian_body(x_ang)
        w(f"  BB x=Px/p:      body={body_lit:+.6f}")
        w(f"  old 2pi*Px/p:   body={body_ang:+.6f}")

    text = "\n".join(lines) + "\n"
    out_path.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description="BB blind Laplacian test")
    ap.add_argument("--prec", type=int, default=280)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    text = run_blind(prec=args.prec, out_path=args.out)
    print(text)


if __name__ == "__main__":
    main()
