#!/usr/bin/env python3
"""
P135 sqrt-fractional ladder on y_135:

  s = floor(sqrt(n))
  f = sqrt(n) - s
  r2 = floor(f * n)
  n1 = s + r2
  repeat until n1 in [2^134, 2^135), EC gate each hit.
"""

from __future__ import annotations

import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ecdsa import SECP256k1
from puzzle_keys_53125 import parse_53125

getcontext().prec = 300

G = SECP256k1.generator
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LO, HI = 1 << 134, 1 << 135
Y135 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
PX = 9210836494447108270027136741376870869791784014198948301625976867708124077590
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
EX = 61960156549280238354782280810886539078612
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "p135_sqrt_ladder.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def ladder_step(n: int) -> tuple[int, int, int, int]:
    r = Decimal(n).sqrt()
    s = int(r)
    frac = r - s
    r2 = int(frac * n)
    n1 = s + r2
    return n1, s, r2, n1.bit_length()


def ec_hit(d: int) -> bool:
    for x in (d, (N - d) % N):
        if not (LO <= x < HI):
            continue
        pt = x * G
        if pt.x() == PX and pt.y() == PY:
            return True
    return False


def run_ladder(start: int, name: str, max_steps: int = 500) -> int:
    log(f"=== ladder from {name} start_bits={start.bit_length()} ===")
    n = start
    band_hits: list[tuple[int, int]] = []
    for step in range(max_steps):
        n1, s, r2, bits = ladder_step(n)
        in_band = LO <= n1 < HI
        log(
            f"  step {step}: s_bits={s.bit_length()} r2_bits={r2.bit_length()} "
            f"n1_bits={bits} in_band={in_band}"
        )
        if in_band:
            band_hits.append((step, n1))
            hit = ec_hit(n1)
            log(f"    BAND d={n1} EC={hit}")
            if hit:
                log(f"*** HIT d={n1} step={step} from {name} ***")
                return 0
        if n1 >= n and step > 0:
            log(f"  stop: n1 >= n at step {step}")
            break
        if n1.bit_length() < 100:
            log(f"  stop: collapsed at step {step}")
            break
        n = n1

    log(f"  band hits: {len(band_hits)}")
    return 1


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log("P135 sqrt-fractional ladder")

    # User example verification
    n1, s, r2, _ = ladder_step(EX)
    log(f"EX step0: s={s} r2={r2} n1={n1}")
    log(f"  user n1=27021670877058826554937076559869210115698")

    starts = [
        ("y_135", Y135),
        ("EX", EX),
        ("user_n1_EX", 27021670877058826554937076559869210115698),
        ("ladder_n1_EX", n1),
    ]
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    ysq = (Y135 * Y135 - 7) % p
    starts.append(("y_sq_mod_p_low136", ysq % (1 << 136)))

    for name, start in starts:
        if run_ladder(start, name) == 0:
            return 0

    log("no EC hit")
    return 1


if __name__ == "__main__":
    sys.exit(main())
