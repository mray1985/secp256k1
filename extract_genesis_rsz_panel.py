#!/usr/bin/env python3
"""
Extract RSZ from all spends of genesis tx 08389f34… (puzzles 1–256).
Run scalar panel: r/N, s/N, z/N, k^-1 mod N vs puzzle index; project P135.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hashkeys_rsz import N as N_ORDER, PUZZLE_RSZ  # noqa: E402
from puzzle_catalog import load_catalog  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402
from puzzle_rsz_blockchain import PuzzleRSZRecord, rsz_from_txid  # noqa: E402

GENESIS = "08389f34c98c606322740c0be6a7125d9860bb8d5cb182c02f98461e5fa6cd15"
SWEEP_161_256 = "5d45587cfd1d5b0fb826805541da7d94c61fe432259e68ee26f4a04544384164"
BASE = "https://mempool.space/api"
OUT_DIR = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys"
CACHE = ROOT / "ARCHIVE" / "puzzle_rsz_cache.json"
GENESIS_RSZ = OUT_DIR / "puzzle_genesis_rsz_1_256.json"


def fetch_json(url: str, retries: int = 4) -> dict | list:
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "genesis-rsz/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1 + i)
    raise RuntimeError("unreachable")


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def left5(x: int) -> int:
    return int(str(x)[:5]) if x else 0


def recover_k(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N_ORDER) * (z + r * d)) % N_ORDER


def record_to_dict(rec: PuzzleRSZRecord, puzzle: int, genesis_vout: int) -> dict:
    return {
        "puzzle": puzzle,
        "genesis_vout": genesis_vout,
        "source": rec.source or "genesis spend",
        "txid": rec.txid,
        "input_index": rec.input_index,
        "r": rec.r,
        "s": rec.s,
        "z": rec.z,
        "pub_compressed": rec.pub_compressed,
        "r_hex": f"{rec.r:064x}",
        "s_hex": f"{rec.s:064x}",
        "z_hex": f"{rec.z:064x}",
    }


def rsz_for_genesis_input(spend_txid: str, genesis_vout: int) -> PuzzleRSZRecord | None:
    """Find RSZ on input spending genesis:GENESIS_vout."""
    try:
        stx = fetch_json(f"{BASE}/tx/{spend_txid}")
    except Exception:
        return None
    for i, vin in enumerate(stx.get("vin", [])):
        if vin.get("txid") == GENESIS and vin.get("vout") == genesis_vout:
            rows = rsz_from_txid(spend_txid)
            if i < len(rows):
                row = rows[i]
                row.txid = spend_txid
                row.input_index = i
                row.source = "genesis outspend"
                return row
    return None


def extract_all_genesis_rsz() -> dict[int, dict]:
    print("Fetching genesis outspends…")
    outspends = fetch_json(f"{BASE}/tx/{GENESIS}/outspends")
    assert len(outspends) == 256

    # prefer hashkeys for P65–P160 where frozen table exists
    by_puzzle: dict[int, dict] = {}
    keys53125 = parse_53125()

    for vout, osp in enumerate(outspends):
        n = vout + 1
        if n in PUZZLE_RSZ:
            rsz = PUZZLE_RSZ[n]
            by_puzzle[n] = {
                "puzzle": n,
                "genesis_vout": vout,
                "source": "hashkeys_rsz",
                "txid": "17e4e323cfbc68d7f0071cad09364e8193eedf8fefbcbd8a21b4b65717a4b3d3",
                "input_index": -1,
                "r": rsz.r,
                "s": rsz.s,
                "z": rsz.z,
                "pub_compressed": rsz.pub_compressed,
                "r_hex": f"{rsz.r:064x}",
                "s_hex": f"{rsz.s:064x}",
                "z_hex": f"{rsz.z:064x}",
            }
            continue

        if not osp.get("spent"):
            print(f"  P{n}: unspent")
            continue

        spend_txid = osp["txid"]
        # batch sweep: one tx for many puzzles — still map by vout
        print(f"  P{n}: spend {spend_txid[:16]}… vout={vout}")
        time.sleep(0.15)
        rec = rsz_for_genesis_input(spend_txid, vout)
        if rec:
            by_puzzle[n] = record_to_dict(rec, n, vout)
        else:
            print(f"    WARNING: RSZ not found for P{n}")

    return by_puzzle


def load_merged_rsz() -> dict[int, dict]:
    """Merge genesis extract + existing cache + hashkeys."""
    merged: dict[int, dict] = {}
    if CACHE.exists():
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if v:
                merged[int(k)] = v
    for n, rsz in PUZZLE_RSZ.items():
        merged[n] = merged.get(n) or {
            "puzzle": n,
            "r": rsz.r,
            "s": rsz.s,
            "z": rsz.z,
            "pub_compressed": rsz.pub_compressed,
            "source": "hashkeys_rsz",
        }
    if GENESIS_RSZ.exists():
        for row in json.loads(GENESIS_RSZ.read_text(encoding="utf-8")):
            merged[row["puzzle"]] = row
    return merged


def sweep_extract_161_256() -> list[dict]:
    """Fast path: all P161–P256 RSZ from single sweep tx."""
    stx = fetch_json(f"{BASE}/tx/{SWEEP_161_256}")
    rows = rsz_from_txid(SWEEP_161_256)
    out = []
    for i, vin in enumerate(stx["vin"]):
        if vin.get("txid") != GENESIS:
            continue
        vout = vin["vout"]
        n = vout + 1
        if i >= len(rows):
            continue
        rec = rows[i]
        rec.txid = SWEEP_161_256
        rec.input_index = i
        rec.source = "genesis sweep 161-256"
        out.append(record_to_dict(rec, n, vout))
    return sorted(out, key=lambda x: x["puzzle"])


def panel_analysis(rsz_map: dict[int, dict]) -> dict:
    keys = parse_53125()
    rows = []
    for n, rec in sorted(rsz_map.items()):
        r, s, z = rec["r"], rec["s"], rec["z"]
        d = keys[n].d if n in keys and keys[n].d else None
        k = recover_k(r, s, z, d) if d else None
        kinv = pow(k, -1, N_ORDER) if k else None
        rows.append(
            {
                "n": n,
                "r_over_N": r / N_ORDER,
                "s_over_N": s / N_ORDER,
                "z_over_N": z / N_ORDER,
                "d_over_N": d / N_ORDER if d else None,
                "k_inv_left5": left5(kinv) if kinv else None,
                "r_left5": left5(r),
                "has_d": d is not None,
                "band": "161-256" if n >= 161 else ("65-160" if n >= 65 else "1-64"),
            }
        )

    ns = [float(r["n"]) for r in rows]
    metrics = ["r_over_N", "s_over_N", "z_over_N", "r_left5"]
    corrs = {m: pearson(ns, [r[m] for r in rows]) for m in metrics}

    # k_inv panel on solved-with-d only
    solved = [r for r in rows if r["has_d"]]
    if len(solved) >= 10:
        corrs["k_inv_left5"] = pearson(
            [float(r["n"]) for r in solved],
            [float(r["k_inv_left5"]) for r in solved],
        )

    # band splits
    def band_corr(band: str, metric: str) -> float:
        sub = [r for r in rows if r["band"] == band]
        if len(sub) < 5:
            return float("nan")
        return pearson([float(r["n"]) for r in sub], [r[metric] for r in sub])

    bands = {}
    for b in ("1-64", "65-160", "161-256"):
        bands[b] = {m: band_corr(b, m) for m in metrics}

    # P135 projection
    p135 = rsz_map.get(135)
    f135 = None
    if p135:
        f135 = {
            "r_over_N": p135["r"] / N_ORDER,
            "s_over_N": p135["s"] / N_ORDER,
            "z_over_N": p135["z"] / N_ORDER,
            "r_left5": left5(p135["r"]),
        }
        train = [r for r in rows if 161 <= r["n"] <= 256]
        zscores = {}
        for m in metrics:
            vals = [r[m] for r in train]
            mu = sum(vals) / len(vals)
            sd = math.sqrt(sum((x - mu) ** 2 for x in vals) / len(vals)) or 1.0
            zscores[m] = (f135[m] - mu) / sd
        f135["z_vs_161_256"] = zscores

    # permutation null for r/N on 161-256
    sub = [r for r in rows if 161 <= r["n"] <= 256]
    obs = pearson([float(r["n"]) for r in sub], [r["r_over_N"] for r in sub])
    random.seed(0)
    better = 0
    ys = [r["r_over_N"] for r in sub]
    xs = [float(r["n"]) for r in sub]
    for _ in range(1000):
        sh = ys[:]
        random.shuffle(sh)
        if abs(pearson(xs, sh)) >= abs(obs):
            better += 1

    return {
        "n_total": len(rows),
        "n_with_d": sum(1 for r in rows if r["has_d"]),
        "n_161_256": sum(1 for r in rows if r["n"] >= 161),
        "correlations_all": corrs,
        "correlations_by_band": bands,
        "p135": f135,
        "r_over_N_161_256_perm_p": better / 1000,
        "rows_sample": rows[:5] + rows[160:165] + rows[-3:],
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true", help="Fetch all genesis outspend RSZ (slow)")
    ap.add_argument("--sweep-only", action="store_true", help="Only extract 161-256 from sweep tx")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sweep_only or args.extract:
        if args.extract:
            all_rsz = extract_all_genesis_rsz()
            rows = [all_rsz[n] for n in sorted(all_rsz)]
        else:
            rows = sweep_extract_161_256()
            # merge with cache for 1-160
            merged = load_merged_rsz()
            existing = {n: merged[n] for n in merged if n <= 160}
            new = {r["puzzle"]: r for r in rows}
            all_dict = {**existing, **new}
            rows = [all_dict[n] for n in sorted(all_dict)]

        GENESIS_RSZ.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote {len(rows)} RSZ rows to {GENESIS_RSZ}")

    if not GENESIS_RSZ.exists():
        print("Extracting 161-256 from sweep tx + merging cache…")
        rows = sweep_extract_161_256()
        merged = load_merged_rsz()
        for r in rows:
            merged[r["puzzle"]] = r
        out_rows = [merged[n] for n in sorted(merged)]
        GENESIS_RSZ.write_text(json.dumps(out_rows, indent=2), encoding="utf-8")
        print(f"Wrote {len(out_rows)} rows")

    rsz_map = {r["puzzle"]: r for r in json.loads(GENESIS_RSZ.read_text(encoding="utf-8"))}
    # ensure hashkeys P135 etc.
    for n, rsz in PUZZLE_RSZ.items():
        if n not in rsz_map:
            rsz_map[n] = {
                "puzzle": n,
                "r": rsz.r,
                "s": rsz.s,
                "z": rsz.z,
                "pub_compressed": rsz.pub_compressed,
                "source": "hashkeys_rsz",
            }

    report = panel_analysis(rsz_map)

    print("\n=== RSZ scalar panel (genesis spends) ===")
    print(f"Total puzzles with RSZ: {report['n_total']}  (d known: {report['n_with_d']})")
    print(f"P161-256 RSZ count: {report['n_161_256']}")
    print("\nPearson(n, feature) ALL:")
    for k, v in report["correlations_all"].items():
        print(f"  {k:16s} r={v:.4f}")

    print("\nBy band:")
    for band, vals in report["correlations_by_band"].items():
        print(f"  {band}: r/N={vals.get('r_over_N', float('nan')):.4f}  z/N={vals.get('z_over_N', float('nan')):.4f}")

    if report.get("p135"):
        print("\nP135 vs 161-256 training (z-score):")
        for k, v in report["p135"].get("z_vs_161_256", {}).items():
            print(f"  {k}: z={v:+.2f}  P135={report['p135'][k]:.6f}")

    print(f"\n161-256 r/N perm p={report['r_over_N_161_256_perm_p']:.3f}")

    out_json = OUT_DIR / "puzzle_genesis_rsz_panel.json"
    out_md = OUT_DIR / "puzzle_genesis_rsz_panel.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# Genesis RSZ scalar panel",
        "",
        f"Genesis: `{GENESIS}`",
        f"Sweep 161-256: `{SWEEP_161_256}`",
        "",
        f"Puzzles with RSZ: **{report['n_total']}** (d known: {report['n_with_d']})",
        "",
        "## Pearson(n, feature)",
        "",
        "| feature | r (all) |",
        "|---------|---------|",
    ]
    for k, v in report["correlations_all"].items():
        md.append(f"| {k} | {v:.4f} |")
    md.extend(["", "## P135 projection", ""])
    if report.get("p135"):
        for k in ("r_over_N", "s_over_N", "z_over_N"):
            z = report["p135"].get("z_vs_161_256", {}).get(k, 0)
            md.append(f"- {k}: P135={report['p135'][k]:.6f}, z vs 161-256={z:+.2f}")
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
