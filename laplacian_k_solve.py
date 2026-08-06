#!/usr/bin/env python3
"""Laplacian k-solve — three separate tracks:

  A) RSZ residue mod N / mod p / mod delta
  B) Cartesian Px slot (no r^2)
  C) deltaCURVE (k in angle, r^2 from signature r)

Core identity (polar, k linear in amplitude):
  L = k * D,   D = 256*p*sec(theta)(2*sec^2(theta)-1) / r^2
  k = L / D
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

from hashkeys_rsz import N, PUZZLE_RSZ, p, recover_r_point_from_sig, y_roots_from_x  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

DELTA = 384414070692677040834422699137645700276
GAP = p - N

SOLVED_53125 = tuple(range(65, 131, 5))
UNSOLVED = (135, 160)


@dataclass(frozen=True)
class LaplacianGeom:
    theta: float
    body: float
    r2: int
    d_factor: Decimal


def sec(theta: float) -> float:
    c = math.cos(theta)
    if abs(c) < 1e-18:
        raise ValueError("sec pole")
    return 1.0 / c


def laplacian_body(theta: float) -> float:
    s = sec(theta)
    return s * (2.0 * s * s - 1.0)


def angle_px_over_p(px: int) -> float:
    return float((px % p) / p) * 2.0 * math.pi


def angle_atan2(px: int, py: int) -> float:
    return math.atan2(float(py % p), float(px % p))


def angle_k_phase(k: int) -> float:
    return float(k % N) * (2.0 * math.pi / float(N))


def pubkey_xy(n: int, keys: dict) -> tuple[int, int]:
    if n in keys:
        return keys[n].px, keys[n].py
    rsz = PUZZLE_RSZ[n]
    pub = rsz.pub_compressed
    px = int(pub[2:], 16)
    yp, yn = y_roots_from_x(px)
    py = yp if pub.startswith("02") else yn
    return px, py


def geom(
    px: int,
    py: int,
    *,
    theta_mode: str = "atan2",
    r2_mode: str = "pubkey",
    r_sig: int | None = None,
    k_for_angle: int | None = None,
    prec: int = 240,
) -> LaplacianGeom:
    getcontext().prec = prec
    if theta_mode == "atan2":
        th = angle_atan2(px, py)
    elif theta_mode == "px_over_p":
        th = angle_px_over_p(px)
    elif theta_mode == "k_phase":
        if k_for_angle is None:
            raise ValueError("k_phase needs k_for_angle")
        th = angle_k_phase(k_for_angle)
    else:
        raise ValueError(theta_mode)

    body = laplacian_body(th)
    if r2_mode == "pubkey":
        r2 = px * px + py * py
    elif r2_mode == "sig_r":
        if r_sig is None:
            raise ValueError("sig_r needs r_sig")
        r2 = r_sig * r_sig
    elif r2_mode == "r_point":
        if r_sig is None:
            raise ValueError("r_point needs r_sig")
        pt = recover_r_point_from_sig(r_sig)
        if pt is None:
            raise ValueError("cannot lift R")
        rx, ry = pt
        r2 = rx * rx + ry * ry
    else:
        raise ValueError(r2_mode)

    d_factor = Decimal(256) * Decimal(p) * Decimal(body) / Decimal(r2)
    return LaplacianGeom(theta=th, body=body, r2=r2, d_factor=d_factor)


def cart_k1(px: int, *, prec: int = 240) -> Decimal:
    getcontext().prec = prec
    th = angle_px_over_p(px)
    body = laplacian_body(th)
    return Decimal(256) * Decimal(p) * Decimal(body)


def cart_x_arg(px: int, mode: str, *, prec: int = 240) -> float:
    """Cartesian x-slot argument for sec(x) — mode selects how Px maps to x."""
    getcontext().prec = prec
    xf = Decimal(px % p) / Decimal(p)  # Px/p in (0,1)
    if mode == "literal_unit":
        # BB: x = Px/p directly (no 2pi) — Wolfram Cartesian coordinate
        return float(xf)
    if mode == "angle_2pi":
        return float(xf * Decimal(2) * Decimal(str(math.pi)))
    if mode == "literal_pi":
        return float(xf * Decimal(str(math.pi)))
    if mode == "bits256":
        return float(Decimal(px % p) / Decimal(2**256))
    if mode == "field_log2":
        return math.log2(float(px % p) or 1.0) / 256.0
    raise ValueError(mode)


def cart_A(px: int, mode: str, *, prec: int = 240) -> tuple[Decimal, float, float]:
    """Cartesian Laplacian base A at k=1: 256*p*sec(x)(2*sec^2(x)-1)."""
    getcontext().prec = prec
    x = cart_x_arg(px, mode, prec=prec)
    body = laplacian_body(x)
    A = Decimal(256) * Decimal(p) * Decimal(body)
    return A, x, body


def polar_D_literal(px: int, py: int, x_mode: str, *, prec: int = 240) -> Decimal:
    """Polar /r^2 with literal Cartesian x in sec (same x as cart)."""
    getcontext().prec = prec
    x = cart_x_arg(px, x_mode, prec=prec)
    body = laplacian_body(x)
    r2 = px * px + py * py
    return Decimal(256) * Decimal(p) * Decimal(body) / Decimal(r2)


def rsz_L(name: str, rsz, d: int = 0) -> int:
    if name == "z":
        return rsz.z
    if name == "r":
        return rsz.r
    if name == "s":
        return rsz.s
    if name == "z+r":
        return (rsz.z + rsz.r) % N
    if name == "z-r":
        return (rsz.z - rsz.r) % N
    if name == "r*s":
        return (rsz.r * rsz.s) % N
    if name == "z*s":
        return (rsz.z * rsz.s) % N
    if name == "z*r":
        return (rsz.z * rsz.r) % N
    if name == "z+rd":
        return (rsz.z + rsz.r * d) % N
    if name == "r*px":
        return 0  # filled per puzzle
    raise KeyError(name)


def k_from_real(L: Decimal, D: Decimal) -> int:
    return int(L / D)


def mod_inv_scaled(num: int, den_real: Decimal, modulus: int, scale_exp: int) -> int | None:
    """k ?= num * scale / round(den_real * scale) mod modulus."""
    if den_real <= 0:
        return None
    scale = Decimal(10) ** scale_exp
    den = int((den_real * scale).to_integral_value())
    if den <= 0 or math.gcd(den, modulus) != 1:
        return None
    return (num * scale % modulus) * pow(den, -1, modulus) % modulus


# ---------------------------------------------------------------------------
# TRACK A — RSZ residue mod N / mod p / mod delta
# ---------------------------------------------------------------------------

def track_rsz(*, prec: int = 240) -> None:
    keys = parse_53125()
    print("=" * 72)
    print("TRACK A: RSZ RESIDUE  (mod N / mod p / mod delta)")
    print("  k ?= L_mod * inv(D_mod)   with L from RSZ scalars, D polar atan2/pubkey")
    print("=" * 72)

    l_names = ("z", "r", "s", "z+r", "z-r", "r*s", "z*s", "z*r", "z+rd")
    mods = (("N", N), ("p", p), ("delta", DELTA))
    scale_exps = (40, 60, 80, 100, 120)

    for mod_label, modulus in mods:
        print(f"\n--- mod {mod_label} ---")
        hits: list[str] = []
        for n in SOLVED_53125:
            pk = keys[n]
            rsz = PUZZLE_RSZ[n]
            if not pk.d:
                continue
            k_true = rsz.k or rsz.recover_k_from_d(pk.d)
            g = geom(pk.px, pk.py, prec=prec)
            for lname in l_names:
                Lm = rsz_L(lname, rsz, pk.d) % modulus
                for se in scale_exps:
                    k_est = mod_inv_scaled(Lm, g.d_factor, modulus, se)
                    if k_est is None:
                        continue
                    if modulus == N and k_est == k_true:
                        hits.append(f"P{n} L={lname} scale=10^{se}")
                    elif modulus != N and k_est == (k_true % modulus):
                        hits.append(f"P{n} L={lname} scale=10^{se} (mod {mod_label})")

        print(f"  modular hits: {len(hits)}")
        for h in hits[:12]:
            print(f"    {h}")
        if len(hits) > 12:
            print(f"    ... +{len(hits)-12} more")

    # real-ratio: L = z+rd should match k*D scale (sanity)
    print("\n--- real ratio (z+rd)/D vs k_true (needs d; not a blind solve) ---")
    for n in (65, 80, 100, 130):
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        g = geom(pk.px, pk.py, prec=prec)
        L = Decimal((rsz.z + rsz.r * pk.d) % N)
        k_est = k_from_real(L, g.d_factor)
        rel = float(k_est / Decimal(k_true)) if k_true else 0
        print(f"  P{n}: k_est/k_true ratio ~ {rel:.4e}  (orders apart)")

    # ECDSA baseline on same set
    print("\n--- ECDSA baseline (mod N, needs d) ---")
    ok = 0
    for n in SOLVED_53125:
        pk = keys[n]
        if not pk.d:
            continue
        rsz = PUZZLE_RSZ[n]
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        if rsz.recover_k_from_d(pk.d) == k_true:
            ok += 1
    print(f"  k = s^-1(z+rd) mod N: {ok}/{len(SOLVED_53125)}")

    # unsolved: list L mod N for P135/P160 (no k)
    print("\n--- unsolved RSZ residues (no k) ---")
    for n in UNSOLVED:
        rsz = PUZZLE_RSZ[n]
        for lname in ("z", "r", "s", "z+r", "z-r"):
            Lm = rsz_L(lname, rsz) % N
            print(f"  P{n} {lname} mod N bits={Lm.bit_length()}")


# ---------------------------------------------------------------------------
# TRACK B — Cartesian Px slot
# ---------------------------------------------------------------------------

def track_cartesian(*, prec: int = 240) -> None:
    keys = parse_53125()
    print("=" * 72)
    print("TRACK B: CARTESIAN Px SLOT")
    print("  A = Delta(256*p*sec(Px)) = 256*p*sec(theta)(2*sec^2-1)   [no r^2]")
    print("  k = L / A")
    print("=" * 72)

    l_names = ("z", "r", "s", "z+r", "z-r", "r*s", "d", "px", "py", "z+rd")

    # forward/back with k*A
    print("\n--- forward L = k*A -> k_back (solved) ---")
    ok = 0
    for n in SOLVED_53125:
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        if not pk.d:
            continue
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        A = cart_k1(pk.px, prec=prec)
        L = Decimal(k_true) * A
        k_back = k_from_real(L, A)
        if k_back == k_true:
            ok += 1
        else:
            print(f"  P{n}: off by {k_back - k_true:+d}")
    print(f"  exact: {ok}/{len(SOLVED_53125)}")

    # blind L candidates
    print("\n--- blind k = L_cand / A ---")
    hits = 0
    for n in SOLVED_53125:
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        if not pk.d:
            continue
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        A = cart_k1(pk.px, prec=prec)
        for lname in l_names:
            if lname == "d":
                Lm = Decimal(pk.d)
            elif lname == "px":
                Lm = Decimal(pk.px)
            elif lname == "py":
                Lm = Decimal(pk.py)
            elif lname == "z+rd":
                Lm = Decimal((rsz.z + rsz.r * pk.d) % N)
            else:
                Lm = Decimal(rsz_L(lname, rsz, pk.d))
            if k_from_real(Lm, A) == k_true:
                hits += 1
                print(f"  HIT P{n} L={lname}")
    print(f"  total hits: {hits}")

    # cart vs polar bridge at k=1
    print("\n--- cart A vs polar D at k=1 (ratio A/D) ---")
    for n in (80, 100, 135, 160):
        px, py = pubkey_xy(n, keys)
        A = cart_k1(px, prec=prec)
        D = geom(px, py, prec=prec).d_factor
        ratio = A / D
        print(f"  P{n}: A/D ~ {ratio:.6e}  (r^2 factor)")

    # mod N on Cartesian: k ?= L_mod * inv(A_scaled)
    print("\n--- Cartesian mod N scaled inverse ---")
    mod_hits = 0
    for n in SOLVED_53125:
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        if not pk.d:
            continue
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        A = cart_k1(pk.px, prec=prec)
        for lname in ("z", "r", "s", "z+r", "z+rd"):
            Lm = rsz_L(lname, rsz, pk.d) % N
            for se in (60, 80, 100, 120):
                k_est = mod_inv_scaled(Lm, A, N, se)
                if k_est is not None and k_est == k_true:
                    mod_hits += 1
                    print(f"  HIT P{n} L={lname} scale=10^{se}")
    print(f"  mod N hits: {mod_hits}")


# ---------------------------------------------------------------------------
# TRACK BB — Cartesian literal Px (sec(Px/p), no 2pi)
# ---------------------------------------------------------------------------

BB_MODES = ("literal_unit", "angle_2pi", "literal_pi", "bits256", "field_log2")


def track_bb(*, prec: int = 280) -> None:
    keys = parse_53125()
    print("=" * 72)
    print("TRACK BB: LITERAL CARTESIAN Px")
    print("  x = Px/p  (unit coordinate, NOT 2pi*Px/p)")
    print("  A = 256*p*sec(x)(2*sec^2(x)-1)   Cartesian, no r^2")
    print("  D = A / r^2                        polar with same x")
    print("  k = L / A   or   k = L / D")
    print("=" * 72)

    l_names = ("z", "r", "s", "z+r", "z-r", "r*s", "px", "z+rd")

    for mode in BB_MODES:
        print(f"\n{'='*40} mode: {mode} {'='*40}")

        # forward
        ok = 0
        for n in SOLVED_53125:
            pk = keys[n]
            rsz = PUZZLE_RSZ[n]
            if not pk.d:
                continue
            k_true = rsz.k or rsz.recover_k_from_d(pk.d)
            A, _, _ = cart_A(pk.px, mode, prec=prec)
            L = Decimal(k_true) * A
            if k_from_real(L, A) == k_true:
                ok += 1
        print(f"  forward k=A/A: {ok}/{len(SOLVED_53125)}")

        # blind cart
        hits = 0
        for n in SOLVED_53125:
            pk = keys[n]
            rsz = PUZZLE_RSZ[n]
            if not pk.d:
                continue
            k_true = rsz.k or rsz.recover_k_from_d(pk.d)
            A, _, _ = cart_A(pk.px, mode, prec=prec)
            for lname in l_names:
                if lname == "px":
                    Lm = Decimal(pk.px)
                elif lname == "z+rd":
                    Lm = Decimal((rsz.z + rsz.r * pk.d) % N)
                else:
                    Lm = Decimal(rsz_L(lname, rsz, pk.d))
                if k_from_real(Lm, A) == k_true:
                    hits += 1
                    print(f"  CART HIT P{n} L={lname}")
        print(f"  blind cart hits: {hits}")

        # polar D with same x
        okp = 0
        for n in SOLVED_53125:
            pk = keys[n]
            rsz = PUZZLE_RSZ[n]
            if not pk.d:
                continue
            k_true = rsz.k or rsz.recover_k_from_d(pk.d)
            D = polar_D_literal(pk.px, pk.py, mode, prec=prec)
            L = Decimal(k_true) * D
            if k_from_real(L, D) == k_true:
                okp += 1
        print(f"  forward polar k=L/D: {okp}/{len(SOLVED_53125)}")

        # mod N (literal_unit and angle_2pi only — representative)
        if mode in ("literal_unit", "angle_2pi"):
            mod_hits = 0
            for n in SOLVED_53125:
                pk = keys[n]
                rsz = PUZZLE_RSZ[n]
                if not pk.d:
                    continue
                k_true = rsz.k or rsz.recover_k_from_d(pk.d)
                A, _, _ = cart_A(pk.px, mode, prec=prec)
                for lname in ("z", "r", "s", "z+r", "z+rd"):
                    Lm = rsz_L(lname, rsz, pk.d) % N
                    for se in (80, 100, 120, 140):
                        k_est = mod_inv_scaled(Lm, A, N, se)
                        if k_est is not None and k_est == k_true:
                            mod_hits += 1
                            print(f"  MOD HIT P{n} L={lname} scale=10^{se}")
            print(f"  mod N hits: {mod_hits}")

    # geometry snapshot: literal_unit vs angle_2pi
    print(f"\n{'='*72}")
    print("BB geometry snapshot (literal_unit vs angle_2pi)")
    for n in (80, 135, 160):
        px, py = pubkey_xy(n, keys)
        for mode in ("literal_unit", "angle_2pi"):
            A, x, body = cart_A(px, mode, prec=prec)
            D = polar_D_literal(px, py, mode, prec=prec)
            print(f"  P{n} {mode}: x={x:.8f} body={body:.6f} A~{A:.4e} D~{D:.4e}")

def delta_L(k: int, r_sig: int, *, prec: int = 240) -> Decimal:
    """L(k) = k * D(k) with theta = k phase, r^2 = r_sig^2."""
    getcontext().prec = prec
    th = angle_k_phase(k)
    body = laplacian_body(th)
    r2 = r_sig * r_sig
    D = Decimal(256) * Decimal(p) * Decimal(body) / Decimal(r2)
    return Decimal(k) * D


def track_deltacurve(*, prec: int = 240, p135_samples: int = 2000) -> None:
    keys = parse_53125()
    print("=" * 72)
    print("TRACK C: deltaCURVE")
    print("  theta = (k mod N) * 2pi/N")
    print("  r^2 = r_sig^2")
    print("  L(k) = k * 256*p*sec(theta)(2*sec^2-1) / r^2")
    print("=" * 72)

    # solved: forward k = L/D(k) — nonlinear because D depends on k
    print("\n--- solved: k_back = L(k_true)/D(k_true) ---")
    ok = 0
    for n in SOLVED_53125:
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        if not pk.d:
            continue
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        L = delta_L(k_true, rsz.r, prec=prec)
        th = angle_k_phase(k_true)
        body = laplacian_body(th)
        D = Decimal(256) * Decimal(p) * Decimal(body) / Decimal(rsz.r * rsz.r)
        k_back = k_from_real(L, D)
        if k_back == k_true:
            ok += 1
        else:
            print(f"  P{n}: off by {k_back - k_true:+d}")
    print(f"  exact: {ok}/{len(SOLVED_53125)}")

    # match L(k_true) mod N to RSZ residues
    print("\n--- L(k_true) mod N vs RSZ scalars (solved) ---")
    for n in (65, 80, 100, 130):
        pk = keys[n]
        rsz = PUZZLE_RSZ[n]
        k_true = rsz.k or rsz.recover_k_from_d(pk.d)
        L = delta_L(k_true, rsz.r, prec=prec)
        Lm = int(L) % N
        matches = []
        for lname in ("z", "r", "s", "z+r", "z-r"):
            if Lm == rsz_L(lname, rsz, pk.d) % N:
                matches.append(lname)
        print(f"  P{n}: L_mod matches {matches or 'none'}")

    # intensity target search on P135: L(k) mod N == z|r|s?
    print(f"\n--- P135 blind search: L(k) mod N in RSZ set ({p135_samples} samples) ---")
    rsz = PUZZLE_RSZ[135]
    targets = {name: rsz_L(name, rsz) % N for name in ("z", "r", "s", "z+r", "z-r")}
    lo, hi = 2**134, 2**135 - 1
    step = max((hi - lo) // p135_samples, 1)
    found: dict[str, list[int]] = {t: [] for t in targets}
    for i in range(p135_samples):
        k_cand = lo + i * step
        Lm = int(delta_L(k_cand, rsz.r, prec=prec)) % N
        for tname, tval in targets.items():
            if Lm == tval and len(found[tname]) < 3:
                found[tname].append(k_cand)
    for tname, ks in found.items():
        print(f"  L mod N == {tname}: {len(ks)} hits in sample  {['hex('+hex(k)+')' for k in ks]}")

    # P160 sample
    print(f"\n--- P160 blind search ({p135_samples} samples in 2^159 band) ---")
    rsz160 = PUZZLE_RSZ[160]
    targets160 = {name: rsz_L(name, rsz160) % N for name in ("z", "r", "s")}
    lo, hi = 2**159, 2**160 - 1
    step = max((hi - lo) // p135_samples, 1)
    for tname in targets160:
        cnt = 0
        for i in range(min(p135_samples, 500)):
            k_cand = lo + i * step
            Lm = int(delta_L(k_cand, rsz160.r, prec=prec)) % N
            if Lm == targets160[tname]:
                cnt += 1
        print(f"  L mod N == {tname}: {cnt} hits in first 500 samples")

    # D sensitivity in P135 band
    print("\n--- P135 D(k) variation across band ---")
    d0 = geom(0, 0, theta_mode="k_phase", r2_mode="sig_r", r_sig=rsz.r, k_for_angle=2**134, prec=prec)
    d1 = geom(0, 0, theta_mode="k_phase", r2_mode="sig_r", r_sig=rsz.r, k_for_angle=2**135 - 1, prec=prec)
    print(f"  D(2^134) = {d0.d_factor:.6e}")
    print(f"  D(2^135-1) = {d1.d_factor:.6e}")
    print(f"  relative spread: {float((d1.d_factor-d0.d_factor)/d0.d_factor):.6e}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Laplacian k-solve — three tracks")
    ap.add_argument(
        "--track",
        choices=("rsz", "cart", "bb", "delta", "all"),
        default="all",
        help="which track to run (default: all, separately)",
    )
    ap.add_argument("--prec", type=int, default=240)
    ap.add_argument("--p135-samples", type=int, default=2000)
    args = ap.parse_args()

    if args.track in ("rsz", "all"):
        track_rsz(prec=args.prec)
        print()
    if args.track in ("cart", "all"):
        track_cartesian(prec=args.prec)
        print()
    if args.track in ("bb", "all"):
        track_bb(prec=args.prec)
        print()
    if args.track in ("delta", "all"):
        track_deltacurve(prec=args.prec, p135_samples=args.p135_samples)


if __name__ == "__main__":
    main()
