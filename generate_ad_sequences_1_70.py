#!/usr/bin/env python3
"""
Build AD sequences P1-P70 from DOUBLE_AND_ADD+BREAKDOWN.txt cheat sheet.

P21 corrected: P20 ends A(1); P21 must start D (not A).
P31/P32: formula-aligned fixes where cheat-sheet AD sum drifted.
P35-P70: arithmetic lines from extended breakdown (no AD lines in source).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BREAKDOWN_F = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt")
BREAKDOWN_LOCAL = ROOT / "02_Research" / "notes" / "DOUBLE_AND_ADD+BREAKDOWN.txt"
OUT_DIR = ROOT / "ARCHIVE" / "briefcase" / "Double Add"
PAPER = OUT_DIR / "AD_Sequences_P1_through_P70.md"
OUT_JSON = OUT_DIR / "ad_sequences_1_70_generated.json"

D: dict[int, int] = {
    1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224, 9: 467, 10: 514,
    11: 1155, 12: 2683, 13: 5216, 14: 10544, 15: 26867, 16: 51510, 17: 95823,
    18: 198669, 19: 357535, 20: 863317, 21: 1811764, 22: 3007503, 23: 5598802,
    24: 14428676, 25: 33185509, 26: 54538862, 27: 111949941, 28: 227634408,
    29: 400708894, 30: 1033162084, 31: 2102388551, 32: 3093472814,
    33: 7137437912, 34: 14133072157, 35: 20112871792, 36: 42387769980,
    37: 100251560595, 38: 146971536592, 39: 323724968937, 40: 1003651412950,
    41: 1458252205147, 42: 2895374552463, 43: 7409811047825, 44: 15404761757071,
    45: 19996463086597, 46: 51408670348612, 47: 119666659114170,
    48: 191206974700443, 49: 409118905032525, 50: 611140496167764,
    51: 2058769515153876, 52: 4216495639600700, 53: 6763683971478124,
    54: 9974455244496707, 55: 30045390491869460, 56: 44218742292676575,
    57: 138245758910846492, 58: 199976667976342049, 59: 525070384258266191,
    60: 1135041350219496382, 61: 1425787542618654982, 62: 3908372542507822062,
    63: 8993229949524469768, 64: 17799667357578236628, 65: 30568377312064202855,
    66: 46346217550346335726, 67: 132656943602386256302, 68: 219898266213316039825,
    69: 297274491920375905804, 70: 970436974005023690481,
}

V2N = {v: n for n, v in D.items()}
OP_RE = re.compile(r"([AD])\((\d+)\)")
ARITH = re.compile(r"^\*?(\d+)\s*=\s*(.+)$")

# P20 ends A(1); original cheat P21 wrongly started A(18). Valid D-start path, same d(21).
P21_CORRECTED = "D(20)A(16)D(14)A(14)D(10)A(10)D(7)A(8)D(5)A(5)D(2)A(1)"

# Cheat-sheet typos vs formula (delta +3 and missing d(29) block).
P31_CORRECTED = (
    "D(28)A(28)D(28)A(28)D(28)A(28)D(24)A(24)D(22)A(22)D(19)A(19)D(17)A(17)"
    "D(12)A(12)D(9)A(9)D(8)A(8)D(6)A(5)D(4)A(4)D(1)A(1)"
)

P32_CORRECTED = (
    "D(29)A(29)D(29)A(29)D(26)A(26)D(25)A(25)D(23)A(23)D(21)A(21)D(20)A(20)"
    "D(17)A(17)D(16)A(16)D(15)A(13)D(13)A(11)D(11)A(8)D(8)A(7)D(7)A(4)D(4)A(3)D(3)A(1)D(1)"
)

MANUAL_AD: dict[int, str] = {
    21: P21_CORRECTED,
    31: P31_CORRECTED,
    32: P32_CORRECTED,
}


def val(op: str, m: int) -> int:
    return D[m] if op == "A" else 2 * D[m]


def fmt(ops: list[tuple[str, int]]) -> str:
    return "".join(f"{o}({m})" for o, m in ops)


def arith(ops: list[tuple[str, int]]) -> str:
    return " + ".join(str(val(o, m)) if o == "A" else f"2*{D[m]}" for o, m in ops)


def parse_ops(ad: str) -> list[tuple[str, int]]:
    return [(g, int(i)) for g, i in OP_RE.findall(ad)]


def join_formula_lines(text: str) -> list[str]:
    raw = [ln.strip() for ln in text.splitlines()]
    merged: list[str] = []
    buf = ""
    for line in raw:
        if not line:
            if buf:
                merged.append(buf)
                buf = ""
            continue
        if re.match(r"^\d+\s*[:=]", line) and not ARITH.match(line):
            if buf:
                merged.append(buf)
                buf = ""
            continue
        if ARITH.match(line):
            if buf:
                merged.append(buf)
            buf = line.lstrip("*")
        elif buf and re.match(r"^[2\d]", line):
            buf += " " + line
        elif buf:
            merged.append(buf)
            buf = ""
    if buf:
        merged.append(buf)
    return merged


def load_breakdown() -> tuple[dict[int, str], dict[int, str]]:
    path = BREAKDOWN_F if BREAKDOWN_F.exists() else BREAKDOWN_LOCAL
    text = path.read_text(encoding="utf-8", errors="replace")
    formulas: dict[int, str] = {}
    ads: dict[int, str] = {}
    i = 0
    lines = join_formula_lines(text)
    for line in lines:
        m = ARITH.match(line.strip())
        if not m:
            continue
        target = int(m.group(1))
        n = V2N.get(target)
        if n is None or n > 70:
            continue
        formulas[n] = m.group(2).strip()
    # second pass for AD lines paired with formulas in file order
    raw = [ln.strip() for ln in text.splitlines() if ln.strip()]
    i = 0
    while i < len(raw):
        m = ARITH.match(raw[i].lstrip("*"))
        if not m:
            i += 1
            continue
        target = int(m.group(1))
        n = V2N.get(target)
        if n and n <= 70 and i + 1 < len(raw) and OP_RE.search(raw[i + 1]):
            ads[n] = raw[i + 1]
            i += 2
        else:
            i += 1
    for n, ad in MANUAL_AD.items():
        ads[n] = ad
    return formulas, ads


def normalize_formula(s: str) -> str:
    s = re.sub(r"2\((\d+)\)", r"2*\1", s)
    return re.sub(r"\s+", "", s)


def parse_expansion_line(line: str) -> list[tuple[str, int]]:
    rhs = line.split("=", 1)[1].strip() if "=" in line else line.strip()
    rhs = normalize_formula(rhs)
    tokens: list[tuple[str, int]] = []
    i = 0
    sign = 1
    while i < len(rhs):
        if rhs[i] == "+":
            sign = 1
            i += 1
            continue
        if rhs[i] == "-":
            sign = -1
            i += 1
            continue
        if rhs.startswith("2*", i):
            i += 2
            j = i
            while j < len(rhs) and rhs[j].isdigit():
                j += 1
            tokens.append(("double", sign * int(rhs[i:j])))
            sign = 1
            i = j
            continue
        j = i
        while j < len(rhs) and rhs[j].isdigit():
            j += 1
        tokens.append(("single", sign * int(rhs[i:j])))
        sign = 1
        i = j
    return tokens


def tokens_to_ops(tokens: list[tuple[str, int]], need: str) -> list[tuple[str, int]] | None:
    ops: list[tuple[str, int]] = []
    i = 0
    while i < len(tokens):
        kind, v = tokens[i]
        if v < 0:
            i += 1
            continue
        v = abs(v)
        if v not in V2N:
            return None
        m = V2N[v]
        if i + 1 < len(tokens) and tokens[i + 1][1] > 0:
            k2, v2 = tokens[i + 1]
            if abs(v2) in V2N and V2N[abs(v2)] == m:
                if kind == "double" and k2 == "single":
                    pair = [("D", m), ("A", m)]
                elif kind == "single" and k2 == "double":
                    pair = [("A", m), ("D", m)]
                elif kind == "double" and k2 == "double":
                    pair = [("D", m), ("A", m), ("D", m), ("A", m)]
                else:
                    pair = []
                if pair:
                    if pair[0][0] != need:
                        return None
                    ops.extend(pair)
                    need = pair[-1][0]
                    need = "D" if need == "A" else "A"
                    i += 2
                    continue
        op = "D" if kind == "double" else "A"
        if op != need:
            return None
        ops.append((op, m))
        need = "D" if op == "A" else "A"
        i += 1
    return ops


def derive_from_formula(formula: str, need: str | None, target: int) -> list[tuple[str, int]] | None:
    toks = parse_expansion_line(f"= {formula}")
    if need:
        for start in (need, "D" if need == "A" else "A"):
            ops = tokens_to_ops(toks, start)
            if ops and sum(val(o, m) for o, m in ops) == target:
                return ops
        return None
    for start in ("A", "D"):
        ops = tokens_to_ops(toks, start)
        if ops and sum(val(o, m) for o, m in ops) == target:
            return ops
    return None


def main() -> None:
    formulas, ads = load_breakdown()
    results: dict[int, dict] = {}
    failed: list[int] = []
    prev_end: str | None = None

    for n in range(1, 71):
        ops: list[tuple[str, int]] | None = None
        source = "cheat_sheet"
        if n in ads:
            ops = parse_ops(ads[n])
            source = "cheat_sheet" + (" (corrected)" if n in MANUAL_AD else "")
        elif n in formulas:
            need = None if n == 1 else ("D" if prev_end == "A" else "A")
            ops = derive_from_formula(formulas[n], need, D[n])
            source = "breakdown_formula"
        if not ops:
            failed.append(n)
            prev_end = None
            continue
        s = sum(val(o, m) for o, m in ops)
        if s != D[n]:
            failed.append(n)
            prev_end = None
            continue
        if n > 1 and prev_end and ops[0][0] == prev_end:
            failed.append(n)
            prev_end = None
            continue
        prev_end = ops[-1][0]
        results[n] = {
            "d": D[n],
            "ops": fmt(ops),
            "arith": arith(ops),
            "formula": formulas.get(n, ""),
            "source": source,
        }

    lines = [
        "# Double Add Sequences — Puzzles 1 Through 70",
        "",
        "Source: **`DOUBLE_AND_ADD+BREAKDOWN.txt`** (cheat sheet).",
        "",
        "| Op | Meaning |",
        "|----|---------|",
        "| A(m) | + d(m) |",
        "| D(m) | + 2·d(m) |",
        "",
        "**P21 fix:** P20 ends `A(1)`; P21 must start **D** (not `A(18)`).",
        "Corrected P21 AD path is in this paper; original cheat line had a boundary AA.",
        "",
        "**P31–P32:** cheat-sheet AD lines aligned to breakdown formulas (`D(4)A(4)` etc.).",
        "",
        "**P35–P70:** breakdown provides arithmetic only; AD from formula conversion where needed.",
        "",
        "**Ceiling:** P70 last solved transcript. P71–P74 empty.",
        "",
        "---",
        "",
    ]
    for n in range(1, 71):
        lines.append(f"## Puzzle {n}")
        lines.append("")
        if n not in results:
            lines.append("*Pending — no validated AD in this pass.*")
            lines.append("")
            continue
        r = results[n]
        lines.append(f"**d({n})** = {r['d']}")
        lines.append("")
        lines.append(f"**AD sequence:** `{r['ops']}`")
        lines.append("")
        lines.append(f"**Sum:** {r['arith']}")
        lines.append("")
        if r.get("formula"):
            f = r["formula"]
            lines.append(f"*Breakdown formula:* `{f[:120]}{'…' if len(f) > 120 else ''}`")
            lines.append("")
        lines.append(f"*Source:* {r['source']}")
        lines.append("")

    if failed:
        lines.extend(["---", "", f"Not validated: {failed}", ""])

    lines.extend(["---", "", "*Generated by `generate_ad_sequences_1_70.py`*"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results)}/70  failed={failed}")
    print(PAPER)


if __name__ == "__main__":
    main()
