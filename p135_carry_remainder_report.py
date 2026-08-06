#!/usr/bin/env python3
"""P135 carry-layer match report for rem = (N*s) mod r (barcode lane)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    N,
    PuzzleConfig,
    apply_puzzle_defaults,
    compute_order_in_the_court,
    p,
    run_pipeline,
)

# Barcode / truersmxy lane (user-confirmed)
S_BAR = 15509729875763924304053419655647994379903175655107184284998698212653288468986
R_BAR = 90653255469745952335985143920649543885181555095025199315947044135806663628368
M_BAR = 66278737796829840734606014530466656889790152192829793669891337810330530090951
K_BAR = 19089036453356401353257357002647987614981495902151757130742235757133693952525
M_HEX = int("92886FAAF53F90A5C03D6AF773A726E75097179306B980E5D28772E612E00FC7", 16)


def lo_dist(a: int, b: int, lo: int) -> int:
    d = (a - b) % lo
    return min(d, lo - d)


def bx_carry(lambda_n: int, qx: int, qx_scaled: int) -> tuple[int | None, int]:
  num = lambda_n * qx - qx_scaled
  rem = num % N
  if rem == 0:
      return num // N, 0
  return None, rem


def build_p135_bridge(puzzle_row: int = 2) -> dict[str, int]:
    """Compute P135 bridge integers (row index 0-based; 2 = notebook row 3)."""
    cfg = PuzzleConfig(puzzle_num=135, row=puzzle_row)
    apply_puzzle_defaults(cfg)
    lo, hi = cfg.lo, cfg.hi
    delta = p - N
    px_triple, rx_triple = cfg.Px, cfg.rx
    py = cfg.Py if cfg.Py is not None else 0
    ry = cfg.ry if cfg.ry is not None else 0

    qx = [(px_triple[i] * delta) % N for i in range(3)]
    qy = (py * delta) % N
    qry = (ry * delta) % N
    lambda_ns = [(qx[i] * pow(rx_triple[i], -1, N)) % N for i in range(3)]
    lam_y_n = (py * pow(ry, -1, N)) % N
    lambda_p = (px_triple[puzzle_row] * pow(rx_triple[puzzle_row], -1, p)) % p

    gap = (lambda_ns[puzzle_row] - lambda_p) % N
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=rx_triple,
        qy=ry,
        qx_scaled=qx,
        qy_scaled=qy,
        lambda_ns=lambda_ns,
        lam_y_n=lam_y_n,
    )

    out: dict[str, int] = {
        "GAP": gap,
        "Lambda_N_row": lambda_ns[puzzle_row],
        "shelf2": oitc.shelf2,
        "shelf3": oitc.shelf3,
        "shelf_y": oitc.shelf_y,
        "C_floor": oitc.c_floor,
        "d_cube_lift2": oitc.d_cube_lift2,
        "d_cube_lift3": oitc.d_cube_lift3,
        "d_cube_res_y": oitc.d_cube_res_y,
        "defect_lo": (delta + lo) % N,
        "defect_hi": (delta + (hi - 1)) % N,
        "Px_target": px_triple[puzzle_row],
        "Py": py,
        "rx_target": rx_triple[puzzle_row],
        "ry": ry,
        "rx2_true": rx_triple[1],
    }

    by_num = lam_y_n * qry - qy
    if by_num % N == 0:
        out["byN"] = by_num // N
    b3y_num = lam_y_n * ry - py
    if b3y_num % p == 0:
        out["b3y"] = b3y_num // p

    for i in range(3):
        b, rem = bx_carry(lambda_ns[puzzle_row], rx_triple[i], qx[i])
        if b is not None:
            out[f"bx_row{puzzle_row+1}_ownrowL{i+1}"] = b
        if rem:
            out[f"rem_bx_row{puzzle_row+1}_slot{i+1}"] = rem

    for i in range(3):
        lam_i = (qx[i] * pow(rx_triple[i], -1, N)) % N
        b, rem = bx_carry(lam_i, rx_triple[i], qx[i])
        if b is not None:
            out[f"bx_ownrowL{i+1}"] = b
        if rem:
            out[f"rem_bx_ownrowL{i+1}"] = rem

    return out


def build_barcode_lane() -> dict[str, int]:
    rem = (N * S_BAR) % R_BAR
    skm = S_BAR * K_BAR - M_BAR
    px = ((skm * pow(R_BAR, -1, N)) % N)
    return {
        "rem_Ns_mod_r": rem,
        "q_Ns_div_r": (N * S_BAR) // R_BAR,
        "s_barcode": S_BAR,
        "r_rx2_true": R_BAR,
        "m_hash": M_BAR,
        "k_nonce": K_BAR,
        "M_hex": M_HEX,
        "N_minus_s": N - S_BAR,
        "N_minus_m": N - M_BAR,
        "N_minus_Mhex": N - M_HEX,
        "skm_mod_r": skm % R_BAR,
        "skm_div_r_floor": skm // R_BAR,
        "Px_from_skm_modN": px,
        "s_times_r_modN": (S_BAR * R_BAR) % N,
        "m_times_r_modN": (M_BAR * R_BAR) % N,
    }


def rank_family(rem: int, family: dict[str, int], lo: int) -> list[tuple[int, str, int, bool]]:
    rows: list[tuple[int, str, int, bool]] = []
    for name, val in family.items():
        exact = val == rem
        rows.append((0 if exact else lo_dist(val, rem, lo), name, val % lo, exact))
    rows.sort(key=lambda t: (0 if t[3] else 1, t[0]))
    return rows


def main() -> None:
    lo = 1 << 134
    delta = p - N
    rem = (N * S_BAR) % R_BAR

    print("=" * 72)
    print("P135 CARRY REMAINDER REPORT")
    print("=" * 72)
    print(f"rem = (N*s) mod r")
    print(f"  rem bitlen = {rem.bit_length()}")
    print(f"  q bitlen   = {((N * S_BAR) // R_BAR).bit_length()}")
    print(f"  f = rem/r  = {rem / R_BAR}")
    print(f"  rem mod LO = {rem % lo}")
    print(f"  rem mod delta = {rem % delta}")
    print(f"  rem // delta  = {rem // delta}")
    print()

    bridge = build_p135_bridge(puzzle_row=2)
    barcode = build_barcode_lane()

    print("--- EXACT INTEGER MATCHES TO rem ---")
    exact_hits = [name for name, v in {**bridge, **barcode}.items() if v == rem]
    if exact_hits:
        for name in exact_hits:
            print(f"  EXACT: {name}")
    else:
        print("  (none)")
    print()

    for title, family in [
        ("P135 bridge carries (row 3)", bridge),
        ("Barcode / ECDSA lane", barcode),
    ]:
        print(f"--- {title}: closest mod LO ---")
        for dist, name, residue, exact in rank_family(rem, family, lo)[:12]:
            tag = "EXACT" if exact else f"dist={dist}"
            print(f"  {name:28} {tag:28} mod LO = {residue}")
        print()

    print("--- delta ladder (rem - X) // delta ---")
    for name, val in sorted(bridge.items(), key=lambda kv: kv[0]):
        if name.startswith(("bx", "byN", "b3y", "GAP", "rem_", "shelf")):
            diff = rem - val
            if diff % delta == 0:
                print(f"  rem - {name} = {diff // delta} * delta")

    print()
    print("--- sibling remainders (same s,r family) ---")
    skm_rem = barcode["skm_mod_r"]
    print(f"  (s*k - m) mod r = {skm_rem}")
    print(f"  differs from rem by {abs(skm_rem - rem).bit_length()} bits")
    print(f"  Px recovered = {barcode['Px_from_skm_modN']}")
    print(f"  P135 Px      = {bridge['Px_target']}")
    print(f"  Px match     = {barcode['Px_from_skm_modN'] == bridge['Px_target']}")
    print()

    # Optional: regenerate frozen pipeline output for audit trail
    out_path = Path(__file__).resolve().parent / "p135_carry_remainder_report.txt"
    cfg = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(cfg)
    pl = run_pipeline(cfg)
    out_path.write_text("\n".join(pl.lines) + "\n", encoding="utf-8")
    print(f"Full pipeline log written: {out_path}")


if __name__ == "__main__":
    main()
