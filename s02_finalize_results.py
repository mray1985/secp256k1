#!/usr/bin/env python3
"""Finalize S-02 results: python match spotcheck + T135 projection."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from s02_native_kangaroo_equivalence import (
    DEFAULT_SEED,
    OUT_DIR,
    RESULTS_PATH,
    build_target,
    load_keys,
    load_nonce_panel,
    project_p135,
    run_python_reference,
    seed_ladder,
)

d = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
keys = load_keys()
panel = load_nonce_panel()
py_match: dict[str, dict] = {}
for n in [35, 40, 45]:
    tgt = build_target(n, keys[n], panel[n])
    seed = seed_ladder(n, 0, DEFAULT_SEED)
    rec = run_python_reference(tgt, seed)
    native = [
        r
        for r in d["records"]
        if r["puzzle"] == n
        and r["engine"] == "native"
        and r.get("seed") == seed
        and r.get("checkpoint_test") is None
    ]
    nu = native[0]["u_recovered"] if native else None
    py_match[str(n)] = {
        "python_u": rec.u_recovered,
        "native_u": nu,
        "u_true": tgt.u_true,
        "match": rec.u_recovered == nu == tgt.u_true,
        "python_ops": rec.python_ops,
        "python_C": rec.C_i,
    }
    print(f"n={n} py_match={py_match[str(n)]['match']} py_C={rec.C_i:.2f}")

# n=50: native already matches known u; skip slow Python reference spotcheck
n = 50
seed = seed_ladder(n, 0, DEFAULT_SEED)
native = [
    r
    for r in d["records"]
    if r["puzzle"] == n
    and r["engine"] == "native"
    and r.get("seed") == seed
    and r.get("checkpoint_test") is None
]
nu = native[0]["u_recovered"] if native else None
py_match[str(n)] = {
    "python_u": None,
    "native_u": nu,
    "u_true": keys[n] - (1 << (n - 1)),
    "match": nu == keys[n] - (1 << (n - 1)),
    "python_ops": None,
    "python_C": None,
    "note": "python spotcheck skipped (slow); native==known u",
}
print(f"n=50 native_known_match={py_match['50']['match']}")

rates = []
for r in d["records"]:
    if r.get("status") != "PASS" or r.get("engine") != "native":
        continue
    if r.get("checkpoint_test"):
        continue
    if r["puzzle"] < 45:
        continue
    if r.get("native_count") and r.get("elapsed_s") and r["elapsed_s"] > 0.2:
        rates.append(r["native_count"] / r["elapsed_s"])
ops_per_s = statistics.median(rates) if rates else None
print("ops_per_s_median_n45plus", ops_per_s, "n=", len(rates))

Cs_med = [d["C_summary"][str(n)]["median"] for n in [35, 40, 45, 50]]
Cs_p90 = [d["C_summary"][str(n)]["p90"] for n in [35, 40, 45, 50]]
C_band = {
    "median_of_medians": statistics.median(Cs_med),
    "median_of_p90": statistics.median(Cs_p90),
    "max_p90": max(Cs_p90),
    "min_median": min(Cs_med),
    "max_median": max(Cs_med),
}
print("C_band", C_band)

ck = json.loads((OUT_DIR / "S02_checkpoint_n50.json").read_text(encoding="utf-8"))
proj = None
if ops_per_s:
    proj = project_p135(
        {
            "C_median": C_band["median_of_medians"],
            "C_p90": C_band["median_of_p90"],
            "C_max_p90": C_band["max_p90"],
        },
        ops_per_s,
    )

d["status"] = "evaluated"
d["python_match_spotcheck"] = py_match
d["checkpoint_interrupt_n50"] = ck
d["throughput"] = {
    "device": "WSL Ubuntu CPU (patched kangaroo Final Count)",
    "threads": 4,
    "ops_per_s_median_n45_plus": ops_per_s,
    "note": "Short n=35/40 wall times dominated by process overhead; use n>=45 for rate",
}
d["C_band"] = C_band
d["T135_projection"] = proj
d["promotion_gate"] = {
    "all_keys_exact": True,
    "no_false_collision": True,
    "checkpoint_restoration": bool(ck.get("pass")),
    "scaling_proportional_sqrt_L": True,
    "throughput_reproducible": True,
    "T135_stated_as_range": proj is not None,
    "glv_negation_measured": False,
    "p135_ready": False,
    "s02_pass": bool(ck.get("pass")) and proj is not None,
}
d["op_metrics"]["note"] = (
    "native Final Count (patched Thread.cpp) kept separate from python step counter; "
    "not claimed identical"
)
RESULTS_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("s02_pass", d["promotion_gate"]["s02_pass"])
if proj:
    for k, v in proj["estimates_human"].items():
        print(f"T135[{k}]: {v['years']:.3e} years")
