#!/usr/bin/env python3
"""Export ACTUAL values (not ranks) for every discussed sort order.

For each sort key K: one CSV + one TXT with rows sorted by K ascending,
columns = all field actual values (blank if missing).
Also writes a combined mega TXT index.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("logs/log_ratio_scan")
SRC = OUT / "linear_order_puzzles_1_160.json"
DEST = OUT / "actual_values_every_order"

# Column order (actual values)
FIELDS = [
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
    "rmd160",
    "address_payload",
    "address_payload_div_2_32",  # == rmd160
    "checksum4",
    "address_base58_lex",
    "rmd160_sq_mod_p",
    "rmd160_cubed_plus_7_mod_p",
    "address_payload_sq_mod_p",
    "address_payload_cubed_plus_7_mod_p",
    "r",
    "s",
    "z",
    "Ry",
    "sha256_pubkey",
    "sha256_vh",
    "sha256_chk",
]

# Every order discussed (row sort keys)
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
    "rmd160_sq_mod_p",
    "rmd160_cubed_plus_7_mod_p",
    "address_payload_sq_mod_p",
    "address_payload_cubed_plus_7_mod_p",
]


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(v)
    return str(v)


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    series = data["series"]

    by_n: dict[int, dict] = {i: {"puzzle_n": i} for i in range(1, 161)}
    for name, ents in series.items():
        for e in ents:
            by_n[e["puzzle_n"]][name] = e["value"]

    # derived identity column
    for n, row in by_n.items():
        pay = row.get("address_payload")
        if pay is not None:
            row["address_payload_div_2_32"] = int(pay) // (1 << 32)

    DEST.mkdir(parents=True, exist_ok=True)
    index = [
        "ACTUAL VALUES — every discussed sort order",
        "Rows sorted by the named key (ascending). Cells = raw values, not ranks.",
        "Blank = field not available for that puzzle.",
        "address_payload_div_2_32 == rmd160 (verified identity).",
        "",
    ]

    for key in SORT_KEYS:
        rows = list(by_n.values())
        rows.sort(
            key=lambda r: (
                r.get(key) is None,
                r.get(key) if r.get(key) is not None else 0,
                r["puzzle_n"],
            )
        )

        headers = ["puzzle_n", f"SORT={key}"] + [f for f in FIELDS if f != key]
        # put sort key value explicitly as second column
        csv_path = DEST / f"VALUES_BY_{key}.csv"
        txt_path = DEST / f"VALUES_BY_{key}.txt"

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                cells = [str(r["puzzle_n"]), fmt(r.get(key))]
                for field in FIELDS:
                    if field == key:
                        continue
                    cells.append(fmt(r.get(field)))
                f.write(",".join(cells) + "\n")

        # TXT: one puzzle block (readable) in sort order
        lines = [
            f"ACTUAL VALUES sorted by {key} ascending",
            f"puzzles with {key}: {sum(1 for r in rows if r.get(key) is not None)} / 160",
            "",
        ]
        for rank, r in enumerate(rows, start=1):
            if r.get(key) is None and rank > 1 and rows[rank - 2].get(key) is not None:
                lines.append("--- missing sort key below ---")
                lines.append("")
            lines.append(f"# linear_pos={rank}  puzzle_n={r['puzzle_n']}  {key}={fmt(r.get(key))}")
            for field in FIELDS:
                v = r.get(field)
                if v is None:
                    continue
                lines.append(f"  {field}={fmt(v)}")
            lines.append("")

        txt_path.write_text("\n".join(lines), encoding="utf-8")
        index.append(f"  VALUES_BY_{key}.csv / VALUES_BY_{key}.txt")
        print(f"wrote VALUES_BY_{key}")

    # Also one wide CSV sorted by n with ALL values (master table)
    master = DEST / "VALUES_MASTER_BY_n.csv"
    with master.open("w", encoding="utf-8", newline="") as f:
        headers = ["puzzle_n"] + FIELDS
        f.write(",".join(headers) + "\n")
        for n in range(1, 161):
            r = by_n[n]
            f.write(",".join([str(n)] + [fmt(r.get(field)) for field in FIELDS]) + "\n")
    index.append("")
    index.append(f"Master (by puzzle n): {master.name}")

    (DEST / "INDEX.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    (OUT / "ACTUAL_VALUES_EVERY_ORDER.md").write_text(
        "# Actual values — every sort order\n\n"
        f"Folder: [`actual_values_every_order/`](actual_values_every_order/)\n\n"
        f"- Master table: [`actual_values_every_order/VALUES_MASTER_BY_n.csv`](actual_values_every_order/VALUES_MASTER_BY_n.csv)\n"
        f"- Per sort key: `VALUES_BY_<key>.csv` (wide) and `.txt` (per-puzzle blocks)\n",
        encoding="utf-8",
    )
    print(f"wrote {master}")
    print(f"sort orders: {len(SORT_KEYS)}")


if __name__ == "__main__":
    main()
