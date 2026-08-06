#!/usr/bin/env python3
"""
F-20260709-02 — Mersenne carry ladder (preregistered before eval).

A_j = 2^j - 1
u = (d - A_j) mod N
Q = P - [A_j]G
S_j = corr(phi(u), phi((Qx+Qy) mod p))   # feature locked from F-01
M_real = max_j |Delta_j|; p_global from shuffle max over 257 rungs
j* selected on train only, frozen for holdout.
"""
from __future__ import annotations

import json
import random
import statistics
from dataclasses import asdict
from datetime import date
from pathlib import Path

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point

from pairing_advantage_filter import (
    ARCHIVE,
    ARCHIVE_PREREG,
    N_ORDER,
    OUT_DIR,
    P_FIELD,
    lead_frac,
    load_prereg,
    load_puzzles,
    pearson,
    save_prereg,
    score_native_lead_corr,
    shuffle_points,
)

G = SECP256k1.generator
CURVE = SECP256k1.curve
CANDIDATE_ID = "F-20260709-02"
J_MAX = 256
B_SHUF = 500
RNG = random.Random(20260709)
TRAIN_MAX = 50
OUT = OUT_DIR / "F-20260709-02_mersenne_ladder_result.txt"
PREREG_MD = OUT_DIR / "prereg" / "F-20260709-02_mersenne_carry_ladder.md"


def precompute_AjG() -> list[Point | None]:
    """[A_j]G for j=0..256. j=0 -> A=0 -> identity (None)."""
    pts: list[Point | None] = []
    for j in range(J_MAX + 1):
        A = (1 << j) - 1
        if A == 0:
            pts.append(None)  # identity
        else:
            pts.append(A * G)
    return pts


def build_tables(puzzles, AjG: list[Point | None]):
    """u_phi[i][j], g_phi[i][j] (None if Q=O); ns[i]."""
    n_p = len(puzzles)
    u_phi = [[None] * (J_MAX + 1) for _ in range(n_p)]
    g_phi = [[None] * (J_MAX + 1) for _ in range(n_p)]
    ns = [r.n for r in puzzles]
    for i, r in enumerate(puzzles):
        P = Point(CURVE, r.px, r.py)
        for j in range(J_MAX + 1):
            A = (1 << j) - 1
            u = (r.d - A) % N_ORDER
            Q = P if AjG[j] is None else P + (-AjG[j])
            if Q.x() is None:
                continue
            u_phi[i][j] = lead_frac(u)
            g_phi[i][j] = lead_frac((int(Q.x()) + int(Q.y())) % P_FIELD)
    return u_phi, g_phi, ns


def corr_at_j(u_phi, g_phi, j: int, indices: list[int], pi: list[int] | None = None) -> float | None:
    """Pearson at rung j over indices; pi permutes the Q/g side."""
    xs, ys = [], []
    for i in indices:
        ui = u_phi[i][j]
        gi = g_phi[pi[i] if pi is not None else i][j]
        if ui is None or gi is None:
            continue
        xs.append(ui)
        ys.append(gi)
    if len(xs) < 8:
        return None
    return pearson(xs, ys)


def ladder_scores(u_phi, g_phi, indices: list[int], pi: list[int] | None = None) -> list[float | None]:
    return [corr_at_j(u_phi, g_phi, j, indices, pi) for j in range(J_MAX + 1)]


def region_indices(ns: list[int], j: int, region: str, base: list[int]) -> list[int]:
    if region == "all":
        return base
    if region == "payload":
        return [i for i in base if j <= ns[i] - 1]
    if region == "wrap":
        return [i for i in base if j >= ns[i]]
    raise ValueError(region)


def hinge_scores(u_phi, g_phi, ns: list[int], indices: list[int], which: str, pi=None):
    """
    Per-puzzle j = n-1 or j = n (different rung per puzzle), then one corr.
    which in {'nm1','n'}
    """
    xs, ys = [], []
    for i in indices:
        j = ns[i] - 1 if which == "nm1" else ns[i]
        if j < 0 or j > J_MAX:
            continue
        ui = u_phi[i][j]
        gi = g_phi[pi[i] if pi is not None else i][j]
        if ui is None or gi is None:
            continue
        xs.append(ui)
        ys.append(gi)
    if len(xs) < 8:
        return None
    return pearson(xs, ys)


def max_abs_delta(real: list[float | None], means: list[float]) -> tuple[float, int]:
    best_m, best_j = -1.0, -1
    for j, s in enumerate(real):
        if s is None:
            continue
        d = abs(s - means[j])
        if d > best_m:
            best_m, best_j = d, j
    return best_m, best_j


def signed_delta(real: list[float | None], means: list[float], j: int) -> float | None:
    if real[j] is None:
        return None
    return real[j] - means[j]


def main() -> None:
    prereg = load_prereg(CANDIDATE_ID)
    prereg.assert_ready()
    print(f"Prereg LOCKED: {prereg.candidate_id} — {prereg.short_name}")
    print("Building [A_j]G and (u,Q) tables...")

    puzzles = load_puzzles(70)
    AjG = precompute_AjG()
    u_phi, g_phi, ns = build_tables(puzzles, AjG)
    n_p = len(puzzles)
    all_idx = list(range(n_p))
    train_idx = [i for i, r in enumerate(puzzles) if r.n <= TRAIN_MAX]
    test_idx = [i for i, r in enumerate(puzzles) if r.n > TRAIN_MAX]
    range_lo = [i for i, r in enumerate(puzzles) if 1 <= r.n <= 35]
    range_hi = [i for i, r in enumerate(puzzles) if 36 <= r.n <= 70]

    # --- real ladder (all puzzles) ---
    S_real = ladder_scores(u_phi, g_phi, all_idx)

    # --- shuffle ladders ---
    print(f"Running {B_SHUF} full-ladder shuffles...")
    S_shuf: list[list[float | None]] = []
    for b in range(B_SHUF):
        pi = list(range(n_p))
        RNG.shuffle(pi)
        S_shuf.append(ladder_scores(u_phi, g_phi, all_idx, pi))
        if (b + 1) % 100 == 0:
            print(f"  shuffle {b+1}/{B_SHUF}")

    # means per rung (treat None as skip in mean)
    means = []
    for j in range(J_MAX + 1):
        vals = [S_shuf[b][j] for b in range(B_SHUF) if S_shuf[b][j] is not None]
        means.append(statistics.fmean(vals) if vals else 0.0)

    deltas = [signed_delta(S_real, means, j) for j in range(J_MAX + 1)]
    M_real, j_peak = max_abs_delta(S_real, means)

    # global null: for each shuffle, max_j |S_b[j] - mean[j]|
    M_b = []
    for b in range(B_SHUF):
        m = 0.0
        for j in range(J_MAX + 1):
            s = S_shuf[b][j]
            if s is None:
                continue
            m = max(m, abs(s - means[j]))
        M_b.append(m)
    ge = sum(1 for m in M_b if m >= M_real)
    p_global = (ge + 1) / (B_SHUF + 1)

    # per-rung ordinary p (for reporting only — not for promotion)
    def rung_p(j: int) -> float:
        if S_real[j] is None:
            return 1.0
        thr = abs(S_real[j] - means[j])
        c = sum(
            1
            for b in range(B_SHUF)
            if S_shuf[b][j] is not None and abs(S_shuf[b][j] - means[j]) >= thr
        )
        return (c + 1) / (B_SHUF + 1)

    # --- train-only j* then freeze ---
    S_train = ladder_scores(u_phi, g_phi, train_idx)
    # shuffle means on train (reuse same π's restricted)
    train_shuf_means = []
    # rebuild train shuffles from same RNG stream? Use fresh dedicated train shuffles
    rng_tr = random.Random(20260709 + 1)
    S_train_shuf = []
    for _ in range(B_SHUF):
        pi = list(range(n_p))
        rng_tr.shuffle(pi)
        S_train_shuf.append(ladder_scores(u_phi, g_phi, train_idx, pi))
    for j in range(J_MAX + 1):
        vals = [S_train_shuf[b][j] for b in range(B_SHUF) if S_train_shuf[b][j] is not None]
        train_shuf_means.append(statistics.fmean(vals) if vals else 0.0)
    _, j_star = max_abs_delta(S_train, train_shuf_means)

    S_test = corr_at_j(u_phi, g_phi, j_star, test_idx)
    # test shuffle at frozen j*
    rng_te = random.Random(20260709 + 2)
    test_shuf = []
    for _ in range(B_SHUF):
        pi = list(range(n_p))
        rng_te.shuffle(pi)
        test_shuf.append(corr_at_j(u_phi, g_phi, j_star, test_idx, pi))
    test_vals = [v for v in test_shuf if v is not None]
    test_mean = statistics.fmean(test_vals) if test_vals else 0.0
    delta_test = (S_test - test_mean) if S_test is not None else None
    if S_test is not None:
        thr = abs(delta_test)
        ge_t = sum(1 for v in test_vals if abs(v - test_mean) >= thr)
        p_test = (ge_t + 1) / (len(test_vals) + 1)
    else:
        p_test = 1.0

    delta_train = signed_delta(S_train, train_shuf_means, j_star)
    delta_all_star = deltas[j_star]

    # --- payload vs wrap at j_star and at peak ---
    def region_S(j, region, indices, pi=None):
        idx = region_indices(ns, j, region, indices)
        return corr_at_j(u_phi, g_phi, j, idx, pi)

    # --- hinge ---
    S_hinge_nm1 = hinge_scores(u_phi, g_phi, ns, all_idx, "nm1")
    S_hinge_n = hinge_scores(u_phi, g_phi, ns, all_idx, "n")
    hinge_shuf_nm1, hinge_shuf_n = [], []
    rng_h = random.Random(20260709 + 3)
    for _ in range(B_SHUF):
        pi = list(range(n_p))
        rng_h.shuffle(pi)
        hinge_shuf_nm1.append(hinge_scores(u_phi, g_phi, ns, all_idx, "nm1", pi))
        hinge_shuf_n.append(hinge_scores(u_phi, g_phi, ns, all_idx, "n", pi))

    def hinge_stats(real, shuf):
        vals = [v for v in shuf if v is not None]
        mean = statistics.fmean(vals) if vals else 0.0
        if real is None:
            return None, mean, 1.0
        d = real - mean
        ge = sum(1 for v in vals if abs(v - mean) >= abs(d))
        return d, mean, (ge + 1) / (len(vals) + 1)

    d_nm1, m_nm1, p_nm1 = hinge_stats(S_hinge_nm1, hinge_shuf_nm1)
    d_n, m_n, p_n = hinge_stats(S_hinge_n, hinge_shuf_n)

    # control sawtooth on original
    ctrl_real = score_native_lead_corr(puzzles)
    ctrl_shuf = [
        score_native_lead_corr(shuffle_points(puzzles, RNG)) for _ in range(200)
    ]
    ctrl_adv = ctrl_real - statistics.fmean(ctrl_shuf)

    # top rungs by |Delta|
    ranked = sorted(
        ((abs(deltas[j]), j, deltas[j], S_real[j], means[j], rung_p(j)) for j in range(J_MAX + 1) if deltas[j] is not None),
        reverse=True,
    )[:15]

    # promotion checks on frozen j*
    adv_ok = delta_test is not None and abs(delta_test) > 0.12
    # use signed advantage > 0.12 if expected higher; prereg says |Delta| — require abs
    p_ok = p_test < 0.01
    g_ok = p_global < 0.01
    # direction: train and test delta same sign
    dir_ok = (
        delta_train is not None
        and delta_test is not None
        and (delta_train > 0) == (delta_test > 0)
        and abs(delta_train) > 0.05
        and abs(delta_test) > 0.05
    )
    if g_ok and adv_ok and p_ok and dir_ok and abs(delta_test) > abs(ctrl_adv) + 0.02:
        verdict = "PROMOTE"
    elif abs(M_real) < 0.05 or p_global > 0.10:
        verdict = "FAIL"
    else:
        verdict = "BORDERLINE"

    lines = []
    def w(s=""):
        lines.append(s)
        print(s)

    w("=" * 72)
    w("F-20260709-02 Mersenne carry ladder")
    w("=" * 72)
    w(f"N puzzles={n_p}  B={B_SHUF}  j=0..{J_MAX}")
    w(f"Feature: locked phi(u) vs phi((Qx+Qy) mod p)  [same as F-01]")
    w()
    w(f"M_real = max|Delta_j| = {M_real:.4f}  at j_peak={j_peak}")
    w(f"p_global = {p_global:.4f}  ({ge}/{B_SHUF} shuffles with M_b >= M_real)")
    w(f"null M_b: mean={statistics.fmean(M_b):.4f}  p95={sorted(M_b)[int(0.95*(B_SHUF-1))]:.4f}")
    w(f"sawtooth control advantage = {ctrl_adv:+.4f}")
    w()
    w("TOP |Delta_j| (ordinary per-rung p is NOT for promotion):")
    for ab, j, d, s, m, p in ranked:
        w(f"  j={j:3d}  S={s:+.4f}  mean_shuf={m:+.4f}  Delta={d:+.4f}  p_rung={p:.3f}")
    w()
    w("--- Train-selected j* (frozen) ---")
    w(f"j* = {j_star}  (argmax |Delta| on train n=1..50)")
    w(f"train: S={S_train[j_star]:+.4f}  Delta={delta_train:+.4f}" if S_train[j_star] is not None else "train: None")
    w(f"test:  S={S_test:+.4f}  Delta={delta_test:+.4f}  p={p_test:.4f}" if S_test is not None else "test: None")
    w(f"all:   S={S_real[j_star]:+.4f}  Delta={delta_all_star:+.4f}" if S_real[j_star] is not None else "all: None")
    # payload vs wrap at j*
    for region in ("payload", "wrap"):
        s = region_S(j_star, region, all_idx)
        w(f"  region {region:8s} at j*: S={s:+.4f}" if s is not None else f"  region {region:8s} at j*: n/a")
    w()
    w("--- Hinge j=n-1 -> j=n (per-puzzle aligned) ---")
    w(f"j=n-1: S={S_hinge_nm1:+.4f}  Delta={d_nm1:+.4f}  p={p_nm1:.4f}" if S_hinge_nm1 is not None else "j=n-1: n/a")
    w(f"j=n:   S={S_hinge_n:+.4f}  Delta={d_n:+.4f}  p={p_n:.4f}" if S_hinge_n is not None else "j=n: n/a")
    w()
    w("PROMOTION (frozen j* + p_global):")
    w(f"  [ {'OK' if adv_ok else 'NO'} ] |Delta_test| > 0.12")
    w(f"  [ {'OK' if p_ok else 'NO'} ] p_test < 0.01")
    w(f"  [ {'OK' if g_ok else 'NO'} ] p_global < 0.01")
    w(f"  [ {'OK' if dir_ok else 'NO'} ] train/test Delta same direction")
    w(f"VERDICT: {verdict}")
    w()
    w("Note: (2^256-1) mod N is ~129 bits — top rungs are modular complements,")
    w("not largest translated magnitudes. Payload vs wrap reported separately.")

    # fill prereg md
    block = f"""
## Result (evaluated {date.today().isoformat()})

| Metric | Value |
|--------|------:|
| M_real | {M_real:.4f} (j_peak={j_peak}) |
| p_global | {p_global:.4f} |
| j* (train) | {j_star} |
| holdout S / Δ / p | {S_test:+.4f} / {delta_test:+.4f} / {p_test:.4f} |
| hinge j=n-1 Δ / p | {d_nm1:+.4f} / {p_nm1:.4f} |
| hinge j=n Δ / p | {d_n:+.4f} / {p_n:.4f} |
| Verdict | {verdict} |

Notes: Feature locked from F-01. Global null pays for 257-rung search. j* frozen from train.
"""
    if PREREG_MD.exists():
        text = PREREG_MD.read_text(encoding="utf-8")
        marker = "## Result (fill only after evaluation)"
        if marker in text:
            text = text.split(marker)[0] + block.lstrip()
        text = text.replace(
            "| Date first evaluated | *(pending)* |",
            f"| Date first evaluated | {date.today().isoformat()} |",
        )
        PREREG_MD.write_text(text, encoding="utf-8")
        (ARCHIVE_PREREG / PREREG_MD.name).write_text(text, encoding="utf-8")

    prereg.evaluated_date = date.today().isoformat()
    save_prereg(prereg)

    payload = {
        "candidate_id": CANDIDATE_ID,
        "M_real": M_real,
        "j_peak": j_peak,
        "p_global": p_global,
        "j_star": j_star,
        "S_test": S_test,
        "delta_test": delta_test,
        "p_test": p_test,
        "hinge": {
            "nm1": {"S": S_hinge_nm1, "delta": d_nm1, "p": p_nm1},
            "n": {"S": S_hinge_n, "delta": d_n, "p": p_n},
        },
        "top_deltas": [
            {"j": j, "S": s, "delta": d, "p_rung": p} for ab, j, d, s, m, p in ranked
        ],
        "control_advantage": ctrl_adv,
        "verdict": verdict,
        "A_256_mod_N_bits": ((1 << 256) - 1) % N_ORDER,
    }
    # bit length of (2^256-1) mod N
    payload["A_256_mod_N"] = ((1 << 256) - 1) % N_ORDER
    payload["A_256_mod_N_bitlength"] = payload["A_256_mod_N"].bit_length()

    text = "\n".join(lines) + "\n\n" + json.dumps(payload, indent=2)
    OUT.write_text(text, encoding="utf-8")
    (ARCHIVE / OUT.name).write_text(text, encoding="utf-8")
    w()
    w(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
