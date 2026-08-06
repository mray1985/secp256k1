#!/usr/bin/env python3
"""
K-00 panel admissibility + K-01 orbit-safe byte-bin recurrence.

Preregistered before evaluation.
k* = min(k, N-k); b = min(255, floor(256 * 2*k*/N))
R(k) = 1 iff b(k) in B_train
"""
from __future__ import annotations

import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    N_ORDER,
    OUT_DIR,
    load_prereg,
    save_prereg,
)

PANEL = OUT_DIR / "SOLVED_NONCE_PANEL.json"
RSZ = Path(r"C:\Users\mitch\Desktop\secp256k1\ARCHIVE\puzzle_rsz_cache.json")
RNG = random.Random(20260710)

OUT_K00_JSON = OUT_DIR / "K00_PANEL_ADMISSIBILITY.json"
OUT_K00_CSV = OUT_DIR / "K00_PANEL_ADMISSIBILITY.csv"
OUT_K00_MD = OUT_DIR / "K00_PANEL_ADMISSIBILITY.md"
OUT_K01 = OUT_DIR / "K-20260710-01_byte_bin_result.txt"
PREREG_K00 = OUT_DIR / "prereg" / "K-20260710-00_panel_admissibility.md"
PREREG_K01 = OUT_DIR / "prereg" / "K-20260710-01_orbit_safe_byte_bin.md"


def k_star(k: int) -> int:
    k = k % N_ORDER
    return min(k, (N_ORDER - k) % N_ORDER)


def byte_bin(k: int) -> int:
    """Locked 8-bit bin on orbit-safe k*."""
    ks = k_star(k)
    # c = 2*k*/N in [0,1]; for k*=0, c=0; for k*=floor(N/2), c≈1
    # use integer: floor(256 * 2 * k* / N) = floor(512 * k* / N)
    b = (512 * ks) // N_ORDER
    return min(255, b)


def era_proxy(n: int) -> str:
    if n <= 50:
        return "early_n_le_50"
    if n <= 100:
        return "mid_51_100"
    return "late_gt_100"


def build_k00(panel: list[dict], rsz: dict) -> list[dict]:
    rows = []
    for row in panel:
        n = int(row["puzzle"])
        rec = rsz.get(str(n)) or {}
        s = int(row["s"])
        k = int(row["k"])
        ks = k_star(k)
        rows.append(
            {
                "puzzle": n,
                "source": rec.get("source") or "unknown",
                "txid": row.get("txid") or rec.get("txid") or "",
                "pub_compressed": row.get("pub_compressed") or "",
                "input_index": rec.get("input_index", ""),
                "note": rec.get("note") or "",
                "low_S": s <= N_ORDER // 2,
                "s": s,
                "k": k,
                "k_star": ks,
                "k_star_bit_length": ks.bit_length(),
                "byte_bin": byte_bin(k),
                "era_proxy": era_proxy(n),
                "sighash": "unknown",
                "segwit": "unknown",
            }
        )
    return rows


def write_k00(rows: list[dict]) -> dict:
    by_src = Counter(r["source"] for r in rows)
    by_era = Counter(r["era_proxy"] for r in rows)
    low_s = sum(1 for r in rows if r["low_S"])
    bins = Counter(r["byte_bin"] for r in rows)
    # unique pubs / txids
    n_pub = len({r["pub_compressed"] for r in rows if r["pub_compressed"]})
    n_tx = len({r["txid"] for r in rows if r["txid"]})

    summary = {
        "n_rows": len(rows),
        "by_source": dict(by_src),
        "by_era_proxy": dict(by_era),
        "low_S_count": low_s,
        "low_S_fraction": low_s / len(rows),
        "unique_pubkeys": n_pub,
        "unique_txids": n_tx,
        "unique_byte_bins_all": len(bins),
        "byte_bin_histogram": dict(sorted(bins.items())),
        "warning": (
            "82/82 r-verification proves algebraic correctness, NOT a shared "
            "nonce-generation process. Do not train a universal P135 rule from "
            "a mixture unless it survives leave-one-source-out."
        ),
    }

    OUT_K00_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    with OUT_K00_CSV.open("w", newline="", encoding="utf-8") as f:
        fields = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    md = f"""# K-00 Panel admissibility

**Date:** {date.today().isoformat()}

## Warning

{summary['warning']}

Also: Bitcoin low-S normalization can flip recovered nonce `k -> N-k`.
All nonce-pattern tests use `k* = min(k, N-k)`.

## Stratification

| Tag | Counts |
|-----|--------|
| source | {dict(by_src)} |
| era_proxy | {dict(by_era)} |
| low_S | {low_s}/{len(rows)} ({100*low_s/len(rows):.1f}%) |
| unique pubkeys | {n_pub} |
| unique txids | {n_tx} |
| unique 8-bit bins (all panel) | {len(bins)} / 256 |

Sighash / SegWit: **unknown** (not in RSZ cache).

## Implication for K-01+

Train universal rules only if they survive **leave-one-source-out**.
The heterogeneous 82-row set remains useful as a **null panel**.
"""
    OUT_K00_MD.write_text(md, encoding="utf-8")
    if PREREG_K00.exists():
        text = PREREG_K00.read_text(encoding="utf-8")
        text = text.replace("## Result\n\n*(fill after run)*", "## Result\n\n" + md)
        PREREG_K00.write_text(text, encoding="utf-8")
        (ARCHIVE_PREREG / PREREG_K00.name).write_text(text, encoding="utf-8")
    return summary


def retention(bins_set: set[int], rows: list[dict]) -> float:
    if not rows:
        return float("nan")
    return sum(1 for r in rows if r["byte_bin"] in bins_set) / len(rows)


def run_k01(tagged: list[dict]) -> dict:
    train = [r for r in tagged if r["puzzle"] <= 50]
    test = [r for r in tagged if r["puzzle"] > 50]
    B_train = {r["byte_bin"] for r in train}
    surv = len(B_train) / 256.0
    ret_test = retention(B_train, test)
    ret_train = retention(B_train, train)  # should be 1.0 by construction

    # random uniform k*
    rand_pass = []
    for _ in range(5000):
        k = RNG.randrange(1, N_ORDER)
        rand_pass.append(1.0 if byte_bin(k) in B_train else 0.0)
    rand_rate = statistics.fmean(rand_pass)

    # k <-> N-k control: bins identical
    kk_ok = all(byte_bin(r["k"]) == byte_bin((N_ORDER - r["k"]) % N_ORDER) for r in tagged)

    # leave-one-source-out
    sources = sorted({r["source"] for r in tagged})
    loso = {}
    for S in sources:
        tr = [r for r in tagged if r["source"] != S]
        te = [r for r in tagged if r["source"] == S]
        if len(te) < 3 or len(tr) < 8:
            loso[S] = {"n_test": len(te), "n_train": len(tr), "skipped": True}
            continue
        B = {r["byte_bin"] for r in tr}
        loso[S] = {
            "n_test": len(te),
            "n_train": len(tr),
            "B_size": len(B),
            "survivor_fraction": len(B) / 256.0,
            "retention": retention(B, te),
            "skipped": False,
        }

    # temporal: also report mid/late within test
    test_mid = [r for r in test if r["era_proxy"] == "mid_51_100"]
    test_late = [r for r in test if r["era_proxy"] == "late_gt_100"]

    promote = (
        ret_test == 1.0
        and surv < 0.25  # <<1 ; precommit soft: need much smaller ideally
        and kk_ok
        and all(
            (v.get("skipped") or v["retention"] == 1.0)
            for v in loso.values()
        )
    )
    # stricter: survivor <<1 means clearly sparse; if retention fails -> FAIL
    if ret_test < 1.0 or not kk_ok:
        verdict = "FAIL"
    elif surv >= 0.5:
        verdict = "FAIL"  # not meaningful narrowing
    elif ret_test == 1.0 and surv < 0.25:
        # check LOSO
        loso_fail = [
            s for s, v in loso.items() if not v.get("skipped") and v["retention"] < 1.0
        ]
        if loso_fail:
            verdict = "FAIL"
        elif abs(rand_rate - surv) > 0.05 and ret_test == 1.0:
            # random should track survivor fraction; if retention 100% on real but
            # that's expected if bins cover; promote only if sparse AND 100%
            verdict = "BORDERLINE" if surv >= 0.1 else "PROMOTE"
        else:
            verdict = "BORDERLINE" if surv >= 0.1 else "PROMOTE"
    else:
        verdict = "BORDERLINE"

    # refine: user said promote only if retention 100% AND |B|/256 << 1
    # and survives random (pass≈|B|/256), LOSO, k<->N-k
    loso_ok = all(v.get("skipped") or v["retention"] == 1.0 for v in loso.values())
    random_ok = abs(rand_rate - surv) < 0.03  # random tracks fraction
    if ret_test == 1.0 and surv < 0.05 and loso_ok and kk_ok and random_ok:
        verdict = "PROMOTE"
    elif ret_test < 1.0 or not kk_ok or not loso_ok:
        verdict = "FAIL"
    elif ret_test == 1.0 and surv >= 0.05:
        # 100% retention but not sparse enough / or bins nearly cover by chance
        verdict = "FAIL" if surv > 0.2 else "BORDERLINE"
    else:
        verdict = "FAIL"

    return {
        "n_train": len(train),
        "n_test": len(test),
        "B_train_size": len(B_train),
        "B_train_sorted": sorted(B_train),
        "survivor_fraction": surv,
        "retention_train": ret_train,
        "retention_test": ret_test,
        "retention_test_mid": retention(B_train, test_mid) if test_mid else None,
        "retention_test_late": retention(B_train, test_late) if test_late else None,
        "random_uniform_pass_rate": rand_rate,
        "k_flip_control_ok": kk_ok,
        "loso": loso,
        "loso_ok": loso_ok,
        "verdict": verdict,
    }


def main() -> None:
    load_prereg("K-20260710-00").assert_ready()
    prereg1 = load_prereg("K-20260710-01")
    prereg1.assert_ready()

    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    rsz = json.loads(RSZ.read_text(encoding="utf-8"))
    tagged = build_k00(panel, rsz)
    summary = write_k00(tagged)
    print("K-00 done:", summary["by_source"], "low_S", summary["low_S_count"])

    res = run_k01(tagged)
    print()
    print("=" * 72)
    print("K-20260710-01 orbit-safe byte-bin recurrence")
    print("=" * 72)
    print(f"|B_train| = {res['B_train_size']} / 256  survivor_fraction = {res['survivor_fraction']:.4f}")
    print(f"retention train = {res['retention_train']:.4f}")
    print(f"retention test  = {res['retention_test']:.4f}")
    print(f"random pass     = {res['random_uniform_pass_rate']:.4f}  (expect ~ survivor_fraction)")
    print(f"k<->N-k control = {res['k_flip_control_ok']}")
    print("LOSO:")
    for s, v in res["loso"].items():
        print(f"  {s}: {v}")
    print(f"VERDICT: {res['verdict']}")

    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| B_train size / 256 | {res['B_train_size']}/256 = {res['survivor_fraction']:.4f} |
| holdout retention | {res['retention_test']:.4f} |
| random pass rate | {res['random_uniform_pass_rate']:.4f} |
| LOSO ok | {res['loso_ok']} |
| k star flip control | {res['k_flip_control_ok']} |
| Verdict | {res['verdict']} |

LOSO detail: {json.dumps(res['loso'])}
"""
    if PREREG_K01.exists():
        text = PREREG_K01.read_text(encoding="utf-8")
        marker = "## Result (fill only after evaluation)"
        if marker in text:
            text = text.split(marker)[0] + block.lstrip()
        text = text.replace(
            "| Date first evaluated | *(pending)* |",
            f"| Date first evaluated | {date.today().isoformat()} |",
        )
        PREREG_K01.write_text(text, encoding="utf-8")
        (ARCHIVE_PREREG / PREREG_K01.name).write_text(text, encoding="utf-8")

    prereg1.evaluated_date = date.today().isoformat()
    save_prereg(prereg1)

    lines = [
        "K-20260710-01 orbit-safe byte-bin recurrence",
        f"survivor_fraction = {res['survivor_fraction']:.6f}",
        f"retention_test = {res['retention_test']:.6f}",
        f"random_pass = {res['random_uniform_pass_rate']:.6f}",
        f"k_flip_ok = {res['k_flip_control_ok']}",
        f"loso_ok = {res['loso_ok']}",
        f"VERDICT = {res['verdict']}",
        "",
        json.dumps({"k00_summary": summary, "k01": res}, indent=2),
    ]
    text = "\n".join(lines)
    OUT_K01.write_text(text, encoding="utf-8")
    (ARCHIVE / OUT_K01.name).write_text(text, encoding="utf-8")
    (ARCHIVE / OUT_K00_MD.name).write_text(OUT_K00_MD.read_text(encoding="utf-8"), encoding="utf-8")
    (ARCHIVE / OUT_K00_JSON.name).write_text(OUT_K00_JSON.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {OUT_K00_MD}")
    print(f"Wrote {OUT_K01}")


if __name__ == "__main__":
    main()
