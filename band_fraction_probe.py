#!/usr/bin/env python3
"""
Probe band-fraction d grid; report discrete-log alignment via signature formula.

Formula (mod N):
  k0 = z * s^-1
  delta_k = r * s^-1
  k = k0 + d * delta_k

Lines up when k*G matches spend-signature R (rx, ry).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, resolve_r_true_from_rsz  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "band_fraction_probe.txt"
CSV_OUT = ROOT / "ARCHIVE" / "band_fraction_probe.csv"

DEFAULT_UNSOLVED = [135, 140, 145, 150, 155, 160]


def anchor_d(n: int, frac: float) -> int:
    lo, hi, _ = puzzle_band(n)
    d = int(2 ** (n - 1 + frac))
    return max(lo, min(d, hi - 1))


def band_frac(d: int, n: int) -> float:
    lo, hi, _ = puzzle_band(n)
    return (d - lo) / (hi - lo)


def bounce_probes(anchor: int, n: int, count: int, span_pow: int) -> list[int]:
    lo, hi, _ = puzzle_band(n)
    span = min(1 << span_pow, (hi - lo) // 4)
    step = max(1, span // max(1, count // 2))
    out: list[int] = []
    seen: set[int] = set()

    def add(d: int) -> None:
        if lo <= d < hi and d not in seen:
            seen.add(d)
            out.append(d)

    add(anchor)
    ring = 1
    while len(out) < count and ring * step <= span:
        add(anchor + ring * step)
        add(anchor - ring * step)
        ring += 1
    fine = max(1, step // 16)
    off = 1
    while len(out) < count and off <= span:
        add(anchor + off)
        add(anchor - off)
        off += fine
    return out[:count]


def bridge_constants(r: int, s: int, z: int) -> tuple[int, int]:
    s_inv = pow(s, -1, N)
    k0 = (z * s_inv) % N
    delta_k = (r * s_inv) % N
    return k0, delta_k


def k_from_formula(d: int, k0: int, delta_k: int) -> int:
    return (k0 + d * delta_k) % N


def discrete_log_align(
    d: int, k0: int, delta_k: int, rx: int, ry: int
) -> dict:
    """Check if formula k lands on signature R."""
    k = k_from_formula(d, k0, delta_k)
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

    try:
        kx, ky = pubkey_from_scalar(k)
    except Exception:
        return {
            "k": k,
            "rx_match": False,
            "ry_match": False,
            "ry_neg_match": False,
            "lined_up": False,
            "formula_roundtrip": True,
        }

    rx_match = (kx % N) == (rx % N)
    ry_match = ky == ry
    ry_neg_match = ky == ((-ry) % p)
    lined_up = rx_match and (ry_match or ry_neg_match)
    return {
        "k": k,
        "rx_match": rx_match,
        "ry_match": ry_match,
        "ry_neg_match": ry_neg_match,
        "lined_up": lined_up,
        "formula_roundtrip": True,
    }


def probe_puzzle(
    n: int,
    frac: float,
    count: int,
    span_pow: int,
    keys: dict,
) -> tuple[list[dict], dict]:
    rsz = PUZZLE_RSZ.get(n)
    if rsz is None:
        return [], {}
    rpt = resolve_r_true_from_rsz(n)
    if not rpt:
        return [], {}
    rx, ry = rpt[0], rpt[1]
    k0, delta_k = bridge_constants(rsz.r, rsz.s, rsz.z)
    anc = anchor_d(n, frac)
    probes = bounce_probes(anc, n, count, span_pow)
    true_d = keys[n].d if n in keys and keys[n].d else None

    rows: list[dict] = []
    for i, d in enumerate(probes):
        alg = discrete_log_align(d, k0, delta_k, rx, ry)
        rows.append(
            {
                "puzzle": n,
                "idx": i,
                "frac_target": frac,
                "anchor": anc,
                "d": d,
                "d_bits": d.bit_length(),
                "band_frac": round(band_frac(d, n), 6),
                "offset_from_anchor": d - anc,
                "is_true_d": d == true_d if true_d else False,
                "k_bits": alg["k"].bit_length(),
                "rx_match": alg["rx_match"],
                "ry_match": alg["ry_match"],
                "lined_up": alg["lined_up"],
                "formula_roundtrip": alg["formula_roundtrip"],
            }
        )

    meta = {
        "true_d": true_d,
        "true_d_band_frac": round(band_frac(true_d, n), 6) if true_d else None,
        "true_d_lined_up": None,
        "anchor": anc,
    }
    if true_d:
        t = discrete_log_align(true_d, k0, delta_k, rx, ry)
        meta["true_d_lined_up"] = t["lined_up"]
    return rows, meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Band-fraction d probes — discrete log formula alignment")
    ap.add_argument("--frac", type=float, default=0.58)
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--span-pow", type=int, default=22)
    ap.add_argument(
        "--puzzles",
        type=int,
        nargs="*",
        default=[130] + DEFAULT_UNSOLVED,
        help="default: P130 + unsolved high puzzles",
    )
    args = ap.parse_args()

    keys = parse_53125()
    all_rows: list[dict] = []
    lines = [
        "BAND-FRACTION PROBE — DISCRETE LOG FORMULA ALIGNMENT",
        "k = k0 + d*delta_k (mod N);  lined_up = k*G matches spend R (rx, ry)",
        f"anchor = int(2^(n-1+{args.frac}))  probes={args.count}  span=2^{args.span_pow}",
        "",
    ]

    for n in args.puzzles:
        rows, meta = probe_puzzle(n, args.frac, args.count, args.span_pow, keys)
        if not rows:
            lines.append(f"=== P{n} — no RSZ / R recover ===")
            lines.append("")
            continue

        all_rows.extend(rows)
        hits = [r for r in rows if r["lined_up"]]
        lines.append(
            f"=== P{n} anchor bf={band_frac(meta['anchor'], n):.4f} "
            f"probes={len(rows)} formula_lined_up={len(hits)} ==="
        )
        if meta["true_d"]:
            lines.append(
                f"  TRUE d bf={meta['true_d_band_frac']}  "
                f"lined_up={meta['true_d_lined_up']}  "
                f"d={meta['true_d']}"
            )
            in_grid = any(r["is_true_d"] for r in rows)
            lines.append(f"  true d in probe grid: {in_grid}")
        if hits:
            for r in hits[:10]:
                lines.append(
                    f"  LINED_UP idx={r['idx']} d=...{str(r['d'])[-14:]} "
                    f"bf={r['band_frac']:.4f} off={r['offset_from_anchor']:+d}"
                )
        else:
            lines.append("  no probes lined up on R via formula")
        lines.append("")

    lines.append(
        "NOTE: formula roundtrip d->k->d is algebraic identity for all d. "
        "lined_up is the real discrete-log gate (k*G == R)."
    )
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    if all_rows:
        with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
    print(text)
    print(f"\nwrote {REPORT}\nwrote {CSV_OUT}")
    return 0 if any(r["lined_up"] for r in all_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
