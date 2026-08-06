#!/usr/bin/env python3
"""Full rank-first ledger: every field as ranks, every sort order, Spearman matrix,
modular distance profile, s^{-1}*z mod N, h160 Hamming weight.

Spine documents mirror LINEAR_ORDER_ALL_IN_ONE_EVERY_SORT_KEY but ranks-only,
plus correlation matrix (1s on diagonal) and unsolved-gap distance table.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import (
    P,
    N,
    load_rows,
    recover_xy_from_pubkey,
    spearman,
)

getcontext().prec = 80
OUT = Path("logs/log_ratio_scan")
DEST = OUT / "rank_first_full_matrix"


def dense_ranks(values: dict[int, int | float | str]) -> dict[int, int]:
    items = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    return {pn: i for i, (pn, _) in enumerate(items, start=1)}


def hamming_weight(x: int) -> int:
    return int(x).bit_count()


def spearman_exact(xs: list[float], ys: list[float]) -> float:
    """Spearman via float Pearson-on-ranks (same as codebase); also return clamped."""
    rho = spearman(xs, ys)
    if rho is None:
        return float("nan")
    # document float artifact near +/-1
    if abs(abs(rho) - 1.0) < 1e-12:
        return math.copysign(1.0, rho)
    return float(rho)


def main() -> None:
    cat = load_catalog()
    rsz = {r.n: r for r in load_rows()}
    DEST.mkdir(parents=True, exist_ok=True)

    # ---------- raw fields per puzzle ----------
    raw: dict[int, dict] = {}
    for n in range(1, 161):
        e = cat[n]
        h160 = int(e.hash160, 16)
        vh = b"\x00" + h160.to_bytes(20, "big")
        import hashlib

        sha_vh = hashlib.sha256(vh).digest()
        sha_chk = hashlib.sha256(sha_vh).digest()
        c4 = int.from_bytes(sha_chk[:4], "big")
        payload = int.from_bytes(vh + sha_chk[:4], "big")

        row: dict = {
            "n": n,
            "rmd160": h160,
            "h160": h160,
            "address_payload": payload,
            "checksum4": c4,
            "addr_x": payload // (1 << 32),
            "addr_y": payload % (1 << 32),
            "sha256_vh": int.from_bytes(sha_vh, "big"),
            "sha256_chk": int.from_bytes(sha_chk, "big"),
            "sVH": int.from_bytes(sha_vh, "big"),
            "sCHK": int.from_bytes(sha_chk, "big"),
            "h160_hamming": hamming_weight(h160),
            "address": e.address,
            "solved": e.solved,
            "d": e.private_key if e.private_key > 0 else None,
        }

        px = py = None
        if e.public_key:
            px, py = recover_xy_from_pubkey(e.public_key)
        rr = rsz.get(n)
        if px is None and rr and rr.Px:
            px, py = rr.Px, rr.Py

        if px is not None and py is not None:
            Yfull = py * py
            Xfull = px * px * px + 7
            C = (Xfull - Yfull) // P
            Ymod = Yfull % P
            Xmod = Xfull % P
            row.update(
                {
                    "Px": px,
                    "Py": py,
                    "Pmy": P - py,
                    "neg_y": (-py) % P,
                    "y2_full": Yfull,
                    "x3plus7_full": Xfull,
                    "p_carry": C,
                    "Y2p": Ymod,  # y^2 mod p
                    "X3p": Xmod,  # x^3+7 mod p  (== Ymod on curve)
                    "sha256_pubkey": int.from_bytes(
                        bytes.fromhex(e.public_key) if e.public_key else b"", "big"
                    )
                    if e.public_key
                    else int.from_bytes(
                        (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big"),
                        "big",
                    ),
                }
            )
            # modular distance mod N of the FULL values reduced mod N (not the trivial mod-p identity)
            row["X3p_mod_N"] = Xmod % N  # same as Ymod % N
            row["Y2p_mod_N"] = Ymod % N
            row["Delta_mod_N"] = (Xmod - Ymod) % N  # always 0 for on-curve mod-p
            row["Delta_full_over_p"] = C  # the real carry
            # unreduced rank delta computed later

        if rr:
            row["r"] = rr.r
            row["s"] = rr.s
            row["z"] = rr.z
            row["Ry"] = rr.Ry
            if rr.s and rr.z is not None:
                s_inv = pow(rr.s, -1, N)
                row["s_inv_z_mod_N"] = (s_inv * (rr.z % N)) % N
                # also s^{-1}(z + r*d) = k when d known — skip for non-d matrix
                row["s_inv_mod_N"] = s_inv

        if e.public_key:
            row["sha256_pubkey"] = int.from_bytes(
                hashlib.sha256(bytes.fromhex(e.public_key)).digest(), "big"
            )

        raw[n] = row

    # ---------- rank every numeric field ----------
    rank_fields = [
        "n",
        "d",
        "Px",
        "Py",
        "Pmy",
        "neg_y",
        "Y2p",
        "X3p",
        "y2_full",
        "x3plus7_full",
        "p_carry",
        "r",
        "s",
        "z",
        "Ry",
        "h160",
        "rmd160",
        "address_payload",
        "checksum4",
        "addr_x",
        "addr_y",
        "sVH",
        "sCHK",
        "sha256_vh",
        "sha256_chk",
        "sha256_pubkey",
        "h160_hamming",
        "s_inv_z_mod_N",
        "s_inv_mod_N",
        "Delta_mod_N",
        "Delta_full_over_p",
    ]
    # dedupe aliases: rmd160==h160==addr_x values; sVH==sha256_vh; sCHK==sha256_chk
    # still rank aliases separately for chart labels (identical ranks)

    ranks: dict[str, dict[int, int]] = {}
    for f in rank_fields:
        vals = {n: raw[n][f] for n in range(1, 161) if raw[n].get(f) is not None}
        if not vals:
            continue
        ranks[f] = dense_ranks(vals)

    # Delta_Rk = Rank(X3p) - Rank(Y2p)  — trivial 0 when using mod-p
    # Also Delta_Rk_full = Rank(x3plus7_full) - Rank(y2_full)
    for n in range(1, 161):
        if n in ranks.get("X3p", {}) and n in ranks.get("Y2p", {}):
            raw[n]["Delta_Rk_modp"] = ranks["X3p"][n] - ranks["Y2p"][n]
        if n in ranks.get("x3plus7_full", {}) and n in ranks.get("y2_full", {}):
            raw[n]["Delta_Rk_full"] = ranks["x3plus7_full"][n] - ranks["y2_full"][n]

    ranks["Delta_Rk_modp"] = dense_ranks(
        {n: raw[n]["Delta_Rk_modp"] for n in range(1, 161) if "Delta_Rk_modp" in raw[n]}
    ) if any("Delta_Rk_modp" in raw[n] for n in range(1, 161)) else {}
    # Actually Delta_Rk_modp is always 0 — ranking that is degenerate. Keep raw delta columns.

    # ---------- Spearman matrix (non-d cohort: solved with all of Px,sVH,sCHK,h160,z,r) ----------
    corr_fields = ["Px", "sVH", "sCHK", "h160", "z", "r"]
    cohort = [
        n
        for n in range(1, 161)
        if raw[n].get("d")
        and all(raw[n].get(f) is not None for f in corr_fields)
    ]
    # use ranks within this cohort for Spearman (non-d: correlate the public limbs, not d)
    cohort_ranks: dict[str, dict[int, int]] = {}
    for f in corr_fields:
        cohort_ranks[f] = dense_ranks({n: raw[n][f] for n in cohort})

    matrix: dict[str, dict[str, float]] = {a: {} for a in corr_fields}
    for a in corr_fields:
        for b in corr_fields:
            xs = [float(cohort_ranks[a][n]) for n in cohort]
            ys = [float(cohort_ranks[b][n]) for n in cohort]
            # Spearman of values == Pearson of these dense ranks if no ties; use value spearman
            xs_v = [float(raw[n][a]) for n in cohort]
            ys_v = [float(raw[n][b]) for n in cohort]
            matrix[a][b] = spearman_exact(xs_v, ys_v)

    # broader matrix: all public fields on max overlapping solved set
    broad = [
        "Px",
        "Py",
        "neg_y",
        "Y2p",
        "X3p",
        "y2_full",
        "x3plus7_full",
        "p_carry",
        "r",
        "s",
        "z",
        "Ry",
        "h160",
        "sVH",
        "sCHK",
        "checksum4",
        "h160_hamming",
        "s_inv_z_mod_N",
        "sha256_pubkey",
    ]
    broad_cohort = [
        n
        for n in range(1, 161)
        if raw[n].get("d") and all(raw[n].get(f) is not None for f in ["Px", "r", "s", "z", "Ry"])
    ]
    # for fields missing on some, pairwise cohort
    broad_matrix: dict[str, dict[str, float | None]] = {a: {} for a in broad}
    for a in broad:
        for b in broad:
            ns = [
                n
                for n in range(1, 161)
                if raw[n].get(a) is not None and raw[n].get(b) is not None and raw[n].get("d")
            ]
            if len(ns) < 5:
                broad_matrix[a][b] = None
                continue
            broad_matrix[a][b] = spearman_exact(
                [float(raw[n][a]) for n in ns], [float(raw[n][b]) for n in ns]
            )

    # ---------- distance profile table ----------
    profile_ns = list(range(1, 7)) + [88, 135, 140, 145, 150, 155, 160]
    # 88 may not exist as unsolved with pubkey — check
    profile_lines = [
        "MODULAR / RANK DISTANCE PROFILE",
        "X3p,Y2p = (x^3+7 mod p), (y^2 mod p) — EQUAL on curve => Delta_Rk_modp always 0 (trivial)",
        "Delta_Rk_full = Rank(x3plus7_full)-Rank(y2_full) — NON-trivial (unreduced)",
        "",
        f"{'n':>3} {'X3p':>5} {'Y2p':>5} {'dMod':>5} {'X3f':>5} {'Y2f':>5} {'dFull':>6} "
        f"{'sVH':>5} {'sCHK':>5} {'hWt':>4} {'sInvZ':>5}  status",
    ]
    for n in profile_ns:
        if n not in raw:
            continue
        r = raw[n]
        status = "Solved Anchor" if r.get("d") else "UNSOLVED GAP"
        if r.get("Px") is None:
            status += " (no pubkey)"
        def rk(f):
            return ranks[f].get(n, "") if f in ranks else ""

        profile_lines.append(
            f"{n:3d} {rk('X3p')!s:>5} {rk('Y2p')!s:>5} {r.get('Delta_Rk_modp','')!s:>5} "
            f"{rk('x3plus7_full')!s:>5} {rk('y2_full')!s:>5} {r.get('Delta_Rk_full','')!s:>6} "
            f"{rk('sVH')!s:>5} {rk('sCHK')!s:>5} {rk('h160_hamming')!s:>4} "
            f"{rk('s_inv_z_mod_N')!s:>5}  {status}"
        )

    # ---------- every-sort-key rank charts ----------
    sort_keys = [f for f in rank_fields if f in ranks]
    # prefer unique conceptual keys for "every order"
    sort_keys_unique = []
    seen_val_id = set()
    # still do ALL listed sort keys as user asked
    sort_keys_unique = list(dict.fromkeys(sort_keys))

    charts_dir = DEST / "charts_by_each"
    charts_dir.mkdir(parents=True, exist_ok=True)

    # column order for charts
    col_order = [
        "h160",
        "Px",
        "Py",
        "neg_y",
        "Y2p",
        "X3p",
        "y2_full",
        "x3plus7_full",
        "p_carry",
        "r",
        "s",
        "z",
        "Ry",
        "sVH",
        "sCHK",
        "checksum4",
        "addr_y",
        "h160_hamming",
        "s_inv_z_mod_N",
        "sha256_pubkey",
        "d",
        "n",
    ]

    mega = [
        "RANK-FIRST FULL MATRIX — every sort key",
        f"Solved Spearman cohort size (Px,sVH,sCHK,h160,z,r): {len(cohort)}",
        "Cells = dense linear ranks (1=smallest). Blank=missing.",
        "Y2p/X3p Delta_Rk always 0 (mod-p identity). Use y2_full/x3plus7_full/p_carry for real account.",
        "",
    ]

    for key in sort_keys_unique:
        ordered = sorted(
            range(1, 161),
            key=lambda n: (
                n not in ranks[key],
                ranks[key].get(n, 10**9),
                n,
            ),
        )
        headers = ["puzzle_n", f"r_{key}"] + [f"r_{c}" for c in col_order if c != key and c in ranks]
        # CSV
        csv_path = charts_dir / f"RANKS_BY_{key}.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(",".join(headers) + "\n")
            for n in ordered:
                cells = [str(n), str(ranks[key].get(n, ""))]
                for c in col_order:
                    if c == key or c not in ranks:
                        continue
                    cells.append(str(ranks[c].get(n, "")))
                fh.write(",".join(cells) + "\n")

        # compact text
        short_cols = [("n", 3), (key[:4], 4)] + [
            (c[:4], 4) for c in col_order if c != key and c in ranks
        ][:14]
        block = [f"=== ROW ORDER = rank({key}) ===", " ".join(h.rjust(w) for h, w in short_cols)]
        block.append("-" * (sum(w for _, w in short_cols) + len(short_cols) - 1))
        for n in ordered:
            vals = [n, ranks[key].get(n, "")]
            for c in col_order:
                if c == key or c not in ranks:
                    continue
                vals.append(ranks[c].get(n, ""))
                if len(vals) >= len(short_cols):
                    break
            block.append(
                " ".join(str(v)[:w].rjust(w) for v, (_, w) in zip(vals, short_cols))
            )
        block.append("")
        (charts_dir / f"RANKS_BY_{key}.txt").write_text("\n".join(block) + "\n", encoding="utf-8")
        mega.extend(block)

    (DEST / "LINEAR_ORDER_ALL_RANKS_EVERY_SORT_KEY.txt").write_text(
        "\n".join(mega) + "\n", encoding="utf-8"
    )

    # ---------- Spearman docs with diagonal 1s ----------
    def fmt_mat(fields, mat, title, cohort_n):
        lines = [
            title,
            f"cohort_n={cohort_n}  (Spearman on raw values; diagonal = 1 by definition)",
            "",
        ]
        hdr = f"{'':>10}" + "".join(f"{f:>10}" for f in fields)
        lines.append(hdr)
        lines.append("-" * len(hdr))
        for a in fields:
            row = f"{a:>10}"
            for b in fields:
                v = mat[a][b]
                if v is None:
                    row += f"{'NA':>10}"
                elif a == b:
                    row += f"{'1.0000':>10}"  # force display diagonal identity
                else:
                    row += f"{v:+10.4f}"
            lines.append(row)
        lines.append("")
        lines.append("Diagonal alignment: every self-correlation is exactly 1 (rank identity).")
        lines.append("Off-diagonal: non-d public structure only (no d column).")
        return lines

    corr_txt = DEST / "SPEARMAN_NON_D_MATRIX.txt"
    corr_txt.write_text(
        "\n".join(
            fmt_mat(
                corr_fields,
                matrix,
                "HIGH-PRECISION SPEARMAN (non-d) — Px,sVH,sCHK,h160,z,r",
                len(cohort),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    broad_txt = DEST / "SPEARMAN_BROAD_PUBLIC_MATRIX.txt"
    broad_txt.write_text(
        "\n".join(
            fmt_mat(
                broad,
                broad_matrix,
                "SPEARMAN BROAD PUBLIC MATRIX (solved pairwise)",
                len(broad_cohort),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    # diagonal-only highlight doc
    diag = [
        "DIAGONAL ONES — Spearman self-alignment",
        "",
        "In any correlation matrix, the main diagonal is the identity of each column with itself:",
        "",
    ]
    for f in corr_fields:
        diag.append(f"  {f:>8} vs {f:<8} = {matrix[f][f]:.4f}  -> displayed 1.0000")
    diag += [
        "",
        "Visually the 1's form a top-left to bottom-right diagonal.",
        "That is definitional (perfect rank self-match), not a curve discovery.",
        "",
        "Strongest |off-diagonal| in core matrix:",
    ]
    offs = []
    for i, a in enumerate(corr_fields):
        for b in corr_fields[i + 1 :]:
            offs.append((abs(matrix[a][b]), matrix[a][b], a, b))
    offs.sort(reverse=True)
    for ab, rho, a, b in offs[:8]:
        diag.append(f"  {a} vs {b}: {rho:+.4f}")

    (DEST / "SPEARMAN_DIAGONAL_ONES.txt").write_text("\n".join(diag) + "\n", encoding="utf-8")
    (DEST / "DISTANCE_PROFILE.txt").write_text("\n".join(profile_lines) + "\n", encoding="utf-8")

    # Hamming for anomalies + all
    ham_lines = ["h160 Hamming weight ranks (all 160)", "n  h160_hamming  rank  status"]
    for n in range(1, 161):
        ham_lines.append(
            f"{n:3d}  {raw[n]['h160_hamming']:3d}  {ranks['h160_hamming'][n]:3d}  "
            f"{'solved' if raw[n].get('d') else 'unsolved'}"
        )
    for focus in [135, 150, 155, 160]:
        ham_lines.append(
            f"FOCUS P{focus}: wt={raw[focus]['h160_hamming']} rank={ranks['h160_hamming'][focus]}"
        )
    (DEST / "H160_HAMMING_WEIGHTS.txt").write_text("\n".join(ham_lines) + "\n", encoding="utf-8")

    # s_inv_z table
    inv_lines = ["s^{-1} * z mod N  ranks", "n  s_inv_z_mod_N  rank  status"]
    for n in range(1, 161):
        if "s_inv_z_mod_N" not in raw[n]:
            continue
        inv_lines.append(
            f"{n:3d}  {raw[n]['s_inv_z_mod_N']}  {ranks['s_inv_z_mod_N'][n]}  "
            f"{'solved' if raw[n].get('d') else 'unsolved'}"
        )
    (DEST / "S_INV_Z_MOD_N.txt").write_text("\n".join(inv_lines) + "\n", encoding="utf-8")

    # master ranks CSV by h160 order (spine)
    master_cols = [c for c in col_order if c in ranks]
    with (DEST / "RANKS_MASTER_BY_h160.csv").open("w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(["puzzle_n", "status"] + [f"r_{c}" for c in master_cols]) + "\n")
        for n in sorted(range(1, 161), key=lambda i: ranks["h160"][i]):
            st = "solved" if raw[n].get("d") else "unsolved"
            fh.write(
                ",".join(
                    [str(n), st] + [str(ranks[c].get(n, "")) for c in master_cols]
                )
                + "\n"
            )

    # JSON bundle
    (DEST / "bundle.json").write_text(
        json.dumps(
            {
                "cohort_spearman_core": len(cohort),
                "spearman_core": matrix,
                "spearman_broad": broad_matrix,
                "note_Y2p_X3p": "mod-p values identical on curve => Delta_Rk always 0",
                "note_diagonal": "Spearman diagonal is identically 1 (self-rank)",
                "sort_keys": sort_keys_unique,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (DEST / "README.md").write_text(
        "\n".join(
            [
                "# Rank-first full matrix",
                "",
                "- `LINEAR_ORDER_ALL_RANKS_EVERY_SORT_KEY.txt` — every field as row order",
                "- `charts_by_each/RANKS_BY_<key>.*`",
                "- `SPEARMAN_NON_D_MATRIX.txt` — core matrix with **1s on diagonal**",
                "- `SPEARMAN_DIAGONAL_ONES.txt` — diagonal callout",
                "- `DISTANCE_PROFILE.txt` — solved anchors + unsolved gaps",
                "- `S_INV_Z_MOD_N.txt`, `H160_HAMMING_WEIGHTS.txt`",
                "- `RANKS_MASTER_BY_h160.csv` — spine = rmd160/h160 ranks",
                "",
                "Caution: `Y2p`/`X3p` rank delta is trivially 0 (curve mod p).",
                "Use `y2_full` / `x3plus7_full` / `p_carry` for the unreduced account.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("cohort", len(cohort))
    print("core Spearman:")
    for a in corr_fields:
        print(" ", a, {b: round(matrix[a][b], 4) for b in corr_fields})
    print("wrote", DEST)


if __name__ == "__main__":
    main()
