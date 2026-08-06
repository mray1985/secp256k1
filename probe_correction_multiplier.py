#!/usr/bin/env python3
"""
Composite probe: correction shim C = (p-N)/B^4 against packet + Λ/GAP ledger.

Prior pass: B, B4, Δ, C alone do not land on ledger objects (mul/exp/EC).
This pass asks whether *scaling known ledger objects by C* (or dividing by C)
lands on another known object — the accounting-layer test.

Writes ONLY under ARCHIVE/briefcase/real/.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    CSN,
    DELTA,
    Gx,
    LAMBDA,
    LAMBDA1,
    N,
    Px,
    inv,
    p,
    rx,
)

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "real"

B = (1 << 32) + 977
B4 = pow(B, 4)
C_P = (DELTA * inv(B4 % p, p)) % p
C_N = (DELTA * inv(B4 % N, N)) % N
CORRECTION = Decimal(DELTA) / Decimal(B4)

PACKET_P = Decimal(
    "0.07954633649946046255450180288304075379977001785594624365740374798873"
    "7825607683797376362420847353351108638651635660059457338972369055727427"
    "831496239538405074"
)

LAMBDA_N = 107329397079532295557318141750802481743365519021307735330654746890138631346025
LAMBDA_Y = 92736738943421429813433900502071579205213592459201379042094542895571506924317
LAMBDA_Y_N = 113614481683161747575519665309249021091587411735886135183509632463006678705193
GAP_X = 9877711216647209374859589709910323233441283359683132101603896077651377656524
GAP_Y = 6285084603629452018201523558446539348221892714578399852854885572868047359168
DELTA_K = CSN["delta_k"]

GX = Gx[1]


def ledger_p() -> dict[str, int]:
    return {
        "Gx1": Gx[0], "Gx2": Gx[1], "Gx3": Gx[2],
        "Px1": Px[0], "Px2": Px[1], "Px3": Px[2],
        "rx1": rx[0], "rx2": rx[1], "rx3": rx[2],
        "beta": BETA, "beta_sq": BETA_SQ,
        "Lambda": LAMBDA, "Lambda1": LAMBDA1, "lambda_y": LAMBDA_Y,
        "C_p": C_P, "B4_mod_p": B4 % p, "DELTA_mod_p": DELTA % p,
        "Gx_inv": inv(GX, p),
        "2Gx": (2 * GX) % p,
    }


def ledger_n() -> dict[str, int]:
    return {
        "Lambda_N": LAMBDA_N,
        "lambda_y_N": LAMBDA_Y_N,
        "GAP_x": GAP_X,
        "GAP_y": GAP_Y,
        "delta_k": DELTA_K,
        "Lambda_mod_N": LAMBDA % N,
        "Lambda1_mod_N": LAMBDA1 % N,
        "lambda_y_mod_N": LAMBDA_Y % N,
        "C_N": C_N,
        "B4_mod_N": B4 % N,
        "DELTA": DELTA,
        "LAMBDA_x_DELTA": CSN["LAMBDA_x_DELTA"],
        "LAMBDA3_x_DELTA": CSN["LAMBDA3_x_DELTA"],
        "LAMBDA3_N": CSN["LAMBDA3_N"],
        "RQ": CSN["RQ"],
        "Rq": CSN["Rq"],
        "Cq": CSN["Cq"],
        "Px3_mod_N": Px[2] % N,
        "rx2_mod_N": rx[1] % N,
        "rx3_mod_N": rx[2] % N,
        "beta_mod_N": BETA % N,
    }


def hits(val: int, objs: dict[str, int], skip: set[str] | None = None) -> list[str]:
    skip = skip or set()
    return sorted(name for name, obj in objs.items() if name not in skip and val == obj)


def main() -> int:
    lp, ln = ledger_p(), ledger_n()
    inv_c_p = inv(C_P, p)
    inv_c_n = inv(C_N, N)

    # --- Fp: scale ledger objects by C_p / inv(C_p) ---
    p_scale_targets = {
        "Lambda": LAMBDA,
        "Lambda1": LAMBDA1,
        "lambda_y": LAMBDA_Y,
        "beta": BETA,
        "beta_sq": BETA_SQ,
        "Px3": Px[2],
        "rx2": rx[1],
        "rx3": rx[2],
        "Gx2": GX,
        "GAP_x_as_p": GAP_X % p,  # only if it appears in Fp by chance
        "delta_k_as_p": DELTA_K % p,
    }

    p_tests: list[dict] = []
    for name, val in p_scale_targets.items():
        mul = (val * C_P) % p
        div = (val * inv_c_p) % p
        p_tests.append({
            "object": name,
            "times_C_p": {"value": str(mul), "hits": hits(mul, lp, {name, "C_p"})},
            "div_C_p": {"value": str(div), "hits": hits(div, lp, {name, "C_p"})},
        })

    # --- FN: scale by C_N / inv(C_N) ---
    n_scale_targets = {
        "Lambda_N": LAMBDA_N,
        "lambda_y_N": LAMBDA_Y_N,
        "GAP_x": GAP_X,
        "GAP_y": GAP_Y,
        "delta_k": DELTA_K,
        "Lambda_mod_N": LAMBDA % N,
        "Lambda1_mod_N": LAMBDA1 % N,
        "LAMBDA_x_DELTA": CSN["LAMBDA_x_DELTA"],
        "RQ": CSN["RQ"],
        "Rq": CSN["Rq"],
        "Cq": CSN["Cq"],
    }

    n_tests: list[dict] = []
    for name, val in n_scale_targets.items():
        mul = (val * C_N) % N
        div = (val * inv_c_n) % N
        n_tests.append({
            "object": name,
            "times_C_N": {"value": str(mul), "hits": hits(mul, ln, {name, "C_N"})},
            "div_C_N": {"value": str(div), "hits": hits(div, ln, {name, "C_N"})},
        })

    # --- packet composites (decimal, then floor) ---
    packet_tests = {
        "packet_p * correction": PACKET_P * CORRECTION,
        "packet_p * B4": PACKET_P * Decimal(B4),
        "packet_p * DELTA": PACKET_P * Decimal(DELTA),
        "packet_p * (DELTA - B4)": PACKET_P * Decimal(DELTA - B4),
        "packet_p * C_p (as int embed)": PACKET_P * Decimal(C_P),
    }
    packet_rows = []
    for label, val in packet_tests.items():
        floor_v = int(val)
        frac = val - floor_v
        # compare floor to ledger ints (p and N)
        h_p = hits(floor_v % p, lp)
        h_n = hits(floor_v % N, ln)
        packet_rows.append({
            "label": label,
            "value": format(val, "f"),
            "floor": str(floor_v),
            "frac": format(frac, "f"),
            "floor_mod_p_hits": h_p,
            "floor_mod_N_hits": h_n,
        })

    # --- special identities worth checking ---
    specials = []
    # Does Λ * C_p ≡ Λ * Δ * B4^-1 relate to LAMBDA_x_DELTA?
    # LAMBDA_x_DELTA is Λ*Δ mod N (CS-N), different modulus.
    lam_c_p = (LAMBDA * C_P) % p
    lam_delta_p = (LAMBDA * (DELTA % p)) % p
    specials.append({
        "name": "Lambda * C_p mod p",
        "value": str(lam_c_p),
        "hits_p": hits(lam_c_p, lp),
        "equals_Lambda_times_DELTA_mod_p": lam_c_p == (LAMBDA * DELTA) % p,
    })
    # GAP_x / C_N ==? something
    gap_x_div = (GAP_X * inv_c_n) % N
    gap_y_div = (GAP_Y * inv_c_n) % N
    specials.append({
        "name": "GAP_x / C_N mod N",
        "value": str(gap_x_div),
        "hits_n": hits(gap_x_div, ln, {"GAP_x", "C_N"}),
    })
    specials.append({
        "name": "GAP_y / C_N mod N",
        "value": str(gap_y_div),
        "hits_n": hits(gap_y_div, ln, {"GAP_y", "C_N"}),
    })
    # Does C_p == correction mod p? (correction is real, C_p is modular)
    # Integer correction is not an int — skip.
    # Bridge: floor(packet*DELTA) vs floor(packet*B4)*something
    floor_delta = int(PACKET_P * Decimal(DELTA))
    floor_b4 = int(PACKET_P * Decimal(B4))
    # ratio of floors ≈ correction?
    floor_ratio = Decimal(floor_delta) / Decimal(floor_b4) if floor_b4 else Decimal(0)
    specials.append({
        "name": "floor(packet*DELTA) / floor(packet*B4)",
        "value": format(floor_ratio, "f"),
        "correction": format(CORRECTION, "f"),
        "abs_diff": format(abs(floor_ratio - CORRECTION), "f"),
        "near_correction": abs(floor_ratio - CORRECTION) < Decimal("1e-10"),
    })

    # collect all non-empty hits
    all_hits = []
    for t in p_tests:
        for op in ("times_C_p", "div_C_p"):
            if t[op]["hits"]:
                all_hits.append({
                    "courtroom": "Fp",
                    "object": t["object"],
                    "op": op,
                    "hits": t[op]["hits"],
                })
    for t in n_tests:
        for op in ("times_C_N", "div_C_N"):
            if t[op]["hits"]:
                all_hits.append({
                    "courtroom": "FN",
                    "object": t["object"],
                    "op": op,
                    "hits": t[op]["hits"],
                })
    for row in packet_rows:
        if row["floor_mod_p_hits"] or row["floor_mod_N_hits"]:
            all_hits.append({
                "courtroom": "packet",
                "object": row["label"],
                "op": "floor",
                "hits": row["floor_mod_p_hits"] + [f"{h}(N)" for h in row["floor_mod_N_hits"]],
            })
    for s in specials:
        hp = s.get("hits_p") or s.get("hits_n") or []
        if hp:
            all_hits.append({
                "courtroom": "special",
                "object": s["name"],
                "op": "—",
                "hits": hp,
            })
        if s.get("near_correction"):
            all_hits.append({
                "courtroom": "special",
                "object": s["name"],
                "op": "near_correction",
                "hits": ["correction_multiplier"],
            })

    payload = {
        "exhibit": "correction_multiplier_probe",
        "location": "ARCHIVE/briefcase/real/",
        "constants": {
            "B": str(B),
            "B4": str(B4),
            "DELTA": str(DELTA),
            "C_p": str(C_P),
            "C_N": str(C_N),
            "correction": format(CORRECTION, "f"),
        },
        "verdict": {
            "status": "PROBED",
            "hit_count": len(all_hits),
            "note": (
                "Composite C-scaling of ledger objects. "
                "Hits are accounting links, not d recovery."
            ),
        },
        "fp_scale_tests": p_tests,
        "fn_scale_tests": n_tests,
        "packet_tests": packet_rows,
        "specials": specials,
        "hits": all_hits,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "probe_correction_multiplier.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Probe: correction multiplier composites",
        "",
        "Prior pass: B / B4 / Δ / C alone do not land on ledger objects.",
        "This pass: scale known objects by `C` / `C⁻¹`, and packet × correction.",
        "",
        f"`correction = (p−N)/B^4 = {CORRECTION}`",
        f"`C_p = Δ·B4⁻¹ mod p = {C_P}`",
        f"`C_N = Δ·B4⁻¹ mod N = {C_N}`",
        "",
        f"**Hit count:** {len(all_hits)}",
        "",
        "## Hits",
        "",
    ]
    if not all_hits:
        lines.append("_No composite hits._")
    else:
        for h in all_hits:
            lines.append(
                f"- **{h['courtroom']}** `{h['object']}` / `{h['op']}` → "
                + ", ".join(f"`{x}`" for x in h["hits"])
            )
    lines.append("")
    lines.append("## Special: packet floor ratio vs correction")
    lines.append("")
    for s in specials:
        if "floor(packet" in s["name"]:
            lines.append(f"- {s['name']} = `{s['value']}`")
            lines.append(f"- correction = `{s['correction']}`")
            lines.append(f"- abs_diff = `{s['abs_diff']}`")
            lines.append(f"- near_correction = `{s['near_correction']}`")
    lines.append("")
    lines.append("## Ruling")
    lines.append("")
    lines.append(
        "If correction appears as a scale between ledger objects, it is part of "
        "the modulus-accounting layer. Still not a key."
    )
    lines.append("")

    md = OUT / "probe_correction_multiplier.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"hits={len(all_hits)}")
    for h in all_hits:
        print(f"  {h['courtroom']} {h['object']} / {h['op']} -> {h['hits']}")
    # always print the floor ratio result
    for s in specials:
        if "floor(packet" in s["name"]:
            print(f"  floor_ratio={s['value'][:40]}... near={s['near_correction']}")
    print(f"wrote {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
