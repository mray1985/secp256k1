#!/usr/bin/env python3
"""One full linear-rank chart per series as the row-order key.

For each sort key K in the cohort:
  rows = puzzles sorted by K's linear_rank ascending (missing K at bottom)
  columns = linear_rank of every other series (+ d_bits / d_value in CSV)
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("logs/log_ratio_scan")
SRC = OUT / "linear_order_puzzles_1_160.json"

# Every series that can be the linear (row) column
SORT_KEYS = [
    "n",
    "d",
    "log2d",
    "Px",
    "Py",
    "Pmy",
    "neg_y",
    "y2_mod_p",
    "x3_plus_7_mod_p",
    "y2_full",
    "x3plus7_full",
    "p_carry",
    "rmd160_cubed_plus_7_mod_p",
    "address_payload_sq_mod_p",
    "rmd160_sq_mod_p",
    "address_payload_cubed_plus_7_mod_p",
    "r",
    "s",
    "z",
    "Ry",
    "rmd160",
    "address_payload",
    "address_base58_lex",
    "sha256_pubkey",
    "sha256_vh",
    "sha256_chk",
    "checksum4",
]

# Short headers for fixed-width text
SHORT = {
    "puzzle_n": ("n", 3),
    "n": ("nRk", 3),
    "d": ("d", 3),
    "log2d": ("l2d", 3),
    "Px": ("Px", 3),
    "Py": ("Py", 3),
    "Pmy": ("Pmy", 3),
    "neg_y": ("-y", 3),
    "y2_mod_p": ("y2p", 4),
    "x3_plus_7_mod_p": ("x3p", 4),
    "y2_full": ("Y2f", 4),
    "x3plus7_full": ("X3f", 4),
    "p_carry": ("C", 3),
    "rmd160_cubed_plus_7_mod_p": ("h3p", 4),
    "address_payload_sq_mod_p": ("a2p", 4),
    "rmd160_sq_mod_p": ("h2p", 4),
    "address_payload_cubed_plus_7_mod_p": ("a3p", 4),
    "r": ("r", 3),
    "s": ("s", 3),
    "z": ("z", 3),
    "Ry": ("Ry", 3),
    "rmd160": ("h160", 4),
    "address_payload": ("pay", 4),
    "address_base58_lex": ("lex", 4),
    "sha256_pubkey": ("sPub", 4),
    "sha256_vh": ("sVH", 4),
    "sha256_chk": ("sCHK", 4),
    "checksum4": ("c4", 4),
    "d_bits": ("dbit", 4),
}


def cell(v, w: int) -> str:
    s = "" if v is None else str(v)
    return (s[:w]).rjust(w)


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    series = data["series"]

    by_n: dict[int, dict] = {n: {"puzzle_n": n, "d_val": None} for n in range(1, 161)}
    for name in SORT_KEYS:
        for e in series[name]:
            pn = e["puzzle_n"]
            by_n[pn][name] = e["linear_rank"]
            if name == "d":
                by_n[pn]["d_val"] = int(e["value"])

    dest = OUT / "linear_rank_charts_by_each"
    dest.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "LINEAR RANK CHARTS — every series as row order",
        f"Source: {SRC.name}",
        "Each file: rows sorted by that field's linear_rank (1=smallest); other fields as columns.",
        "Missing sort-key values sink to the bottom (by puzzle_n).",
        "",
        "Files:",
    ]

    mega = [
        "LINEAR ORDER — EVERY SORT KEY",
        "One chart per series as the linear (row) column; everything else to the right.",
        "",
    ]

    for key in SORT_KEYS:
        others = [k for k in SORT_KEYS if k != key]
        col_order = [key] + others  # sort key first among ranks, then rest

        rows = list(by_n.values())
        rows.sort(
            key=lambda r: (
                r.get(key) is None,
                r.get(key) if r.get(key) is not None else 10**9,
                r["puzzle_n"],
            )
        )

        # CSV
        headers = ["puzzle_n"] + col_order + ["d_value"]
        csv_path = dest / f"BY_{key}.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                cells = [str(r["puzzle_n"])]
                for c in col_order:
                    v = r.get(c)
                    cells.append("" if v is None else str(v))
                cells.append("" if r["d_val"] is None else str(r["d_val"]))
                f.write(",".join(cells) + "\n")

        # fixed-width block
        short_cols = [("puzzle_n",) + SHORT["puzzle_n"]]
        short_cols.append((key,) + SHORT[key])
        for c in others:
            short_cols.append((c,) + SHORT[c])
        short_cols.append(("d_bits",) + SHORT["d_bits"])

        block = []
        block.append("=" * 88)
        block.append(f"ROW ORDER = {key}  (linear_rank ascending)")
        block.append("=" * 88)
        block.append(" ".join(cell(h, w) for _, h, w in short_cols))
        block.append("-" * (sum(w for *_, w in short_cols) + len(short_cols) - 1))
        for r in rows:
            lookup = dict(r)
            lookup["d_bits"] = (
                r["d_val"].bit_length() if r["d_val"] is not None else None
            )
            vals = [
                cell("" if lookup.get(src) is None else lookup.get(src), w)
                for src, _, w in short_cols
            ]
            block.append(" ".join(vals))
        block.append("")

        txt_path = dest / f"BY_{key}.txt"
        txt_path.write_text("\n".join(block) + "\n", encoding="utf-8")

        mega.extend(block)
        index_lines.append(f"  BY_{key}.txt / BY_{key}.csv")

        print(f"wrote BY_{key} ({sum(1 for r in rows if r.get(key) is not None)} ranked)")

    mega_path = OUT / "LINEAR_ORDER_ALL_IN_ONE_EVERY_SORT_KEY.txt"
    mega_path.write_text("\n".join(mega) + "\n", encoding="utf-8")

    index_path = dest / "INDEX.txt"
    index_lines.append("")
    index_lines.append(f"Combined document: ../{mega_path.name}")
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    (OUT / "LINEAR_ORDER_EVERY_SORT_KEY.md").write_text(
        "# Linear rank charts — every sort key\n\n"
        f"Combined: [`LINEAR_ORDER_ALL_IN_ONE_EVERY_SORT_KEY.txt`](LINEAR_ORDER_ALL_IN_ONE_EVERY_SORT_KEY.txt)\n\n"
        f"Per-key folder: [`linear_rank_charts_by_each/`](linear_rank_charts_by_each/)\n\n"
        "Each series gets one turn as the **row order** (linear column); all other ranks sit to the right.\n",
        encoding="utf-8",
    )

    print(f"\nwrote {mega_path}")
    print(f"wrote {index_path}")
    print(f"charts: {len(SORT_KEYS)}")


if __name__ == "__main__":
    main()
