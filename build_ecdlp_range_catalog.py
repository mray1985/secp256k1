#!/usr/bin/env python3
"""
Full ECDLP-range catalog for all puzzles 1–160.

For each puzzle bit-window [2^(n-1), 2^n):
  - p−y branch (primary) and y branch
  - N-side shadows (map_p_to_n, packet·N, N−d when solved)
  - β slots, defect shell, e_lo / e_hinge / e_hi warps
  - on-curve + [d]G verify when solved
  - bit-length checks: does each quantity sit in / near the puzzle window?

Writes ONLY under ARCHIVE/briefcase/ecdlp_range/
Does not overwrite other briefcase trees.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "ecdlp_range"

B = (1 << 32) + 977
B4 = pow(B, 4)
CORRECTION = Decimal(DELTA) / Decimal(B4)
HINGE = Decimal("0.58496250072115618145373894394781650875981440769248106045575265")
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def bitlen(x: int) -> int:
    return x.bit_length() if x > 0 else 0


def in_window(x: int, lo: int, hi: int) -> bool:
    return lo <= x <= hi


def d_window(n: int) -> tuple[int, int]:
    """Puzzle scalar window [2^(n-1), 2^n - 1]."""
    return 1 << (n - 1), (1 << n) - 1


def n_mirror_window(n: int) -> tuple[int, int]:
    """
    N-side mirror of the puzzle bit-window.

    d ∈ [2^(n-1), 2^n)  maps under d ↦ N−d (order complement) to
        N−d ∈ (N−2^n, N−2^(n-1)]

    Classified as the closed interval used for checks:
        [N − 2^n + 1, N − 2^(n-1)]
    reported bounds (user wording): N−2^n  ..  N−2^(n-1)

    Floor/height switch: low d → high N−d, high d → low N−d.
    """
    # inclusive classification bounds matching exact N-d for d in [2^(n-1), 2^n-1]
    lo = N - (1 << n) + 1
    hi = N - (1 << (n - 1))
    return lo, hi


def near_d_window(x: int, n: int) -> dict:
    """Is x in the puzzle d bit-window?"""
    lo, hi = d_window(n)
    bl = bitlen(x)
    return {
        "value": str(x),
        "bit_length": bl,
        "window": "d_range",
        "lo": str(lo),
        "hi": str(hi),
        "lo_hex": hex(lo),
        "hi_hex": hex(hi),
        "in_range": in_window(x, lo, hi),
        "bit_length_in_band": (n - 1) <= bl <= n or (n == 1 and x == 1),
        "band": f"[2^{n-1}, 2^{n})",
    }


def near_n_mirror_window(x: int, n: int) -> dict:
    """Is x in the N-side mirror window [N-2^n+1, N-2^(n-1)]?"""
    lo, hi = n_mirror_window(n)
    # also report the open-style labels N-2^n and N-2^(n-1)
    label_lo = N - (1 << n)
    label_hi = N - (1 << (n - 1))
    bl = bitlen(x)
    return {
        "value": str(x),
        "bit_length": bl,
        "window": "N_mirror",
        "lo": str(lo),
        "hi": str(hi),
        "lo_hex": hex(lo),
        "hi_hex": hex(hi),
        "label_lo_N_minus_2_n": str(label_lo),
        "label_hi_N_minus_2_n_minus_1": str(label_hi),
        "band": f"[N-2^{n}+1, N-2^{n-1}]  (labels N-2^{n} .. N-2^{n-1})",
        "in_range": in_window(x, lo, hi),
        "height_floor_switched": True,
        "note": "low d ↔ high N-d; high d ↔ low N-d",
    }


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def packet(px: int, y_digits: int) -> Decimal:
    return Decimal(f"{px}.{y_digits}")


def branch_block(px: int, y_digits: int, label: str, n: int) -> dict:
    # Correct silhouette: stitch x.y as decimal placement (~156 digits), then normalize.
    # Do NOT promote stitch to a giant int first.
    s_px, s_y = str(px), str(y_digits)
    stitched_s = f"{s_px}.{s_y}"
    pkt = Decimal(stitched_s)
    two256 = Decimal(1 << 256)
    pkt_over_2_256 = pkt / two256  # x.y / 2^256  (fixed binary lens)
    pkt_p = pkt / Decimal(p)  # x.y / p        (packet / field lens)
    floor_p = int(pkt_p * Decimal(p))
    floor_n = int(pkt_p * Decimal(N))
    floor_delta = int(pkt_p * Decimal(DELTA))
    floor_b4 = int(pkt_p * Decimal(B4))
    int_only = map_p_to_n(px)
    off_by = floor_n - int_only
    ratio = Decimal(floor_delta) / Decimal(floor_b4) if floor_b4 else None
    # hex stitch: 0x.<Hx><Hy> / 2^512
    H = f"{px:064x}{y_digits:064x}"
    hex_frac = Decimal(int(H, 16)) / Decimal(1 << 512)
    return {
        "branch": label,
        "silhouette": "decimal_stitch_then_normalize",
        "y_digits": str(y_digits),
        "stitched_decimal_string": stitched_s,
        "integer_digits": len(s_px),
        "fractional_digits": len(s_y),
        "total_decimal_digits": len(s_px) + len(s_y),
        "packet": str(pkt),
        "x_y_over_2_256": format(pkt_over_2_256, "f"),
        "packet_p": format(pkt_p, "f"),
        "hex_stitch_over_2_512": format(hex_frac, "f"),
        "hex_stitch": f"0x.{H}",
        "floor_packet_times_p": str(floor_p),
        "floor_packet_times_N": str(floor_n),
        "floor_packet_times_DELTA": str(floor_delta),
        "floor_packet_times_B4": str(floor_b4),
        "map_p_to_n_Px": str(int_only),
        "off_by_map_p_to_n": off_by,
        "shell_ratio": format(ratio, "f") if ratio is not None else None,
        "shell_ratio_minus_correction": (
            format(ratio - CORRECTION, "f") if ratio is not None else None
        ),
        "matches_Px": floor_p == px,
        # N-mirror window classification (not d-window)
        "floor_packet_N_in_N_mirror": near_n_mirror_window(floor_n, n),
        "map_p_to_n_Px_in_N_mirror": near_n_mirror_window(int_only, n),
    }


def beta_slots(px: int) -> dict:
    px3 = px
    px2 = (px * inv(BETA, p)) % p
    px1 = (px * inv(BETA_SQ, p)) % p
    return {
        "Px1": str(px1),
        "Px2": str(px2),
        "Px3": str(px3),
        "Px2_times_beta_eq_Px3": (px2 * BETA) % p == px3,
        "Px1_times_beta_sq_eq_Px3": (px1 * BETA_SQ) % p == px3,
    }


def hinge_powers(px: int, py: int, n: int) -> dict:
    pmy = (p - py) % p
    out = {}
    for name, e in (
        ("e_lo", (n - 1) / 256.0),
        ("e_hinge", (n - 1 + float(HINGE)) / 256.0),
        ("e_hi", n / 256.0),
    ):
        def pw(v: int) -> float:
            v = v % p
            return ((v if v else 1) / float(p)) ** e

        pkt = float(f"{px}.{pmy}") / float(p)
        out[name] = {
            "exponent": e,
            "Px_pow": pw(px),
            "Py_pow": pw(py),
            "p_minus_y_pow": pw(pmy),
            "packet_pow": pkt ** e,
            "Px_minus_Gx_pow": pw((px - GX) % p),
        }
    return out


def verify_dG(d: int, px: int, py: int) -> dict:
    dN = d % N
    if dN == 0:
        return {"ok": False, "reason": "d ≡ 0 mod N"}
    sk = SigningKey.from_secret_exponent(dN, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    dx, dy = pt.x(), pt.y()
    ok = dx == px and (dy == py or dy == (p - py) % p)
    return {
        "ok": ok,
        "d_mod_N": str(dN),
        "computed_Px": str(dx),
        "computed_Py": str(dy),
        "matches_pubkey": ok,
        "bit_length_d": bitlen(d),
    }


def process_puzzle(n: int, e) -> dict:
    lo, hi = e.range_min, e.range_max
    # ECDLP statement
    rec: dict = {
        "puzzle": n,
        "ecdlp": {
            "statement": f"find d in [{lo}, {hi}] with [d]G = P",
            "range_lo": str(lo),
            "range_hi": str(hi),
            "range_lo_hex": hex(lo),
            "range_hi_hex": hex(hi),
            "d_window": f"[2^{n-1}, 2^{n})",
            "N_mirror": f"[N-2^{n}+1, N-2^{n-1}]",
            "bit_band": [n - 1, n],
            "width": str(hi - lo + 1),
            "width_bits": bitlen(hi - lo + 1),
        },
        "identity": {
            "address": e.address,
            "hash160": e.hash160,
            "btc_value": e.btc_value,
            "solved": e.solved,
            "has_pubkey": bool(e.public_key),
            "solve_date": e.solve_date or None,
        },
    }

    if not e.public_key:
        rec["status"] = "NO_PUBKEY"
        rec["note"] = (
            "ECDLP is address/hash160 only until spend leaks P. "
            "Cannot run coordinate / N-y / packet stack."
        )
        rec["gates_available"] = ["range_only_when_candidate_d"]
        return rec

    px, py = pubkey_xy(e.public_key)
    pmy = (p - py) % p
    on_curve = (pow(py, 2, p) - (pow(px, 3, p) + 7)) % p == 0

    rec["status"] = "SOLVED" if e.solved and e.private_key > 0 else "UNSOLVED_PUBKEY"
    rec["pubkey"] = {
        "compressed": e.public_key,
        "Px": str(px),
        "Py": str(py),
        "p_minus_y": str(pmy),
        "on_curve": on_curve,
        "Px_bit_length": bitlen(px),
        "Py_bit_length": bitlen(py),
        "Px_in_field_not_range": True,  # coordinates are mod p, not in d-range
        "note": "Px,Py live in Fp (~256-bit), not in puzzle d bit-window",
    }

    # both y branches meticulously
    rec["branch_y"] = branch_block(px, py, "y", n)
    rec["branch_p_minus_y"] = branch_block(px, pmy, "p_minus_y", n)
    rec["primary_branch"] = "p_minus_y"

    rec["beta_slots"] = beta_slots(px)
    rec["hinge_power_slices"] = hinge_powers(px, py, n)

    # N-mirror window for this puzzle bit-height
    n_lo, n_hi = n_mirror_window(n)
    rec["N_mirror_window"] = {
        "lo": str(n_lo),
        "hi": str(n_hi),
        "lo_hex": hex(n_lo),
        "hi_hex": hex(n_hi),
        "label": f"[N-2^{n}+1, N-2^{n-1}]",
        "user_labels": f"N-2^{n} .. N-2^{n-1}",
        "height_floor_switch": (
            "d-range floor 2^(n-1) ↔ N-mirror height N-2^(n-1); "
            "d-range height 2^n ↔ N-mirror floor N-2^n"
        ),
        "map": {
            "d_floor": str(1 << (n - 1)),
            "d_ceil": str(1 << n),
            "N_minus_d_floor_maps_to": str(N - (1 << (n - 1))),
            "N_minus_d_ceil_maps_to": str(N - (1 << n)),
        },
    }

    # N-side explicit block — classify in N-mirror window
    m_px = map_p_to_n(px)
    m_py = map_p_to_n(py)
    m_pmy = map_p_to_n(pmy)
    rec["N_side"] = {
        "map_p_to_n_Px": str(m_px),
        "map_p_to_n_Py": str(m_py),
        "map_p_to_n_p_minus_y": str(m_pmy),
        "map_p_to_n_Px_in_N_mirror": near_n_mirror_window(m_px, n),
        "map_p_to_n_Py_in_N_mirror": near_n_mirror_window(m_py, n),
        "map_p_to_n_p_minus_y_in_N_mirror": near_n_mirror_window(m_pmy, n),
        "DELTA": str(DELTA),
        "B": str(B),
        "B4": str(B4),
        "correction": format(CORRECTION, "f"),
        "note": (
            "N-side quantities classified in N-mirror window "
            "[N-2^n+1, N-2^(n-1)], not the d-window"
        ),
    }

    # Solved: full ECDLP closure + N-d in N-mirror window
    if e.solved and e.private_key > 0:
        d = e.private_key
        n_minus_d = (N - d) % N  # N - d in 0..N-1
        rec["scalar"] = {
            "d": str(d),
            "d_hex": hex(d),
            "d_bit_length": bitlen(d),
            "d_in_puzzle_range": in_window(d, lo, hi),
            "d_bit_band_ok": (n - 1) <= bitlen(d) <= n or (n == 1 and d == 1),
            "scalar_position": (d - lo) / (hi - lo + 1),
            "d_range_check": near_d_window(d, n),
            "N_minus_d": str(n_minus_d),
            "N_minus_d_hex": hex(n_minus_d),
            "N_minus_d_bit_length": bitlen(n_minus_d),
            "N_minus_d_in_N_mirror": near_n_mirror_window(n_minus_d, n),
            "N_minus_d_note": (
                "N-d lives in the N-mirror of the puzzle bit-window: "
                "[N-2^n+1, N-2^(n-1)]. Floor/height switched vs d."
            ),
            # position within N-mirror (0 at high end / low d, 1 at low end / high d)
            "N_mirror_position": (
                (n_hi - n_minus_d) / (n_hi - n_lo) if n_hi > n_lo else None
            ),
        }
        rec["ecdlp_verify"] = verify_dG(d, px, py)
        # powered priv norms at e_lo for filter scoring
        e_lo = (n - 1) / 256.0
        rec["e_lo_priv_norms"] = {
            "exponent": e_lo,
            "d_over_2_256_pow": (d / float(1 << 256)) ** e_lo,
            "d_over_2_n_pow": (d / float(1 << n)) ** e_lo,
            "d_over_2_n_minus_1_pow": (d / float(1 << (n - 1))) ** e_lo,
        }
        # distance e_lo Px_pow vs d_over_2_256_pow (filter score, not predictor)
        px_pow = rec["hinge_power_slices"]["e_lo"]["Px_pow"]
        rec["e_lo_filter_distance"] = abs(
            px_pow - rec["e_lo_priv_norms"]["d_over_2_256_pow"]
        )
    else:
        rec["scalar"] = {
            "d": None,
            "note": "unknown — ECDLP open in bit-window",
        }
        rec["ecdlp_verify"] = {"ok": None, "reason": "d unknown"}

    # Consistency flags
    rec["consistency"] = {
        "on_curve": on_curve,
        "beta_ok": rec["beta_slots"]["Px2_times_beta_eq_Px3"],
        "packet_y_matches_Px": rec["branch_y"]["matches_Px"],
        "packet_pmy_matches_Px": rec["branch_p_minus_y"]["matches_Px"],
        "off_by_y": rec["branch_y"]["off_by_map_p_to_n"],
        "off_by_pmy": rec["branch_p_minus_y"]["off_by_map_p_to_n"],
        "shell_ok_pmy": (
            abs(Decimal(rec["branch_p_minus_y"]["shell_ratio_minus_correction"] or "1"))
            < Decimal("1e-8")
        ),
        "ecdlp_closed": rec["ecdlp_verify"].get("ok") is True,
        "d_in_bit_range": (
            rec.get("scalar", {}).get("d_in_puzzle_range")
            if rec.get("scalar", {}).get("d")
            else None
        ),
        "N_minus_d_in_N_mirror": (
            rec.get("scalar", {}).get("N_minus_d_in_N_mirror", {}).get("in_range")
            if rec.get("scalar", {}).get("d")
            else None
        ),
        "map_p_to_n_Px_in_N_mirror": rec["N_side"]["map_p_to_n_Px_in_N_mirror"][
            "in_range"
        ],
        "floor_packet_N_pmy_in_N_mirror": rec["branch_p_minus_y"][
            "floor_packet_N_in_N_mirror"
        ]["in_range"],
    }
    return rec


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    rows = []
    for n in range(1, 161):
        rows.append(process_puzzle(n, catalog[n]))
        if n % 20 == 0:
            print(f"  processed {n}/160")

    # summaries
    n_pubkey = sum(1 for r in rows if r["identity"]["has_pubkey"])
    n_solved = sum(1 for r in rows if r["status"] == "SOLVED")
    n_closed = sum(1 for r in rows if r.get("consistency", {}).get("ecdlp_closed"))
    n_beta = sum(1 for r in rows if r.get("consistency", {}).get("beta_ok"))
    n_shell = sum(1 for r in rows if r.get("consistency", {}).get("shell_ok_pmy"))
    n_d_in_range = sum(
        1 for r in rows if r.get("consistency", {}).get("d_in_bit_range") is True
    )
    n_Nd_in_mirror = sum(
        1
        for r in rows
        if r.get("consistency", {}).get("N_minus_d_in_N_mirror") is True
    )
    n_map_in_mirror = sum(
        1
        for r in rows
        if r.get("consistency", {}).get("map_p_to_n_Px_in_N_mirror") is True
    )
    n_floorN_in_mirror = sum(
        1
        for r in rows
        if r.get("consistency", {}).get("floor_packet_N_pmy_in_N_mirror") is True
    )

    summary = {
        "puzzles": 160,
        "with_pubkey": n_pubkey,
        "solved": n_solved,
        "ecdlp_closed_dG": n_closed,
        "beta_ok": n_beta,
        "shell_ok_pmy": n_shell,
        "d_in_d_window": n_d_in_range,
        "N_minus_d_in_N_mirror": n_Nd_in_mirror,
        "map_p_to_n_Px_in_N_mirror": n_map_in_mirror,
        "floor_packet_N_pmy_in_N_mirror": n_floorN_in_mirror,
        "primary_branch": "p_minus_y",
        "two_windows": {
            "d_window": "[2^(n-1), 2^n)",
            "N_mirror": "[N-2^n+1, N-2^(n-1)]  (labels N-2^n .. N-2^(n-1))",
            "floor_height_switch": (
                "d floor 2^(n-1) ↔ N-mirror height N-2^(n-1); "
                "d height 2^n ↔ N-mirror floor N-2^n"
            ),
        },
        "bit_range_rule": (
            "d lives in d-window [2^(n-1), 2^n). "
            "N-d and N-side shadows are classified in the N-mirror "
            "[N-2^n+1, N-2^(n-1)] where floor/height are switched."
        ),
        "ruling": (
            "Full stack per puzzle with correct N-mirror classification. "
            "N-d must sit in N-mirror when d sits in d-window."
        ),
    }

    payload = {
        "exhibit": "ecdlp_range_catalog",
        "location": "ARCHIVE/briefcase/ecdlp_range/",
        "summary": summary,
        "puzzles": rows,
    }

    (OUT / "ecdlp_range_catalog.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    # per-puzzle markdown index (compact)
    lines = [
        "# ECDLP range catalog — all puzzles",
        "",
        "Primary branch: **p−y**. N-side shadows included. Solved puzzles fully close `[d]G = P`.",
        "",
        "## Two windows (floor/height switch)",
        "",
        "```text",
        "d-window:     [2^(n-1), 2^n)",
        "N-mirror:     [N-2^n+1, N-2^(n-1)]   labels: N-2^n .. N-2^(n-1)",
        "",
        "d floor  2^(n-1)  ↔  N-mirror height  N-2^(n-1)",
        "d height 2^n      ↔  N-mirror floor   N-2^n",
        "",
        "N-d for solved d must sit in N-mirror.",
        "map_p_to_n / floor(packet·N) classified in N-mirror (may or may not land).",
        "```",
        "",
        "## Summary",
        "",
        f"- pubkey puzzles: **{n_pubkey}**/160",
        f"- solved: **{n_solved}**",
        f"- ECDLP closed (`[d]G`): **{n_closed}**/{n_solved}",
        f"- beta ok: **{n_beta}**/{n_pubkey}",
        f"- shell ok (p−y): **{n_shell}**/{n_pubkey}",
        f"- d in d-window: **{n_d_in_range}**/{n_solved}",
        f"- N−d in N-mirror: **{n_Nd_in_mirror}**/{n_solved}",
        f"- map_p_to_n(Px) in N-mirror: **{n_map_in_mirror}**/{n_pubkey}",
        f"- floor(packet·N) p−y in N-mirror: **{n_floorN_in_mirror}**/{n_pubkey}",
        "",
        "## Per-puzzle",
        "",
        "| P | status | d in d-win | N−d in N-mir | [d]G | beta | shell | off_by | mapN in mir | floorN in mir |",
        "|---|--------|------------|--------------|------|------|-------|--------|-------------|---------------|",
    ]
    for r in rows:
        st = r["status"]
        if st == "NO_PUBKEY":
            lines.append(
                f"| {r['puzzle']} | NO_PUBKEY | — | — | — | — | — | — | — | — |"
            )
            continue
        c = r["consistency"]
        lines.append(
            f"| {r['puzzle']} | {st} | "
            f"{c.get('d_in_bit_range')} | {c.get('N_minus_d_in_N_mirror')} | "
            f"{c.get('ecdlp_closed')} | {c.get('beta_ok')} | {c.get('shell_ok_pmy')} | "
            f"{c.get('off_by_pmy')} | {c.get('map_p_to_n_Px_in_N_mirror')} | "
            f"{c.get('floor_packet_N_pmy_in_N_mirror')} |"
        )

    lines.extend([
        "",
        "## Stack applied per pubkey puzzle",
        "",
        "```text",
        "1. ECDLP statement in d-window [2^(n-1), 2^n)",
        "2. N-mirror window [N-2^n+1, N-2^(n-1)]",
        "3. Px, Py, p−y, on-curve",
        "4. branch y + branch p−y packets",
        "5. map_p_to_n / floor(packet·N) / off_by — classified in N-mirror",
        "6. defect shell",
        "7. beta slots",
        "8. e_lo / e_hinge / e_hi warps",
        "9. if solved: d in d-window, N−d in N-mirror, [d]G verify",
        "```",
        "",
        "Rebuild: `python build_ecdlp_range_catalog.py`",
        "",
        "Judge Popcorn: **d docks in the low bit slip; N−d docks in the mirrored "
        "high slip. Floor and height trade places across the order.**",
        "",
    ])

    (OUT / "ecdlp_range_catalog.md").write_text("\n".join(lines), encoding="utf-8")

    # also write individual JSON files per puzzle for briefcase browsing
    per = OUT / "puzzles"
    per.mkdir(exist_ok=True)
    for r in rows:
        n = r["puzzle"]
        (per / f"puzzle_{n:03d}_ecdlp.json").write_text(
            json.dumps(r, indent=2), encoding="utf-8"
        )

    (OUT / "README.md").write_text(
        "\n".join([
            "# briefcase/ecdlp_range",
            "",
            "Meticulous ECDLP-range stack for all 160 puzzles.",
            "",
            "| Path | Purpose |",
            "|------|---------|",
            "| `ecdlp_range_catalog.md` / `.json` | full index + summary |",
            "| `puzzles/puzzle_NNN_ecdlp.json` | per-puzzle full stack |",
            "",
            "Primary branch: **p−y**. N-side included. Solved puzzles close `[d]G`.",
            "",
            "```text",
            "python build_ecdlp_range_catalog.py",
            "```",
            "",
        ]),
        encoding="utf-8",
    )

    print("summary:", json.dumps(summary, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
