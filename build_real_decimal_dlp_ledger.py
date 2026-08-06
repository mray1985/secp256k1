#!/usr/bin/env python3
"""
Real-decimal DLP embedding ledger.

Writes ONLY under ARCHIVE/briefcase/real/ — does not overwrite existing exhibits.

DLP_decimal(d) = Decimal(str(Px) + "." + str(Y)) / p
  Y ∈ {Py, p−Py}  (both branches recorded)

This is a fingerprint / filter / shadow table — not a real-log inversion of ECC.
Accept candidates only if [d]G verifies.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path
from statistics import mean, pstdev

from build_complexity_operations_ledger import N, p, y_roots
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog

getcontext().prec = 120

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "ARCHIVE" / "briefcase" / "real"
DELTA = p - N
TWO256 = 1 << 256
LOG2_E = math.log2(math.e)

# P135 target (p−y branch) — verified coordinate_packet_shadow exhibit
P135_TARGET_PACKET_P = Decimal(
    "0.07954633649946046255450180288304075379977001785594624365740374798873"
    "7825607683797376362420847353351108638651635660059457338972369055727427"
    "831496239538405074"
)
P135_MIDPOINT_FRAC = Decimal("0.584962500721156181453738943947816508759814407692481060455752654541")


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def make_packet(px: int, y_digits: int) -> Decimal:
    """Decimal(str(Px) + '.' + str(Y)) — real-decimal point fingerprint."""
    return Decimal(f"{px}.{y_digits}")


def packet_row(px: int, py: int, branch: str) -> dict:
    y_digits = py if branch == "y" else (p - py) % p
    packet = make_packet(px, y_digits)
    packet_p = packet / Decimal(p)
    packet_n = packet / Decimal(N)
    packet_2 = packet / Decimal(TWO256)
    floor_p = int(packet_p * Decimal(p))
    floor_n = int(packet_p * Decimal(N))
    floor_delta = int(packet_p * Decimal(DELTA))
    int_only = map_p_to_n(px)
    # real log2 of packet_p (fingerprint only)
    log2_packet = float(packet_p.ln() / Decimal(math.log(2)))
    frac_n = packet_p * Decimal(N) - floor_n
    return {
        "branch": branch,
        "y_digits": str(y_digits),
        "packet": str(packet),
        "packet_p": format(packet_p, "f"),
        "packet_N": format(packet_n, "f"),
        "packet_2_256": format(packet_2, "f"),
        "floor_packet_p_times_p": str(floor_p),
        "floor_packet_p_times_N": str(floor_n),
        "floor_packet_p_times_DELTA": str(floor_delta),
        "map_p_to_n_Px": str(int_only),
        "off_by_map_p_to_n": floor_n - int_only,
        "frac_packet_p_times_N": format(frac_n, "f"),
        "log2_packet_p": log2_packet,
        "matches_Px_integer": floor_p == px,
    }


def build_entry(n: int, d: int | None, px: int, py: int, role: str) -> dict:
    rows = {
        "y": packet_row(px, py, "y"),
        "p_minus_y": packet_row(px, py, "p_minus_y"),
    }
    # prefer p−y for P135-style target compare; also record y
    primary = rows["p_minus_y"]
    entry: dict = {
        "puzzle": n,
        "role": role,
        "d": str(d) if d else None,
        "Px": str(px),
        "Py": str(py),
        "packets": rows,
        "primary_branch": "p_minus_y",
    }
    if d and d > 0:
        log2_d = math.log2(d)
        entry["log2_d"] = log2_d
        entry["scalar_minus_real_log"] = log2_d - primary["log2_packet_p"]
        entry["scalar_over_real_log"] = log2_d / primary["log2_packet_p"]
        # distance of log2(d) fractional part from n.58496… hinge
        frac_d = log2_d - math.floor(log2_d)
        entry["frac_log2_d"] = frac_d
        entry["dist_to_hinge_58496"] = abs(frac_d - float(P135_MIDPOINT_FRAC))
        # distance of packet_p from 0.5 midpoint
        pp = Decimal(primary["packet_p"])
        entry["dist_packet_p_from_half"] = format(abs(pp - Decimal("0.5")), "f")
    # filter: does primary packet_p match P135 target?
    entry["matches_P135_target_packet_p"] = (
        Decimal(primary["packet_p"]) == P135_TARGET_PACKET_P
        or primary["packet_p"].startswith(
            "0.079546336499460462554501802883040753799770017855946243657403747988737825607683"
        )
    )
    return entry


def correlation_summary(entries: list[dict]) -> dict:
    solved = [e for e in entries if e.get("log2_d") is not None]
    if len(solved) < 2:
        return {"n": len(solved)}
    diffs = [e["scalar_minus_real_log"] for e in solved]
    ratios = [e["scalar_over_real_log"] for e in solved]
    hinges = [e["dist_to_hinge_58496"] for e in solved]
    offbys = [e["packets"]["p_minus_y"]["off_by_map_p_to_n"] for e in solved]
    return {
        "n_solved": len(solved),
        "scalar_minus_real_log": {
            "mean": mean(diffs),
            "stdev": pstdev(diffs),
            "min": min(diffs),
            "max": max(diffs),
        },
        "scalar_over_real_log": {
            "mean": mean(ratios),
            "stdev": pstdev(ratios),
            "min": min(ratios),
            "max": max(ratios),
        },
        "dist_to_hinge_58496": {
            "mean": mean(hinges),
            "stdev": pstdev(hinges),
            "min": min(hinges),
            "max": max(hinges),
        },
        "off_by_map_p_to_n_counts": {
            str(k): sum(1 for x in offbys if x == k) for k in sorted(set(offbys))
        },
        "ruling": (
            "If stdev of (scalar_log - real_log) is large vs mean structure, "
            "real-decimal log is fingerprint-only. Cluster would open a heuristic lane."
        ),
    }


def render_md(entries: list[dict], summary: dict) -> str:
    lines = [
        "# Real-decimal DLP embedding ledger",
        "",
        "Location: `ARCHIVE/briefcase/real/` (new tree — does not overwrite prior exhibits).",
        "",
        "## Ruling",
        "",
        "```text",
        "DLP_decimal(d) = Decimal(str(Px) + '.' + str(Y)) / p",
        "Y ∈ {Py, p−Py}",
        "",
        "Forward:  d → [d]G → Px,Py → packet → packet/p",
        "Easy reverse: packet/p → Px,Py",
        "Hard reverse: Px,Py → d   (still ECDLP)",
        "",
        "Not homomorphic:",
        "  packet([a+b]G) ≠ packet([a]G) + packet([b]G)",
        "  log(packet([d]G)) ≠ d",
        "```",
        "",
        "Use as fingerprint, filter, p/N shadow table, or BSGS index —",
        "only accept if `[d]G` verifies.",
        "",
        "## P135 target (`p_minus_y` branch)",
        "",
        f"`packet_p` = `{P135_TARGET_PACKET_P}`",
        "",
        "Filter: candidate → decimal packet → ×p → integer part == Px?",
        "",
        "## Correlation summary (solved controls)",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
        "## Rows",
        "",
    ]
    for e in entries:
        lines.append(f"### Puzzle {e['puzzle']} ({e['role']})")
        lines.append("")
        if e.get("d"):
            lines.append(f"- **d** = `{e['d']}`")
            lines.append(f"- **log2(d)** = `{e['log2_d']}`")
            lines.append(
                f"- **scalar − real log** = `{e['scalar_minus_real_log']}`"
            )
            lines.append(
                f"- **dist to hinge .58496…** = `{e['dist_to_hinge_58496']}`"
            )
        lines.append(f"- **Px** = `{e['Px']}`")
        lines.append(f"- **Py** = `{e['Py']}`")
        for branch, row in e["packets"].items():
            lines.append(f"- **branch `{branch}`**")
            lines.append(f"  - packet_p = `{row['packet_p']}`")
            lines.append(f"  - floor(packet_p·N) = `{row['floor_packet_p_times_N']}`")
            lines.append(f"  - map_p_to_n(Px) = `{row['map_p_to_n_Px']}`")
            lines.append(f"  - off_by_map_p_to_n = `{row['off_by_map_p_to_n']}`")
            lines.append(
                f"  - floor(packet_p·Δ) = `{row['floor_packet_p_times_DELTA']}`"
            )
            lines.append(f"  - matches_Px = `{row['matches_Px_integer']}`")
        lines.append(
            f"- **matches P135 target packet_p** = `{e['matches_P135_target_packet_p']}`"
        )
        lines.append("")
    lines.append("## Bridge to RSZ lock")
    lines.append("")
    lines.append(
        "Find a scalar-side operation that predicts the P135 decimal packet, "
        "then convert the predicted point back through EC verification. "
        "Decimal microscope alone does not open the lock."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    entries: list[dict] = []

    for n in range(1, 161):
        e = catalog[n]
        if e.solved and e.public_key:
            px, py = pubkey_xy(e.public_key)
            entries.append(build_entry(n, e.private_key, px, py, "solved_control"))
        elif n == 135 and e.public_key:
            px, py = pubkey_xy(e.public_key)
            entries.append(build_entry(n, None, px, py, "P135_target"))
        elif e.public_key and not e.solved:
            # pubkey-exposed unsolved — fingerprint only, no d
            px, py = pubkey_xy(e.public_key)
            entries.append(build_entry(n, None, px, py, "unsolved_pubkey"))

    summary = correlation_summary(entries)
    payload = {
        "exhibit": "real_decimal_dlp",
        "location": "ARCHIVE/briefcase/real/",
        "overwrites_prior_exhibits": False,
        "formula": "DLP_decimal(d) = Decimal(str(Px)+'.'+str(Y))/p",
        "branches": ["y", "p_minus_y"],
        "P135_target_packet_p": str(P135_TARGET_PACKET_P),
        "DELTA": str(DELTA),
        "correlation": summary,
        "entries": entries,
    }

    (OUT_DIR / "README.md").write_text(
        "\n".join(
            [
                "# briefcase/real — real-decimal DLP embedding",
                "",
                "New tree. Does **not** overwrite `exhibit_coordinate_packet_shadow.*` or puzzle ledgers.",
                "",
                "| File | Purpose |",
                "|------|---------|",
                "| `decimal_dlp_ledger.md` | Human ledger + ruling |",
                "| `decimal_dlp_ledger.json` | Full rows + correlation |",
                "",
                "Rebuild: `python build_real_decimal_dlp_ledger.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "decimal_dlp_ledger.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "decimal_dlp_ledger.md").write_text(
        render_md(entries, summary), encoding="utf-8"
    )

    solved_n = sum(1 for e in entries if e["role"] == "solved_control")
    print(f"real/: {len(entries)} rows ({solved_n} solved controls + targets)")
    print(f"  {OUT_DIR / 'decimal_dlp_ledger.md'}")
    if summary.get("scalar_minus_real_log"):
        s = summary["scalar_minus_real_log"]
        print(
            f"  scalar-real log: mean={s['mean']:.4f} stdev={s['stdev']:.4f} "
            f"range=[{s['min']:.4f},{s['max']:.4f}]"
        )
        print(f"  off_by counts: {summary['off_by_map_p_to_n_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
