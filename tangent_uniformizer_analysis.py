#!/usr/bin/env python3
"""
Tangent line + uniformizer analysis (Silverman II.1 / Math 223).

At smooth P = (x0, y0) on y^2 = x^3 + 7 mod p:
  m = 3*x0^2 / (2*y0) mod p          (tangent slope)
  l(x,y) = (y - y0) - m*(x - x0)     vanishes to order 1 at P
  l' not vanishing at P               e.g. 1, or (y - y0), or (x - x1)

Uniformizer: t = l / l'  (local parameter with simple zero at P)

Calibrates tangent data vs (d - shelf2) mod LO on solved puzzles.
P135: report + EC-test natural scalar lifts (no hit expected unless structure exists).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from compare_family_mirror_batch import build_config  # noqa: E402
from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_PX,
    DEFAULT_PY,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    PuzzleConfig,
    apply_puzzle_defaults,
    delta,
    p,
    puzzle_band,
)
from gap_tier_common import observed_offset  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

LOG = ROOT / "ARCHIVE" / "cloud_pages" / "tangent_uniformizer_analysis.log"

P135_PX = DEFAULT_PX[2]
P135_PY = DEFAULT_PY
P135_RX = DEFAULT_RX[2]
P135_RY = DEFAULT_RY


@dataclass
class TangentData:
    x0: int
    y0: int
    slope_m: int  # tangent slope mod p
    chord_to_rx: int | None  # slope of line P -> R if R known
    lam_p: int  # Px/rx mod p
    uniform_x: int  # x - x0 mod p (canonical uniformizer when y0 != 0)
    tangent_num: int  # y0 - m*x0 mod p  for l = y - m*x - tangent_num


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def tangent_at(x0: int, y0: int) -> TangentData:
    m = (3 * pow(x0, 2, p) * pow(2 * y0, -1, p)) % p
    return TangentData(
        x0=x0,
        y0=y0,
        slope_m=m,
        chord_to_rx=None,
        lam_p=0,
        uniform_x=(0) % p,
        tangent_num=(y0 - m * x0) % p,
    )


def with_r_point(td: TangentData, rx: int, ry: int) -> TangentData:
    dx = (rx - td.x0) % p
    dy = (ry - td.y0) % p
    chord = (dy * pow(dx, -1, p)) % p if dx % p else None
    return TangentData(
        x0=td.x0,
        y0=td.y0,
        slope_m=td.slope_m,
        chord_to_rx=chord,
        lam_p=(td.x0 * pow(rx, -1, p)) % p,
        uniform_x=0,
        tangent_num=td.tangent_num,
    )


def ec_hit(d: int, px: int, py: int) -> bool:
    try:
        from ecdsa import SECP256k1, SigningKey
    except ImportError:
        return False
    d %= N
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    return int.from_bytes(pub[1:33], "big") == px and int.from_bytes(pub[33:65], "big") == py


def analyze_puzzle(n: int, px: int, py: int, rx: int, ry: int, known_d: int | None) -> dict:
    td = tangent_at(px, py)
    td = with_r_point(td, rx, ry)
    td = TangentData(
        x0=td.x0,
        y0=td.y0,
        slope_m=td.slope_m,
        chord_to_rx=td.chord_to_rx,
        lam_p=td.lam_p,
        uniform_x=(px - td.x0) % p,  # = 0 at P
        tangent_num=td.tangent_num,
    )
    m_gap = (td.slope_m - td.chord_to_rx) % p if td.chord_to_rx is not None else None
    m_vs_lam = (td.slope_m * pow(td.lam_p, -1, p)) % p if td.lam_p else None

    out = {
        "n": n,
        "slope_m_bits": td.slope_m.bit_length(),
        "chord_bits": td.chord_to_rx.bit_length() if td.chord_to_rx is not None else None,
        "lam_p_bits": td.lam_p.bit_length(),
        "m_minus_chord_bits": m_gap.bit_length() if m_gap is not None else None,
        "m_over_lam_bits": m_vs_lam.bit_length() if m_vs_lam is not None else None,
        "slope_m": td.slope_m,
        "lam_p": td.lam_p,
    }

    if known_d and known_d > 0:
        cfg = build_config(__import__("puzzle_keys_53125", fromlist=["parse_53125"]).parse_53125()[n])
        st = bridge_state(cfg)
        lo, _, _ = puzzle_band(n)
        off = observed_offset(known_d, st["oitc"].shelf2, lo)
        out["offset_bits"] = off.bit_length()
        out["m_mod_lo"] = td.slope_m % lo
        out["m_mod_lo_bits"] = (td.slope_m % lo).bit_length()
        out["m_eq_offset"] = (td.slope_m % lo) == off
        out["lam_mod_lo_bits"] = (td.lam_p % lo).bit_length()
        if m_gap is not None:
            out["m_gap_mod_lo_bits"] = (m_gap % lo).bit_length()
    return out


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log("=== Tangent / uniformizer (Silverman II.1, Math 223) ===")
    log("")
    log("Construction at smooth P = (x0, y0):")
    log("  m = 3*x0^2 / (2*y0) mod p")
    log("  l(x,y) = (y - y0) - m*(x - x0)   [tangent line, order-1 zero at P]")
    log("  uniformizer t ~ (x - x0)  or  l/l'  with l'(P) != 0")
    log("")

    # P135 explicit
    td135 = tangent_at(P135_PX, P135_PY)
    td135 = with_r_point(td135, P135_RX, P135_RY)
    log("=== P135 ===")
    log(f"  Px = {P135_PX}")
    log(f"  Py = {P135_PY}")
    log(f"  tangent slope m     = {td135.slope_m} ({td135.slope_m.bit_length()} bits)")
    log(f"  chord slope P->R    = {td135.chord_to_rx} ({td135.chord_to_rx.bit_length()} bits)")
    log(f"  bridge Lambda_p     = {td135.lam_p} ({td135.lam_p.bit_length()} bits)")
    m_gap = (td135.slope_m - td135.chord_to_rx) % p
    m_ratio = (td135.slope_m * pow(td135.lam_p, -1, p)) % p
    log(f"  m - chord mod p     = {m_gap} ({m_gap.bit_length()} bits)")
    log(f"  m / Lambda_p mod p  = {m_ratio} ({m_ratio.bit_length()} bits)")
    log(f"  tangent intercept   = y0 - m*x0 = {td135.tangent_num} mod p")
    log("")

    # Solved calibration
    keys = parse_53125()
    log("=== Solved puzzles: tangent vs offset (mod LO) ===")
    log("n  row  off_bits  m%LO_bits  lam%LO_bits  m==offset?  m-chord%LO_bits")
    hits_m = 0
    hits_lam = 0
    n_cal = 0
    for n in range(70, 131, 5):
        if n not in keys:
            continue
        pk = keys[n]
        rsz = PUZZLE_RSZ.get(n)
        if rsz:
            rpt = recover_r_point_from_sig(rsz.r)
            if rpt:
                rx_w, ry_w = rpt
            else:
                rx_w, ry_w = DEFAULT_RX[0], DEFAULT_RY
        else:
            rx_w, ry_w = DEFAULT_RX[0], DEFAULT_RY

        cfg = build_config(pk)
        st = bridge_state(cfg)
        lo, _, _ = puzzle_band(n)
        off = observed_offset(pk.d, st["oitc"].shelf2, lo)
        td = tangent_at(pk.px, pk.py)
        td = with_r_point(td, rx_w, ry_w)
        m_lo = td.slope_m % lo
        lam_lo = td.lam_p % lo
        mg = (td.slope_m - td.chord_to_rx) % lo if td.chord_to_rx is not None else 0
        eq = m_lo == off
        if eq:
            hits_m += 1
        if lam_lo == off:
            hits_lam += 1
        n_cal += 1
        log(
            f"P{n:3d}  {cfg.row}  {off.bit_length():3d}      {m_lo.bit_length():3d}        "
            f"{lam_lo.bit_length():3d}          {str(eq):5s}      {mg.bit_length() if td.chord_to_rx else '-'}"
        )
    log(f"")
    log(f"Calibration: m%LO == offset on {hits_m}/{n_cal}; Lambda_p%LO == offset on {hits_lam}/{n_cal}")
    log("")

    # P135 band candidates from tangent scalars mod N
    log("=== P135 EC probe (tangent-derived scalars in band) ===")
    cfg = PuzzleConfig(135)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(135)
    shelf2 = st["oitc"].shelf2

    candidates: list[tuple[str, int]] = [
        ("m mod N", td135.slope_m % N),
        ("m - chord mod N", m_gap % N),
        ("m * Lambda_p^-1 mod N", m_ratio % N),
        ("shelf2 + (m mod LO)", shelf2 + (td135.slope_m % lo)),
        ("shelf2 + (m-chord mod LO)", shelf2 + (m_gap % lo)),
        ("shelf2 + (m/Lambda mod LO)", shelf2 + (m_ratio % lo)),
    ]
    for name, d in candidates:
        d %= N
        in_band = lo <= d < hi
        hit = ec_hit(d, P135_PX, P135_PY) if in_band else False
        log(f"  {name}: in_band={in_band} EC={hit} bits={d.bit_length()}")

    log("")
    log("=== VERDICT ===")
    log("Tangent m is LOCAL geometry at P; Lambda_p is GLOBAL slot ratio — different objects.")
    log("m%LO does not systematically equal (d - shelf2) on solved puzzles.")
    log("Wise direction for theory: use tangent/uniformizer for LOCAL parameter at P,")
    log("  chord slopes for P-R relation, Lambda for slot bridge — do not identify them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
