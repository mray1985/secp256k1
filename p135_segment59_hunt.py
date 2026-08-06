#!/usr/bin/env python3
"""P135: try decimal 59,450,174,... as segment 59F04F28B offset / scalar / lift splice."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdsa import SECP256k1
from puzzle_keys_53125 import parse_53125
from p135_f97_nibble_lift import (
    calibrate_f97_nibbles,
    calibrate_segment_offsets,
    f97_pattern,
    lane68_variants,
    lift_with_f97_nibbles,
)
from p135_p130_tail_calibrate import (
    SEGMENTS,
    ec_hit,
    extract_segment,
    lane68_candidates,
    lift_all,
)

G = SECP256k1.generator
V = 59_450_174_081_283_062_889_886_570_312_404
PARTS = [59, 450, 174, 81, 283, 62, 889, 886, 570, 312, 404]
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_segment59_hunt.log"
LO, TOP = 1 << 134, (1 << 135) - 1
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SHELF2 = 35959002268835125861687979158600974388545


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def try_d(name: str, d: int) -> bool:
    for x in (d, (N - d) % N):
        if LO <= x <= TOP:
            h = ec_hit(x)
            if h:
                log(f"*** HIT d={h} [{name}] ***")
                return True
    return False


def try_lift(name: str, lift: str, seen: set[int]) -> bool:
    for d in list(lane68_candidates(lift)) + [x[1] for x in lane68_variants(lift)]:
        if d in seen:
            continue
        seen.add(d)
        if try_d(f"{name}/lane68", d):
            return True
    hx = lift.lstrip("0") or "0"
    if len(hx) <= 34:
        d = int(hx.ljust(34, "0")[:34], 16)
        if LO <= d <= TOP and d not in seen:
            seen.add(d)
            if try_d(f"{name}/raw", d):
                return True
    return False


def seg59_pattern() -> str:
    for label, pat, _ in SEGMENTS:
        if label == "59F04F28B":
            return pat
    raise KeyError("59F04F28B")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    x135 = format(keys[135].px, "x")
    y135 = format(keys[135].py, "x")
    k130 = keys[130]
    priv130 = format(k130.d, "x").lower().lstrip("0")
    seg130 = calibrate_segment_offsets(
        format(k130.px, "x"), format(k130.py, "x"), priv130
    )
    f97_offs, _ = calibrate_f97_nibbles(x135, y135, f97_pattern(), "f897c603")
    pat59 = seg59_pattern()
    plen = len(pat59)
    seen: set[int] = set()

    log(f"V={V} bits={V.bit_length()} hex={format(V,'x')}")
    log(f"segment59 pattern len={plen}")

    # --- scalar candidates ---
    log("=== scalar EC ===")
    scalars = [
        ("V", V),
        ("shelf2+V", (SHELF2 + V) % N),
        ("shelf2-V", (SHELF2 - V) % N),
        ("LO+(V mod LO)", LO + (V % LO)),
        ("59f04f28b", int("59f04f28b", 16)),
        ("LO+59f04f28b", LO + int("59f04f28b", 16)),
        ("V xor 59f04f28b", V ^ int("59f04f28b", 16)),
    ]
    for name, d in scalars:
        if try_d(name, d):
            return 0

    # --- segment 59 offsets from comma groups ---
    log("=== segment 59F04F28B offset sweeps ===")
    offset_triples = [
        ("59,450", (59, 450)),
        ("174,81", (174, 81)),
        ("283,62", (283, 62)),
        ("889,886", (889, 886)),
        ("570,312", (570, 312)),
        ("404,0", (404, 0)),
        ("V%plen,(V//plen)%plen", (V % plen, (V // plen) % plen)),
        ("450,59", (450, 59)),
    ]
    for name, (xo, yo) in offset_triples:
        offs = list(seg130)
        idx = next(i for i, (lab, _, _) in enumerate(SEGMENTS) if lab == "59F04F28B")
        offs[idx] = (xo, yo)
        lift = lift_with_f97_nibbles(x135, y135, offs, f97_pattern(), f97_offs)
        seg = extract_segment(x135, y135, pat59, xo, yo)
        log(f"  {name} xo={xo} yo={yo} seg={seg} lift={lift}")
        if try_lift(name, lift, seen):
            return 0

    # --- inject decimal/hex as fixed 59F04F28B target ---
    log("=== fixed segment injection ===")
    dec_str = str(V)
    inject_targets = [
        ("dec9", dec_str[:9]),
        ("dec9_tail", dec_str[-9:]),
        ("hex9", format(V, "x")[:9].ljust(9, "0")),
        ("hex9_tail", format(V, "x")[-9:].rjust(9, "0")),
        ("59f04f28b", "59f04f28b"),
        ("parts_hex", "".join(format(p, "x") for p in PARTS)[:9].ljust(9, "0")),
    ]
    head = "".join(
        extract_segment(x135, y135, pat, xo, yo)
        for (lab, pat, _), (xo, yo) in zip(SEGMENTS, seg130)
        if lab != "59F04F28B"
    )
    # rebuild lift with injected seg59
    pos = 0
    parts_lift: list[str] = []
    for (lab, _pat, n), (xo, yo) in zip(SEGMENTS, seg130):
        if lab == "59F04F28B":
            continue
        if lab == "F97C03":
            from p135_f97_nibble_lift import extract_f97_nibbles

            parts_lift.append(extract_f97_nibbles(x135, y135, f97_pattern(), f97_offs))
        elif lab == "C9":
            parts_lift.append(priv130[-2:])
        else:
            parts_lift.append(
                extract_segment(x135, y135, _pat, xo, yo)
            )
    # simpler: splice into calibrated lift
    base = lift_with_f97_nibbles(x135, y135, seg130, f97_pattern(), f97_offs)
    idx59_start = 4 + 3 + 2 + 2  # 33E7+665+70+53 = 11 hex chars
    for iname, tgt in inject_targets:
        if len(tgt) != 9:
            continue
        lift = base[:idx59_start] + tgt.lower() + base[idx59_start + 9 :]
        log(f"  inject {iname} -> {lift}")
        if try_lift(iname, lift, seen):
            return 0

    # --- lane68 with 59 prefix from decimal ---
    lift68 = "68" + base[2:]
    lift59 = "59" + base[2:] if base else base
    for name, lift in [("lane68_base", lift68), ("lane59_base", lift59)]:
        log(f"  {name} {lift}")
        if try_lift(name, lift, seen):
            return 0

    log(f"DONE no hit ({len(seen)} d tried)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
