#!/usr/bin/env python3
"""
Three-courtroom probe: defect-shell constants vs known ledger objects.

Courtrooms:
  1. Field scaling:   Gx * a mod p
  2. Field exponent:  Gx^a mod p
  3. EC scalar:       x([a]G)   (a mod N)

Smoke test 2Gx already failed for blunt forms; this maps B, B4, Δ, C_p, C_N
onto β/Λ/RSZ ledger values.

Writes ONLY under ARCHIVE/briefcase/real/.
"""

from __future__ import annotations

import json
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

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

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "real"

# Generator x (standard G) is middle of CS β-triple list
GX = Gx[1]
# 2Gx field product (smoke target)
TWO_GX_FIELD = (2 * GX) % p

B = (1 << 32) + 977
B4 = pow(B, 4)  # integer, not mod
C_P = (DELTA * inv(B4 % p, p)) % p
C_N = (DELTA * inv(B4 % N, N)) % N

# P135 ledger shadows (from briefcase puzzle_135)
LAMBDA_N = 107329397079532295557318141750802481743365519021307735330654746890138631346025
LAMBDA_Y = 92736738943421429813433900502071579205213592459201379042094542895571506924317
LAMBDA_Y_N = 113614481683161747575519665309249021091587411735886135183509632463006678705193
GAP_X = 9877711216647209374859589709910323233441283359683132101603896077651377656524
GAP_Y = 6285084603629452018201523558446539348221892714578399852854885572868047359168
DELTA_K = CSN["delta_k"]


def ec_x(scalar: int) -> int:
    """x([scalar]G) with scalar reduced mod N (EC courtroom)."""
    a = scalar % N
    if a == 0:
        raise ValueError("scalar ≡ 0 mod N")
    sk = SigningKey.from_secret_exponent(a, curve=SECP256k1)
    return sk.verifying_key.pubkey.point.x()


def ledger_objects() -> dict[str, int]:
    """Known β/Λ/RSZ ledger objects only — not the defect constants under test."""
    objs: dict[str, int] = {
        "Gx1": Gx[0],
        "Gx2": Gx[1],
        "Gx3": Gx[2],
        "Px1": Px[0],
        "Px2": Px[1],
        "Px3": Px[2],
        "rx1": rx[0],
        "rx2": rx[1],
        "rx3": rx[2],
        "beta": BETA,
        "beta_sq": BETA_SQ,
        "Lambda": LAMBDA,
        "Lambda1": LAMBDA1,
        "lambda_y": LAMBDA_Y,
        "Lambda_N": LAMBDA_N,
        "lambda_y_N": LAMBDA_Y_N,
        "GAP_x": GAP_X,
        "GAP_y": GAP_Y,
        "delta_k": DELTA_K,
        "2Gx_field": TWO_GX_FIELD,
        "Gx_inv": inv(GX, p),
        # CS-N delta-scaled Λ labels
        "LAMBDA_x_DELTA": CSN["LAMBDA_x_DELTA"],
        "LAMBDA3_x_DELTA": CSN["LAMBDA3_x_DELTA"],
        "LAMBDA3_N": CSN["LAMBDA3_N"],
        "RQ": CSN["RQ"],
        "Rq": CSN["Rq"],
        "Cq": CSN["Cq"],
    }
    # N-side reductions of p-side objects
    for name in (
        "Gx1", "Gx2", "Gx3", "Px1", "Px2", "Px3", "rx1", "rx2", "rx3",
        "beta", "beta_sq", "Lambda", "Lambda1", "lambda_y",
    ):
        objs[f"{name}_mod_N"] = objs[name] % N
    return objs


def match_value(val: int, objs: dict[str, int], modulus: int | None = None) -> list[str]:
    hits: list[str] = []
    for name, obj in objs.items():
        if modulus is not None:
            if val % modulus == obj % modulus:
                hits.append(name)
        elif val == obj:
            hits.append(name)
    return hits


def probe_scalar(name: str, a: int, objs: dict[str, int]) -> dict:
    # three courtrooms
    field_mul = (GX * (a % p)) % p
    # field exponent: reduce exponent mod (p-1) for Fp*
    field_exp = pow(GX, a % (p - 1), p)
    ec = ec_x(a)

    return {
        "name": name,
        "a": str(a),
        "a_mod_p": str(a % p),
        "a_mod_N": str(a % N),
        "a_hits_ledger": match_value(a % p, objs) + [
            f"{h}(mod N)" for h in match_value(a % N, objs) if h not in match_value(a % p, objs)
        ],
        "field_mul_Gx": {
            "value": str(field_mul),
            "equals_2Gx": field_mul == TWO_GX_FIELD,
            "hits": match_value(field_mul, objs),
        },
        "field_exp_Gx": {
            "value": str(field_exp),
            "equals_2Gx": field_exp == TWO_GX_FIELD,
            "hits": match_value(field_exp, objs),
        },
        "ec_x_aG": {
            "value": str(ec),
            "equals_2Gx": ec == TWO_GX_FIELD,
            "hits": match_value(ec, objs),
            "hits_mod_N": match_value(ec % N, objs),
        },
    }


def main() -> int:
    objs = ledger_objects()
    scalars = {
        "B": B,
        "B4": B4,
        "DELTA": DELTA,
        "C_p": C_P,
        "C_N": C_N,
    }

    # also probe correction as integer ratio is not in Fp; use C_p/C_N only

    results = [probe_scalar(name, a, objs) for name, a in scalars.items()]

    # smoke: confirm 2Gx not hit by any blunt form (user's first pass)
    any_2gx = any(
        r["field_mul_Gx"]["equals_2Gx"]
        or r["field_exp_Gx"]["equals_2Gx"]
        or r["ec_x_aG"]["equals_2Gx"]
        for r in results
    )

    hits_only = []
    for r in results:
        for court in ("field_mul_Gx", "field_exp_Gx", "ec_x_aG"):
            h = r[court]["hits"]
            if court == "ec_x_aG":
                h = h + [f"{x}(mod N)" for x in r[court].get("hits_mod_N", [])]
            # de-dup
            h = sorted(set(h))
            if h:
                hits_only.append({"scalar": r["name"], "courtroom": court, "hits": h})
        if r["a_hits_ledger"]:
            hits_only.append(
                {"scalar": r["name"], "courtroom": "a_itself", "hits": r["a_hits_ledger"]}
            )

    payload = {
        "exhibit": "defect_shell_ledger_map",
        "location": "ARCHIVE/briefcase/real/",
        "verdict": {
            "status": "PROBED",
            "any_equals_2Gx": any_2gx,
            "ledger_hits": len(hits_only),
            "note": (
                "Field mul/exp ≠ EC scalar. "
                "Hits mean value equality to a named ledger object, not a d recovery."
            ),
        },
        "constants": {
            "B": str(B),
            "B4": str(B4),
            "DELTA": str(DELTA),
            "C_p": str(C_P),
            "C_N": str(C_N),
            "Gx": str(GX),
            "2Gx_field": str(TWO_GX_FIELD),
        },
        "results": results,
        "hits_summary": hits_only,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "probe_defect_shell_ledger_map.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # markdown
    lines = [
        "# Probe: defect-shell constants vs ledger objects",
        "",
        "Three courtrooms — do not mix them:",
        "",
        "```text",
        "1. Field scaling:  Gx * a mod p",
        "2. Field exponent: Gx^a mod p",
        "3. EC scalar:      x([a]G)",
        "```",
        "",
        f"**Any form equals 2Gx?** `{any_2gx}`",
        "",
        f"**Ledger object hits:** {len(hits_only)}",
        "",
        "## Constants",
        "",
        f"- B = `{B}`",
        f"- B4 = `{B4}`",
        f"- Δ = `{DELTA}`",
        f"- C_p = Δ · B4⁻¹ mod p = `{C_P}`",
        f"- C_N = Δ · B4⁻¹ mod N = `{C_N}`",
        "",
        "## Hits (value lands on a known ledger object)",
        "",
    ]
    if not hits_only:
        lines.append("_No hits — defect shell does not land on β/Λ/RSZ ledger objects in this pass._")
        lines.append("")
    else:
        for h in hits_only:
            lines.append(
                f"- **{h['scalar']}** / `{h['courtroom']}` → {', '.join(f'`{x}`' for x in h['hits'])}"
            )
        lines.append("")

    lines.append("## Per-scalar results")
    lines.append("")
    for r in results:
        lines.append(f"### {r['name']}")
        lines.append("")
        lines.append(f"- a mod p = `{r['a_mod_p']}`")
        lines.append(f"- a mod N = `{r['a_mod_N']}`")
        for court, label in (
            ("field_mul_Gx", "Gx * a mod p"),
            ("field_exp_Gx", "Gx^a mod p"),
            ("ec_x_aG", "x([a]G)"),
        ):
            block = r[court]
            hits = block["hits"]
            if court == "ec_x_aG":
                hits = sorted(set(hits + [f"{x}(mod N)" for x in block.get("hits_mod_N", [])]))
            lines.append(f"- **{label}**")
            lines.append(f"  - value = `{block['value']}`")
            lines.append(f"  - equals 2Gx = `{block['equals_2Gx']}`")
            lines.append(f"  - hits = `{hits if hits else 'none'}`")
        lines.append("")

    lines.append("## Ruling")
    lines.append("")
    lines.append(
        "2Gx was a smoke test. This pass asks whether B / B4 / Δ / C land on "
        "known β/Λ/RSZ ledger objects across the three courtrooms. "
        "Hits (if any) are bookkeeping coincidences until `[d]G` verifies."
    )
    lines.append("")

    md_path = OUT / "probe_defect_shell_ledger_map.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"any_2Gx={any_2gx} ledger_hits={len(hits_only)}")
    for h in hits_only:
        print(f"  HIT {h['scalar']} / {h['courtroom']} -> {h['hits']}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
