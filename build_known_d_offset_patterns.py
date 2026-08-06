#!/usr/bin/env python3
"""
Hunt overlooked patterns in offsets from *known* private keys.

For every solved puzzle:
  d known
  offsets from range rulers, packet landings, N-mirror, bit structure of (d-L)

Look for:
  - shared relative bitmasks (global and per band)
  - modular structure (mod small m, mod 2^k)
  - leading/trailing bits of (d - L)
  - correlation of offset metrics with n
  - N-d mirror position vs scalar position (should be flipped)
  - popcount / runs of bits
  - whether low bits of d equal low bits of any public signal

Writes: ARCHIVE/briefcase/The Real Decimal/known_d_offset_patterns.*
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
HINGE = Decimal(str(math.log2(1.5)))
TWO256 = Decimal(1 << 256)


def set_bits(x: int) -> list[int]:
    x = abs(x)
    bits = []
    i = 0
    while x:
        if x & 1:
            bits.append(i)
        x >>= 1
        i += 1
    return bits


def runs(bits: list[int]) -> list[tuple[int, int]]:
    """Contiguous runs (start, length) in sorted bit list."""
    if not bits:
        return []
    bits = sorted(bits)
    out = []
    start = prev = bits[0]
    for b in bits[1:]:
        if b == prev + 1:
            prev = b
            continue
        out.append((start, prev - start + 1))
        start = prev = b
    out.append((start, prev - start + 1))
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    rows = []
    for n in range(1, 161):
        e = catalog[n]
        if not e.solved or e.private_key <= 0 or not e.public_key:
            continue
        d = e.private_key
        lo, hi = e.range_min, e.range_max
        width = hi - lo + 1
        px, py = pubkey_xy(e.public_key)
        pmy = (p - py) % p
        st = Decimal(f"{px}.{pmy}")
        pkt_p = st / Decimal(p)
        pkt_256 = st / TWO256

        # rulers → offsets from known d
        rulers = {
            "lower": lo,
            "upper": hi,
            "mid": lo + (hi - lo) // 2,
            "hinge": lo + int(Decimal(width) * HINGE),
            "packet_p_landing": lo + int(pkt_p * Decimal(width)),
            "packet_256_landing": lo + int(pkt_256 * Decimal(width)),
            "px_over_p_landing": lo + int(Decimal(px) * Decimal(width) / Decimal(p)),
        }
        offsets = {name: d - exp for name, exp in rulers.items()}

        # core offset from floor of range
        delta = d - lo  # always in [0, width)
        bits = set_bits(delta)
        rel = [b - (n - 1) for b in bits]  # relative to MSB of window
        # bits of delta only use positions 0 .. n-2 typically (width = 2^(n-1))
        # so relative to (n-1): all negative or -1 max

        q = (N - d) % N
        mlo, mhi = N - (1 << n) + 1, N - (1 << (n - 1))
        # mirror position: 0 at high q (low d), 1 at low q (high d)
        # low d → high q; mirror_pos 0 at mlo (high d), 1 at mhi (low d)
        # scalar_pos + mirror_pos = (width-1)/width ≈ 1
        mirror_span = mhi - mlo + 1
        mirror_pos = (q - mlo) / mirror_span if mirror_span else None
        scalar_pos = (d - lo) / width

        # low-bit agreement: do low k bits of d match low k bits of public ints?
        lowbit_hits = {}
        for k in (8, 16, 32):
            mask = (1 << k) - 1
            lowbit_hits[f"d_vs_px_low{k}"] = (d & mask) == (px & mask)
            lowbit_hits[f"d_vs_pmy_low{k}"] = (d & mask) == (pmy & mask)
            lowbit_hits[f"delta_vs_px_low{k}"] = (delta & mask) == (px & mask)
            lowbit_hits[f"delta_vs_floor_pktN_low{k}"] = (
                (delta & mask) == (int(pkt_p * Decimal(N)) & mask)
            )

        # mod structure of delta
        mods = {m: delta % m for m in (3, 5, 7, 16, 256, 65536)}

        rows.append({
            "puzzle": n,
            "d": str(d),
            "d_hex": hex(d),
            "lo": str(lo),
            "delta_d_minus_L": str(delta),
            "delta_hex": hex(delta),
            "scalar_position": scalar_pos,
            "offsets": {k: str(v) for k, v in offsets.items()},
            "offset_signs": {k: (0 if v == 0 else (1 if v > 0 else -1)) for k, v in offsets.items()},
            "delta_bits": bits,
            "delta_popcount": len(bits),
            "delta_relative_bits_msb": rel,
            "delta_bit_runs": runs(bits),
            "delta_highest_bit": bits[-1] if bits else None,
            "delta_lowest_bit": bits[0] if bits else None,
            "delta_mods": mods,
            "N_minus_d": str(q),
            "mirror_position": mirror_pos,
            "scalar_plus_mirror": (
                scalar_pos + mirror_pos if mirror_pos is not None else None
            ),
            "lowbit_hits": lowbit_hits,
            "pkt_p": format(pkt_p, "f"),
            "pkt_256": format(pkt_256, "f"),
        })

    n_solved = len(rows)

    # --- pattern hunts ---
    findings = []

    # 1) scalar + mirror ≈ 1 - 1/width (floor/height switch)
    sums = [r["scalar_plus_mirror"] for r in rows if r["scalar_plus_mirror"] is not None]
    # exact target depends on width; use 1 - 1/width per puzzle
    sum_err = []
    for r in rows:
        if r["scalar_plus_mirror"] is None:
            continue
        e = catalog[r["puzzle"]]
        w = e.range_max - e.range_min + 1
        sum_err.append(abs(r["scalar_plus_mirror"] - (1.0 - 1.0 / w)))
    findings.append({
        "name": "scalar_position + N_mirror_position = 1 - 1/width",
        "mean_abs_err": sum(sum_err) / len(sum_err),
        "max_abs_err": max(sum_err),
        "holds": max(sum_err) < 1e-12,
        "note": "Floor/height switch identity (exact with inclusive bounds)",
    })

    # 2) relative bit patterns of (d-L)
    pat_counts = Counter(tuple(r["delta_relative_bits_msb"]) for r in rows)
    top_pats = pat_counts.most_common(10)
    findings.append({
        "name": "shared relative bitmasks of (d - L)",
        "unique_patterns": len(pat_counts),
        "top": [{"pattern": list(p), "count": c} for p, c in top_pats[:5]],
        "entropy": -sum(
            (c / n_solved) * math.log2(c / n_solved) for c in pat_counts.values()
        ),
        "note": "High unique count / entropy ⇒ no shared shifted mask",
    })

    # 3) band-local shared patterns (n±10 style buckets: 1-32, 33-64, 65-96, 97-130)
    band_findings = []
    for lo_b, hi_b in ((1, 32), (33, 64), (65, 96), (97, 130)):
        band = [r for r in rows if lo_b <= r["puzzle"] <= hi_b]
        if len(band) < 4:
            continue
        pc = Counter(tuple(r["delta_relative_bits_msb"]) for r in band)
        top = pc.most_common(3)
        ent = -sum((c / len(band)) * math.log2(c / len(band)) for c in pc.values())
        band_findings.append({
            "band": f"{lo_b}-{hi_b}",
            "n": len(band),
            "unique": len(pc),
            "entropy": ent,
            "top": [{"pattern": list(p), "count": c} for p, c in top],
        })
    findings.append({"name": "band-local delta bitmasks", "bands": band_findings})

    # 4) mod structure: is delta mod m constant or low-entropy?
    mod_findings = []
    for m in (3, 5, 7, 16, 256):
        ctr = Counter(r["delta_mods"][m] for r in rows)
        ent = -sum((c / n_solved) * math.log2(c / n_solved) for c in ctr.values())
        # uniform entropy = log2(m)
        # with only n_solved samples, max entropy is log2(n_solved), not log2(m)
        max_ent = math.log2(min(m, n_solved))
        mod_findings.append({
            "mod": m,
            "entropy": ent,
            "max_entropy_for_sample": max_ent,
            "top": ctr.most_common(5),
            "skew": ent < max_ent - 0.5,
        })
    findings.append({"name": "delta mod m distribution", "mods": mod_findings})

    # 5) low-bit agreement rates with public signals
    lowbit_rates = {}
    for key in rows[0]["lowbit_hits"]:
        lowbit_rates[key] = sum(1 for r in rows if r["lowbit_hits"][key]) / n_solved
    findings.append({
        "name": "low-bit agreement d/delta vs public ints",
        "rates": lowbit_rates,
        "note": "Rate near 1/2^k is chance; much higher would be a leak",
    })

    # 6) popcount of delta vs n
    pops = [r["delta_popcount"] for r in rows]
    ns = [float(r["puzzle"]) for r in rows]
    findings.append({
        "name": "delta popcount vs n",
        "mean_popcount": sum(pops) / n_solved,
        "spearman_popcount_vs_n": spearman(pops, ns),
        "note": "Random delta in 2^(n-1) width has expected popcount ~(n-1)/2",
    })

    # 7) offset signs for packet landings — always above/below?
    for ruler in ("packet_p_landing", "packet_256_landing", "hinge", "mid"):
        signs = Counter(r["offset_signs"][ruler] for r in rows)
        findings.append({
            "name": f"offset sign bias: d - {ruler}",
            "signs": dict(signs),
            "frac_positive": signs.get(1, 0) / n_solved,
            "frac_negative": signs.get(-1, 0) / n_solved,
            "frac_zero": signs.get(0, 0) / n_solved,
        })

    # 8) |offset|/width distribution — clustered?
    for ruler in ("packet_p_landing", "hinge", "mid"):
        norms = [
            abs(int(r["offsets"][ruler])) / (
                int(r["lo"]) and (int(catalog[r["puzzle"]].range_max) - int(r["lo"]) + 1)
            )
            for r in rows
        ]
        # fix width
        norms = []
        for r in rows:
            e = catalog[r["puzzle"]]
            w = e.range_max - e.range_min + 1
            norms.append(abs(int(r["offsets"][ruler])) / w)
        findings.append({
            "name": f"|d-{ruler}|/width",
            "mean": sum(norms) / n_solved,
            "stdev": math.sqrt(
                sum((x - sum(norms) / n_solved) ** 2 for x in norms) / n_solved
            ),
            "min": min(norms),
            "max": max(norms),
        })

    # 9) delta in upper half of window (random ~0.5)
    upper_half = 0
    upper_half_of = 0
    for r in rows:
        n = r["puzzle"]
        if n < 2:
            continue
        upper_half_of += 1
        half = 1 << (n - 2)
        if int(r["delta_d_minus_L"]) >= half:
            upper_half += 1
    findings.append({
        "name": "delta in upper half of window",
        "count": upper_half,
        "of": upper_half_of,
        "frac": upper_half / upper_half_of if upper_half_of else None,
        "note": "Random would be ~0.5",
    })

    # 10) longest run of set bits in delta — any shared run length?
    run_lens = []
    for r in rows:
        rs = r["delta_bit_runs"]
        run_lens.append(max((ln for _, ln in rs), default=0))
    findings.append({
        "name": "longest set-bit run in (d-L)",
        "mean": sum(run_lens) / n_solved,
        "max": max(run_lens),
        "distribution": Counter(run_lens).most_common(8),
    })

    # 11) overlooked: does (d XOR lo) have fewer bits than random?
    xor_pops = []
    for r in rows:
        d = int(r["d"])
        lo = int(r["lo"])
        xor_pops.append(bin(d ^ lo).count("1"))
    # d ^ lo = d - lo when lo is power of 2 and d in [lo, 2*lo)
    # For lo=2^(n-1), d in [lo, 2^n), d^lo has bit (n-1) clear and low bits = delta
    # So popcount(d^lo) = popcount(delta) always when lo is power of 2!
    findings.append({
        "name": "popcount(d XOR L) vs popcount(d-L)",
        "mean_xor": sum(xor_pops) / n_solved,
        "mean_delta": sum(pops) / n_solved,
        "always_equal": all(
            xor_pops[i] == pops[i] for i in range(n_solved)
        ),
        "note": "When L=2^(n-1), d^L equals d-L bit pattern (bit n-1 off). Identity, not a leak.",
    })

    # 12) packet offset vs scalar position correlation (residual style)
    pkt_off_norm = []
    for r in rows:
        e = catalog[r["puzzle"]]
        w = e.range_max - e.range_min + 1
        pkt_off_norm.append(int(r["offsets"]["packet_p_landing"]) / w)
    findings.append({
        "name": "spearman(scalar_position, packet_p_offset/width)",
        "rho": spearman(
            [r["scalar_position"] for r in rows],
            pkt_off_norm,
        ),
        "note": "Near ±1 would mean packet landing tracks d; near 0 means independent",
    })

    # overlooked candidates worth flagging
    overlooked = []
    if findings[0]["holds"]:
        overlooked.append(
            "CONFIRMED identity: scalar_position + N_mirror_position = 1 - 1/width "
            "(floor/height switch)."
        )
    # findings index for lowbit - find by name
    for f in findings:
        if f["name"] == "low-bit agreement d/delta vs public ints":
            for k, rate in f["rates"].items():
                kbits = int(k.split("low")[-1])
                chance = 1.0 / (1 << kbits)
                if rate > max(chance * 4, 0.08):
                    overlooked.append(
                        f"Elevated low-bit hit rate {k}: {rate:.4f} vs chance {chance:.6f}"
                    )
        if f["name"] == "delta mod m distribution":
            for mf in f["mods"]:
                if mf["skew"]:
                    overlooked.append(
                        f"delta mod {mf['mod']} skewed "
                        f"(entropy {mf['entropy']:.3f} < max {mf['max_entropy_for_sample']:.3f})"
                    )
        if f["name"].startswith("offset sign bias"):
            if f["frac_positive"] > 0.65 or f["frac_negative"] > 0.65:
                overlooked.append(
                    f"{f['name']}: bias pos={f['frac_positive']:.2f} "
                    f"neg={f['frac_negative']:.2f}"
                )
        if f["name"] == "delta in upper half of window" and f["frac"] is not None:
            if abs(f["frac"] - 0.5) > 0.12:
                overlooked.append(
                    f"Upper-half bias for (d-L): frac={f['frac']:.3f} (chance ~0.5)"
                )

    if len(overlooked) <= 1:  # only the identity
        overlooked.append(
            "No strong overlooked leak beyond the N-mirror identity: "
            "bitmasks high-entropy, mods near chance, low-bits near chance, "
            "packet landings uncorrelated with d."
        )

    payload = {
        "exhibit": "known_d_offset_patterns",
        "n_solved": n_solved,
        "findings": findings,
        "overlooked_summary": overlooked,
        "rows": rows,
    }
    (OUT / "known_d_offset_patterns.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Known-d offset pattern hunt",
        "",
        f"Solved puzzles with known `d`: **{n_solved}**",
        "",
        "Offsets = `actual_d − expected` from range/packet rulers; "
        "plus structure of `(d − L)` and `N−d`.",
        "",
        "## Overlooked? Summary",
        "",
    ]
    for o in overlooked:
        lines.append(f"- {o}")

    lines.extend(["", "## Findings", ""])
    for f in findings:
        lines.append(f"### {f['name']}")
        lines.append("")
        lines.append("```json")
        # compact json without rows
        lines.append(json.dumps({k: v for k, v in f.items() if k != "name"}, indent=2)[:2000])
        lines.append("```")
        lines.append("")

    lines.extend([
        "## Sample (d − L) bit structure",
        "",
        "| P | scalar_pos | popcount(d−L) | lowest | highest | mod 256 |",
        "|---|------------|---------------|--------|---------|---------|",
    ])
    for r in rows[:20]:
        lines.append(
            f"| {r['puzzle']} | {r['scalar_position']:.4f} | {r['delta_popcount']} | "
            f"{r['delta_lowest_bit']} | {r['delta_highest_bit']} | "
            f"{r['delta_mods'][256]} |"
        )

    lines.extend([
        "",
        "## Ruling",
        "",
        "Patterns from known private keys were re-checked for subtle structure.",
        "Clean structural hit: N-mirror identity",
        "`scalar_position + mirror_position = 1 - 1/width`.",
        "No transferable offset mask or public low-bit leak stood out.",
        "",
        "Rebuild: `python build_known_d_offset_patterns.py`",
        "",
    ])
    (OUT / "known_d_offset_patterns.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"solved={n_solved}")
    for o in overlooked:
        print(f"  - {o}")
    print(f"delta bitmask entropy={findings[1]['entropy']:.3f} unique={findings[1]['unique_patterns']}")
    print(f"wrote {OUT / 'known_d_offset_patterns.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
