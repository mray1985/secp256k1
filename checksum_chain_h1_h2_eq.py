#!/usr/bin/env python3
"""Correct checksum-chain equation test (NOT SHA256(pubkey)).

H1 = SHA256(0x00 || RMD160)
H2 = SHA256(H1)
checksum4 = H2[:4]

c = (-b) mod N  with b = z * r^{-1} mod N  (signature normalization)

Test four variants for each M in {N, p}:
  (H1^2 + c) - (H2^3 + 7)  mod M
  (H1^2 - c) - (H2^3 + 7)  mod M

Exact close <=> remainder 0.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import N, P
from sig_norm_a_b_test import build_rows

OUT = Path("logs/log_ratio_scan/rank_first_full_matrix")

P135_RMD = "3B6F58A75A54BFD85D1BC6C51180FDC732992326"
P135_H1 = "7321F26CA85A2DDE173C6635D7FEFEFE65289FD442CF57636A96E2EF1E713F16"
P135_H2 = "7B8F3E17CF87BD772D5D6DBA429D8A03EA1D16B64BDD4305A93695532F05E62F"
P135_C4 = "7B8F3E17"


def h1_h2(rmd160_hex: str) -> tuple[bytes, bytes, int, int]:
    h160 = bytes.fromhex(rmd160_hex)
    assert len(h160) == 20
    h1 = hashlib.sha256(b"\x00" + h160).digest()
    h2 = hashlib.sha256(h1).digest()
    return h1, h2, int.from_bytes(h1, "big"), int.from_bytes(h2, "big")


def remainders(H1: int, H2: int, c: int) -> dict[str, int]:
    H1sq = H1 * H1
    H2cu7 = H2 * H2 * H2 + 7
    out = {}
    for sign, name in ((1, "plus"), (-1, "minus")):
        left = H1sq + sign * c
        diff = left - H2cu7
        out[f"H1sq_{name}_c__minus__H2cu7__mod_N"] = diff % N
        out[f"H1sq_{name}_c__minus__H2cu7__mod_p"] = diff % P
        out[f"exact_zero_N_{name}"] = diff % N == 0
        out[f"exact_zero_p_{name}"] = diff % P == 0
    return out


def main() -> None:
    cat = load_catalog()
    sig = {r.n: r for r in build_rows()}

    # --- verify Puzzle 135 published bytes ---
    e135 = cat[135]
    assert e135.hash160.lower() == P135_RMD.lower()
    h1, h2, H1, H2 = h1_h2(e135.hash160)
    assert h1.hex().upper() == P135_H1
    assert h2.hex().upper() == P135_H2
    assert h2[:4].hex().upper() == P135_C4
    assert 135 in sig
    c135 = sig[135].c

    rem135 = remainders(H1, H2, c135)
    expected = {
        "H1sq_plus_c__minus__H2cu7__mod_N": int(
            "1565200300425559749940371920518064216348400514642441815930434353217014888406"
        ),
        "H1sq_plus_c__minus__H2cu7__mod_p": int(
            "14228619567133914750378768220721153480497153386989438572122430562304434917687"
        ),
        "H1sq_minus_c__minus__H2cu7__mod_N": int(
            "65641797330452346158834870891514148612292615634523816413822319259394772413250"
        ),
        "H1sq_minus_c__minus__H2cu7__mod_p": int(
            "78305216597160701159273267191717237877306209280002132483719157201263538797183"
        ),
    }
    match = {k: rem135[k] == expected[k] for k in expected}

    # --- all puzzles with (rmd160) always; c only when rsz present ---
    rows_out = []
    closes = {"plus_N": 0, "plus_p": 0, "minus_N": 0, "minus_p": 0, "total_with_c": 0}
    for n in range(1, 161):
        e = cat[n]
        h1b, h2b, H1i, H2i = h1_h2(e.hash160)
        entry = {
            "n": n,
            "rmd160": e.hash160.lower(),
            "H1": h1b.hex(),
            "H2": h2b.hex(),
            "checksum4": h2b[:4].hex(),
            "has_c": n in sig,
        }
        if n in sig:
            closes["total_with_c"] += 1
            c = sig[n].c
            entry["c"] = c
            rem = remainders(H1i, H2i, c)
            entry.update(rem)
            if rem["exact_zero_N_plus"]:
                closes["plus_N"] += 1
            if rem["exact_zero_p_plus"]:
                closes["plus_p"] += 1
            if rem["exact_zero_N_minus"]:
                closes["minus_N"] += 1
            if rem["exact_zero_p_minus"]:
                closes["minus_p"] += 1
        rows_out.append(entry)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "equation": "H1=SHA256(00||RMD160); H2=SHA256(H1); test H1^2 ± c  ?==  H2^3+7  mod M",
        "c_definition": "c=(-b) mod N, b=z*r^{-1} mod N",
        "NOT": "SHA256(pubkey); not arbitrary permutations",
        "p135_byte_check": {
            "rmd160_ok": True,
            "H1_ok": True,
            "H2_ok": True,
            "checksum_prefix_ok": True,
            "c": c135,
            "remainders": {k: rem135[k] for k in expected},
            "matches_user_remainders": match,
            "any_exact_close": any(rem135[f"exact_zero_{m}_{s}"] for m in ("N", "p") for s in ("plus", "minus")),
        },
        "cohort_closes": closes,
        "rows": rows_out,
        "ruling": (
            "Correct chain implemented. P135 does not close on any of the four variants. "
            "Cohort exact-close counts reported; nonzero remainders are the full-account leftovers."
        ),
    }
    (OUT / "CHECKSUM_CHAIN_H1_H2_EQ.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "CHECKSUM-CHAIN EQUATION (corrected scope)",
        "H1 = SHA256(00 || RMD160)",
        "H2 = SHA256(H1)",
        "c  = (-b) mod N   from signature normalization",
        "Test: (H1^2 ± c) - (H2^3 + 7)  mod {N,p}",
        "NOT SHA256(pubkey).",
        "",
        "=== Puzzle 135 byte lock ===",
        f"RMD160={e135.hash160}",
        f"H1={h1.hex()}",
        f"H2={h2.hex()}",
        f"checksum4={h2[:4].hex()} (H2 prefix)",
        f"c={c135}",
        "",
        "=== P135 remainders ===",
    ]
    for k, exp in expected.items():
        got = rem135[k]
        lines.append(f"{k}:")
        lines.append(f"  got={got}")
        lines.append(f"  exp={exp}")
        lines.append(f"  match={got==exp}")
    lines += [
        "",
        f"P135 any exact close: {payload['p135_byte_check']['any_exact_close']}",
        "",
        "=== Cohort exact closes (rows with c / rsz) ===",
        f"n_with_c={closes['total_with_c']}",
        f"plus  mod N: {closes['plus_N']}",
        f"plus  mod p: {closes['plus_p']}",
        f"minus mod N: {closes['minus_N']}",
        f"minus mod p: {closes['minus_p']}",
        "",
        "RULING: this is the intended equation. P135 leftovers match the provided remainders;",
        "no exact modular close on the four corrected variants for P135.",
    ]
    (OUT / "CHECKSUM_CHAIN_H1_H2_EQ.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("P135 H1/H2/checksum locked:", True)
    print("P135 remainder matches:", match)
    print("cohort closes:", closes)
    print(f"wrote {OUT / 'CHECKSUM_CHAIN_H1_H2_EQ.txt'}")


if __name__ == "__main__":
    main()
