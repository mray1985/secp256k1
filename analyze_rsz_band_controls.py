#!/usr/bin/env python3
"""Control tests for RSZ band 65-160 correlation (r vs n)."""

from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DATA = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_1_256.json"
SWEEP = "5d45587cfd1d5b0fb826805541da7d94c61fe432259e68ee26f4a04544384164"
HASHKEYS_TX = "17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3"
OUT = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_band_controls.json"


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def partial_corr(x: list[float], y: list[float], z: list[float]) -> float:
    """Pearson correlation of x,y after linear residualization on z (simple)."""
    def resid(a, b):
        rb = pearson(a, b)
        sa, sb = statistics.pstdev(a), statistics.pstdev(b)
        ma, mb = statistics.mean(a), statistics.mean(b)
        return [ai - ma - rb * (sb / sa) * (bi - mb) for ai, bi in zip(a, b)]

    rx, ry = resid(x, z), resid(y, z)
    return pearson(rx, ry)


def perm_within_buckets(ns: list[float], ys: list[float], buckets: list[int], trials: int = 3000) -> float:
    random.seed(0)
    obs = pearson(ns, ys)
    by: dict[int, list[int]] = {}
    for i, b in enumerate(buckets):
        by.setdefault(b, []).append(i)
    count = 0
    for _ in range(trials):
        sh = ys[:]
        for idxs in by.values():
            if len(idxs) < 2:
                continue
            sub = [sh[i] for i in idxs]
            random.shuffle(sub)
            for j, i in enumerate(idxs):
                sh[i] = sub[j]
        if abs(pearson(ns, sh)) >= abs(obs):
            count += 1
    return count / trials


def load_rows() -> list[dict]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    from puzzle_keys_53125 import parse_53125

    keys = parse_53125()
    rows = []
    for rec in raw:
        n = rec["puzzle"]
        r = rec["r"]
        rows.append(
            {
                "n": n,
                "r": r,
                "r_over_N": r / N,
                "r_bits": r.bit_length(),
                "log2_n": math.log2(n),
                "txid": rec.get("txid", ""),
                "source": rec.get("source", ""),
                "has_d": n in keys and keys[n].d > 0,
                "independent": rec.get("txid") not in (SWEEP, HASHKEYS_TX),
            }
        )
    return rows


def band_report(rows: list[dict], label: str) -> dict:
    if len(rows) < 5:
        return {"label": label, "n": len(rows), "note": "too few"}
    ns = [float(r["n"]) for r in rows]
    rN = [r["r_over_N"] for r in rows]
    bits = [float(r["r_bits"]) for r in rows]
    logn = [r["log2_n"] for r in rows]

    return {
        "label": label,
        "n": len(rows),
        "r_n_vs_r_over_N": pearson(ns, rN),
        "r_n_vs_r_bits": pearson(ns, bits),
        "r_bits_vs_r_over_N": pearson(bits, rN),
        "partial_n_rN_given_r_bits": partial_corr(ns, rN, bits),
        "partial_n_rN_given_log2_n": partial_corr(ns, rN, logn),
        "perm_within_r_bits_p": perm_within_buckets(ns, rN, [r["r_bits"] for r in rows]),
    }


def main() -> None:
    rows = load_rows()
    b65160 = [r for r in rows if 65 <= r["n"] <= 160]
    solved = [r for r in b65160 if r["has_d"]]
    indep = [r for r in b65160 if r["independent"]]
    indep_solved = [r for r in indep if r["has_d"]]

    reports = [
        band_report(b65160, "65-160 all"),
        band_report(solved, "65-160 solved-with-d"),
        band_report(indep, "65-160 independent-tx-only"),
        band_report(indep_solved, "65-160 independent+solved"),
        band_report([r for r in rows if 161 <= r["n"] <= 256], "161-256 sweep"),
        band_report([r for r in rows if 1 <= r["n"] <= 64], "1-64 all"),
    ]

    print("=== RSZ band control tests ===\n")
    for rep in reports:
        print(f"--- {rep['label']} (n={rep.get('n')}) ---")
        if rep.get("note"):
            print(rep["note"])
            continue
        print(f"  Pearson(n, r/N)              = {rep['r_n_vs_r_over_N']:.4f}")
        print(f"  Pearson(n, r.bit_length)     = {rep['r_n_vs_r_bits']:.4f}")
        print(f"  Pearson(r.bits, r/N)         = {rep['r_bits_vs_r_over_N']:.4f}")
        print(f"  partial(n, r/N | r.bits)     = {rep['partial_n_rN_given_r_bits']:.4f}")
        print(f"  perm within r.bits buckets p = {rep['perm_within_r_bits_p']:.4f}")
        print()

    # interpretation line
    main = reports[0]
    if main.get("partial_n_rN_given_r_bits") is not None:
        p_partial = main["partial_n_rN_given_r_bits"]
        p_perm = main["perm_within_r_bits_p"]
        if abs(p_partial) < 0.2:
            verdict = (
                f"0.61 band: partial(n,r/N|r.bits)={p_partial:.2f} — n signal not independent of "
                f"r.bit_length; perm p={p_perm:.3f} (n=24, uneven puzzle sampling)"
            )
        elif p_perm > 0.05:
            verdict = "0.61 survives bit-bucket shuffle — warrants deeper look"
        else:
            verdict = "mixed: inspect sub-bands and sampling"

    out = {"reports": reports, "verdict_band_65160": verdict}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"VERDICT: {verdict}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
