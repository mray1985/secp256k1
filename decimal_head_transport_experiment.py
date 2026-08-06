#!/usr/bin/env python3
"""
Measure leading-decimal transport maps across mod p, N, and delta = p - N.

For solved puzzles and deterministic random control points, compute:
  1. x^3 + 7 mod m  versus y^2 mod m
  2. x^2 mod m      versus y^3 + 7 mod m

For each modulus m in {p, N, delta}, record the first 2 and 3 decimal digits
of each reduced residue and summarize repeated head mappings like 57->26.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import (  # noqa: E402
    DEFAULT_RY,
    N,
    P135_R_TRUE_X,
    all_cube_roots_mod,
    delta,
    n_slot_y_compress_constant,
    p,
    pubkey_from_scalar,
    slot_compress_carry,
    compressed_slot_y2,
)
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT_TXT = ARCHIVE / "decimal_head_transport_report.txt"
DETAIL_TSV = ARCHIVE / "decimal_head_transport_rows.tsv"
REPORT_PDF = ARCHIVE / "decimal_head_transport_report.pdf"

MODS = (("p", p), ("N", N), ("delta", delta))
HEAD_SIZES = (2, 3)
CONTROL_COUNT = 32
CONTROL_SEED = 71_325


@dataclass(frozen=True)
class Sample:
    group: str
    label: str
    puzzle_n: int
    scalar: int
    x: int
    y: int


def head_dec(value: int, digits: int) -> str:
    s = str(value)
    return s[:digits] if len(s) >= digits else s


def residues(x: int, y: int, mod: int) -> dict[str, int]:
    return {
        "x3p7": (pow(x, 3, mod) + 7) % mod,
        "y2": pow(y, 2, mod),
        "x2": pow(x, 2, mod),
        "y3p7": (pow(y, 3, mod) + 7) % mod,
    }


def solved_samples() -> list[Sample]:
    keys = parse_53125()
    out: list[Sample] = []
    for n in sorted(keys):
        key = keys[n]
        if key.d > 0:
            out.append(Sample("solved", f"P{n}", n, key.d, key.px, key.py))
    return out


def control_samples(count: int = CONTROL_COUNT, seed: int = CONTROL_SEED) -> list[Sample]:
    rng = random.Random(seed)
    out: list[Sample] = []
    for i in range(count):
        d = rng.randrange(1, N)
        x, y = pubkey_from_scalar(d)
        out.append(Sample("control", f"R{i+1}", 0, d, x, y))
    return out


def iter_rows(samples: list[Sample]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sample in samples:
        for mod_name, mod in MODS:
            vals = residues(sample.x, sample.y, mod)
            row = {
                "group": sample.group,
                "label": sample.label,
                "puzzle_n": str(sample.puzzle_n),
                "lane3": str(sample.puzzle_n % 3) if sample.puzzle_n else "-",
                "lane5": str(sample.puzzle_n % 5) if sample.puzzle_n else "-",
                "scalar": str(sample.scalar),
                "mod": mod_name,
                "eq1_lhs": str(vals["x3p7"]),
                "eq1_rhs": str(vals["y2"]),
                "eq2_lhs": str(vals["x2"]),
                "eq2_rhs": str(vals["y3p7"]),
            }
            for k in HEAD_SIZES:
                row[f"eq1_h{k}"] = f"{head_dec(vals['x3p7'], k)}->{head_dec(vals['y2'], k)}"
                row[f"eq2_h{k}"] = f"{head_dec(vals['x2'], k)}->{head_dec(vals['y3p7'], k)}"
            rows.append(row)
    return rows


def summarize(rows: list[dict[str, str]], field: str, group: str, mod_name: str) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter(
        row[field]
        for row in rows
        if row["group"] == group and row["mod"] == mod_name
    )
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def distinct_count(rows: list[dict[str, str]], field: str, group: str, mod_name: str) -> int:
    return len({row[field] for row in rows if row["group"] == group and row["mod"] == mod_name})


def write_tsv(rows: list[dict[str, str]]) -> None:
    headers = [
        "group",
        "label",
        "puzzle_n",
        "lane3",
        "lane5",
        "scalar",
        "mod",
        "eq1_lhs",
        "eq1_rhs",
        "eq1_h2",
        "eq1_h3",
        "eq2_lhs",
        "eq2_rhs",
        "eq2_h2",
        "eq2_h3",
    ]
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append("\t".join(row[h] for h in headers))
    DETAIL_TSV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_detail_lines(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "DETAILED ROWS",
        "group\tlabel\tpuzzle_n\tlane3\tlane5\tmod\teq1_h2\teq1_h3\teq2_h2\teq2_h3",
    ]
    for row in rows:
        lines.append(
            "\t".join(
                [
                    row["group"],
                    row["label"],
                    row["puzzle_n"],
                    row["lane3"],
                    row["lane5"],
                    row["mod"],
                    row["eq1_h2"],
                    row["eq1_h3"],
                    row["eq2_h2"],
                    row["eq2_h3"],
                ]
            )
        )
    return lines


def write_pdf(summary_text: str, detail_lines: list[str], pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font_name = "Courier"
    try:
        pdfmetrics.registerFont(
            TTFont("DejaVuSansMono", str(Path("C:/Windows/Fonts/consola.ttf")))
        )
        font_name = "DejaVuSansMono"
    except Exception:
        pass

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    left = 36
    top = height - 36
    bottom = 36
    font_size = 7
    line_gap = 9

    def new_page(page_no: int) -> float:
        c.setFont(font_name, font_size)
        c.drawRightString(width - left, height - 24, f"Page {page_no}")
        return top

    page_no = 1
    y = new_page(page_no)
    for line in summary_text.splitlines() + [""] + detail_lines:
        if y < bottom:
            c.showPage()
            page_no += 1
            y = new_page(page_no)
        c.drawString(left, y, line[:170])
        y -= line_gap
    c.save()


def summarize_lane(
    rows: list[dict[str, str]],
    field: str,
    mod_name: str,
    lane_field: str,
    lane_value: str,
) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter(
        row[field]
        for row in rows
        if row["group"] == "solved" and row["mod"] == mod_name and row[lane_field] == lane_value
    )
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def sqrt_mod_prime(a: int, mod: int) -> list[int]:
    a %= mod
    if a == 0:
        return [0]
    if pow(a, (mod - 1) // 2, mod) != 1:
        return []
    q = mod - 1
    s = 0
    while q % 2 == 0:
        s += 1
        q //= 2
    z = 2
    while pow(z, (mod - 1) // 2, mod) != mod - 1:
        z += 1
    m = s
    c = pow(z, q, mod)
    t = pow(a, q, mod)
    r = pow(a, (q + 1) // 2, mod)
    while t != 1:
        i = 1
        while pow(t, 2**i, mod) != 1:
            i += 1
        b = pow(c, 2 ** (m - i - 1), mod)
        m = i
        c = (b * b) % mod
        t = (t * b * b) % mod
        r = (r * b) % mod
    return [r, mod - r]


def render_p135_worked_example() -> str:
    rx = P135_R_TRUE_X
    ry = DEFAULT_RY
    x3n = pow(rx, 3, N)
    y2n = pow(ry, 2, N)
    x3p = pow(rx, 3, p)
    y2p = pow(ry, 2, p)
    meet = x3n + 4
    roots_p = all_cube_roots_mod(p, x3p, witness=rx)
    witness_n = 2834851001216865213370562256662376911139918172405549224971084278201255654682
    roots_n = all_cube_roots_mod(N, meet, witness=witness_n) if pow(witness_n, 3, N) == meet else []
    ys = sqrt_mod_prime(meet, N)
    carry, carry_ok = slot_compress_carry(ry, rx)
    ycomp = compressed_slot_y2((rx * delta) % N, n_slot_y_compress_constant(carry)) if carry_ok else 0

    lines = [
        "=== P135 rx transport worked example ===",
        f"P135 true rx tail ...{str(rx)[-3:]}",
        f"bridge ry tail  ...{str(ry)[-3:]}",
        "",
        "mod p (curve law):",
        f"  x^3 mod p tail ...{str(x3p)[-4:]}",
        f"  y^2 mod p tail ...{str(y2p)[-4:]}",
        f"  y^2 - x^3 = {y2p - x3p}",
        f"  x^3 + 4 = y^2 - 3 ? {x3p + 4 == y2p - 3}",
        f"  x^3 + 7 = y^2 ? {x3p + 7 == y2p}",
        f"  p cube-root branches (same x^3 mod p): {len(roots_p)}",
        "",
        "mod N (fingerprint transport):",
        f"  (x^3+4) mod N tail ...{str((x3n+4)%N)[-3:]}  (lhs; Wolfram ...768)",
        f"  (y^2-3) mod N tail ...{str((y2n-3)%N)[-3:]}  (rhs; bridge ry)",
        f"  lhs == rhs mod N ? {(x3n+4)%N == (y2n-3)%N}",
        f"  law: px^3 + 4 == py^2 - 3  (equiv px^3 + 7 == py^2)",
        f"  head2 lhs->{head_dec((x3n+4)%N,2)} rhs->{head_dec((y2n-3)%N,2)}",
        f"  head3 lhs->{head_dec((x3n+4)%N,3)} rhs->{head_dec((y2n-3)%N,3)}",
        f"  meet cube roots mod N: {len(roots_n)}",
        f"  meet sqrt roots mod N: {len(ys)}",
        "",
        "modulus cube lift:",
        f"  p^3 mod N == delta^3 mod N ? {pow(p, 3, N) == pow(delta, 3, N)}",
        "",
        "heaven lift (bridge rx,ry):",
        f"  carry ok: {carry_ok}",
        f"  y_comp mod N tail ...{str(ycomp)[-3:] if carry_ok else 'n/a'}",
        f"  y_comp == meet ? {ycomp == meet if carry_ok else False}",
        "",
        "=== next step ===",
        "1. Keep P135 true rx branch (90653...368), not bridge slot 26000...739.",
        "2. N transport: rx^3 mod N (...764) + 4 -> meet ...768.",
        "3. p transport: x^3 + 7 = y^2 via bridge ry (...9841).",
        "4. Meet pairs (x^3==y^2 mod N) are NOT on-curve mod p -> use heaven lift, not raw meet coords.",
        "5. Hunt P135 d with shelf2+offset AND filter (px^3+4)==(py^2-3) mod p.",
        "6. On mod N, lhs (...768) and rhs (...962) split — that gap is the N displacement.",
        "",
    ]
    for i, y in enumerate(ys):
        on_p = (y * y - rx * rx * rx - 7) % p == 0
        lines.append(f"  meet sqrt y{i} tail ...{str(y)[-3:]} on-curve-p with rx: {on_p}")
    return "\n".join(lines) + "\n"


def render_summary(rows: list[dict[str, str]]) -> str:
    lines: list[str] = []
    solved_n = sum(1 for row in rows if row["group"] == "solved" and row["mod"] == "p")
    control_n = sum(1 for row in rows if row["group"] == "control" and row["mod"] == "p")

    lines.append("DECIMAL HEAD TRANSPORT EXPERIMENT")
    lines.append(f"mods: p, N, delta=p-N")
    lines.append(f"samples: solved={solved_n} controls={control_n} seed={CONTROL_SEED}")
    lines.append("")

    for eq_field, title in (("eq1", "x^3+7  -> y^2"), ("eq2", "x^2 -> y^3+7")):
        lines.append(f"=== {title} ===")
        for k in HEAD_SIZES:
            field = f"{eq_field}_h{k}"
            lines.append(f"-- head{k} mappings --")
            for mod_name, _mod in MODS:
                lines.append(f"mod {mod_name}:")
                for group in ("solved", "control"):
                    total = sum(1 for row in rows if row["group"] == group and row["mod"] == mod_name)
                    uniq = distinct_count(rows, field, group, mod_name)
                    top = summarize(rows, field, group, mod_name)[:10]
                    lines.append(f"  {group}: total={total} distinct={uniq}")
                    for mapping, count in top:
                        lines.append(f"    {mapping}: {count}")
                lines.append("")
        lines.append("")

    lines.append("=== solved lane slices ===")
    for eq_field, title in (("eq1", "x^3+7  -> y^2"), ("eq2", "x^2 -> y^3+7")):
        lines.append(f"-- {title} --")
        for k in HEAD_SIZES:
            field = f"{eq_field}_h{k}"
            for lane_field, lane_mod in (("lane3", 3), ("lane5", 5)):
                lines.append(f"head{k} by {lane_field}:")
                for mod_name, _mod in MODS:
                    lines.append(f"  mod {mod_name}:")
                    for lane_value in map(str, range(lane_mod)):
                        total = sum(
                            1
                            for row in rows
                            if row["group"] == "solved"
                            and row["mod"] == mod_name
                            and row[lane_field] == lane_value
                        )
                        uniq = len(
                            {
                                row[field]
                                for row in rows
                                if row["group"] == "solved"
                                and row["mod"] == mod_name
                                and row[lane_field] == lane_value
                            }
                        )
                        top = summarize_lane(rows, field, mod_name, lane_field, lane_value)[:5]
                        lines.append(f"    {lane_field}={lane_value}: total={total} distinct={uniq}")
                        for mapping, count in top:
                            lines.append(f"      {mapping}: {count}")
                lines.append("")
        lines.append("")

    lines.append("=== sample solved rows ===")
    for row in rows:
        if row["group"] != "solved":
            continue
        if row["label"] not in {"P65", "P66", "P67", "P68", "P69", "P70", "P71", "P75", "P80"}:
            continue
        lines.append(
            f"{row['label']:>4} l3={row['lane3']} l5={row['lane5']} mod {row['mod']:<5} "
            f"eq1 h2={row['eq1_h2']:<7} h3={row['eq1_h3']:<9} "
            f"eq2 h2={row['eq2_h2']:<7} h3={row['eq2_h3']}"
        )
    lines.append("")
    lines.append(render_p135_worked_example().rstrip())
    lines.append("")
    lines.append("=== unsolved batch anchor gaps (rx + bridge ry) ===")
    try:
        from unsolved_full_transport_hunt import build_ctx  # noqa: WPS433
        from puzzle_keys_53125 import parse_53125 as _p53125  # noqa: WPS433
        from unsolved_batch import UNSOLVED_PUZZLES as _UP  # noqa: WPS433

        _keys = _p53125()
        for n in _UP:
            ctx = build_ctx(n, _keys)
            lines.append(
                f"P{n} gap_h2={head_dec(ctx.anchor_gap,2)} gap_h3={head_dec(ctx.anchor_gap,3)} "
                f"lhs...{str(ctx.anchor_lhs)[-3:]} rhs...{str(ctx.anchor_rhs)[-3:]}"
            )
    except Exception as exc:
        lines.append(f"(batch anchors skipped: {exc})")
    lines.append("")
    lines.append(f"rows -> {DETAIL_TSV}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Decimal head transport experiment")
    ap.add_argument("--controls", type=int, default=CONTROL_COUNT, help="number of deterministic random control keys")
    ap.add_argument("--seed", type=int, default=CONTROL_SEED, help="seed for deterministic random control keys")
    ap.add_argument("--pdf", action="store_true", help="also write a PDF report")
    args = ap.parse_args()

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    rows = iter_rows(solved_samples() + control_samples(args.controls, args.seed))
    write_tsv(rows)
    text = render_summary(rows)
    REPORT_TXT.write_text(text, encoding="utf-8")
    if args.pdf:
        write_pdf(text, build_detail_lines(rows), REPORT_PDF)
    print(text, end="")
    print(f"wrote {REPORT_TXT}")
    print(f"wrote {DETAIL_TSV}")
    if args.pdf:
        print(f"wrote {REPORT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
