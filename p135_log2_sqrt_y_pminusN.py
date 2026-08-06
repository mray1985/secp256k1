#!/usr/bin/env python3
"""log2(sqrt(Py)) vs log2(p-N) analysis + sqrt(y) flip EC test for P135."""

from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from bucket_slice_search import band_midpoint, verify_candidate  # noqa: E402
from ecdlp_full_pipeline import puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
LOG2_SQRT_Y = Decimal("127.33957572369160989277861220187748116567052430661080322039981")
LOG2_P_MINUS_N = Decimal("128.34570214660884155727994158781146915925012929756885086000832493")
REPORT = ROOT / "ARCHIVE" / "p135_log2_sqrt_y_pminusN.txt"


def isqrt(n: int) -> int:
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def main() -> int:
    getcontext().prec = 80
    pn = P - N
    sqrt_y = isqrt(PY)
    lo, hi, _ = puzzle_band(135)
    mid = band_midpoint(lo, hi)
    delta = LOG2_P_MINUS_N - LOG2_SQRT_Y

    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn

    log2_pn_calc = Decimal(pn).ln() / Decimal(2).ln()
    log2_sy_calc = (Decimal(PY).ln() / Decimal(2).ln()) / 2

    lines = [
        "P135 log2(sqrt(y)) vs log2(p-N)",
        "",
        f"Py tail ...{str(PY)[-6:]}",
        f"sqrt(Py) = {sqrt_y}",
        f"p - N = {pn}  ({pn.bit_length()} bits)",
        "",
        "log2 values (user vs computed):",
        f"  log2(sqrt(y))  user {LOG2_SQRT_Y}",
        f"  log2(sqrt(y))  calc {log2_sy_calc}",
        f"  log2(p-N)      user {LOG2_P_MINUS_N}",
        f"  log2(p-N)      calc {log2_pn_calc}",
        f"  log2(p) - log2(N) = {(Decimal(P).ln()-Decimal(N).ln())/Decimal(2).ln()}  (ratio gap, ~0 at float64)",
        "",
        f"delta = log2(p-N) - log2(sqrt(y)) = {delta}",
        f"delta - 1 = {delta - 1}  (offset past one bit in log2 space)",
        "",
        "Normalize by 256 (bit-height axis):",
        f"  log2(sqrt(y))/256 = {float(LOG2_SQRT_Y/256):.8f}",
        f"  log2(p-N)/256     = {float(LOG2_P_MINUS_N/256):.8f}",
        f"  delta/256         = {float(delta/256):.8f}",
        f"  135/256 (Case1)   = {135/256:.8f}",
        "",
        "sqrt(y) flip corridor (only 101 m values):",
    ]

    u = sqrt_y
    m_start = (lo + u - 1) // u
    m_end = (hi - 1) // u
    hits = []
    for m in range(m_start, m_end + 1):
        d = m * u
        frac = (d - lo) / lo
        log_pos = math.log2(d) - 134
        ok = verify_candidate(d, px, py)
        if ok:
            hits.append((m, d))
        if m in (m_start, m_start + (m_end - m_start) // 2, m_end) or ok:
            lines.append(
                f"  m={m:3d} frac_d={frac:.6f} log_pos={log_pos:.6f} upper={d>=mid} ec={ok}"
            )

    # anchors from delta
    lines.append("")
    lines.append("d anchors from log delta:")
    anchors = [
        ("LO * 2^(delta-1)", lo * (2 ** float(delta - 1))),
        ("LO * (1 + (delta-1))", lo * (1 + float(delta - 1))),
        ("LO * log2(sqrt(y))/log2(p-N)", lo * float(LOG2_SQRT_Y / LOG2_P_MINUS_N)),
        ("mid * 2^(delta-1)", mid * (2 ** float(delta - 1))),
    ]
    for tag, d_f in anchors:
        d = int(d_f)
        if lo <= d < hi:
            ok = verify_candidate(d, px, py)
            lines.append(
                f"  {tag}: frac={(d-lo)/lo:.6f} log_pos={math.log2(d)-134:.6f} ec={ok}"
            )
            if ok:
                hits.append((-1, d))

    lines.extend(["", f"EC hits: {len(hits)}"])
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
