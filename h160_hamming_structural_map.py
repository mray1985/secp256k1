#!/usr/bin/env python3
"""Hamming-weight structural map + s*r^{-1} mod N on boundary clusters.

Verifies binomial baseline claims, builds focus/tail tables, merges with
sCHK / unreduced Delta ranks, and computes modular scales:
  s * r^{-1} mod N
  s^{-1} * z mod N
  s^{-1} * r mod N
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N, load_rows, recover_xy_from_pubkey, P

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")
MU = 80.0
SIG = math.sqrt(160 * 0.5 * 0.5)


def dense_ranks(values: dict[int, int | float]) -> dict[int, int]:
    items = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    return {pn: i for i, (pn, _) in enumerate(items, start=1)}


def main() -> None:
    cat = load_catalog()
    rsz = {r.n: r for r in load_rows()}

    rows: dict[int, dict] = {}
    for n in range(1, 161):
        e = cat[n]
        h160 = int(e.hash160, 16)
        wt = h160.bit_count()
        rows[n] = {
            "n": n,
            "h160": h160,
            "wt": wt,
            "zscore": (wt - MU) / SIG,
            "solved": e.solved,
            "d": e.private_key if e.private_key > 0 else None,
        }
        rr = rsz.get(n)
        if rr and rr.r and rr.s and rr.z is not None:
            r_inv = pow(rr.r, -1, N)
            s_inv = pow(rr.s, -1, N)
            rows[n]["r"] = rr.r
            rows[n]["s"] = rr.s
            rows[n]["z"] = rr.z
            rows[n]["s_r_inv"] = (rr.s * r_inv) % N  # s * r^{-1} mod N
            rows[n]["s_inv_z"] = (s_inv * (rr.z % N)) % N
            rows[n]["s_inv_r"] = (s_inv * (rr.r % N)) % N

        px = py = None
        if e.public_key:
            px, py = recover_xy_from_pubkey(e.public_key)
        if px is None and rr and rr.Px:
            px, py = rr.Px, rr.Py
        if px is not None and py is not None:
            Y = py * py
            X = px * px * px + 7
            rows[n]["y2_full"] = Y
            rows[n]["x3plus7_full"] = X
            rows[n]["p_carry"] = (X - Y) // P
            rows[n]["Y2p"] = Y % P
            rows[n]["X3p"] = X % P
            rows[n]["Delta_Rk_modp"] = 0  # identical values

        # sCHK = sha256_chk rank later
        import hashlib

        vh = b"\x00" + h160.to_bytes(20, "big")
        sha_chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()
        rows[n]["sCHK"] = int.from_bytes(sha_chk, "big")
        sha_vh = hashlib.sha256(vh).digest()
        rows[n]["sVH"] = int.from_bytes(sha_vh, "big")

    wt_rank = dense_ranks({n: rows[n]["wt"] for n in range(1, 161)})
    schk_rank = dense_ranks({n: rows[n]["sCHK"] for n in range(1, 161)})
    svh_rank = dense_ranks({n: rows[n]["sVH"] for n in range(1, 161)})
    y2f_rank = dense_ranks(
        {n: rows[n]["y2_full"] for n in range(1, 161) if "y2_full" in rows[n]}
    )
    x3f_rank = dense_ranks(
        {n: rows[n]["x3plus7_full"] for n in range(1, 161) if "x3plus7_full" in rows[n]}
    )
    s_r_inv_rank = dense_ranks(
        {n: rows[n]["s_r_inv"] for n in range(1, 161) if "s_r_inv" in rows[n]}
    )
    s_inv_z_rank = dense_ranks(
        {n: rows[n]["s_inv_z"] for n in range(1, 161) if "s_inv_z" in rows[n]}
    )

    for n in range(1, 161):
        rows[n]["wt_rank"] = wt_rank[n]
        rows[n]["sCHK_rank"] = schk_rank[n]
        rows[n]["sVH_rank"] = svh_rank[n]
        if n in y2f_rank:
            rows[n]["y2_full_rank"] = y2f_rank[n]
            rows[n]["x3plus7_full_rank"] = x3f_rank[n]
            rows[n]["Delta_Rk_full"] = x3f_rank[n] - y2f_rank[n]
        if n in s_r_inv_rank:
            rows[n]["s_r_inv_rank"] = s_r_inv_rank[n]
            rows[n]["s_inv_z_rank"] = s_inv_z_rank[n]

    wts = [rows[n]["wt"] for n in range(1, 161)]
    sample_mean = sum(wts) / 160
    sample_std = math.sqrt(sum((w - sample_mean) ** 2 for w in wts) / 160)

    # match cohorts by identical wt
    def same_wt(n: int) -> list[int]:
        w = rows[n]["wt"]
        return [m for m in range(1, 161) if rows[m]["wt"] == w]

    focus = [135, 150, 155, 160]
    low_tail = [137, 78, 128, 8, 159]
    high_tail = [153, 98, 97, 16, 142]

    lines = []
    lines += [
        "H160 HAMMING WEIGHT STRUCTURAL MAP + MODULAR SCALES",
        f"theoretical mu={MU}  sigma={SIG:.6f}",
        f"sample mean={sample_mean:.5f}  sample stdev={sample_std:.5f}",
        "",
        "NOTE: Delta_Rk on Y2p/X3p is always 0 (mod-p curve identity).",
        "      Use Delta_Rk_full = Rank(x3plus7_full)-Rank(y2_full) for non-trivial spatial delta.",
        "",
        "=" * 72,
        "1. FOCUS UNSOLVED",
        "=" * 72,
    ]
    for n in focus:
        r = rows[n]
        peers = same_wt(n)
        lines.append(
            f"P{n}: wt={r['wt']} rank={r['wt_rank']} z={r['zscore']:+.2f} "
            f"sVH_rk={r['sVH_rank']} sCHK_rk={r['sCHK_rank']} "
            f"Delta_modp=0 Delta_full={r.get('Delta_Rk_full', '')}"
        )
        lines.append(
            f"  same-wt peers: {peers}"
        )

    lines += [
        "",
        "=" * 72,
        "2. TAIL THRESHOLDS",
        "=" * 72,
        "LOWEST 5 (bit squeezing):",
    ]
    by_rank = sorted(range(1, 161), key=lambda n: rows[n]["wt_rank"])
    for n in by_rank[:5]:
        r = rows[n]
        lines.append(
            f"  rank {r['wt_rank']:3d}  P{n:3d}  wt={r['wt']}  z={r['zscore']:+.2f}  "
            f"{'SOLVED' if r['solved'] else 'unsolved'}"
        )
    unsolved_low = sum(1 for n in by_rank[:5] if not rows[n]["solved"])
    lines.append(f"  unsolved among lowest 5: {unsolved_low}/5")
    lines.append("HIGHEST 5:")
    for n in by_rank[-5:]:
        r = rows[n]
        lines.append(
            f"  rank {r['wt_rank']:3d}  P{n:3d}  wt={r['wt']}  z={r['zscore']:+.2f}  "
            f"{'SOLVED' if r['solved'] else 'unsolved'}"
        )

    lines += [
        "",
        "=" * 72,
        "3. MERGE: Hamming + spatial + sCHK",
        "=" * 72,
        f"{'n':>3} {'wt':>3} {'wtRk':>4} {'dFull':>5} {'sVH':>4} {'sCHK':>4}  note",
    ]
    for n in focus:
        r = rows[n]
        lines.append(
            f"{n:3d} {r['wt']:3d} {r['wt_rank']:4d} {r.get('Delta_Rk_full',''):>5} "
            f"{r['sVH_rank']:4d} {r['sCHK_rank']:4d}  "
            f"{'median control' if n==160 else 'focus'}"
        )

    # P150 vs P2 dual match
    lines += [
        "",
        "P150 vs P2 dual-metric check:",
        f"  P150 wt={rows[150]['wt']} wtRk={rows[150]['wt_rank']} sCHK_rk={rows[150]['sCHK_rank']}",
        f"  P2   wt={rows[2]['wt']} wtRk={rows[2]['wt_rank']} sCHK_rk={rows[2]['sCHK_rank']}",
        f"  same wt: {rows[150]['wt']==rows[2]['wt']}  "
        f"(sCHK ranks differ: {rows[150]['sCHK_rank']} vs {rows[2]['sCHK_rank']})",
    ]

    # Modular multiplicative scales on clusters
    clusters = {
        "focus_unsolved": [n for n in focus if "s_r_inv" in rows[n]],
        "low_tail": [n for n in low_tail if "s_r_inv" in rows[n]],
        "high_tail": [n for n in high_tail if "s_r_inv" in rows[n]],
        "wt86_cluster": [n for n in same_wt(150) if "s_r_inv" in rows[n]],
        "wt90_cluster": [n for n in same_wt(155) if "s_r_inv" in rows[n]],
        "wt82_cluster": [n for n in same_wt(135) if "s_r_inv" in rows[n]],
    }

    lines += [
        "",
        "=" * 72,
        "4. MODULAR MULTIPLICATIVE SCALES  s*r^{-1}, s^{-1}*z, s^{-1}*r  (mod N)",
        "=" * 72,
    ]
    for name, ns in clusters.items():
        lines.append(f"--- {name} ({len(ns)}) ---")
        lines.append(
            f"{'n':>3} {'solved':>6} {'wt':>3} {'s*r^-1 rank':>12} {'s^-1*z rank':>12}  s*r^-1 mod N"
        )
        for n in sorted(ns, key=lambda i: rows[i].get("s_r_inv_rank", 999)):
            r = rows[n]
            lines.append(
                f"{n:3d} {str(r['solved']):>6} {r['wt']:3d} "
                f"{r.get('s_r_inv_rank',''):>12} {r.get('s_inv_z_rank',''):>12}  "
                f"{r.get('s_r_inv','')}"
            )
        lines.append("")

    # Full 160 wt table
    lines += [
        "=" * 72,
        "5. FULL COHORT wt / rank / zscore",
        "=" * 72,
        f"{'n':>3} {'wt':>3} {'rank':>4} {'z':>6} {'status':>8}",
    ]
    for n in by_rank:
        r = rows[n]
        lines.append(
            f"{n:3d} {r['wt']:3d} {r['wt_rank']:4d} {r['zscore']:+6.2f} "
            f"{'solved' if r['solved'] else 'unsolved':>8}"
        )

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "H160_HAMMING_STRUCTURAL_MAP.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # CSV of modular scales for all with rsz
    csv_path = OUT / "MODULAR_SCALES_S_R_INV.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(
            "n,solved,wt,wt_rank,sCHK_rank,sVH_rank,Delta_Rk_full,"
            "s_r_inv,s_r_inv_rank,s_inv_z,s_inv_z_rank,s_inv_r\n"
        )
        for n in range(1, 161):
            r = rows[n]
            if "s_r_inv" not in r:
                continue
            fh.write(
                f"{n},{int(r['solved'])},{r['wt']},{r['wt_rank']},{r['sCHK_rank']},{r['sVH_rank']},"
                f"{r.get('Delta_Rk_full','')},"
                f"{r['s_r_inv']},{r['s_r_inv_rank']},{r['s_inv_z']},{r['s_inv_z_rank']},{r['s_inv_r']}\n"
            )

    # JSON summary
    (OUT / "H160_HAMMING_STRUCTURAL_MAP.json").write_text(
        json.dumps(
            {
                "mu": MU,
                "sigma": SIG,
                "sample_mean": sample_mean,
                "sample_std": sample_std,
                "focus": {str(n): {
                    "wt": rows[n]["wt"],
                    "wt_rank": rows[n]["wt_rank"],
                    "zscore": rows[n]["zscore"],
                    "sCHK_rank": rows[n]["sCHK_rank"],
                    "sVH_rank": rows[n]["sVH_rank"],
                    "Delta_Rk_full": rows[n].get("Delta_Rk_full"),
                    "same_wt_peers": same_wt(n),
                    "s_r_inv": rows[n].get("s_r_inv"),
                    "s_r_inv_rank": rows[n].get("s_r_inv_rank"),
                } for n in focus},
                "low_tail": low_tail,
                "high_tail": [153, 98, 97, 16, 142],
                "p150_vs_p2": {
                    "same_wt": rows[150]["wt"] == rows[2]["wt"],
                    "p150_sCHK_rank": rows[150]["sCHK_rank"],
                    "p2_sCHK_rank": rows[2]["sCHK_rank"],
                    "note": "same Hamming wt=86; sCHK ranks are NOT equal",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"wrote {path}")
    print(f"wrote {csv_path}")
    print("focus:")
    for n in focus:
        print(
            f"  P{n}: wt={rows[n]['wt']} rk={rows[n]['wt_rank']} "
            f"sCHK={rows[n]['sCHK_rank']} s_r_inv_rk={rows[n].get('s_r_inv_rank')}"
        )
    print(
        f"P150 vs P2: same wt={rows[150]['wt']==rows[2]['wt']} "
        f"sCHK {rows[150]['sCHK_rank']} vs {rows[2]['sCHK_rank']}"
    )


if __name__ == "__main__":
    main()
