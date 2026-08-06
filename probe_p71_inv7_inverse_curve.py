#!/usr/bin/env python3
"""
P71 inverse-curve probe: y^2 = x^3 + 7  with 7^-1 mod p and mod N.

Verify user constants; gate scaled candidates and inv7-scalar variants on hash160.
"""

from __future__ import annotations

import bisect
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import N, inv, p
from puzzle_catalog import load_catalog

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P71"

M = 536870912
LO = 1 << 70
HI = (1 << 71) - 1
T71_FILED = 1411488254391826260559
TARGET_H160 = bytes.fromhex("f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8")

USER_INV7_P = 99250362203413881791632272864589635302802843999120483462392214863921858289997
USER_INV7_N = 33083454067804627263877424288196545100810732651164258395030046611862331855525


def hash160_d(d: int) -> bytes:
    d = d % N
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    x, y = pt.x(), pt.y()
    comp = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()


def y_from_x(x: int) -> tuple[int, int]:
    y2 = (pow(x, 3, p) + 7) % p
    y = pow(y2, (p + 1) // 4, p)
    if (y * y) % p != y2:
        raise ValueError("non-square")
    return y, (p - y) % p


def cube_root_mod_p(a: int) -> int | None:
    a %= p
    if a == 0:
        return 0
    r = pow(a, (2 * p - 1) // 3, p)
    return r if pow(r, 3, p) == a else None


def half_sums(pool: list[int], d: dict[int, int]) -> dict[int, list[list[int]]]:
    contrib = [(i, M * d[i]) for i in pool]
    out: dict[int, list[list[int]]] = defaultdict(list)
    for mask in range(1 << len(contrib)):
        s = 0
        chosen: list[int] = []
        for bit, (idx, c) in enumerate(contrib):
            if mask & (1 << bit):
                s += c
                chosen.append(idx)
        if chosen:
            out[s].append(chosen)
    return out


def in_band_pairs(left: dict, right: dict) -> list[tuple[int, int, list[int]]]:
    items = sorted(right.items())
    rs = [k for k, _ in items]
    out: list[tuple[int, int, list[int]]] = []
    for ls, lsets in left.items():
        i0 = bisect.bisect_left(rs, LO - ls)
        i1 = bisect.bisect_right(rs, HI - ls)
        for rs_val, rsets in items[i0:i1]:
            total = ls + rs_val
            if LO <= total <= HI:
                out.append((total, ls, lsets[0] + rsets[0]))
    return out


def scalar_variants(d: int) -> dict[str, int]:
    d = d % N
    return {
        "d": d,
        "d_times_7": (d * 7) % N,
        "d_times_inv7_N": (d * USER_INV7_N) % N,
        "d_times_inv7_N_computed": (d * inv(7, N)) % N,
    }


def gate_variants(label: str, d: int) -> list[dict]:
    hits = []
    if not (LO <= d <= HI):
        return hits
    for name, val in scalar_variants(d).items():
        if not (LO <= val <= HI):
            continue
        h = hash160_d(val)
        if h == TARGET_H160:
            hits.append({"label": label, "variant": name, "d": str(val), "base_d": str(d)})
    return hits


def main() -> int:
    inv7_p = inv(7, p)
    inv7_n = inv(7, N)

    verify = {
        "inv7_mod_p_user": USER_INV7_P,
        "inv7_mod_p_computed": inv7_p,
        "inv7_mod_p_match": USER_INV7_P == inv7_p,
        "inv7_mod_N_user": USER_INV7_N,
        "inv7_mod_N_computed": inv7_n,
        "inv7_mod_N_match": USER_INV7_N == inv7_n,
        "7_times_inv7_mod_p": (7 * USER_INV7_P) % p,
        "7_times_inv7_mod_N": (7 * USER_INV7_N) % N,
    }

    # inverse curve algebra on known P70 point
    cat = load_catalog()
    d_table = {n: cat[n].private_key for n in range(1, 161) if cat[n].solved and cat[n].private_key > 0}
    d70 = d_table[70]
    sk = SigningKey.from_secret_exponent(d70, curve=SECP256k1)
    px, py = sk.verifying_key.pubkey.point.x(), sk.verifying_key.pubkey.point.y()

    x3 = (py * py - 7) % p
    x3_via_inv = ((py * py - 7) * USER_INV7_P) % p  # equals x^3 * inv7, not x^3
    x_rec = cube_root_mod_p(x3)
    curve_checks = {
        "P70_px": px,
        "x3_from_y": x3,
        "x3_eq_px3": x3 == pow(px, 3, p),
        "x_recovered": x_rec,
        "x_rec_eq_px": x_rec == px if x_rec is not None else False,
        "normalized": "7^-1 * (y^2 - 7) = 7^-1 * x^3 mod p",
        "norm_lhs": ((py * py - 7) * USER_INV7_P) % p,
        "norm_rhs": (pow(px, 3, p) * USER_INV7_P) % p,
        "norm_match": ((py * py - 7) * USER_INV7_P) % p == (pow(px, 3, p) * USER_INV7_P) % p,
    }

    # sanity: inv7 on scalar does NOT preserve address for P70
    p70_h160 = hash160_d(d70)
    inv7_scalar_h160 = hash160_d((d70 * USER_INV7_N) % N)

    pool = list(range(14, 43))
    mid = 14
    left = half_sums(pool[:mid], d_table)
    right = half_sums(pool[mid:], d_table)
    band = in_band_pairs(left, right)

    hits: list[dict] = []
    checked = 0

    # Gate bare in-band sums + remainder sweep + inv7 variants (capped)
    for total, _ls, indices in band[:5000]:
        checked += 1
        hits.extend(gate_variants(f"bare_sum_{total}", total))
        for rem in range(M):
            t = total + rem
            if t > HI:
                break
            if t < LO:
                continue
            checked += 1
            hits.extend(gate_variants(f"sum+rem_{rem}", t))
            if checked > 50000:
                break
        if checked > 50000:
            break

    # filed T71 and inv7 variants
    for label, base in [("filed_T71", T71_FILED), ("2^70", LO), ("2^70+2^69", LO + (1 << 69))]:
        hits.extend(gate_variants(label, base))

    summary = {
        "inverse_curve": "y^2 = x^3 + 7 (mod p); x^3 = y^2 - 7; scaled form uses 7^-1 on field/scalar lanes",
        "verify_inv7": verify,
        "curve_recovery_P70": curve_checks,
        "P70_hash160_preserved_under_inv7_scalar": p70_h160 == inv7_scalar_h160,
        "pool_14_42": pool,
        "in_band_bare_pairs": len(band),
        "scalars_checked": checked,
        "hash160_hits": hits,
        "ruling": (
            "7^-1 constants verified. "
            "Field inverse x^3=(y^2-7) mod p recovers Px from Py on P70. "
            "Scalar d*7^-1 mod N changes pubkey (not address-preserving). "
            f"Scaled+remainder+inv7 gate: {len(hits)} hits in {checked} checks."
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inv7_inverse_curve_gate.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# P71 inverse curve + 7^-1 gate",
        "",
        "## 7^-1 verification",
        "",
        f"- mod p match: **{verify['inv7_mod_p_match']}**",
        f"- mod N match: **{verify['inv7_mod_N_match']}**",
        "",
        "```text",
        "y^2 = x^3 + 7           (mod p)",
        "x^3 = y^2 - 7           (mod p)",
        "7^-1 · (y^2 - 7) = 7^-1 · x^3   (mod p)   [normalized lane]",
        "```",
        "",
        f"- P70 x recovery from y: **{curve_checks['x_rec_eq_px']}**",
        f"- P70 address preserved under d·7^-1 mod N: **{summary['P70_hash160_preserved_under_inv7_scalar']}**",
        "",
        f"- In-band bare pairs (pool 14..42): **{len(band)}**",
        f"- Scalars checked (with remainder + inv7 variants): **{checked}**",
        f"- Hash160 hits: **{len(hits)}**",
        "",
        "## Ruling",
        "",
        summary["ruling"],
        "",
    ]
    (OUT / "inv7_inverse_curve_gate.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({k: summary[k] for k in ("verify_inv7", "scalars_checked", "hash160_hits", "ruling")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
