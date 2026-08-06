#!/usr/bin/env python3
"""Family bridge + mirror defect calibration across solved puzzles (53125.txt)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from genesis_calibration import bridge_state  # noqa: E402
from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_GX,
    DEFAULT_RX,
    DEFAULT_RY,
    N,
    P115_K,
    PuzzleConfig,
    all_cube_roots_mod_p,
    apply_puzzle_defaults,
    delta,
    p,
    puzzle_band,
    y_even,
)
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from puzzle_keys_53125 import PuzzleKey53125, parse_53125  # noqa: E402
PUZZLE_LIST = [
    5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
    60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110,
    115, 120, 125, 130, 135,
]


def build_config(pk: PuzzleKey53125) -> PuzzleConfig:
    n = pk.n
    if n == 115:
        cfg = PuzzleConfig(puzzle_num=115, known_d=pk.d, known_k=P115_K)
        apply_puzzle_defaults(cfg)
        return cfg

    cfg = PuzzleConfig(puzzle_num=n, known_d=pk.d)
    apply_puzzle_defaults(cfg)

    px_roots = sorted(all_cube_roots_mod_p((pk.py * pk.py - 7) % p, witness=pk.px))
    if pk.px not in px_roots:
        px_roots = sorted(all_cube_roots_mod_p((pk.py * pk.py - 7) % p))
    if len(px_roots) != 3:
        raise ValueError(f"P{n}: expected 3 Px cube roots, got {len(px_roots)}")

    rsz = PUZZLE_RSZ.get(n)
    if rsz is not None:
        r_pt = recover_r_point_from_sig(rsz.r)
        if not r_pt:
            raise ValueError(f"P{n}: cannot recover R from signature r")
        rx_w, ry = r_pt
        rx_roots = sorted(all_cube_roots_mod_p((ry * ry - 7) % p, witness=rx_w))
        if len(rx_roots) != 3:
            raise ValueError(f"P{n}: expected 3 rx cube roots, got {len(rx_roots)}")
    else:
        rx_roots = list(DEFAULT_RX)
        ry = DEFAULT_RY

    cfg.Px = px_roots
    cfg.rx = rx_roots
    cfg.Py = pk.py
    cfg.ry = ry if rsz is not None else DEFAULT_RY
    cfg.Gx = list(DEFAULT_GX)
    cfg.row = px_roots.index(pk.px)
    cfg.known_d = pk.d
    if rsz and rsz.k is not None:
        cfg.known_k = rsz.k
    return cfg


def analyze_one(pk: PuzzleKey53125) -> dict:
    n = pk.n
    lo, hi, top = puzzle_band(n)
    cfg = build_config(pk)
    st = bridge_state(cfg)
    af = st["af"]
    oitc = st["oitc"]
    lns = st["lambda_ns"]
    row = cfg.row
    lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, p)) % p
    lam_n_row = lns[row]
    fam = (lns[0] * lns[1] * lns[2]) % N
    gap_row = (lam_n_row - lam_p) % N
    off = af.offset_shelf2
    terms = dict(st["terms"])
    hits = [name for name, v in terms.items() if off is not None and v == off]
    pred_bits = n - 10
    off_bits = af.offset_bits or 0

    m = None
    if cfg.known_d and cfg.known_k:
        m = (cfg.known_d * pow(cfg.known_k, -1, N)) % N

    return {
        "n": n,
        "d": pk.d,
        "has_k": cfg.known_k is not None,
        "has_rsz": PUZZLE_RSZ.get(n) is not None,
        "row": row,
        "shelf2": oitc.shelf2,
        "offset": off,
        "offset_bits": off_bits,
        "h_minus_10": pred_bits,
        "h10_match": off_bits == pred_bits if off is not None else False,
        "offset_eq_l2_l1": off == (lns[1] - lns[0]) % lo if off is not None else False,
        "term_hits": "|".join(hits[:3]),
        "n_term_hits": len(hits),
        "gap_mod_lo_bits": (gap_row % lo).bit_length() if lo else 0,
        "defect_lo_bits": ((delta + lo) % N).bit_length(),
        "defect_hi_bits": ((delta + top) % N).bit_length(),
        "lambda_family_bits": fam.bit_length(),
        "C_floor": oitc.c_floor,
        "d_minus_lo_bits": (pk.d - lo).bit_length(),
        "shelf2_minus_lo_bits": (oitc.shelf2 - lo).bit_length(),
        "m_bits": m.bit_length() if m else None,
    }


def main() -> None:
    keys = parse_53125()
    rows: list[dict] = []
    missing = []
    for n in PUZZLE_LIST:
        if n not in keys:
            missing.append(n)
            continue
        pk = keys[n]
        try:
            if n == 135 or pk.d == 0:
                cfg = PuzzleConfig(puzzle_num=135)
                apply_puzzle_defaults(cfg)
                st = bridge_state(cfg)
                lo, _, top = puzzle_band(135)
                lns = st["lambda_ns"]
                row = cfg.row
                lam_p = (cfg.Px[row] * pow(cfg.rx[row], -1, p)) % p
                gap_row = (lns[row] - lam_p) % N
                fam = (lns[0] * lns[1] * lns[2]) % N
                rows.append({
                    "n": 135,
                    "d": None,
                    "has_k": False,
                    "row": row,
                    "shelf2": st["oitc"].shelf2,
                    "offset": None,
                    "offset_bits": None,
                    "h_minus_10": 125,
                    "h10_match": False,
                    "offset_eq_l2_l1": False,
                    "term_hits": "",
                    "n_term_hits": 0,
                    "gap_mod_lo_bits": (gap_row % lo).bit_length(),
                    "defect_lo_bits": ((delta + lo) % N).bit_length(),
                    "defect_hi_bits": ((delta + top) % N).bit_length(),
                    "lambda_family_bits": fam.bit_length(),
                    "C_floor": st["oitc"].c_floor,
                    "d_minus_lo_bits": None,
                    "shelf2_minus_lo_bits": (st["oitc"].shelf2 - lo).bit_length(),
                    "m_bits": None,
                })
            else:
                rows.append(analyze_one(pk))
        except Exception as e:
            rows.append({"n": n, "error": str(e)})

    out_txt = ROOT / "family_mirror_batch_report.txt"
    out_csv = ROOT / "ARCHIVE" / "family_mirror_batch.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    good_rows = [r for r in rows if "error" not in r]
    if good_rows:
        fields: list[str] = []
        for r in good_rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(good_rows)

    solved = [r for r in rows if r.get("offset_bits") is not None]
    h10_hits = [r for r in solved if r.get("h10_match")]
    l2l1_hits = [r for r in solved if r.get("offset_eq_l2_l1")]

    lines = [
        "FAMILY BRIDGE + MIRROR DEFECT — batch from 53125.txt",
        f"puzzles requested: {len(PUZZLE_LIST)}  parsed keys: {len(keys)}  analyzed: {len(rows)}",
        f"missing from 53125: {missing}",
        "",
        "H-10 law: offset_bits == puzzle_height - 10",
        f"  matches: {len(h10_hits)} / {len(solved)}",
        "",
        "offset == (L2-L1) mod LO:",
        f"  matches: {len(l2l1_hits)} / {len(solved)}",
        "",
        f"{'n':>4} {'off_bits':>8} {'H-10':>5} {'L2-L1':>5} {'row':>3} {'hits':>4}  term (first)",
        "-" * 72,
    ]
    for r in solved:
        lines.append(
            f"{r['n']:4d} {r['offset_bits']:8d} "
            f"{'Y' if r['h10_match'] else 'N':>5} "
            f"{'Y' if r['offset_eq_l2_l1'] else 'N':>5} "
            f"{r['row']:3d} {r['n_term_hits']:4d}  {r['term_hits'][:40]}"
        )
    errors = [r for r in rows if "error" in r]
    if errors:
        lines += ["", "ERRORS:"]
        for r in errors:
            lines.append(f"  P{r['n']}: {r['error']}")

    r135 = next((r for r in rows if r.get("n") == 135), None)
    if r135 and "error" not in r135:
        lines += [
            "",
            "P135 (unsolved — bridge shell only):",
            f"  shelf2 mod LO bits = {r135.get('shelf2_minus_lo_bits')}",
            f"  row (epsilon landing) = {r135.get('row')}",
            f"  gap mod LO bits = {r135.get('gap_mod_lo_bits')}",
            f"  defect window bits: lo={r135.get('defect_lo_bits')} hi={r135.get('defect_hi_bits')}",
            f"  if H-10 holds: expect offset ~125 bits from shelf2",
        ]

    # P130 without k
    r130 = next((r for r in solved if r["n"] == 130), None)
    if r130:
        lines += [
            "",
            "P130 (d known, k unknown):",
            f"  offset_bits={r130['offset_bits']} (H-10 pred 120: {'Y' if r130['h10_match'] else 'N'})",
            f"  bridge terms matching offset: {r130['term_hits']}",
            "  cannot close m=d*k^-1 or ECDSA k without nonce",
        ]

    # P115 reference
    r115 = next((r for r in solved if r["n"] == 115), None)
    if r115:
        lines += [
            "",
            "P115 reference:",
            f"  offset={r115['offset']} bits={r115['offset_bits']}",
            f"  term_hits={r115['term_hits']}",
            f"  frozen P115_OFFSET expects bits=105: {r115['offset_bits'] == 105}",
        ]

    text = "\n".join(lines) + "\n"
    out_txt.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out_csv}")
    print(f"wrote {out_txt}")


if __name__ == "__main__":
    main()
