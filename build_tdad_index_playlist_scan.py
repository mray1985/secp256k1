#!/usr/bin/env python3
"""
TDAD index playlist scan — fixed rhythm [3,2,1,2], variable index path.

Extract index constraints from solved TDAD paths (thePattern.txt + double_and_add).
Do NOT enumerate operator combinations — operators are low-entropy.

For P135: rhythm likely 10 cycles × 4 = 40 terms; secret is index playlist.

Writes: ARCHIVE/briefcase/The Real Decimal/exhibit_tdad_index_playlist_scan.{md,json}
        ARCHIVE/briefcase/The Real Decimal/P135/tdad_index_playlist_scan.{md,json}
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

from build_complexity_operations_ledger import N
from puzzle_catalog import load_catalog

ROOT = Path(__file__).resolve().parent
PATTERN_TXT = ROOT / "02_Research" / "notes" / "thePattern.txt"
TDAD_TXT = ROOT / "02_Research" / "notes" / "double_and_add.txt"
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal"
P135_OUT = OUT / "P135"

TDAD_CYCLE = [3, 2, 1, 2]
OP_NAME = {3: "triple", 2: "double", 1: "add"}
TERM_CI_RE = re.compile(r"(\d+)\((\d+)\)")

T71 = 1411488254391826260559
T72 = 3041466034261123517719
ANCHOR_INDICES = (65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130)


def parse_value_table(text: str) -> dict[int, int]:
    if "1: 1," not in text:
        return {}
    chunk = text[text.find("1: 1,") : text.find("puzzle 1 = ADD")]
    return {int(m.group(1)): int(m.group(2)) for m in re.finditer(r"(\d+):\s*(\d+)", chunk)}


def parse_tdad_values(path: Path) -> dict[int, int]:
    out: dict[int, int] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"puzzle\s+(\d+):\s*(.*)", line.strip(), re.I)
        if not m:
            continue
        rest = m.group(2).strip()
        if not rest:
            continue
        val_s = rest.split("=")[0].strip().replace("\t", "")
        if val_s and val_s[0].isdigit():
            out[int(m.group(1))] = int(val_s)
    return out


def extract_index_block(section: str, n: int, vals: dict[int, int]) -> tuple[list[tuple[int, int]], int | None, bool]:
    lo, hi = (1 << (n - 1)), (1 << n) - 1
    totals = [int(x) for x in re.findall(r"=\s*(\d{10,})", section)]
    in_range = [t for t in totals if lo <= t <= hi]
    T = in_range[-1] if in_range else (totals[-1] if totals else None)

    blocks: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []
    for line in section.splitlines():
        if not TERM_CI_RE.search(line):
            if current:
                blocks.append(current)
                current = []
            continue
        line_terms = [
            (int(c), int(i))
            for c, i in TERM_CI_RE.findall(line)
            if int(c) in (1, 2, 3) and int(i) < n
        ]
        if line_terms:
            current.extend(line_terms)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    best: list[tuple[int, int]] = []
    for block in blocks:
        if not block:
            continue
        if T is not None and vals:
            calc = sum(c * vals.get(i, 0) for c, i in block)
            if calc == T:
                return block, T, True
        if len(block) > len(best):
            best = block
    if best and T is not None and vals:
        calc = sum(c * vals.get(i, 0) for c, i in best)
        return best, T, calc == T
    return best, T, False


def load_playlists(pattern_path: Path, tdad_vals: dict[int, int]) -> dict[int, dict]:
    text = pattern_path.read_text(encoding="utf-8")
    vals = {**parse_value_table(text), **tdad_vals}
    out: dict[int, dict] = {}

    for m in re.finditer(r"puzzle\s*(\d+)\s*[=:]", text, re.I):
        n = int(m.group(1))
        start = m.end()
        nxt = re.search(r"puzzle\s*\d+\s*[=:]", text[start:], re.I)
        section = text[start : start + nxt.start()] if nxt else text[start:]
        terms, T, eval_ok = extract_index_block(section, n, vals)
        if not terms:
            continue
        coeffs = [c for c, _ in terms]
        indices = [i for _, i in terms]
        da_ok = len(coeffs) % 4 == 0 and all(
            coeffs[i : i + 4] == TDAD_CYCLE for i in range(0, len(coeffs), 4)
        )
        out[n] = {
            "puzzle": n,
            "terms": [{"coeff": c, "index": i} for c, i in terms],
            "T": str(T) if T is not None else None,
            "eval_ok": eval_ok,
            "term_count": len(terms),
            "cycle_count": len(terms) // 4 if len(terms) % 4 == 0 else None,
            "da_cycle_pure": da_ok,
            "indices": indices,
            "coeffs": coeffs,
        }
    return out


def term_contributions(terms: list[tuple[int, int]], vals: dict[int, int]) -> list[dict]:
    rows = []
    for pos, (c, i) in enumerate(terms):
        v = vals.get(i, 0)
        rows.append({
            "pos": pos,
            "cycle_pos": pos % 4,
            "coeff": c,
            "index": i,
            "value": str(v),
            "contrib": c * v,
            "contrib_bits": (c * v).bit_length() if v else 0,
        })
    return rows


def playlist_features(n: int, terms: list[tuple[int, int]], vals: dict[int, int]) -> dict:
    indices = [i for _, i in terms]
    dists = [n - i for i in indices]
    reuse = Counter(indices)
    contribs = term_contributions(terms, vals)
    total = sum(r["contrib"] for r in contribs)

    by_cycle_pos: dict[int, list[int]] = defaultdict(list)
    for pos, (_, idx) in enumerate(terms):
        by_cycle_pos[pos % 4].append(idx)

    return {
        "puzzle": n,
        "term_count": len(terms),
        "cycle_count": len(terms) // 4 if len(terms) % 4 == 0 else None,
        "da_cycle_pure": len(terms) % 4 == 0 and all(
            terms[i][0] for i in range(len(terms))
        ),
        "index_min": min(indices),
        "index_max": max(indices),
        "distance_min": min(dists),
        "distance_max": max(dists),
        "distance_mean": statistics.mean(dists),
        "unique_indices": len(set(indices)),
        "max_reuse": max(reuse.values()),
        "reuse_gt1_count": sum(1 for c in reuse.values() if c > 1),
        "anchor_hits": {str(a): indices.count(a) for a in ANCHOR_INDICES if a in indices},
        "anchor_term_count": sum(indices.count(a) for a in ANCHOR_INDICES),
        "high_half_bias": sum(1 for i in indices if i >= n // 2) / len(indices),
        "cycle_pos_index_mean": {
            str(k): statistics.mean(v) if v else None for k, v in sorted(by_cycle_pos.items())
        },
        "top_contrib_terms": sorted(contribs, key=lambda r: r["contrib"], reverse=True)[:5],
        "total_eval": str(total),
    }


def global_constraints(playlists: dict[int, dict], vals: dict[int, int]) -> dict:
    all_terms: list[tuple[int, int, int]] = []  # puzzle, coeff, index
    cycle_pos_indices: dict[int, Counter[int]] = {0: Counter(), 1: Counter(), 2: Counter(), 3: Counter()}
    index_freq = Counter()
    distance_by_target: dict[int, list[int]] = defaultdict(list)
    reuse_counts = Counter()
    anchor_hits = Counter()
    cycle_counts = Counter()
    pure_count = 0

    for n, pl in playlists.items():
        terms = [(t["coeff"], t["index"]) for t in pl["terms"]]
        if pl.get("da_cycle_pure"):
            pure_count += 1
        if pl.get("cycle_count"):
            cycle_counts[pl["cycle_count"]] += 1
        for pos, (c, i) in enumerate(terms):
            all_terms.append((n, c, i))
            index_freq[i] += 1
            cycle_pos_indices[pos % 4][i] += 1
            distance_by_target[n].append(n - i)
            if i in ANCHOR_INDICES:
                anchor_hits[i] += 1
        for idx, cnt in Counter(t[1] for t in terms).items():
            reuse_counts[cnt] += 1

    # coeff-position index preferences (top 5 indices per cycle slot)
    cycle_prefs = {}
    for slot in range(4):
        cycle_prefs[str(slot)] = {
            "coeff": TDAD_CYCLE[slot],
            "op": OP_NAME[TDAD_CYCLE[slot]],
            "top_indices": index_freq.most_common(8) if slot == 0 else cycle_pos_indices[slot].most_common(8),
        }
    for slot in range(4):
        cycle_prefs[str(slot)] = {
            "coeff": TDAD_CYCLE[slot],
            "op": OP_NAME[TDAD_CYCLE[slot]],
            "top_indices": [(i, c) for i, c in cycle_pos_indices[slot].most_common(10)],
        }

    dist_pool = [d for ds in distance_by_target.values() for d in ds]

    return {
        "playlist_count": len(playlists),
        "pure_3212_playlists": pure_count,
        "cycle_count_distribution": dict(sorted(cycle_counts.items())),
        "unique_indices_used": len(index_freq),
        "unique_term_pairs": len(set((c, i) for _, c, i in all_terms)),
        "index_frequency_top20": index_freq.most_common(20),
        "anchor_hit_counts": dict(sorted(anchor_hits.items())),
        "distance_from_target": {
            "min": min(dist_pool) if dist_pool else None,
            "max": max(dist_pool) if dist_pool else None,
            "mean": statistics.mean(dist_pool) if dist_pool else None,
        },
        "reuse_per_index_distribution": dict(sorted(Counter(
            cnt for pl in playlists.values() for cnt in Counter(t["index"] for t in pl["terms"]).values()
        ).items())),
        "cycle_position_preferences": cycle_prefs,
        "puzzles_with_10_cycles": [n for n, pl in playlists.items() if pl.get("cycle_count") == 10],
        "puzzles_with_8_cycles": [n for n, pl in playlists.items() if pl.get("cycle_count") == 8],
    }


def p135_projection(global_c: dict, vals: dict[int, int]) -> dict:
    """P135: rhythm guess 10 cycles; index slots unknown."""
    n = 135
    expected_terms = 40
    expected_cycles = 10
    available_indices = sorted(i for i in vals if i < n)

    # From P70/P71 10-cycle paths: typical distance stats
    return {
        "puzzle": 135,
        "expected_rhythm": TDAD_CYCLE,
        "expected_cycles_guess": expected_cycles,
        "expected_terms_guess": expected_terms,
        "formula": "T_135 = Σ coeff_i * d_{index_i}  with coeff from [3,2,1,2]*10",
        "index_slots_unknown": expected_terms,
        "available_prior_indices": len(available_indices),
        "available_anchor_indices": [a for a in ANCHOR_INDICES if a in vals and a < n],
        "gates": [
            "T_135 in [2^134, 2^135)",
            "[T_135]G == P135 compressed address",
        ],
        "warnings_from_p71_p72": (
            "Correct [3,2,1,2] rhythm + wrong playlist → range-valid scalar, fails address gate"
        ),
        "constraints_from_solved": {
            "pure_3212_rate": f"{global_c['pure_3212_playlists']}/{global_c['playlist_count']} playlists",
            "common_cycle_counts": global_c["cycle_count_distribution"],
            "top_anchor_indices": list(global_c["anchor_hit_counts"].keys())[:8],
            "distance_mean_prior": global_c["distance_from_target"]["mean"],
            "max_reuse_seen": max(global_c["reuse_per_index_distribution"]) if global_c["reuse_per_index_distribution"] else None,
        },
        "search_target": "index path [a1..a40], NOT operator combinations",
        "status": "index playlist missing — rhythm known",
    }


def render_md(data: dict) -> str:
    g = data["global_constraints"]
    p = data["p135_projection"]
    lines = [
        "# TDAD index playlist scan",
        "",
        "```text",
        "TDAD determinant = fixed rhythm [3,2,1,2] + unique index path",
        "Operators: low-entropy.  Indices: high-entropy.",
        "```",
        "",
        "## Global constraints (solved playlists)",
        "",
        f"| metric | value |",
        f"|--------|-------|",
        f"| playlists parsed | {g['playlist_count']} |",
        f"| pure `[3,2,1,2]^k` | {g['pure_3212_playlists']} |",
        f"| unique prior indices used | {g['unique_indices_used']} |",
        f"| unique `(coeff,index)` pairs | {g['unique_term_pairs']} |",
        f"| cycle count distribution | {g['cycle_count_distribution']} |",
        f"| distance n−index (mean) | {g['distance_from_target']['mean']:.2f} |",
        f"| 10-cycle puzzles | {g['puzzles_with_10_cycles']} |",
        f"| 8-cycle puzzles | {g['puzzles_with_8_cycles']} |",
        "",
        "### Top index frequency (corpus)",
        "",
    ]
    for idx, cnt in g["index_frequency_top20"][:12]:
        lines.append(f"- P{idx}: {cnt} term slots")
    lines += [
        "",
        "### Anchor index hits (65, 70, 75, …)",
        "",
        f"```json",
        json.dumps(g["anchor_hit_counts"], indent=2),
        "```",
        "",
        "### Cycle-position preferences",
        "",
    ]
    for slot in "0123":
        pref = g["cycle_position_preferences"][slot]
        lines.append(f"**Slot {slot} ({pref['op']}, coeff {pref['coeff']})** — top indices: "
                     + ", ".join(f"P{i}×{c}" for i, c in pref["top_indices"][:6]))
    lines += [
        "",
        "## Per-puzzle playlists",
        "",
        "| n | terms | cycles | pure 3212 | unique idx | max reuse | anchors | eval |",
        "|---|-------|--------|-----------|------------|-----------|---------|------|",
    ]
    for row in data["per_puzzle"]:
        lines.append(
            f"| {row['puzzle']} | {row['term_count']} | {row.get('cycle_count','—')} | "
            f"{row.get('da_cycle_pure','—')} | {row['unique_indices']} | {row['max_reuse']} | "
            f"{row['anchor_term_count']} | {row.get('eval_ok','—')} |"
        )
    lines += [
        "",
        "## P135 projection",
        "",
        f"```json",
        json.dumps(p, indent=2),
        "```",
        "",
        "## Ruling",
        "",
        data["ruling"],
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    P135_OUT.mkdir(parents=True, exist_ok=True)

    tdad_vals = parse_tdad_values(TDAD_TXT)
    tdad_vals.update({71: T71, 72: T72})
    playlists = load_playlists(PATTERN_TXT, tdad_vals)
    vals = {**parse_value_table(PATTERN_TXT.read_text(encoding="utf-8")), **tdad_vals}

    per_puzzle = []
    for n in sorted(playlists):
        pl = playlists[n]
        terms = [(t["coeff"], t["index"]) for t in pl["terms"]]
        feat = playlist_features(n, terms, vals)
        feat["eval_ok"] = pl["eval_ok"]
        feat["da_cycle_pure"] = pl["da_cycle_pure"]
        feat["indices_path"] = pl["indices"]
        per_puzzle.append(feat)

    global_c = global_constraints(playlists, vals)
    p135 = p135_projection(global_c, vals)

    ruling = (
        "The drummer is obvious: [3,2,1,2] repeated. The sheet music is the index playlist. "
        "P71/P72 prove rhythm without correct indices fails [T]G=P. "
        "P135 search target: 40 index slots (10 cycles), not operator combos."
    )

    payload = {
        "tdad_core": {
            "operator_cycle": TDAD_CYCLE,
            "operator_names": OP_NAME,
            "low_entropy_operators": True,
            "high_entropy_indices": True,
        },
        "global_constraints": global_c,
        "per_puzzle": per_puzzle,
        "playlists": {
            str(n): {
                **playlists[n],
                "indices_path": playlists[n]["indices"],
            }
            for n in playlists
        },
        "p135_projection": p135,
        "ruling": ruling,
    }

    json_path = OUT / "exhibit_tdad_index_playlist_scan.json"
    md_path = OUT / "exhibit_tdad_index_playlist_scan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_md(payload), encoding="utf-8")

    p135_path = P135_OUT / "tdad_index_playlist_scan.json"
    p135_md = P135_OUT / "tdad_index_playlist_scan.md"
    p135_payload = {
        "puzzle": 135,
        "p135_projection": p135,
        "global_constraints_summary": {
            k: global_c[k]
            for k in (
                "cycle_count_distribution",
                "anchor_hit_counts",
                "distance_from_target",
                "puzzles_with_10_cycles",
            )
        },
        "ruling": ruling,
    }
    p135_path.write_text(json.dumps(p135_payload, indent=2), encoding="utf-8")
    p135_md.write_text(
        f"# P135 TDAD index playlist\n\n"
        f"Rhythm known: `[3,2,1,2]` × 10 cycles (40 terms guess).\n\n"
        f"```json\n{json.dumps(p135, indent=2)}\n```\n\n"
        f"## Ruling\n\n{ruling}\n",
        encoding="utf-8",
    )

    print(f"Wrote {md_path}")
    print(f"playlists={len(playlists)} pure_3212={global_c['pure_3212_playlists']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
