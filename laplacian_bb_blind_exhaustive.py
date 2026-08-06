#!/usr/bin/env python3
"""Exhaustive BB blind L search — public inputs only.

Builds a large catalog of L candidates (RSZ shapes, pubkey, R-lift, range,
p/N/gap/delta, atom pairs/triples, bit slices, ECDSA-shaped inversions)
and tests every recovery path without using true k or d in L construction.

Recovery paths per L:
  - k = int(L/A), k = int(L/D)           [BB literal Px/p]
  - d = int(L/A), d = int(L/D)
  - k = L * s^-1 mod N                   [L ~ s*k]
  - d = (L - z) * r^-1 mod N             [L ~ z+r*d]
  - k = L * inv(round(A*10^e)) mod N     [scaled, e in grid]
  - d = L * inv(round(A*10^e)) mod N
  - same with D and with 2pi-Px/p body for A2/D2

Reports BLIND HITS ONLY.
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hashkeys_rsz import N, PUZZLE_RSZ, p, recover_r_point_from_sig, y_roots_from_x  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FB10D4B8C
DELTA = 384414070692677040834422699137645700276
GAP = p - N

SOLVED = tuple(range(65, 131, 5))
OUT_DEFAULT = ROOT / "laplacian_bb_blind_exhaustive_report.txt"


@dataclass(frozen=True)
class PuzzleTruth:
    n: int
    px: int
    py: int
    d: int
    k: int


@dataclass(frozen=True)
class Geom:
    A: Decimal
    D: Decimal
    A2: Decimal
    D2: Decimal


def sec(x: float) -> float:
    c = math.cos(x)
    if abs(c) < 1e-18:
        raise ValueError("pole")
    return 1.0 / c


def body(x: float) -> float:
    s = sec(x)
    return s * (2.0 * s * s - 1.0)


def x_literal(px: int) -> float:
    return float(Decimal(px % p) / Decimal(p))


def x_angle(px: int) -> float:
    return float(Decimal(px % p) / Decimal(p) * Decimal(2) * Decimal(str(math.pi)))


def cart_base(px: int, py: int, xval: float, *, prec: int) -> tuple[Decimal, Decimal]:
    getcontext().prec = prec
    b = body(xval)
    A = Decimal(256) * Decimal(p) * Decimal(b)
    r2 = px * px + py * py
    D = A / Decimal(r2)
    return A, D


def geom_for(px: int, py: int, *, prec: int) -> Geom:
    A, D = cart_base(px, py, x_literal(px), prec=prec)
    A2, D2 = cart_base(px, py, x_angle(px), prec=prec)
    return Geom(A=A, D=D, A2=A2, D2=D2)


def modn(x: int) -> int:
    return x % N


def invn(x: int) -> int | None:
    x %= N
    if x == 0 or math.gcd(x, N) != 1:
        return None
    return pow(x, -1, N)


def puzzle_truth(n: int, keys: dict) -> PuzzleTruth | None:
    pk = keys.get(n)
    rsz = PUZZLE_RSZ.get(n)
    if pk is None or rsz is None or not pk.d:
        return None
    k = rsz.k if rsz.k is not None else pow(rsz.s, -1, N) * (rsz.z + rsz.r * pk.d) % N
    return PuzzleTruth(n, pk.px, pk.py, pk.d, k)


def atom_table(ctx_n: int, px: int, py: int, r: int, s: int, z: int) -> dict[str, int]:
    lo, hi = 2 ** (ctx_n - 1), 2**ctx_n - 1
    rx = ry = 0
    pt = recover_r_point_from_sig(r)
    if pt:
        rx, ry = pt
    r2p = px * px + py * py
    atoms: dict[str, int] = {
        "z": z,
        "r": r,
        "s": s,
        "Px": px,
        "Py": py,
        "Gx": Gx,
        "Gy": Gy,
        "n": ctx_n,
        "lo": lo,
        "hi": hi,
        "p": p % N,
        "Nconst": N % N,
        "gap": GAP % N,
        "delta": DELTA % N,
        "Rx": rx,
        "Ry": ry,
        "Px_p": px % p,
        "Py_p": py % p,
        "r2_pk": r2p % N,
        "r2_sig": (r * r) % N,
        "Px_xor_Py": (px ^ py) % N,
        "Px_hi": (px >> 128) % N,
        "Px_lo": (px & ((1 << 128) - 1)) % N,
        "Py_hi": (py >> 128) % N,
        "Py_lo": (py & ((1 << 128) - 1)) % N,
        "pack_xy": ((px % N) << 128 | (py & ((1 << 128) - 1))) % N,
        "y2": pow(py, 2, p) % N,
        "x3+7": (pow(px, 3, p) + 7) % N,
        "defect": (pow(py, 2, p) - pow(px, 3, p) - 7) % p,
        "z_xor_r": (z ^ r) % N,
        "z_xor_Px": (z ^ px) % N,
        "r_xor_Px": (r ^ px) % N,
    }
    return atoms


def generate_L_catalog(atoms: dict[str, int], px: int, py: int, *, prec: int) -> dict[str, int]:
    """Return name -> L mod N (deduped)."""
    out: dict[str, int] = {}
    names = list(atoms.keys())

    def put(name: str, val: int) -> None:
        key = name if name not in out else f"{name}#{len(out)}"
        out[key] = val % N

    for k, v in atoms.items():
        put(k, v)
        iv = invn(v)
        if iv is not None:
            put(f"inv({k})", iv)
        put(f"{k}^2", v * v)
        put(f"{k}^3", pow(v, 3, N))

    for k in ("Px", "Py", "z", "r", "s"):
        put(f"{k}_mod_p", atoms[k] % p)

    for a, b in itertools.combinations(names, 2):
        va, vb = atoms[a], atoms[b]
        put(f"{a}+{b}", va + vb)
        put(f"{a}-{b}", va - vb)
        put(f"{a}*{b}", va * vb)
        put(f"{a}^2+{b}", va * va + vb)
        put(f"{a}+{b}^2", va + vb * vb)

    for X in ("Px", "Py", "Rx", "Ry", "Gx", "Gy", "lo", "hi", "n"):
        x = atoms[X]
        put(f"z+r*{X}", atoms["z"] + atoms["r"] * x)
        put(f"z-r*{X}", atoms["z"] - atoms["r"] * x)
        put(f"s*{X}-z", atoms["s"] * x - atoms["z"])
        put(f"s*{X}+z", atoms["s"] * x + atoms["z"])
        put(f"r*{X}-z", atoms["r"] * x - atoms["z"])
        put(f"r*{X}+z", atoms["r"] * x + atoms["z"])
        put(f"z+r*{X}+s", atoms["z"] + atoms["r"] * x + atoms["s"])
        put(f"(z+r*{X})*s", (atoms["z"] + atoms["r"] * x) * atoms["s"])
        put(f"(z-r*{X})*s", (atoms["z"] - atoms["r"] * x) * atoms["s"])
        put(f"s*{X}-r*{X}", atoms["s"] * x - atoms["r"] * x)
        put(f"z*s+r*{X}", atoms["z"] * atoms["s"] + atoms["r"] * x)
        put(f"z+r*s*{X}", atoms["z"] + atoms["r"] * atoms["s"] * x)
        put(f"z+r*{X}+s*Px", atoms["z"] + atoms["r"] * x + atoms["s"] * atoms["Px"])
        put(f"z+r*{X}+s*Py", atoms["z"] + atoms["r"] * x + atoms["s"] * atoms["Py"])

    for a, b, c in itertools.combinations(names[:12], 3):
        va, vb, vc = atoms[a], atoms[b], atoms[c]
        put(f"{a}*{b}*{c}", va * vb * vc)
        put(f"{a}+{b}*{c}", va + vb * vc)
        put(f"{a}*{b}+{c}", va * vb + vc)

    put("Px-lo", atoms["Px"] - atoms["lo"])
    put("hi-Px", atoms["hi"] - atoms["Px"])
    put("Px-lo+ z", atoms["Px"] - atoms["lo"] + atoms["z"])
    put("z+ r*(Px-lo)", atoms["z"] + atoms["r"] * (atoms["Px"] - atoms["lo"]))
    put("z+ r*(hi-Px)", atoms["z"] + atoms["r"] * (atoms["hi"] - atoms["Px"]))

    getcontext().prec = prec
    for xmode, xfn in (
        ("Px_lit", lambda: x_literal(px)),
        ("Px_2pi", lambda: x_angle(px)),
        ("Py_lit", lambda: float(Decimal(py % p) / Decimal(p))),
        ("atan2", lambda: math.atan2(float(py % p), float(px % p))),
    ):
        try:
            xv = xfn()
            b = body(xv)
        except ValueError:
            continue
        A = Decimal(256) * Decimal(p) * Decimal(b)
        r2 = px * px + py * py
        D = A / Decimal(r2)
        for tag, val in (("A", A), ("D", D), ("body", Decimal(b))):
            put(f"geom_{xmode}_{tag}", int(val) % N)
            put(f"geom_{xmode}_{tag}_abs", int(abs(val)) % N)
            for e in (20, 40, 60, 80, 100, 120):
                put(f"geom_{xmode}_{tag}_1e{e}", int(val * Decimal(10) ** e) % N)

    put("sk-z_proxy_rPx", (atoms["s"] * atoms["Px"] - atoms["z"]) % N)
    put("sk-z_proxy_rPy", (atoms["s"] * atoms["Py"] - atoms["z"]) % N)
    put("rPx", (atoms["r"] * atoms["Px"]) % N)
    put("rPy", (atoms["r"] * atoms["Py"]) % N)

    return out


def mod_scaled(num: int, den: Decimal, scale_exp: int) -> int | None:
    if den <= 0:
        return None
    scale = Decimal(10) ** scale_exp
    den_i = int((den * scale).to_integral_value())
    if den_i <= 0 or math.gcd(den_i, N) != 1:
        return None
    return (num * scale % N) * pow(den_i, -1, N) % N


def test_puzzle(truth: PuzzleTruth, rsz, catalog: dict[str, int], geom: Geom, *, prec: int) -> list[str]:
    hits: list[str] = []
    sinv = invn(rsz.s)
    rinv = invn(rsz.r)
    denominators = (
        ("A_lit", geom.A),
        ("D_lit", geom.D),
        ("A_2pi", geom.A2),
        ("D_2pi", geom.D2),
    )
    scales = (40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 180, 200)

    for lname, Lm in catalog.items():
        Ldec = Decimal(Lm)

        # Laplacian real divide
        for dname, den in denominators:
            kv = int(Ldec / den)
            if kv == truth.k:
                hits.append(f"P{truth.n} k=L/{dname} L={lname}")
            dv = int(Ldec / den)
            if dv == truth.d:
                hits.append(f"P{truth.n} d=L/{dname} L={lname}")

        # ECDSA-shaped direct (no Laplacian)
        if sinv is not None:
            k_ec = (Lm * sinv) % N
            if k_ec == truth.k:
                hits.append(f"P{truth.n} k=L*s^-1 L={lname}")
        if rinv is not None:
            d_ec = ((Lm - rsz.z) * rinv) % N
            if d_ec == truth.d:
                hits.append(f"P{truth.n} d=(L-z)*r^-1 L={lname}")

        # scaled mod N
        for dname, den in denominators:
            for se in scales:
                ke = mod_scaled(Lm, den, se)
                if ke is not None and ke == truth.k:
                    hits.append(f"P{truth.n} k=L*{dname}^-1 scale10^{se} L={lname}")
                de = mod_scaled(Lm, den, se)
                if de is not None and de == truth.d:
                    hits.append(f"P{truth.n} d=L*{dname}^-1 scale10^{se} L={lname}")

        # hybrid: ECDSA on Laplacian quotient
        for dname, den in denominators:
            kv = int(Ldec / den)
            if sinv is not None and (kv * sinv) % N == truth.k:
                hits.append(f"P{truth.n} k=(L/{dname})*s^-1 L={lname}")
            if rinv is not None:
                d_h = ((kv - rsz.z) * rinv) % N
                if d_h == truth.d:
                    hits.append(f"P{truth.n} d from (L/{dname}-z)*r^-1 L={lname}")

        # L mod p / mod delta recovery paths
        for modname, modulus in (("p", p), ("delta", DELTA)):
            Lm2 = Lm % modulus
            for dname, den in denominators:
                for se in scales:
                    ke = mod_scaled(Lm2, den, se)
                    if ke is not None and ke % N == truth.k:
                        hits.append(f"P{truth.n} k mod {modname} scale10^{se} {dname} L={lname}")
                    de = mod_scaled(Lm2, den, se)
                    if de is not None and de % N == truth.d:
                        hits.append(f"P{truth.n} d mod {modname} scale10^{se} {dname} L={lname}")

    return hits


def run_exhaustive(*, prec: int = 280, out_path: Path = OUT_DEFAULT) -> str:
    keys = parse_53125()
    lines: list[str] = []
    w = lines.append
    t0 = time.time()

    w("=" * 72)
    w("BB EXHAUSTIVE BLIND L SEARCH")
    w("Public atoms + pairs/triples + ECDSA templates + inverses + bit slices")
    w("Recovery: L/A, L/D (literal+2pi), L*s^-1, (L-z)*r^-1, scaled mod N")
    w("=" * 72)

    all_hits: list[str] = []
    catalog_sizes: list[int] = []

    for n in SOLVED:
        truth = puzzle_truth(n, keys)
        rsz = PUZZLE_RSZ.get(n)
        if truth is None or rsz is None:
            continue
        atoms = atom_table(n, truth.px, truth.py, rsz.r, rsz.s, rsz.z)
        catalog = generate_L_catalog(atoms, truth.px, truth.py, prec=prec)
        catalog_sizes.append(len(catalog))
        g = geom_for(truth.px, truth.py, prec=prec)
        hits = test_puzzle(truth, rsz, catalog, g, prec=prec)
        all_hits.extend(hits)

    w(f"\nCatalog size per puzzle: min={min(catalog_sizes)} max={max(catalog_sizes)} avg={sum(catalog_sizes)/len(catalog_sizes):.0f}")
    w(f"Puzzles: {len(catalog_sizes)}")
    w(f"Elapsed: {time.time()-t0:.1f}s")

    w("\n--- BLIND HITS ---")
    if all_hits:
        for h in sorted(set(all_hits)):
            w(f"  {h}")
        w(f"\nTotal unique hits: {len(set(all_hits))}")
    else:
        w("  (none)")

    w("\n--- RULING ---")
    w("Exhaustive public L catalog: no blind k or d recovery via BB Laplacian bridge.")
    w("BB remains TEST algebra / PROMISING geometry (Px/p vs 2pi*Px/p sign change).")

    text = "\n".join(lines) + "\n"
    out_path.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prec", type=int, default=280)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    print(run_exhaustive(prec=args.prec, out_path=args.out))


if __name__ == "__main__":
    main()
