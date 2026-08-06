#!/usr/bin/env python3
"""
Candidate gate stack for P135 (and optional other puzzles).

Filters candidates — does NOT invent d from public signals.

  candidate d
    → range check
    → [d]G x/y check
    → β slot consistency
    → packet fingerprint match
    → p/N shadow match
    → RSZ check if d known path from k

  candidate k
    → d = (s*k − z) * r⁻¹ mod N
    → same gates
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

# P135 RSZ (hashkeys partial spend) from briefcase ledger
P135_R = 90653255469745952335985143920649543885181555095025199315947044135806663628368
P135_S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
P135_Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def packet_p_from_xy(px: int, py: int, branch: str = "p_minus_y") -> Decimal:
    y_digits = py if branch == "y" else (p - py) % p
    return Decimal(f"{px}.{y_digits}") / Decimal(p)


def ec_xy(d: int) -> tuple[int, int]:
    d = d % N
    if d == 0:
        raise ValueError("d ≡ 0 mod N")
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    return pt.x(), pt.y()


def gate_stack(
    d: int,
    *,
    puzzle: int = 135,
    target_px: int,
    target_py: int,
    lo: int,
    hi: int,
    target_packet_p: Decimal,
) -> dict:
    gates: list[dict] = []

    # 1. range
    in_range = lo <= d <= hi
    gates.append({
        "gate": "range",
        "pass": in_range,
        "detail": f"d in [{lo}, {hi}]",
    })
    if not in_range:
        return {"d": str(d), "pass": False, "gates": gates}

    # 2. [d]G == target
    try:
        dx, dy = ec_xy(d)
    except Exception as exc:
        gates.append({"gate": "ec_multiply", "pass": False, "detail": str(exc)})
        return {"d": str(d), "pass": False, "gates": gates}

    xy_ok = dx == target_px and (dy == target_py or dy == (p - target_py) % p)
    gates.append({
        "gate": "ec_xy_match",
        "pass": xy_ok,
        "detail": f"got Px={dx} Py={dy}",
    })
    # If EC matches, we have the key — remaining gates are consistency checks.
    # If EC fails, still report filter diagnostics.

    # 3. β slot consistency (pubkey is slot 3)
    px2 = (dx * inv(BETA, p)) % p
    px3_check = (px2 * BETA) % p == dx
    gates.append({
        "gate": "beta_slot",
        "pass": px3_check,
        "detail": "Px2 * beta == Px3",
    })

    # 4. packet fingerprint (p−y branch primary)
    cand_packet = packet_p_from_xy(dx, dy, "p_minus_y")
    # match target packet to many decimals (identity)
    packet_ok = cand_packet == target_packet_p or (
        dx == target_px and (dy == target_py or dy == (p - target_py) % p)
    )
    # stricter: if EC matched, packet must match; if not, packet mismatch is expected
    gates.append({
        "gate": "packet_fingerprint",
        "pass": packet_ok,
        "detail": format(cand_packet, "f")[:48] + "…",
    })

    # 5. p/N shadow: floor(packet*N) - map_p_to_n(Px) in {0,1}
    floor_n = int(cand_packet * Decimal(N))
    int_only = map_p_to_n(dx)
    off_by = floor_n - int_only
    shadow_ok = off_by in (0, 1)
    # target shadow match when EC matches
    tgt_packet = target_packet_p
    tgt_floor_n = int(tgt_packet * Decimal(N))
    shadow_match = (floor_n == tgt_floor_n) if xy_ok else shadow_ok
    gates.append({
        "gate": "p_N_shadow",
        "pass": shadow_match,
        "detail": f"off_by={off_by} floor_N={floor_n}",
    })

    # 6. RSZ identity check: s*k = z + r*d  ⇒  k = (z + r*d) * s^-1
    # For a d candidate, derive k and check k in 1..N-1 (always) and optional [k]G x == r
    k = ((P135_Z + P135_R * d) * inv(P135_S, N)) % N
    # verify ECDSA equation consistency (tautological by construction of k)
    # stronger: x([k]G) == r (nonce point)
    try:
        kx, _ky = ec_xy(k)
        rsz_ok = kx == P135_R
    except Exception:
        rsz_ok = False
    gates.append({
        "gate": "rsz_nonce_point",
        "pass": rsz_ok,
        "detail": f"k={k} x([k]G)==r",
    })

    all_pass = all(g["pass"] for g in gates)
    return {
        "puzzle": puzzle,
        "d": str(d),
        "k_from_rsz": str(k),
        "pass": all_pass,
        "ec_match": xy_ok,
        "gates": gates,
    }


def d_from_k(k: int) -> int:
    """d = (s*k − z) * r⁻¹ mod N."""
    return ((P135_S * k - P135_Z) * inv(P135_R, N)) % N


def main() -> int:
    ap = argparse.ArgumentParser(description="P135 candidate gate stack")
    ap.add_argument("--d", type=str, help="candidate private key (int or 0x hex)")
    ap.add_argument("--k", type=str, help="candidate nonce k (int or 0x hex)")
    ap.add_argument("--puzzle", type=int, default=135)
    ap.add_argument("--json-out", type=str, default="")
    args = ap.parse_args()

    if not args.d and not args.k:
        ap.error("provide --d or --k")

    catalog = load_catalog()
    e = catalog[args.puzzle]
    if not e.public_key:
        raise SystemExit(f"puzzle {args.puzzle} has no pubkey")
    tpx, tpy = pubkey_xy(e.public_key)
    tgt_packet = packet_p_from_xy(tpx, tpy, "p_minus_y")

    results = []
    if args.k:
        k = int(args.k, 0)
        d = d_from_k(k)
        print(f"from k: d = (s*k - z) * r^-1 mod N = {d}")
        results.append(
            gate_stack(
                d,
                puzzle=args.puzzle,
                target_px=tpx,
                target_py=tpy,
                lo=e.range_min,
                hi=e.range_max,
                target_packet_p=tgt_packet,
            )
        )
    if args.d:
        d = int(args.d, 0)
        results.append(
            gate_stack(
                d,
                puzzle=args.puzzle,
                target_px=tpx,
                target_py=tpy,
                lo=e.range_min,
                hi=e.range_max,
                target_packet_p=tgt_packet,
            )
        )

    for res in results:
        print(f"\nd={res['d']}")
        print(f"PASS={res['pass']}  ec_match={res['ec_match']}")
        for g in res["gates"]:
            flag = "OK" if g["pass"] else "FAIL"
            print(f"  [{flag}] {g['gate']}: {g['detail']}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0 if results and results[0]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
