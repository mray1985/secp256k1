#!/usr/bin/env python3
"""P135 d-sweep: mirror defect band, notebook Λ_N(d)=Λ_N+d carries, k-distance, d*G==P."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    N,
    delta,
    PuzzleConfig,
    apply_puzzle_defaults,
    carry,
    pubkey_from_scalar,
    verify_n_y_compression,
    y_even,
)
from genesis_calibration import bridge_state  # noqa: E402
from k_xy_mod134_distance import bridge_k_pair, puzzle_k_transforms  # noqa: E402

try:
    from ecdsa import SECP256k1  # noqa: F401

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

PUZZLE_N = 135


def in_band(d: int, lo: int, hi: int) -> bool:
    return lo <= d < hi


def defect_val(d: int) -> int:
    return (delta + d) % N


def defect_in_window(d: int, lo: int, top: int) -> bool:
    dv = defect_val(d)
    lo_d = delta + lo
    top_d = delta + top
    return lo_d <= dv <= top_d


def carry_rows(lambda_n: int, Qx: list[int], qx: list[int]) -> tuple[int, list[bool], list[int]]:
    ok_count = 0
    oks: list[bool] = []
    rems: list[int] = []
    for i in range(3):
        num = lambda_n * qx[i] - Qx[i]
        ok, rem, _b = carry(num, N)
        oks.append(ok)
        rems.append(rem)
        if ok:
            ok_count += 1
    return ok_count, oks, rems


def carry_rows_shifted(
    lambda_n_base: int, d_shift: int, Qx: list[int], qx: list[int]
) -> tuple[int, list[bool]]:
    lam = (lambda_n_base + d_shift) % N
    ok_count = 0
    oks: list[bool] = []
    for i in range(3):
        num = lam * qx[i] - Qx[i]
        ok, _, _ = carry(num, N)
        oks.append(ok)
        if ok:
            ok_count += 1
    return ok_count, oks


def solve_d_mod_for_row(rem: int, qx_i: int) -> int:
    return (-rem * pow(qx_i, -1, N)) % N


def band_lift(d_mod: int, lo: int, hi: int) -> int | None:
    """Unique d in [lo, hi) with d ≡ d_mod (mod N) if it exists."""
    if in_band(d_mod, lo, hi):
        return d_mod
    return None


def min_k_distance(n: int, d: int, kx: int, ky: int) -> tuple[int, str]:
    best = 1 << 300
    best_lbl = ""
    for prefix, k in (("kx", kx), ("ky", ky)):
        t = puzzle_k_transforms(n, k)
        for tag, val in (("r1", t["floor_lift"]), ("r2", t["height_residue"])):
            dist = abs(d - val)
            if dist < best:
                best = dist
                best_lbl = f"{prefix}_{tag}"
    return best.bit_length(), best_lbl


def ec_hit(d: int, px: int, py: int) -> bool:
    if not _HAS_ECDSA:
        return False
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def add_candidate(
    pool: dict[int, dict],
    d: int,
    source: str,
    lo: int,
    hi: int,
    top: int,
    *,
    lambda_n_base: int,
    Qx: list[int],
    qx: list[int],
    lam_y_n: int,
    qy: int,
    Qy: int,
    qy_r: int,
    kx: int,
    ky: int,
) -> None:
    if not in_band(d, lo, hi):
        return
    if d in pool and pool[d]["source"].count(source) == 0:
        pool[d]["source"] += f";{source}"
        return
    if d in pool:
        return

    x_ok_base, _ = carry_rows_shifted(lambda_n_base, 0, Qx, qx)
    x_ok_shift, x_oks = carry_rows_shifted(lambda_n_base, d, Qx, qx)
    num_y = lam_y_n * qy_r - Qy
    y_ok, _, _ = carry(num_y, N)

    k_bits, k_best = min_k_distance(PUZZLE_N, d, kx, ky)
    hit = ec_hit(d, Qx[2], Qy)

    pool[d] = {
        "d": d,
        "d_bits": d.bit_length(),
        "source": source,
        "defect": defect_val(d),
        "defect_bits": defect_val(d).bit_length(),
        "defect_in_window": defect_in_window(d, lo, top),
        "x_carry_base_3": x_ok_base,
        "x_carry_shift_3": x_ok_shift,
        "x_row1": x_oks[0],
        "x_row2": x_oks[1],
        "x_row3": x_oks[2],
        "y_carry_ok": y_ok,
        "k_dist_bits": k_bits,
        "k_best": k_best,
        "ec_hit": hit,
        "score": (
            (1000 if hit else 0)
            + x_ok_shift * 100
            + (10 if y_ok else 0)
            + (5 if defect_in_window(d, lo, top) else 0)
            - k_bits
        ),
    }


def main() -> None:
    cfg = PuzzleConfig(puzzle_num=135, row=2)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi = st["lo"], st["hi"]
    top = hi - 1
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    py = cfg.Py or y_even(px[row])
    ry = cfg.ry or y_even(rx[row])

    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    Qy = (py * delta) % N
    qy_r = (ry * delta) % N
    lambda_n_base = (px[row] * pow(rx[row], -1, N)) % N
    lam_y_n = verify_n_y_compression(px_triple=px, rx_triple=rx, py=py, ry=ry).lambda_y_n

    kx, ky, _, _ = bridge_k_pair(cfg)

    # Baseline remainders (unified Lambda_N on all rows)
    _, _, rems = carry_rows(lambda_n_base, Qx, qx)

    pool: dict[int, dict] = {}
    lines: list[str] = [
        "P135 d-SWEEP",
        f"band d in [{lo}, {hi})  defect(d)=δ+d  window [{delta + lo}, {delta + top}]",
        f"notebook: Λ_N(d)=Λ_N+ d_shift tested with d_shift = candidate d",
        f"ecdsa available: {_HAS_ECDSA}",
        "",
        "BASELINE (d_shift=0):",
        f"  Lambda_N row3 = {lambda_n_base}",
        f"  x_carry rows OK: {carry_rows(lambda_n_base, Qx, qx)[0]}/3",
        f"  row remainders: r1={rems[0].bit_length()}b r2={rems[1].bit_length()}b r3={rems[2]}",
        "",
    ]

    # 1) Carry congruence per row (Λ_N + d closes row i)
    for i in range(3):
        if rems[i] == 0:
            lines.append(f"  row{i+1} carry: already integer at d_shift=0")
            continue
        d_mod = solve_d_mod_for_row(rems[i], qx[i])
        d_band = band_lift(d_mod, lo, hi)
        lines.append(
            f"  row{i+1} d ≡ rem*qx^-1 mod N -> {d_mod} "
            f"({'in band' if d_band else 'out of band'})"
        )
        if d_band is not None:
            add_candidate(
                pool,
                d_band,
                f"carry_row{i+1}",
                lo,
                hi,
                top,
                lambda_n_base=lambda_n_base,
                Qx=Qx,
                qx=qx,
                lam_y_n=lam_y_n,
                qy=Qy,
                Qy=Qy,
                qy_r=qy_r,
                kx=kx,
                ky=ky,
            )

    # 2) Shelf + offset lattice (from bridge_state)
    shelf2 = st["oitc"].shelf2
    for name, off in st["terms"]:
        add_candidate(
            pool,
            (shelf2 + off) % N,
            f"shelf2+{name}",
            lo,
            hi,
            top,
            lambda_n_base=lambda_n_base,
            Qx=Qx,
            qx=qx,
            lam_y_n=lam_y_n,
            qy=Qy,
            Qy=Qy,
            qy_r=qy_r,
            kx=kx,
            ky=ky,
        )

    # 3) Anchors: shelves, cube lifts, band edges
    oitc = st["oitc"]
    for label, val in [
        ("shelf2", oitc.shelf2),
        ("shelf3", oitc.shelf3),
        ("shelf_y", oitc.shelf_y),
        ("cube_lift2", oitc.d_cube_lift2),
        ("cube_lift3", oitc.d_cube_lift3),
        ("LO", lo),
        ("TOP", top),
    ]:
        add_candidate(
            pool,
            val % N,
            label,
            lo,
            hi,
            top,
            lambda_n_base=lambda_n_base,
            Qx=Qx,
            qx=qx,
            lam_y_n=lam_y_n,
            qy=Qy,
            Qy=Qy,
            qy_r=qy_r,
            kx=kx,
            ky=ky,
        )

    # 4) k-probe band targets (r1/r2 as d long-shots)
    for prefix, k in (("kx", kx), ("ky", ky)):
        t = puzzle_k_transforms(PUZZLE_N, k)
        for tag, val in (("r1", t["floor_lift"]), ("r2", t["height_residue"])):
            add_candidate(
                pool,
                val,
                f"{prefix}_{tag}_as_d",
                lo,
                hi,
                top,
                lambda_n_base=lambda_n_base,
                Qx=Qx,
                qx=qx,
                lam_y_n=lam_y_n,
                qy=Qy,
                Qy=Qy,
                qy_r=qy_r,
                kx=kx,
                ky=ky,
            )

    # Legacy endpoint-only probes (superseded by p135_gap_tier_sweep.py interval search)
    lines.append(
        "NOTE: shelf2+2^k endpoint probes removed — use p135_gap_tier_sweep.py "
        "for gap-tier INTERVALS [2^(H-gap-1), 2^(H-gap))."
    )
    rows = sorted(pool.values(), key=lambda r: (-r["score"], r["k_dist_bits"]))
    lines.append(f"CANDIDATES IN BAND: {len(rows)}")
    lines.append("")
    hdr = (
        f"{'score':>5} {'d_bits':>6} {'x3':>3} {'y':>3} {'kdist':>5} {'best':>8} "
        f"{'defW':>4} {'ec':>3} source"
    )
    lines.append(hdr)
    lines.append("-" * len(hdr))

    ec_hits = [r for r in rows if r["ec_hit"]]
    best_x3 = [r for r in rows if r["x_carry_shift_3"] == 3]

    for r in rows[:40]:
        lines.append(
            f"{r['score']:5d} {r['d_bits']:6d} {r['x_carry_shift_3']:3d} "
            f"{'Y' if r['y_carry_ok'] else 'N':>3} {r['k_dist_bits']:5d} {r['k_best']:>8} "
            f"{'Y' if r['defect_in_window'] else 'N':>4} "
            f"{'Y' if r['ec_hit'] else 'N':>3} {r['source'][:60]}"
        )

    lines.append("")
    lines.append(f"EC hits (d*G==P): {len(ec_hits)}")
    lines.append(f"All-3-row x-carry with Λ_N+d: {len(best_x3)}")
    if ec_hits:
        for r in ec_hits:
            lines.append(f"  HIT d={r['d']} source={r['source']}")
    elif best_x3:
        lines.append("  Top x_carry=3 (no EC hit):")
        for r in best_x3[:5]:
            lines.append(
                f"    d={r['d']} k_dist={r['k_dist_bits']}b source={r['source']}"
            )

    report = "\n".join(lines)
    print(report)

    out_txt = ROOT / "ARCHIVE" / "p135_d_sweep_report.txt"
    out_csv = ROOT / "ARCHIVE" / "p135_d_sweep.csv"
    out_txt.write_text(report + "\n", encoding="utf-8")

    if rows:
        fields = list(rows[0].keys())
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(f"\nWrote {out_txt}")
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
