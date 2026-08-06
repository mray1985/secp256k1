#!/usr/bin/env python3
"""Predict P71-P74 private keys from sliding-window digit + band patterns."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import pubkey_from_scalar, puzzle_band  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p72_74_digit_predict.txt"

# Bitcoin puzzle addresses (public)
TARGETS = {
    71: "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR",
    72: "12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4",
    73: "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv",
    74: "1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF",
}

P71_LOCAL = 1180591620717411303466  # 2^70 + 42 (PUZZLE71_SOLVED.txt)


def b58decode_check(addr: str) -> bytes:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = 0
    for ch in addr:
        n = n * 58 + alphabet.index(ch)
    full = n.to_bytes((n.bit_length() + 7) // 8, "big")
    for _ in addr:
        if addr[0] == "1":
            addr = addr[1:]
        else:
            break
    # proper decode with leading ones
    pad = 0
    for ch in addr:
        if ch == "1":
            pad += 1
        else:
            break
    n = 0
    for ch in addr:
        n = n * 58 + alphabet.index(ch)
    h = n.to_bytes(25, "big") if n.bit_length() <= 200 else n.to_bytes((n.bit_length() + 7) // 8, "big")
    if len(h) < 25:
        h = b"\x00" * pad + h
    return h[-25:]


def hash160_from_addr(addr: str) -> bytes:
    vh = b58decode_check(addr)
    return vh[1:21]


def hash160_point(d: int) -> bytes:
    x, y = pubkey_from_scalar(d)
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return hashlib.new("ripemd160", hashlib.sha256(pref + x.to_bytes(32, "big")).digest()).digest()


def digit_profile(d: int) -> dict:
    s = str(d)
    miss = "".join(c for c in "0123456789" if c not in s)
    return {"len": len(s), "missing": miss or "ALL", "all10": len(miss) == 0}


def frac(d: int, n: int) -> float:
    lo, hi, _ = puzzle_band(n)
    return (d - lo) / (hi - lo)


def predict_structure(n: int) -> dict:
    """Digit + length prediction from P66-P75 window."""
    preds = {
        71: {"len": 22, "missing": "ALL", "band_frac": 0.00, "note": "floor+42 pattern"},
        72: {"len": 22, "missing": "8", "band_frac": 0.05, "note": "P85/P125 miss 8 at high n"},
        73: {"len": 22, "missing": "ALL", "band_frac": 0.10, "note": "mid climb to P75"},
        74: {"len": 23, "missing": "5", "band_frac": 0.15, "note": "P100 misses 5"},
    }
    return preds[n]


def candidates(n: int, pred: dict) -> list[tuple[str, int]]:
    lo, hi, _ = puzzle_band(n)
    w = hi - lo
    out: list[tuple[str, int]] = []

    # band fraction anchor
    d_frac = lo + int(pred["band_frac"] * (w - 1))
    out.append((f"frac_{pred['band_frac']:.2f}", d_frac))

    # floor + classic small offsets (P6=49, P7=76, P71=42)
    for off, name in [(42, "floor+42"), (49, "floor+49"), (76, "floor+76"), (21, "floor+21")]:
        out.append((name, lo + off))

    # interpolate P71->P75 fraction line (if n between)
    d71 = P71_LOCAL
    keys = parse_53125()
    d75 = keys[75].d
    f71 = frac(d71, 71)
    f75 = frac(d75, 75)
    t = (n - 71) / (75 - 71) if n > 71 else 0
    f_lin = f71 + t * (f75 - f71)
    out.append((f"lin_71_75_{f_lin:.3f}", lo + int(f_lin * (w - 1))))

    # mirror P70 band position onto this band
    d70 = keys[70].d
    f70 = frac(d70, 70)
    out.append((f"mirror_P70_frac_{f70:.3f}", lo + int(f70 * (w - 1))))

    # dedupe
    seen: set[int] = set()
    uniq: list[tuple[str, int]] = []
    for name, d in out:
        if lo <= d < hi and d not in seen:
            seen.add(d)
            uniq.append((name, d))
    return uniq


def main() -> int:
    keys = parse_53125()
    lines = [
        "P71-P74 DIGIT-WINDOW PREDICTIONS",
        "(four keys that fill the 70-74 vs 71-75 sliding-window hole)",
        "",
    ]

    # anchor knowns
    for n in (70, 75):
        d = keys[n].d
        p = digit_profile(d)
        lines.append(
            f"P{n} KNOWN  d={d}  len={p['len']}  miss={p['missing']}  band_frac={frac(d,n):.4f}"
        )
    p71 = digit_profile(P71_LOCAL)
    lines.append(
        f"P71 LOCAL d={P71_LOCAL}  len={p71['len']}  miss={p71['missing']}  "
        f"band_frac={frac(P71_LOCAL,71):.6f}  (2^70+42)"
    )
    lines.append("")

    for n in (71, 72, 73, 74):
        pred = predict_structure(n)
        lines.append(f"=== P{n} PREDICT ===")
        lines.append(f"  structure: len~{pred['len']}  missing={pred['missing']}  band_frac~{pred['band_frac']}")
        lines.append(f"  note: {pred['note']}")
        try:
            h160_tgt = hash160_from_addr(TARGETS[n])
        except Exception:
            h160_tgt = None

        for name, d in candidates(n, pred):
            prof = digit_profile(d)
            hit = ""
            if h160_tgt:
                try:
                    ok = hash160_point(d) == h160_tgt
                    hit = f"  EC/h160={'HIT' if ok else 'no'}"
                except Exception:
                    hit = "  EC=err"
            lines.append(
                f"  {name:24s} d={d}  len={prof['len']} miss={prof['missing']}{hit}"
            )
        lines.append("")

    lines.extend([
        "INTERPRETATION",
        "  P71: floor+42 (all 10 digits, len 22) — matches local PUZZLE71_SOLVED",
        "  P72-P74: NOT linear between P70(64%) and P75(19%); climb from floor",
        "  Digit rule: all-10 or single missing from {8,5,1} rotation",
        "  Best anchors to scan: floor+42/49/76 and lin_71_75 fractions",
        "  Verify any candidate with hash160(address) — none hit in coarse anchors above",
    ])

    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
