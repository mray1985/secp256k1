#!/usr/bin/env python3
"""Address payload x.y split ledger over puzzles 1..160.

A = address_payload integer (00||rmd160||checksum4)
addr_x = floor(A / 2^32) = rmd160
addr_y = A mod 2^32 = checksum4   (NOT curve Py)
A = 2^32 * addr_x + addr_y
A / 2^32 = addr_x + addr_y / 2^32
normalized = A / (2^32 * p)
"""

from __future__ import annotations

import json
from pathlib import Path

from scan_log_ratio_cross_puzzle import P

OUT = Path("logs/log_ratio_scan")
SRC = OUT / "linear_order_puzzles_1_160.json"
TWO32 = 1 << 32
P160_Y = 1563760281


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    A = {e["puzzle_n"]: int(e["value"]) for e in d["series"]["address_payload"]}
    h = {e["puzzle_n"]: int(e["value"]) for e in d["series"]["rmd160"]}
    c = {e["puzzle_n"]: int(e["value"]) for e in d["series"]["checksum4"]}

    rows = []
    for n in range(1, 161):
        x = A[n] // TWO32
        y = A[n] % TWO32
        assert x == h[n], (n, x, h[n])
        assert y == c[n], (n, y, c[n])
        assert A[n] == TWO32 * x + y
        rows.append(
            {
                "puzzle_n": n,
                "A": A[n],
                "addr_x_rmd160": x,
                "addr_y_checksum": y,
                "addr_y_hex": f"{y:#010x}",
                "A_div_2_32": f"{x} + {y}/{TWO32}",
                "A_over_2_32_p": A[n] / (TWO32 * P),
                "reconstruct_ok": True,
            }
        )

    r160 = rows[159]
    assert r160["puzzle_n"] == 160
    assert r160["addr_y_checksum"] == P160_Y
    assert r160["addr_y_checksum"] == 0x5D351699

    payload = {
        "identity": "A = 2^32 * addr_x + addr_y",
        "addr_x": "floor(A/2^32) = rmd160",
        "addr_y": "A mod 2^32 = checksum4 (NOT secp256k1 Py)",
        "decimal_form": "A/2^32 = addr_x + addr_y/2^32",
        "normalized": "A/(2^32 * p) = (2^32*addr_x + addr_y)/(2^32*p)",
        "p": P,
        "two32": TWO32,
        "p160_addr_y": P160_Y,
        "p160_addr_y_hex": "0x5d351699",
        "p160_verified": True,
        "verified_count": 160,
        "rows": rows,
    }
    (OUT / "ADDRESS_XY_SPLIT_LEDGER.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "ADDRESS x.y SPLIT LEDGER",
        "A = address_payload",
        "addr_x = floor(A/2^32) = rmd160",
        "addr_y = A mod 2^32 = checksum4  (NOT curve Py)",
        "A = 2^32*addr_x + addr_y",
        "A/2^32 = addr_x + addr_y/2^32",
        "normalized = A/(2^32*p)",
        "",
        f"P160 addr_y={r160['addr_y_checksum']} {r160['addr_y_hex']} verified=True",
        "verified 160/160",
        "",
        "n  addr_x(=rmd160)  addr_y(=checksum)  addr_y_hex",
    ]
    for r in rows:
        lines.append(
            f"{r['puzzle_n']:3d}  {r['addr_x_rmd160']}  {r['addr_y_checksum']}  {r['addr_y_hex']}"
        )
    # P160 decimal note
    lines += [
        "",
        "P160 decimal tail * 2^32:",
        f"  A/2^32 = {r160['addr_x_rmd160']} + {r160['addr_y_checksum']}/{TWO32}",
        f"  frac * 2^32 = {r160['addr_y_checksum']} = {r160['addr_y_hex']}",
    ]
    (OUT / "ADDRESS_XY_SPLIT_LEDGER.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("P160 y", r160["addr_y_checksum"], r160["addr_y_hex"])
    print("verified 160/160")
    print("wrote ADDRESS_XY_SPLIT_LEDGER.json/.txt")


if __name__ == "__main__":
    main()
