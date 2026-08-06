#!/usr/bin/env python3
"""Search Puzzle 160 candidates from barcode windows and averages.

Barcodes sourced from F:\\📝 Notes\\160decimals.txt / barcoding.txt.
Re-run after updating BARCODES or pass --barcodes-file.
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
import time
from pathlib import Path

from ecdsa import SECP256k1

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO = 2**159
HI = 2**160
# Decimal width for [2^159, 2^160): LO has 48 digits, HI-1 has 49 (not 41 like puzzle 135).
DEFAULT_WIDTH = len(str(LO))  # 48

TARGET_X = 0xE0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673
TARGET_Y = 0xC2D9690945DD98F6E0E45D4A1F760C9E85ED5AE5FFEEDA74E121EE0D836A7C86
NEG_Y = (-TARGET_Y) % p

G = SECP256k1.generator
NEG_G = (N - 1) * G

# Default: 160decimals.txt / barcoding.txt
BARCODES = {
    "b1_px": "101616124637840542991531253248586524020213215258338643076214814468447630501491",
    "b2_rmd160": "1326093679998364004747100419105194353286137352850",
    "b3_addr": "5695528987025262733892385050884703331087830060656326153881",
    "b4_s": "20216599067027469592215920403903222966042451176868065007483729301938362925663",
    "b0_r": "40567588587096510886779401934085802653423995574119754026847365368948749994020",
    "b5_z": "77167703155167490216844177020898376855310193614022213260692628998515342512468",
    "py": "88132823371574229813684435207239348220522140366126834573803505878170136640646",
    "y2modp": "98931842703096536383023310437099867537616869159883637007323156957547593127931",
    # Mirrored / projected from barcoding.txt (puzzle 160 pattern)
    "m_sha256_a": "14103126014084302816353235822122326996943785814396804931639561917508323422085",
    "m_rmd160": "830235472924759952649828153381049365797114008035",
    "m_sha256_b": "22494257866774545007169672814196531439496086094937776533635309875067145220608",
    "m_sha256_c": "12674348836023742661014272157618088260215617471302779692995492028678801428053",
    "m_addr": "3565834204190937465281520458791678852260145635694276341086",
    "m_proj_addr": "91502620835193259896513599753821211309035045885",
}

DEFAULT_NOTES = Path(r"F:\📝 Notes\160decimals.txt")


def load_barcodes_from_notes(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = dict(BARCODES)
    patterns = [
        (r"x dec\s+(\d+)", "b1_px"),
        (r"RMD160:\s+(\d+)", "b2_rmd160"),
        (r"PUBLIC ADDRESS DEC:\s+(\d+)", "b3_addr"),
        (r"r dec:\s+(\d+)", "b0_r"),
        (r"s dec:\s+(\d+)", "b4_s"),
        (r"message dec:\s+(\d+)", "b5_z"),
        (r"y dec\s+(\d+)", "py"),
        (r"\(y\^2 = x\^3 \+ 7\) mod p dec\s+(\d+)", "y2modp"),
    ]
    for pat, key in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            out[key] = m.group(1)
    return out


def in_range(d: int) -> bool:
    return LO <= d < HI


def branch_point(d: int) -> str | None:
    point = d * G
    if point.x() != TARGET_X:
        return None
    if point.y() == TARGET_Y:
        return "P"
    if point.y() == NEG_Y:
        return "-P"
    return None


def windows(barcodes: dict[str, str], width: int = 41, wrap: bool = True):
    out = []
    for name, s in barcodes.items():
        source = s + (s[: width - 1] if wrap else "")
        max_start = len(s) if wrap else len(s) - width + 1
        for i in range(max_start):
            w = source[i : i + width]
            if len(w) == width:
                out.append((f"{name}[{i}]", int(w)))
    return out


def scan_local(label: str, d0: int, radius: int):
    p0 = d0 * G
    if p0.x() == TARGET_X and p0.y() in (TARGET_Y, NEG_Y):
        b = "P" if p0.y() == TARGET_Y else "-P"
        return f"{label} exact {b}", d0 if b == "P" else (N - d0) % N
    fwd = p0
    bwd = p0
    for i in range(1, radius + 1):
        df = d0 + i
        if df < HI:
            fwd = fwd + G
            if fwd.x() == TARGET_X and fwd.y() in (TARGET_Y, NEG_Y):
                b = "P" if fwd.y() == TARGET_Y else "-P"
                return f"{label}+{i} {b}", df if b == "P" else (N - df) % N
        db = d0 - i
        if db >= LO:
            bwd = bwd + NEG_G
            if bwd.x() == TARGET_X and bwd.y() in (TARGET_Y, NEG_Y):
                b = "P" if bwd.y() == TARGET_Y else "-P"
                return f"{label}-{i} {b}", db if b == "P" else (N - db) % N
    return None


def build_candidates(barcodes: dict[str, str], width: int) -> dict[int, str]:
    wins = windows(barcodes, width=width)
    candidates: dict[int, str] = {}
    for label, val in wins:
        if in_range(val):
            candidates.setdefault(val, label)
    for (la, a), (lb, b) in itertools.combinations(wins, 2):
        for val, tag in [
            ((a + b) // 2, "avg"),
            ((2 * a + b) // 3, "wavg2a"),
            ((a + 2 * b) // 3, "wavg2b"),
            (abs(a - b) + LO, "diff_lo"),
            (abs(a - b) + LO // 2, "diff_mid"),
        ]:
            if in_range(val):
                candidates.setdefault(val, f"{tag}({la},{lb})")
    return candidates, wins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=0, help="local +/- scan around each candidate")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--max-candidates", type=int, default=0)
    ap.add_argument("--barcodes-file", type=Path, default=None)
    ap.add_argument("--notes", type=Path, default=DEFAULT_NOTES)
    ap.add_argument("--list-in-band", action="store_true")
    args = ap.parse_args()

    if args.barcodes_file and args.barcodes_file.is_file():
        import json

        barcodes = json.loads(args.barcodes_file.read_text(encoding="utf-8"))
    elif args.notes.is_file():
        barcodes = load_barcodes_from_notes(args.notes)
    else:
        barcodes = BARCODES

    candidates, wins = build_candidates(barcodes, args.width)
    items = sorted(candidates.items(), key=lambda x: x[0])
    if args.max_candidates:
        items = items[: args.max_candidates]

    print("BARCODE 160 WINDOW/AVERAGE SEARCH")
    print(f"band [{LO}, {HI})  width={args.width}")
    print(f"barcodes: {list(barcodes.keys())}")
    print(f"windows={len(wins)} in_band_candidates={len(items)} radius={args.radius}")

    if args.list_in_band:
        for d, label in items[:50]:
            print(f"  {label}: {d} ({d.bit_length()}b)")
        if len(items) > 50:
            print(f"  ... +{len(items)-50} more")
        if not args.radius and not args.max_candidates:
            return 0

    t0 = time.time()
    checked = 0
    out_path = Path(__file__).resolve().parent / "PUZZLE_160_SOLUTION.txt"

    for idx, (d, label) in enumerate(items, 1):
        if args.radius:
            result = scan_local(label, d, args.radius)
        else:
            b = branch_point(d)
            result = (
                (f"{label} exact {b}", d if b == "P" else (N - d) % N) if b else None
            )
        checked += 1 + (2 * args.radius if args.radius else 0)
        if result:
            method, sol = result
            print("SOLUTION FOUND")
            print(f"candidate={idx}/{len(items)}")
            print(f"method={method}")
            print(f"d={sol}")
            print(f"hex={hex(sol)}")
            out_path.write_text(
                f"method={method}\nd={sol}\nhex={hex(sol)}\n",
                encoding="utf-8",
            )
            return 0
        if idx % 2000 == 0:
            print(f"checked {idx}/{len(items)} elapsed={time.time()-t0:.1f}s")

    print("NO SOLUTION")
    print(f"checked={checked} elapsed={time.time()-t0:.1f}s")
    report = Path(__file__).resolve().parent / "barcode160_candidates_in_band.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write(f"# in-band candidates={len(items)} width={args.width}\n")
        for d, label in items:
            f.write(f"{label}\t{d}\t{hex(d)}\n")
    print(f"Wrote {report}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
