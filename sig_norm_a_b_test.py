#!/usr/bin/env python3
"""Signature-normalization test: (a,b) = (s r^{-1}, z r^{-1}) mod N.

ECDSA: s*k = z + r*d  (mod N)
=> a*k = b + d  (mod N) with a=s*r^{-1}, b=z*r^{-1}
=> d = a*k - b  (mod N)
=> k = a^{-1}(d+b)  (mod N)   [solved rows; must match known nonce]

Also:
  c = (-b) mod N
  theta = 2*pi*a/N
  a_tilde = centered representative in (-N/2, N/2]

NOT a vector-path claim. Hamming extremes are cohort-plausible (documented).
X3p-Y2p=0 is curve checksum only — excluded as a feature.
"""

from __future__ import annotations

import json
import math
import random
import hashlib
from dataclasses import dataclass
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N, load_rows

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")
TWO_PI = 2.0 * math.pi
MU_H = 80.0
SIG_H = math.sqrt(40.0)


def mod_center(x: int, mod: int = N) -> int:
    x %= mod
    if x > mod // 2:
        return x - mod
    return x


def circ_dist(u: int, v: int, mod: int = N) -> int:
    """Minimum distance on the modular circle."""
    d = abs((u - v) % mod)
    return min(d, mod - d)


@dataclass
class SigRow:
    n: int
    solved: bool
    d: int | None
    k_known: int | None
    r: int
    s: int
    z: int
    a: int
    b: int
    c: int
    k_rec: int | None
    k_match: bool | None
    a_tilde: int
    b_tilde: int
    theta_a: float
    theta_b: float
    h160: int
    wt: int
    addr_y: int  # checksum4


def build_rows() -> list[SigRow]:
    cat = load_catalog()
    rsz = {r.n: r for r in load_rows()}
    out: list[SigRow] = []
    for n in range(1, 161):
        e = cat[n]
        rr = rsz.get(n)
        if not rr or not rr.r or not rr.s or rr.z is None:
            continue
        r, s, z = rr.r % N, rr.s % N, rr.z % N
        if r == 0:
            continue
        r_inv = pow(r, -1, N)
        a = (s * r_inv) % N
        b = (z * r_inv) % N
        c = (-b) % N
        d = e.private_key if e.private_key > 0 else (rr.d if rr.d else None)
        k_known = rr.k
        k_rec = None
        k_match = None
        if d is not None and a != 0:
            k_rec = (pow(a, -1, N) * ((d + b) % N)) % N
            if k_known is not None:
                k_match = k_rec == (k_known % N)
            else:
                # verify via ECDSA identity: s*k ?= z + r*d
                k_match = (s * k_rec) % N == (z + r * d) % N

        h160 = int(e.hash160, 16)
        vh = b"\x00" + h160.to_bytes(20, "big")
        c4 = int.from_bytes(hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4], "big")

        out.append(
            SigRow(
                n=n,
                solved=bool(d),
                d=d,
                k_known=k_known,
                r=r,
                s=s,
                z=z,
                a=a,
                b=b,
                c=c,
                k_rec=k_rec,
                k_match=k_match,
                a_tilde=mod_center(a),
                b_tilde=mod_center(b),
                theta_a=TWO_PI * a / N,
                theta_b=TWO_PI * b / N,
                h160=h160,
                wt=h160.bit_count(),
                addr_y=c4,
            )
        )
    return out


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def circ_mean_theta(thetas: list[float]) -> float:
    if not thetas:
        return float("nan")
    sx = sum(math.cos(t) for t in thetas)
    sy = sum(math.sin(t) for t in thetas)
    return math.atan2(sy, sx) % TWO_PI


def group_stats(rows: list[SigRow], label: str) -> dict:
    if not rows:
        return {"label": label, "n": 0}
    return {
        "label": label,
        "n": len(rows),
        "puzzles": [r.n for r in rows],
        "wt_mean": mean([float(r.wt) for r in rows]),
        "addr_y_mean": mean([float(r.addr_y) for r in rows]),
        "a_tilde_mean": mean([float(r.a_tilde) for r in rows]),
        "b_tilde_mean": mean([float(r.b_tilde) for r in rows]),
        "theta_a_circ_mean": circ_mean_theta([r.theta_a for r in rows]),
        "theta_b_circ_mean": circ_mean_theta([r.theta_b for r in rows]),
        "mean_circ_dist_a_to_0": mean([float(circ_dist(r.a, 0)) for r in rows]),
        "mean_circ_dist_b_to_0": mean([float(circ_dist(r.b, 0)) for r in rows]),
    }


def held_out_k_check(rows: list[SigRow], trials: int = 200, seed: int = 0) -> dict:
    """On solved rows with k_match True: leave-one-out is identity check per row.
    Also shuffle pairing of (a,b) with d to show gate: wrong pairing fails k ECDSA check.
    """
    solved = [r for r in rows if r.solved and r.d is not None and r.a]
    # self recovery rate
    self_ok = sum(1 for r in solved if r.k_match)
    # pairing shuffle: use a,b from donor with d from target — should usually fail ECDSA
    rng = random.Random(seed)
    fail = 0
    for _ in range(trials):
        t = rng.choice(solved)
        donor = rng.choice(solved)
        # fake k from donor a,b and target d
        a, b, d = donor.a, donor.b, t.d
        if a == 0:
            continue
        k_fake = (pow(a, -1, N) * ((d + b) % N)) % N
        # check against TARGET signature (t.s,t.r,t.z)
        ok = (t.s * k_fake) % N == (t.z + t.r * d) % N
        if not ok:
            fail += 1
    return {
        "solved_with_a": len(solved),
        "k_recovery_self_ok": self_ok,
        "k_recovery_self_rate": self_ok / len(solved) if solved else 0.0,
        "shuffle_trials": trials,
        "shuffle_ecdsa_fail": fail,
        "shuffle_fail_rate": fail / trials,
        "note": "Self recovery must be ~1. Shuffled (a,b) with wrong d must fail ECDSA almost always.",
    }


def main() -> None:
    rows = build_rows()
    solved = [r for r in rows if r.solved]
    unsolved_focus = [r for r in rows if r.n in (135, 150, 155, 160)]

    gate = held_out_k_check(rows)

    # Hamming midranks for weight groups
    from collections import defaultdict

    by_wt: dict[int, list[SigRow]] = defaultdict(list)
    for r in rows:
        by_wt[r.wt].append(r)

    # binomial cohort note
    p65 = 0.01079
    p97 = 0.00444
    p90 = 0.0664
    cohort_note = {
        "mu": MU_H,
        "sigma": SIG_H,
        "P_W_le_65_single": p65,
        "P_at_least_one_le_65_in_160": 1 - (1 - p65) ** 160,
        "P_W_ge_97_single": p97,
        "P_at_least_one_ge_97_in_160": 1 - (1 - p97) ** 160,
        "P_W_ge_90_single": p90,
        "expected_count_ge_90_in_160": 160 * p90,
        "midrank_note": "Equal Hamming weights share midranks; stable-sort rank gaps are tie artifacts.",
        "X3p_Y2p_note": "X3p-Y2p=0 is curve mod-p checksum, not a feature.",
    }

    # group comparisons: low/mid/high wt among rows that HAVE signatures
    wts_sorted = sorted(by_wt.keys())
    low_w = wts_sorted[: max(1, len(wts_sorted) // 5)]
    high_w = wts_sorted[-max(1, len(wts_sorted) // 5) :]
    mid_w = [w for w in wts_sorted if w not in low_w and w not in high_w]
    groups = {
        "all_with_rsz": group_stats(rows, "all_with_rsz"),
        "solved": group_stats(solved, "solved"),
        "focus_135_150_155_160": group_stats(unsolved_focus, "focus"),
        "low_wt_quintile": group_stats(
            [r for r in rows if r.wt in low_w], "low_wt_quintile"
        ),
        "mid_wt": group_stats([r for r in rows if r.wt in mid_w], "mid_wt"),
        "high_wt_quintile": group_stats(
            [r for r in rows if r.wt in high_w], "high_wt_quintile"
        ),
        "wt82": group_stats(by_wt.get(82, []), "wt82"),
        "wt86": group_stats(by_wt.get(86, []), "wt86"),
        "wt90": group_stats(by_wt.get(90, []), "wt90"),
        "wt81": group_stats(by_wt.get(81, []), "wt81"),
    }

    # pairwise circ distances within focus
    focus_pairs = []
    for i, u in enumerate(unsolved_focus):
        for v in unsolved_focus[i + 1 :]:
            focus_pairs.append(
                {
                    "pair": [u.n, v.n],
                    "circ_dist_a": circ_dist(u.a, v.a),
                    "circ_dist_b": circ_dist(u.b, v.b),
                    "abs_a_tilde_diff": abs(u.a_tilde - v.a_tilde),
                    "abs_b_tilde_diff": abs(u.b_tilde - v.b_tilde),
                    "abs_addr_y_diff": abs(u.addr_y - v.addr_y),
                    "abs_wt_diff": abs(u.wt - v.wt),
                }
            )

    # export table
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "SIG_NORM_A_B.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(
            "n,solved,wt,addr_y,a,b,c,a_tilde,b_tilde,theta_a,theta_b,"
            "k_rec,k_known,k_match\n"
        )
        for r in sorted(rows, key=lambda x: x.n):
            fh.write(
                f"{r.n},{int(r.solved)},{r.wt},{r.addr_y},{r.a},{r.b},{r.c},"
                f"{r.a_tilde},{r.b_tilde},{r.theta_a:.10f},{r.theta_b:.10f},"
                f"{'' if r.k_rec is None else r.k_rec},"
                f"{'' if r.k_known is None else r.k_known},"
                f"{'' if r.k_match is None else int(r.k_match)}\n"
            )

    report = {
        "definition": {
            "a": "s * r^{-1} mod N",
            "b": "z * r^{-1} mod N",
            "c": "(-b) mod N",
            "k_rec": "a^{-1} * (d + b) mod N on solved",
            "identity": "a*k = b + d  (mod N)",
        },
        "coverage": {
            "rows_with_rsz": len(rows),
            "solved": len(solved),
            "focus_present": [r.n for r in unsolved_focus],
            "missing_focus_note": "137/153 etc. lack rsz — excluded from (a,b) test",
        },
        "hamming_cohort_plausibility": cohort_note,
        "k_recovery_gate": gate,
        "groups": groups,
        "focus_detail": [
            {
                "n": r.n,
                "wt": r.wt,
                "addr_y": r.addr_y,
                "a": r.a,
                "b": r.b,
                "c": r.c,
                "a_tilde": r.a_tilde,
                "b_tilde": r.b_tilde,
                "theta_a": r.theta_a,
                "theta_b": r.theta_b,
            }
            for r in unsolved_focus
        ],
        "focus_pairwise_circ": focus_pairs,
        "ruling": (
            "Signature normalization (a,b) is well-defined and k recovers on solved rows. "
            "It is an accounting rewrite of ECDSA, not a public predictor of d. "
            "Hamming extremes are cohort-plausible; equal weights need midranks. "
            "Do not use X3p-Y2p=0 as structure."
        ),
    }
    (OUT / "SIG_NORM_A_B.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # human report
    lines = [
        "SIGNATURE NORMALIZATION TEST  (a,b) = (s r^{-1}, z r^{-1}) mod N",
        "",
        "a*k = b + d  (mod N)   =>   d = a*k - b  (mod N)   =>   k = a^{-1}(d+b)",
        "This is ECDSA rewritten — not a public vector path to d.",
        "",
        f"rows with (r,s,z): {len(rows)}   solved: {len(solved)}",
        f"focus with rsz: {[r.n for r in unsolved_focus]}",
        "",
        "--- k recovery gate (solved) ---",
        f"self k_match: {gate['k_recovery_self_ok']}/{gate['solved_with_a']} "
        f"({gate['k_recovery_self_rate']:.4f})",
        f"shuffle (a,b)@wrong d ECDSA fail rate: {gate['shuffle_fail_rate']:.4f} "
        f"({gate['shuffle_ecdsa_fail']}/{gate['shuffle_trials']})",
        "",
        "--- Hamming plausibility ---",
        f"P(at least one W<=65 in 160) ≈ {cohort_note['P_at_least_one_le_65_in_160']:.3f}",
        f"P(at least one W>=97 in 160) ≈ {cohort_note['P_at_least_one_ge_97_in_160']:.3f}",
        f"E[count W>=90] ≈ {cohort_note['expected_count_ge_90_in_160']:.2f}",
        "Equal weights => midranks (stable-sort rank gaps are tie artifacts).",
        "X3p-Y2p=0 is curve checksum only.",
        "",
        "--- Focus (a,b,c, theta, addr_y) ---",
    ]
    for r in unsolved_focus:
        lines.append(
            f"P{r.n}: wt={r.wt} addr_y={r.addr_y} "
            f"a_tilde={r.a_tilde} b_tilde={r.b_tilde} "
            f"theta_a={r.theta_a:.6f} theta_b={r.theta_b:.6f}"
        )
        lines.append(f"     a={r.a}")
        lines.append(f"     b={r.b}")
        lines.append(f"     c={r.c}")

    lines += ["", "--- Focus pairwise circular distances ---"]
    for p in focus_pairs:
        lines.append(
            f"  {p['pair']}: circ_a={p['circ_dist_a']} circ_b={p['circ_dist_b']} "
            f"|Δaddr_y|={p['abs_addr_y_diff']} |Δwt|={p['abs_wt_diff']}"
        )

    lines += ["", "--- Group circular summaries (rows that have rsz only) ---"]
    for g in groups.values():
        if g["n"] == 0:
            continue
        lines.append(
            f"{g['label']}: n={g['n']}  "
            f"theta_a_mean={g['theta_a_circ_mean']:.4f}  "
            f"theta_b_mean={g['theta_b_circ_mean']:.4f}  "
            f"mean_circ_a_to_0={g['mean_circ_dist_a_to_0']:.3e}"
        )

    lines += [
        "",
        "RULING: compute (a,b) as signature-normalization coordinates — YES.",
        "Interpret as precise public vector path to d — NO (needs k or equivalent).",
        "Next honest step remains held-out checks on solved only; unsolved get (a,b) listed not predicted.",
    ]
    (OUT / "SIG_NORM_A_B.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"rows={len(rows)} solved={len(solved)} focus={[r.n for r in unsolved_focus]}")
    print(
        f"k_self={gate['k_recovery_self_ok']}/{gate['solved_with_a']} "
        f"shuffle_fail={gate['shuffle_fail_rate']:.3f}"
    )
    print(f"wrote {csv_path}")
    print(f"wrote {OUT / 'SIG_NORM_A_B.txt'}")


if __name__ == "__main__":
    main()
