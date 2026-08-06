#!/usr/bin/env python3
"""EC/hash160 gate for scaled P71 TDAD candidates (536870912 = 2^29 phase)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from ecdsa import SECP256k1, SigningKey
from puzzle_catalog import load_catalog

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P71"

LO = 1 << 70
HI = (1 << 71) - 1
M = 536870912  # 2^29
TARGET_H160 = "f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8"
T71_FILED = 1411488254391826260559


def hash160_from_d(d: int) -> str:
    d = d % int(SECP256k1.order)
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    x, y = pt.x(), pt.y()
    comp = (b"\x02" if y % 2 == 0 else b"\x03") + x.to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(comp).digest()).hexdigest()


def gate_scalar(label: str, d: int, meta: dict | None = None) -> dict:
    in_range = LO <= d <= HI
    h160 = hash160_from_d(d) if in_range else None
    hit = h160 == TARGET_H160 if h160 else False
    return {
        "label": label,
        "d": str(d),
        "bits": d.bit_length(),
        "in_range": in_range,
        "hash160_match": hit,
        "hash160": h160,
        **(meta or {}),
    }


def scaled_sum(indices: list[int], d: dict[int, int], remainder: int = 0) -> int:
    return sum(M * d[i] for i in indices) + remainder


def parse_indices(text: str) -> list[int]:
    return [int(i) for _, i in re.findall(r"(\d+)\((\d+)\)", text)]


def main() -> int:
    cat = load_catalog()
    d = {n: cat[n].private_key for n in range(1, 161) if cat[n].solved and cat[n].private_key > 0}

    results: list[dict] = []
    seen: set[int] = set()

    def add(label: str, val: int, meta: dict | None = None) -> None:
        if val in seen:
            return
        seen.add(val)
        results.append(gate_scalar(label, val, meta))

    # --- explicit scalars ---
    add("filed_T71_thePattern", T71_FILED)

    # user band decompositions
    p70_lo = "536870912(41) + 536870912(39) + 536870912(39) + 536870912(36) + 536870912(36) + 536870912(33) + 536870912(30) + 536870912(28) + 536870912(27) + 536870912(25)+ 536870912(21) + 536870912(19) + 536870912(15) + 536870912(13) + 536870912(11) + 536870912(7) + 536870912(7) + 536870912(5) + 536870912(3)"
    p71_hi = "536870912(42) + 536870912(41) + 536870912(36) + 536870912(30) + 536870912(29) + 536870912(29) + 536870912(27) + 536870912(26) + 536870912(24) + 536870912(24) + 536870912(21) + 536870912(18) + 536870912(15) + 536870912(14) + 536870912(13) + 536870912(12) + 536870912(11) + 536870912(10) + 536870912(6) + 536870912(5) + 536870912(2) + 536870912(1) + 536870912(1)"
    add("user_2^70_band_sum", scaled_sum(parse_indices(p70_lo), d))
    add("user_2^71_out_of_band", scaled_sum(parse_indices(p71_hi), d))

    # P70 scaled + remainder pattern applied to P71 index cap
    p70_idx = parse_indices(
        "536870912(41) + 536870912(39) + 536870912(35) + 536870912(32) + 536870912(31) + 536870912(28) + 536870912(26) + 536870912(23) + 536870912(23) + 536870912(19) + 536870912(16) + 536870912(15) + 536870912(13) + 536870912(12) + 536870912(8) + 536870912(7) + 536870912(5) + 536870912(4) + 536870912(4) + 536870912(1)"
    )
    add("P70_scaled_indices_only", scaled_sum(p70_idx, d))
    add("P70_scaled+P70_remainder", scaled_sum(p70_idx, d, 443305713))
    add("P70_scaled+P69_remainder", scaled_sum(p70_idx, d, 314342924))

    # P69 scaled indices at P71
    p69_idx = parse_indices(
        "536870912(39) + 536870912(38) + 536870912(36) + 536870912(35) + 536870912(35) + 536870912(29) + 536870912(23) + 536870912(19) + 536870912(18) + 536870912(13) + 536870912(11) + 536870912(10) + 536870912(9) + 536870912(4) + 536870912(4) + 536870912(2) + 536870912(1)"
    )
    add("P69_scaled_indices_only", scaled_sum(p69_idx, d))
    add("P69_scaled+P69_remainder", scaled_sum(p69_idx, d, 314342924))

    # user 2^71 indices with remainder sweep to pull into band
    hi_idx = parse_indices(p71_hi)
    base_hi = scaled_sum(hi_idx, d)
    # pull down from 2^71 into band by subtracting terms / adding negative remainder
    for rem in range(0, 500_000_000):
        val = base_hi - rem
        if val < LO:
            break
        if val <= HI:
            add(f"2^71_band_pull_rem_{rem}", val, {"indices": hi_idx, "remainder": -rem})
            if len([r for r in results if r.get("remainder")]) > 50:
                break

    # scaled paths: first slot 42, descending anchors like P70/P69
    anchor_sets = [
        ("user_2^71_indices", hi_idx),
        ("user_2^70_indices", parse_indices(p70_lo)),
        (
            "P71_guess_from_P70_shape",
            [42, 41, 36, 33, 32, 29, 27, 24, 24, 20, 17, 16, 14, 13, 9, 8, 6, 5, 5, 2, 1],
        ),
        (
            "P71_dense_low",
            [42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        ),
    ]
    for name, idxs in anchor_sets:
        idxs = [i for i in idxs if i in d and i <= 42]
        if not idxs:
            continue
        base = scaled_sum(idxs, d)
        add(f"{name}_bare", base, {"indices": idxs, "term_count": len(idxs)})
        # remainder to land at LO, MID, HI-1, filed T71 distance
        for target_name, target in [
            ("LO", LO),
            ("MID", LO + (1 << 69)),
            ("HI-1", HI),
            ("filed_T71", T71_FILED),
        ]:
            rem = target - base
            if 0 <= rem <= (1 << 40):
                add(f"{name}_rem_to_{target_name}", base + rem, {"indices": idxs, "remainder": rem})

    # classic [3,2,1,2] filed path from thePattern (value form)
    classic = (
        "3*297274491920375905804 + 2*219898266213316039825 + 46346217550346335726 + 2*8993229949524469768 + "
        "3*3908372542507822062 + 2*1425787542618654982 + 525070384258266191 + 2*199976667976342049 + "
        "3*6763683971478124 + 2*4216495639600700 + 4216495639600700 + 2*409118905032525 + "
        "3*15404761757071 + 2*15404761757071 + 7409811047825 + 2*2895374552463 + "
        "3*1003651412950 + 2*146971536592 + 7137437912 + 2*2102388551 + "
        "3*1033162084 + 2*400708894 + 400708894 + 2*33185509 + "
        "3*14428676 + 2*14428676 + 5598802 + 2*863317 + "
        "3*51510 + 2*26867 + 10544 + 2*10544 + "
        "3*514 + 2*224 + 224 + 2*76 + "
        "3*21 + 2*7 + 7 + 2*3"
    )
    # already filed as T71

    hits = [r for r in results if r["hash160_match"]]
    in_range = [r for r in results if r["in_range"]]

    summary = {
        "target_h160": TARGET_H160,
        "range": [str(LO), str(HI)],
        "candidates_tested": len(results),
        "in_range_count": len(in_range),
        "hash160_hits": len(hits),
        "hits": hits,
        "in_range_samples": in_range[:30],
        "all_results": results,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scaled_ec_gate.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# P71 scaled EC gate",
        "",
        f"Target hash160: `{TARGET_H160}`",
        f"Range: `[2^70, 2^71)`",
        "",
        f"Candidates tested: **{len(results)}**",
        f"In range: **{len(in_range)}**",
        f"Hash160 hits: **{len(hits)}**",
        "",
    ]
    if hits:
        lines.append("## HITS")
        for h in hits:
            lines.append(f"- {h['label']}: d={h['d']}")
    else:
        lines.append("## No hash160 hits")
        lines.append("")
        lines.append("| label | in_range | bits | hash160 (first 16) |")
        lines.append("|-------|----------|------|---------------------|")
        for r in sorted(in_range, key=lambda x: x["label"])[:25]:
            h = r.get("hash160") or ""
            lines.append(f"| {r['label']} | {r['in_range']} | {r['bits']} | `{h[:16]}…` |")

    (OUT / "scaled_ec_gate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"tested={len(results)} in_range={len(in_range)} hits={len(hits)}")
    for r in in_range[:15]:
        print(f"  {r['label']}: bits={r['bits']} h160={r.get('hash160','')[:16]}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
