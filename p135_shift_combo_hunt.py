#!/usr/bin/env python3
"""P135: shelf2 + carry-shift combos (row-2 pattern), EC gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, PuzzleConfig, apply_puzzle_defaults, delta, p, puzzle_band, pubkey_from_scalar
from gap_tier_common import d_candidates_from_offset, observed_offset
from genesis_calibration import bridge_state
from shift_diagnostic import exact_carry_solutions
from compare_family_mirror_batch import build_config
from puzzle_keys_53125 import parse_53125

PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_shift_combo_hunt.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def shifts_mod_lo(cfg, st):
    lo, _, _ = puzzle_band(cfg.puzzle_num)
    row = cfg.row
    px, rx = cfg.Px, cfg.rx
    lam = (px[row] * pow(rx[row], -1, N)) % N
    Qx = [(x * delta) % N for x in px]
    qx = [(x * delta) % N for x in rx]
    return lo, [exact_carry_solutions(lam, qx[i], Qx[i])[0][0] % lo for i in range(3)]


def combos(s1, s2, s3, lo):
    vals = {
        "s1": s1, "s2": s2, "s3": s3,
        "s1+s2": (s1 + s2) % lo,
        "s1-s2": (s1 - s2) % lo,
        "s2-s1": (s2 - s1) % lo,
        "s1+s2+s3": (s1 + s2 + s3) % lo,
        "s2": s2,
    }
    lns = None
    return vals


def ec(d: int) -> bool:
    x, y = pubkey_from_scalar(d)
    return x == PX and y == PY


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    row2 = [15, 35, 45, 50, 70, 90, 100, 120]
    hit_formulas: dict[str, int] = {}

    for n in row2:
        pk = keys[n]
        cfg = build_config(pk)
        st = bridge_state(cfg)
        lo, hi, _ = puzzle_band(n)
        s2 = st["oitc"].shelf2
        o = observed_offset(pk.d, s2, lo)
        _, sm = shifts_mod_lo(cfg, st)
        s1, s2m, s3 = sm
        for name, off in combos(s1, s2m, s3, lo).items():
            if off == o:
                hit_formulas[name] = hit_formulas.get(name, 0) + 1

    log("row-2 offset == combo hits: " + str(hit_formulas))

    cfg = PuzzleConfig(135)
    apply_puzzle_defaults(cfg)
    st = bridge_state(cfg)
    lo, hi, _ = puzzle_band(135)
    s2 = st["oitc"].shelf2
    _, sm = shifts_mod_lo(cfg, st)
    s1, s2m, s3 = sm
    lns = st["lambda_ns"]
    lam_p = (cfg.Px[cfg.row] * pow(cfg.rx[cfg.row], -1, p)) % p
    extra = {
        "gap_row": (lns[cfg.row] - lam_p) % lo,
        "gap_lo": st["gap"] % lo,
    }
    all_offs = {**combos(s1, s2m, s3, lo), **extra}
    log(f"P135 testing {len(all_offs)} offsets (+ direction)")
    for name, off in all_offs.items():
        for d, dr in d_candidates_from_offset(s2, off, lo, hi):
            if dr != "+":
                continue
            if ec(d):
                log(f"*** HIT d={d} [{name}] off_bits={off.bit_length()} ***")
                return 0
            if ec((N - d) % N):
                log(f"*** HIT mirror from d={d} [{name}] ***")
                return 0
            log(f"  {name} off_bits={off.bit_length()} d={format(d,'x')[:20]}... EC=False")

    log("no hit")
    return 1


if __name__ == "__main__":
    sys.exit(main())
