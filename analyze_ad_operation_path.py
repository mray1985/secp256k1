#!/usr/bin/env python3
"""
Parse AD operation paths from canonical F: breakdown file.

Canonical source:
  F:/New folder/secp256k1/DOUBLE_AND_ADD+BREAKDOWN.txt

Rules:
  ARCHIVE/briefcase/Double Add/Double Add Rules.txt

Validates:
  - no AA / DD within puzzle stream
  - puzzle n starts opposite how puzzle n-1 ended
  - arithmetic eval matches d(n)
  - band [2^(n-1), 2^n - 1]

Coupled RSZ cross (solved only):
  - k vs final path partial (should differ — k is nonce)
  - k vs intermediate partials at each op step
  - anchor index n-3 reuse count

Writes:
  ARCHIVE/briefcase/Double Add/ad_operation_paths.{json,md}
"""

from __future__ import annotations

import json
import math
import random
import re
from pathlib import Path

from hashkeys_rsz import N as N_ORDER
from puzzle_catalog import load_catalog
from puzzle_keys_53125 import parse_53125

ROOT = Path(__file__).resolve().parent
RULES = ROOT / "ARCHIVE" / "briefcase" / "Double Add" / "Double Add Rules.txt"
CANONICAL = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt")
FALLBACK = ROOT / "02_Research" / "notes" / "double_and_add.txt"
RSZ_DATA = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys" / "puzzle_genesis_rsz_1_256.json"
OUT_DIR = ROOT / "ARCHIVE" / "briefcase" / "Double Add"
OUT_JSON = OUT_DIR / "ad_operation_paths.json"
OUT_MD = OUT_DIR / "ad_operation_paths.md"

OP_RE = re.compile(r"([AD])\((\d+)\)")
ARITH_LINE = re.compile(r"^(\d+)\s*=\s*(.+)$")

# Transcript ends at P70; P71–P74 unsolved (empty in double_and_add.txt).
# AD reconstruction work ceiling: P73 (anchor d(70) = d(n−3)).
LAST_TRANSCRIPT_PUZZLE = 70
MAX_WORK_PUZZLE = 73
UNSOLVED_BLOCK = frozenset({71, 72, 73, 74})


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def perm_p(ns: list[float], ys: list[float], trials: int = 2000) -> float:
    random.seed(3)
    obs = abs(pearson(ns, ys))
    c = 0
    for _ in range(trials):
        sh = ys[:]
        random.shuffle(sh)
        if abs(pearson(ns, sh)) >= obs:
            c += 1
    return c / trials


def load_d_table() -> dict[int, int]:
    d: dict[int, int] = {}
    for n, pk in parse_53125().items():
        if pk.d:
            d[n] = pk.d
    for n, e in load_catalog().items():
        if e.private_key:
            d[n] = e.private_key
    # Never treat gap puzzles as known scalars (no on-chain / transcript d).
    for n in UNSOLVED_BLOCK:
        d.pop(n, None)
    return d


def known_d_indices(d_table: dict[int, int]) -> frozenset[int]:
    return frozenset(d_table.keys())


def parse_breakdown(path: Path, d_table: dict[int, int]) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    puzzles: list[dict] = []
    i = 0
    while i < len(lines):
        m = ARITH_LINE.match(lines[i])
        if not m:
            i += 1
            continue
        target = int(m.group(1))
        formula = m.group(2).strip()
        ad_line = ""
        if i + 1 < len(lines) and OP_RE.search(lines[i + 1]):
            ad_line = lines[i + 1]
            i += 2
        else:
            i += 1
        ops = [(g, int(idx)) for g, idx in OP_RE.findall(ad_line)]
        puzzles.append(
            {
                "n": None,  # filled after assign by order / match
                "target": target,
                "formula": formula,
                "ad_raw": ad_line,
                "ops": ops,
            }
        )

    # assign puzzle numbers by matching target to d_table or sequential for early
    seq = sorted(d_table.items(), key=lambda x: x[0])
    val_to_n = {v: n for n, v in seq}
    used: set[int] = set()
    for p in puzzles:
        n = val_to_n.get(p["target"])
        if n is not None and n not in used:
            p["n"] = n
            used.add(n)
    # fallback: first unmatched puzzles get lowest free n
    free_ns = [n for n, _ in seq if n not in used]
    for p in puzzles:
        if p["n"] is None and free_ns:
            p["n"] = free_ns.pop(0)

    puzzles.sort(key=lambda x: x["n"] or 9999)
    return [p for p in puzzles if p["n"] is not None]


def eval_formula(formula: str, d_table: dict[int, int]) -> int | None:
    """Evaluate 2*76 + 49 + ... using d_table values by magnitude lookup."""
    # map each bare integer token to puzzle index if it equals some d(m)
    val_to_idx = {v: m for m, v in d_table.items()}
    expr = formula.replace(" ", "")
    expr = re.sub(r"-(\d+)", r"-\1", expr)
    # replace numbers with their value (already decimal)
    def repl_num(m: re.Match) -> str:
        return m.group(0)

    try:
        # safe: only digits, +, -, *, parens
        if not re.fullmatch(r"[\d+\-*/().]+", expr.replace(" ", "")):
            return None
        return int(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return None


def apply_ops(ops: list[tuple[str, int]], d_table: dict[int, int]) -> tuple[int, list[dict]]:
    total = 0
    steps: list[dict] = []
    for op, idx in ops:
        dv = d_table.get(idx)
        if dv is None:
            return total, steps
        if op == "D":
            total += 2 * dv
            kind = "double"
        else:
            total += dv
            kind = "add"
        steps.append({"op": op, "index": idx, "d_ref": dv, "kind": kind, "partial": total})
    return total, steps


def validate_stream(puzzles: list[dict], d_table: dict[int, int]) -> dict:
    violations: list[str] = []
    prev_end: str | None = None
    known = known_d_indices(d_table)
    for p in puzzles:
        n = p["n"]
        ops = p["ops"]
        if n > LAST_TRANSCRIPT_PUZZLE:
            p["skipped"] = "above last solved transcript (P70); gap P71–P74"
            continue
        if not ops:
            violations.append(f"P{n}: no AD ops parsed")
            continue
        bad_refs = sorted({idx for _, idx in ops if idx not in known})
        if bad_refs:
            violations.append(f"P{n}: references unknown d at indices {bad_refs}")
            p["bad_d_refs"] = bad_refs
        if any(idx in UNSOLVED_BLOCK for _, idx in ops):
            violations.append(f"P{n}: illegal ref to unsolved gap index 71–74")
        # alternation within puzzle
        for j in range(len(ops) - 1):
            if ops[j][0] == ops[j + 1][0]:
                violations.append(f"P{n}: {ops[j][0]}{ops[j+1][0]} at step {j}")
        # cross-puzzle start
        if prev_end and ops[0][0] == prev_end:
            violations.append(f"P{n}: starts {ops[0][0]} but P{n-1} ended {prev_end}")
        prev_end = ops[-1][0]

        total, steps = apply_ops(ops, d_table)
        p["steps"] = steps
        p["computed"] = total
        p["expected"] = d_table.get(n, p["target"])
        p["eval_ok"] = total == p["expected"]
        if not p["eval_ok"]:
            violations.append(f"P{n}: AD sum {total} != d {p['expected']}")

        lo, hi = 1 << (n - 1), (1 << n) - 1
        p["in_band"] = lo <= p["expected"] <= hi
        if not p["in_band"]:
            violations.append(f"P{n}: d outside band")

        # n-3 anchor count
        anchor = n - 3
        p["anchor_n_minus_3"] = anchor if anchor >= 1 else None
        p["anchor_repeats"] = sum(1 for op, idx in ops if idx == anchor) if anchor else 0

    active = [p for p in puzzles if p["n"] <= LAST_TRANSCRIPT_PUZZLE and not p.get("skipped")]
    return {
        "puzzle_count": len(active),
        "violations": violations,
        "all_ad_valid": len(violations) == 0,
    }


def recover_k(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N_ORDER) * (z + r * d)) % N_ORDER


def rsz_cross(puzzles: list[dict], d_table: dict[int, int]) -> dict:
    if not RSZ_DATA.exists():
        return {}
    rsz = {r["puzzle"]: r for r in json.loads(RSZ_DATA.read_text(encoding="utf-8"))}
    rows = []
    for p in puzzles:
        n = p["n"]
        if n not in d_table or n not in rsz:
            continue
        d = d_table[n]
        r, s, z = rsz[n]["r"], rsz[n]["s"], rsz[n]["z"]
        k = recover_k(r, s, z, d)
        final_partial = p.get("computed", d)
        rows.append(
            {
                "n": n,
                "k_minus_d": (k - d) % N_ORDER,
                "k_minus_path_final": (k - final_partial) % N_ORDER,
                "k_over_N": k / N_ORDER,
                "path_steps": len(p.get("ops", [])),
                "anchor_repeats": p.get("anchor_repeats", 0),
            }
        )

    if len(rows) < 5:
        return {"n": len(rows)}

    ns = [float(r["n"]) for r in rows]
    return {
        "n": len(rows),
        "r_n_k_minus_path_final": pearson(ns, [r["k_minus_path_final"] / N_ORDER for r in rows]),
        "perm_k_minus_path": perm_p(ns, [r["k_minus_path_final"] / N_ORDER for r in rows]),
        "r_n_anchor_repeats": pearson(ns, [float(r["anchor_repeats"]) for r in rows]),
        "note": "k_minus_path_final is 0 mod N tautologically if path equals d; nonzero measures parse/eval mismatch",
    }


def work_ceiling_note(d_table: dict[int, int]) -> dict:
    d70 = d_table.get(70)
    lo73, hi73 = 1 << 72, (1 << 73) - 1
    anchor = 70
    min_rep = math.ceil(lo73 / d70) if d70 else None
    max_rep = (hi73 // d70) if d70 else None
    return {
        "last_transcript_puzzle": LAST_TRANSCRIPT_PUZZLE,
        "max_work_puzzle": MAX_WORK_PUZZLE,
        "unsolved_gap": sorted(UNSOLVED_BLOCK),
        "cannot_reference_d": "P71–P74 have no known scalar — do not use A(71)…D(74) in paths",
        "P73_target": {
            "band": [lo73, hi73],
            "primary_anchor": f"d({anchor}) = d(n-3)",
            "d70": str(d70) if d70 else None,
            "d70_repeat_count_range": [min_rep, max_rep],
            "next_solved_after_gap": 75,
        },
    }


def early_sequence_note() -> dict:
    """Document P1-P4: raw double_and_add.txt vs corrected breakdown."""
    return {
        "issue": "Early prose in double_and_add.txt mis-describes P4 as 7+1 instead of D(1)A(1)D(1)A(1)D(1)",
        "P3": {"value": 7, "correct_AD": "D(2)A(1)", "raw_prose": "2(3)+1 (ambiguous index)"},
        "P4": {
            "value": 8,
            "correct_AD": "D(1)A(1)D(1)A(1)D(1)",
            "wrong_prose": "7+1 (breaks alternation narrative)",
            "stable_from": "P4 forward AD never breaks (rules item 8)",
        },
        "canonical_file": str(CANONICAL),
    }


def main() -> None:
    src = CANONICAL if CANONICAL.exists() else FALLBACK
    d_table = load_d_table()
    puzzles = parse_breakdown(src, d_table)
    validation = validate_stream(puzzles, d_table)
    rsz = rsz_cross(puzzles, d_table)

    report = {
        "source": str(src),
        "rules": str(RULES),
        "work_ceiling": work_ceiling_note(d_table),
        "early_sequence": early_sequence_note(),
        "validation": validation,
        "rsz_cross": rsz,
        "puzzles": [p for p in puzzles if p.get("n", 999) <= LAST_TRANSCRIPT_PUZZLE and not p.get("skipped")],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    wc = work_ceiling_note(d_table)
    lines = [
        "# AD operation paths",
        "",
        f"Canonical: `{src}`",
        f"Rules: `{RULES.name}`",
        "",
        "## Work ceiling",
        "",
        f"- **Last solved transcript:** P{LAST_TRANSCRIPT_PUZZLE}",
        f"- **Highest active target:** P{MAX_WORK_PUZZLE} (unsolved — path to reconstruct)",
        f"- **Gap (no d):** P{wc['unsolved_gap'][0]}–P{wc['unsolved_gap'][-1]} — cannot reference `d(71)`…`d(74)` in paths",
        f"- **P73 anchor:** `d(70)` (n−3); band `[2^72, 2^73−1]`",
        "",
        "## Early sequence correction (P1–P4)",
        "",
        "Raw `double_and_add.txt` prose for **P4** says `7+1`. Correct path is **D(1)A(1)D(1)A(1)D(1)** per breakdown + rules.",
        "P3 value 7 is **D(2)A(1)** under AD grammar (not “double previous” shorthand).",
        "From P4 forward the global AD alternation is stable.",
        "",
        f"**Validation:** {validation['puzzle_count']} puzzles parsed | "
        f"AD violations: **{len(validation['violations'])}**",
        "",
    ]
    if validation["violations"][:15]:
        lines.append("First violations:")
        for v in validation["violations"][:15]:
            lines.append(f"- {v}")
        lines.append("")

    if rsz:
        lines += [
            "## RSZ cross (k vs path — solved with spend)",
            "",
            f"| metric | value |",
            f"|--------|-------|",
        ]
        for k, v in rsz.items():
            if isinstance(v, float):
                lines.append(f"| {k} | {v:+.4f} |")
            elif k != "note":
                lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## Sample paths",
        "",
        "| n | ops | steps | anchor(n-3) reps | eval ok |",
        "|---|-----|-------|------------------|---------|",
    ]
    for p in puzzles[:10]:
        ops_s = p.get("ad_raw", "")[:40]
        lines.append(
            f"| {p['n']} | {ops_s} | {len(p.get('ops', []))} | {p.get('anchor_repeats', 0)} | {p.get('eval_ok')} |"
        )
    lines.append(f"| … | | | | |")
    for p in puzzles[-3:]:
        ops_s = p.get("ad_raw", "")[:40]
        lines.append(
            f"| {p['n']} | {ops_s} | {len(p.get('ops', []))} | {p.get('anchor_repeats', 0)} | {p.get('eval_ok')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Source: {src}")
    print(f"Puzzles: {len(puzzles)}, violations: {len(validation['violations'])}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
