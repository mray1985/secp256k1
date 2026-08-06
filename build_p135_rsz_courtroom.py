#!/usr/bin/env python3
"""
P135 RSZ courtroom — field-native witnesses meet s*k ≡ z + r*d (mod N).

Places r/s/z under /N roof alongside ledger field-native packets.
Generates k candidates from public witnesses; tests nonce gate [k]G.x == r,
then d = (s*k − z) * r⁻¹ mod N through range / EC / carry consistency.

Sanity: replay puzzle 100 with hashkeys-known k (must pass full stack).

Writes: ARCHIVE/briefcase/The Real Decimal/P135/rsz_courtroom.{md,json}
"""

from __future__ import annotations

import json
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, LAMBDA, LAMBDA1, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from candidate_gate_stack import d_from_k, ec_xy, gate_stack, map_p_to_n, packet_p_from_xy
from hashkeys_rsz import recover_r_point_from_sig
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal" / "P135"
LEDGER_PATH = OUT / "ledger.json"
P2 = p * p

# Canonical P135 RSZ (puzzle_rsz_cache / ledger)
R = 90653255469745952335985143920649543885181555095025199315947044135806663628368
S = 15509729875763924304053419655647994379903175655107184284998698212653288468986
Z = 66278737796829840734606014530466656889790152192829793669891337810330530090951


def ec_x(k: int) -> int | None:
    k = k % N
    if k == 0:
        return None
    sk = SigningKey.from_secret_exponent(k, curve=SECP256k1)
    return sk.verifying_key.pubkey.point.x()


def over_n(v: int) -> str:
    return format(float(Fraction(v, N)), ".60f")


def load_rsz_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.items() if isinstance(v, dict)}


def branch_k_candidates(head: str, branch: str, rec: dict, seen: set[int]) -> list[dict]:
    out: list[dict] = []
    fc = rec.get("field_courtroom", {})
    carry = rec.get("carry_p_to_N", {})
    shadow = rec.get("scalar_shadow", {})
    wrap = rec.get("curve_wrap", {})

    def add(label: str, val: int) -> None:
        v = val % N
        if v == 0 or v in seen:
            return
        seen.add(v)
        out.append({"label": label, "k": v, "head": head, "branch": branch})

    a = int(carry.get("A_map_p_to_n", 0))
    b = int(carry.get("B_floor_pair_N", 0))
    c = int(carry.get("carry", 0))

    add(f"{head}/{branch}/A_map_p_to_n", a)
    add(f"{head}/{branch}/B_floor_pair_N", b)
    if c:
        add(f"{head}/{branch}/A+carry", (a + c) % N)
    add(f"{head}/{branch}/map_p_to_n_x", int(shadow.get("map_p_to_n_x", 0)))
    add(f"{head}/{branch}/map_p_to_n_y", int(shadow.get("map_p_to_n_y", 0)))

    res = fc.get("residue_over_p2", {})
    mrec = fc.get("m_over_p2", {})
    pair = fc.get("P_pair", {})
    if res.get("numerator"):
        num = int(res["numerator"])
        add(f"{head}/{branch}/residue_num mod N", num)
        add(f"{head}/{branch}/floor(residue*N)", (num * N) // P2)
    if mrec.get("numerator"):
        m = int(wrap.get("m", 0)) or int(mrec["numerator"])
        add(f"{head}/{branch}/m mod N", m)
    if pair.get("numerator"):
        add(f"{head}/{branch}/P_pair_num mod N", int(pair["numerator"]))

    x = int(rec.get("x", 0))
    y = int(rec.get("y_limb", 0))
    add(f"{head}/{branch}/(x*p+y) mod N", (x * p + y) % N)

    return out


def collect_k_candidates(ledger: dict) -> list[dict]:
    seen: set[int] = set()
    cands: list[dict] = []

    def walk_slots(key: str, slot_name: str) -> None:
        slot = ledger.get(key, {}).get(slot_name, {})
        for br_name, br in slot.get("branches", {}).items():
            cands.extend(branch_k_candidates(f"{key}/{slot_name}", br_name, br, seen))

    walk_slots("field_native_primary", "branches")
    for slot in ("Px1", "Px2", "Px3"):
        walk_slots("beta_Px_slots", slot)
    for slot in ("rx1", "rx2", "rx3"):
        walk_slots("beta_rx_slots", slot)

    # RSZ / bridge scalars (unlikely k, but filed)
    extras = [
        ("rsz/r", R),
        ("rsz/s", S),
        ("rsz/z", Z),
        ("rsz/map_p_to_n_r", map_p_to_n(R)),
        ("rsz/(r+s) mod N", (R + S) % N),
        ("rsz/(z+r) mod N", (Z + R) % N),
        ("rsz/(z-r) mod N", (Z - R) % N),
        ("rsz/(r*s) mod N", (R * S) % N),
        ("bridge/LAMBDA mod N", LAMBDA % N),
        ("bridge/LAMBDA1 mod N", LAMBDA1 % N),
        ("bridge/DELTA mod N", DELTA % N),
        ("bridge/BETA mod N", BETA % N),
    ]
    px = int(ledger["pubkey"]["Px"])
    py = int(ledger["pubkey"]["Py"])
    extras += [
        ("pubkey/map_p_to_n_Px", map_p_to_n(px)),
        ("pubkey/map_p_to_n_Py", map_p_to_n(py)),
        ("pubkey/map_p_to_n(p-y)", map_p_to_n((p - py) % p)),
    ]
    for label, val in extras:
        v = val % N
        if v and v not in seen:
            seen.add(v)
            cands.append({"label": label, "k": v, "head": "scalar", "branch": "-"})

    return cands


def structural_facts(ledger: dict) -> dict:
    px = int(ledger["pubkey"]["Px"])
    py = int(ledger["pubkey"]["Py"])
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    rx2 = int(ledger["beta_rx_slots"]["rx2"]["x"])
    rx3 = int(ledger["beta_rx_slots"]["rx3"]["x"])
    rx1 = int(ledger["beta_rx_slots"]["rx1"]["x"])

    r_pt = recover_r_point_from_sig(R)
    lam = (px3 * inv(rx3, p)) % p
    lam1 = (px3 * inv(rx2, p)) % p

    facts = {
        "r_equals_rx2": R == rx2,
        "rx3_equals_rx2_beta": rx3 == (rx2 * BETA) % p,
        "rx1_equals_rx2_beta_sq": rx1 == (rx2 * BETA_SQ) % p,
        "R_point_recovered": r_pt is not None,
        "R_x_equals_r": r_pt[0] == R if r_pt else False,
        "Lambda_equals_Px3_over_rx3": lam == (LAMBDA % p),
        "Lambda1_equals_Px3_over_rx2": lam1 == (LAMBDA1 % p),
        "Lambda_over_Lambda1_eq_beta_sq": (lam * inv(lam1, p)) % p == BETA_SQ,
        "Px_slot_chain": px2 * BETA % p == px3,
        "map_p_to_n_r_offset": map_p_to_n(R) - map_p_to_n(px),
        "r_over_N": over_n(R),
        "s_over_N": over_n(S),
        "z_over_N": over_n(Z),
        "Px_over_p_matches_r_over_N_roof": Fraction(px, p) == Fraction(R, N),
    }
    return facts


def field_rsz_comparisons(ledger: dict) -> list[dict]:
    """Document exact / offset relationships — not claiming equality."""
    rows: list[dict] = []
    primary = ledger["field_native_primary"]["branches"]["p_minus_y"]
    fc = primary["field_courtroom"]
    res_num = int(fc["residue_over_p2"]["numerator"])
    pair_num = int(fc["P_pair"]["numerator"])

    pairs = [
        ("r mod p", R % p, "Px mod p", int(ledger["pubkey"]["Px"]) % p),
        ("r mod N", R % N, "map_p_to_n(Px)", map_p_to_n(int(ledger["pubkey"]["Px"]))),
        ("r − map_p_to_n(Px)", (R - map_p_to_n(int(ledger["pubkey"]["Px"]))) % N, None, None),
        ("residue_num mod N", res_num % N, "z mod N", Z % N),
        ("residue_num mod p", res_num % p, "r mod p", R % p),
        ("P_pair_num mod N", pair_num % N, "r mod N", R % N),
        ("carry_y", primary["carry_p_to_N"]["carry"], "carry on rx2/pmy",
         ledger["beta_rx_slots"]["rx2"]["branches"]["p_minus_y"]["carry_p_to_N"]["carry"]),
    ]
    for a_name, a_val, b_name, b_val in pairs:
        row = {"a": a_name, "a_val": str(a_val)}
        if b_name:
            row["b"] = b_name
            row["b_val"] = str(b_val)
            row["equal"] = a_val == b_val
            if isinstance(a_val, int) and isinstance(b_val, int):
                row["diff_mod_256"] = (a_val - b_val) % (1 << 256)
        rows.append(row)
    return rows


def classify_d(d: int, lo: int, hi: int, mirror_lo: int, mirror_hi: int) -> str:
    if lo <= d <= hi:
        return "d_window"
    if mirror_lo <= d <= mirror_hi:
        return "N_mirror"
    return "out_of_band"


def trial_k(
    cand: dict,
    *,
    lo: int,
    hi: int,
    mirror_lo: int,
    mirror_hi: int,
    tpx: int,
    tpy: int,
    tgt_packet,
) -> dict:
    k = cand["k"]
    kx = ec_x(k)
    nonce_ok = kx == R
    d = d_from_k(k) if nonce_ok else ((S * k - Z) * inv(R, N)) % N
    window = classify_d(d, lo, hi, mirror_lo, mirror_hi)

    row = {
        "label": cand["label"],
        "head": cand["head"],
        "branch": cand["branch"],
        "k": str(k),
        "nonce_x_eq_r": nonce_ok,
        "d": str(d),
        "d_bits": d.bit_length(),
        "window": window,
        "full_pass": False,
        "ec_match": False,
    }

    if nonce_ok:
        gs = gate_stack(
            d,
            puzzle=135,
            target_px=tpx,
            target_py=tpy,
            lo=lo,
            hi=hi,
            target_packet_p=tgt_packet,
        )
        row["full_pass"] = gs["pass"]
        row["ec_match"] = gs.get("ec_match", False)
        row["gates"] = gs["gates"]
    return row


def sanity_puzzle_100() -> dict:
    cache = load_rsz_cache()
    rec = cache.get(100)
    if not rec or not rec.get("k"):
        return {"ok": False, "reason": "no puzzle 100 k in cache"}

    catalog = load_catalog()
    e = catalog[100]
    tpx, tpy = pubkey_xy(e.public_key)
    k = int(rec["k"])
    r = int(rec["r"])
    s = int(rec["s"])
    z = int(rec["z"])

    kx = ec_x(k)
    nonce_ok = kx == r
    d = ((s * k - z) * inv(r, N)) % N
    try:
        dx, dy = ec_xy(d)
        ec_ok = dx == tpx and (dy == tpy or dy == (p - tpy) % p)
    except Exception:
        ec_ok = False
    in_range = e.range_min <= d <= e.range_max

    return {
        "ok": nonce_ok and ec_ok and d == e.private_key and in_range,
        "puzzle": 100,
        "k": str(k),
        "d_known": str(e.private_key),
        "d_derived": str(d),
        "nonce_ok": nonce_ok,
        "ec_ok": ec_ok,
        "in_range": in_range,
        "note": "pipeline check only — gate_stack RSZ step is P135-hardcoded",
    }


def render_md(data: dict) -> str:
    lines = [
        "# P135 RSZ courtroom",
        "",
        "Field-native witnesses under `/p` and `/p²` meet RSZ under `/N`.",
        "",
        "## Verdict",
        "",
        f"```text",
        data["verdict"],
        "```",
        "",
        "## Structural RSZ facts",
        "",
        "| fact | pass |",
        "|------|------|",
    ]
    for k, v in data["structural"].items():
        lines.append(f"| `{k}` | {v} |")

    lines += [
        "",
        "## RSZ roof (/N)",
        "",
        "```text",
        f"r/N = {data['rsz_roof']['r']}",
        f"s/N = {data['rsz_roof']['s']}",
        f"z/N = {data['rsz_roof']['z']}",
        "s*k ≡ z + r*d (mod N)",
        "```",
        "",
        "## Field vs RSZ comparisons (honest — mostly unequal)",
        "",
        "| a | b | equal |",
        "|---|---|-------|",
    ]
    for row in data["comparisons"]:
        if "b" in row:
            eq = "yes" if row["equal"] else "no"
            lines.append(f"| {row['a']} | {row['b']} | {eq} |")
        else:
            lines.append(f"| {row['a']} = {row['a_val']} | — | — |")

    lines += [
        "",
        "## k candidate trials",
        "",
        f"Candidates tested: **{data['trial_summary']['total']}**",
        f"Nonce gate `[k]G.x == r`: **{data['trial_summary']['nonce_pass']}**",
        f"Full gate stack pass: **{data['trial_summary']['full_pass']}**",
        "",
    ]
    if data["nonce_hits"]:
        lines.append("### Nonce hits (still not key unless EC+range pass)")
        lines.append("")
        for hit in data["nonce_hits"]:
            lines.append(f"- `{hit['label']}` → d={hit['d'][:32]}… window={hit['window']} ec={hit['ec_match']}")
        lines.append("")

    lines += [
        "## Sanity (puzzle 100 known k)",
        "",
        f"```json",
        json.dumps(data["sanity_100"], indent=2),
        "```",
        "",
        "## Ruling",
        "",
        data["ruling"],
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        raise SystemExit(f"missing ledger: {LEDGER_PATH}")

    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    catalog = load_catalog()
    e = catalog[135]
    tpx, tpy = pubkey_xy(e.public_key)
    tgt_packet = packet_p_from_xy(tpx, tpy, "p_minus_y")
    lo, hi = e.range_min, e.range_max
    mirror_lo = int(ledger["identity"]["N_mirror_lo"])
    mirror_hi = int(ledger["identity"]["N_mirror_hi"])

    structural = structural_facts(ledger)
    comparisons = field_rsz_comparisons(ledger)
    candidates = collect_k_candidates(ledger)

    trials = [
        trial_k(
            c,
            lo=lo,
            hi=hi,
            mirror_lo=mirror_lo,
            mirror_hi=mirror_hi,
            tpx=tpx,
            tpy=tpy,
            tgt_packet=tgt_packet,
        )
        for c in candidates
    ]
    nonce_hits = [t for t in trials if t["nonce_x_eq_r"]]
    full_pass = [t for t in trials if t["full_pass"]]

    sanity = sanity_puzzle_100()

    if full_pass:
        verdict = "UNEXPECTED: full gate pass — inspect immediately"
    elif nonce_hits:
        verdict = "Nonce hits without key recovery — RSZ lane open, no d yet"
    else:
        verdict = "0 nonce hits — field-native k map does not reach R point"

    ruling = (
        "Residue retained as witness only. RSZ is the open lane.\n"
        "Field-native scalars (map_p_to_n, floor pair, residue num) do not yield k "
        "with x([k]G)=r. Next: structural RSZ algebra (Λ bridges, rx slot packets) "
        "or external k search — not residue numerators."
    )

    payload = {
        "puzzle": 135,
        "courtroom": "RSZ meets field-native",
        "equation": "s*k ≡ z + r*d (mod N)",
        "rsz": {"r": str(R), "s": str(S), "z": str(Z)},
        "rsz_roof": {"r": over_n(R), "s": over_n(S), "z": over_n(Z)},
        "structural": structural,
        "comparisons": comparisons,
        "k_candidates": [{"label": c["label"], "k": str(c["k"])} for c in candidates],
        "trials": trials,
        "trial_summary": {
            "total": len(trials),
            "nonce_pass": len(nonce_hits),
            "full_pass": len(full_pass),
            "d_window_from_nonce": sum(1 for t in nonce_hits if t["window"] == "d_window"),
            "N_mirror_from_nonce": sum(1 for t in nonce_hits if t["window"] == "N_mirror"),
        },
        "nonce_hits": nonce_hits,
        "full_pass_hits": full_pass,
        "sanity_100": sanity,
        "verdict": verdict,
        "ruling": ruling,
        "residue_lane": "closed — witness only",
    }

    json_path = OUT / "rsz_courtroom.json"
    md_path = OUT / "rsz_courtroom.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_md(payload), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Candidates: {len(trials)}  nonce_pass: {len(nonce_hits)}  full_pass: {len(full_pass)}")
    print(f"Sanity P100: {sanity.get('ok')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
