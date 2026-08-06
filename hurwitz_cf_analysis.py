#!/usr/bin/env python3
"""
Analyze Hurwitz continued fractions from sec(N)^priv^-1 (cntdfractionspuzzles.txt).

Hypothesis for collapse at high n:
  z ≈ sec(N°)^(1/d)  with sec = 1/cos in degrees
  => z ≈ 1 + (1/d)*log(sec(N°))  => single large Gaussian partial quotient.
"""

from __future__ import annotations

import cmath
import math
import re
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_keys_53125 import parse_53125

getcontext().prec = 80

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
CF_PATH = ROOT / "00_Projects" / "patent" / "cntdfractionspuzzles.txt"


def parse_gaussian(s: str) -> complex:
    s = s.strip().replace(" ", "").replace("\n", "")
    if not s:
        raise ValueError("empty")
    if s in ("i", "+i"):
        return 1j
    if s == "-i":
        return -1j
    if "i" not in s:
        return complex(int(s))
    s = s.replace("i", "j")
    if s[0] not in "+-":
        s = "+" + s
    return complex(s)


def hurwitz_eval(terms: list[complex]) -> complex:
    """[a0; a1, a2, ...] Hurwitz."""
    if not terms:
        return 0j
    v = terms[-1]
    for t in reversed(terms[1:-1]):
        v = t + 1.0 / v
    if len(terms) == 1:
        return terms[0]
    return terms[0] + 1.0 / v


def parse_cf_line(line: str) -> tuple[int, list[complex]]:
    m = re.match(r"(\d+):\s*\[(.+)\]\s*$", line.replace("\n", " "))
    if not m:
        raise ValueError(f"bad line: {line[:80]}")
    n = int(m.group(1))
    body = m.group(2)
    if ";" in body:
        a0_s, rest = body.split(";", 1)
        parts = [a0_s.strip()] + [p.strip() for p in rest.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in body.split(",") if p.strip()]
    terms = [parse_gaussian(p) for p in parts]
    return n, terms


def load_cf(path: Path) -> dict[int, list[complex]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    out: dict[int, list[complex]] = {}
    buf = ""
    for line in raw.splitlines():
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1]
            continue
        buf += line
        if re.match(r"^\d+:\s*\[", buf.strip()):
            chunk = buf.split("(using")[0].strip()
            chunk = re.sub(r"\s+", " ", chunk)
            try:
                n, terms = parse_cf_line(chunk)
                out[n] = terms
            except Exception as e:
                pass
        buf = ""
    return out


def sec_deg(x: float) -> float:
    r = math.cos(math.radians(x))
    if abs(r) < 1e-15:
        return float("inf")
    return 1.0 / r


def z_model_sec_power(d: int, angle_mode: str = "N_mod_360") -> complex:
    if angle_mode == "N_mod_360":
        ang = N % 360
    elif angle_mode == "n":
        ang = d  # placeholder replaced by caller
    else:
        ang = float(angle_mode)
    s = sec_deg(ang)
    if s <= 0:
        s = abs(s)
    # z = s^(1/d) via exp(log(s)/d)
    return cmath.exp(cmath.log(s) / d)


def z_model_csc_angle(d: int, n: int) -> complex:
    """From 130break-in: exponent uses csc(7π/180) for P130 — test n-scaled angle."""
    # 7 for P130: 7 = 130 - 123? or gcd. Try 7 = n // 18 rounded?
    k = round(7 * n / 130) if n else 7
    theta = k * math.pi / 180
    csc = 1.0 / math.sin(theta)
    return cmath.exp(cmath.log(csc) / d)


def main() -> None:
    keys = parse_53125()
    cfs = load_cf(CF_PATH)
    lines = [
        "HURWITZ CF ANALYSIS — sec(N)^priv^-1",
        f"parsed {len(cfs)} puzzles from {CF_PATH.name}",
        "",
        "=== CF length & first quotient (real, imag, |imag/real|) ===",
    ]

    for n in sorted(cfs):
        terms = cfs[n]
        q1 = terms[1] if len(terms) > 1 else None
        d = keys[n].d if n in keys else None
        ir = ""
        if q1 is not None and q1.real != 0:
            ir = f"{abs(q1.imag / q1.real):.6f}"
        lines.append(
            f"  P{n:3d}  len={len(terms):3d}  a0={terms[0]}  "
            f"q1={q1 if q1 is not None else '-'}  imag/real={ir}  d_bits={d.bit_length() if d else '-'}"
        )

    lines += ["", "=== Collapsed puzzles (only a0 + one partial quotient) ==="]
    for n in sorted(cfs):
        if len(cfs[n]) == 2:
            q1 = cfs[n][1]
            lines.append(f"  P{n:3d}  q1_real={int(q1.real)}  q1_imag={int(q1.imag)}")

    lines += ["", "=== imag/real ratio of q1 (|im/re|) for n>=70 ==="]
    ratios = []
    for n in sorted(cfs):
        if n < 70 or len(cfs[n]) < 2:
            continue
        q1 = cfs[n][1]
        if q1.real:
            r = abs(q1.imag / q1.real)
            ratios.append((n, r))
            lines.append(f"  P{n:3d}  |im/re|={r:.8f}")
    if ratios:
        rs = [r for _, r in ratios]
        lines.append(f"  mean={sum(rs)/len(rs):.8f}  ~3/2={1.5}")

    lines += ["", "=== Reconstruct z = [a0;q1] for collapsed n ==="]
    for n in (115, 120, 125, 130):
        if n not in cfs:
            continue
        terms = cfs[n]
        z = hurwitz_eval(terms)
        d = keys[n].d
        lines.append(f"  P{n}  z≈{z}")
        lines.append(f"       |z-1|={abs(z-1):.6e}")
        ang = N % 360
        s = sec_deg(ang)
        z_sec = cmath.exp(cmath.log(s) / d) if d else 0
        lines.append(f"       sec(N°)^(1/d) real={z_sec.real:.12f} imag={z_sec.imag:.12e}")
        lines.append(f"       N mod 360 = {ang}  sec(N°)={s:.10f}")

    lines += ["", "=== Closed form (sec(N°)^(1/d), N mod 360 = 97, sec = -8.2055…) ==="]
    ang = N % 360
    secv = sec_deg(ang)
    ln = math.log(abs(secv))
    pi = math.pi
    slope = pi / ln
    c_rd = ln / (ln * ln + pi * pi)
    lines.append(f"  |q1_imag/q1_real| -> pi/ln|sec| = {slope:.12f}")
    lines.append(f"  q1_real/d -> ln|sec|/(ln^2+pi^2) = {c_rd:.15f}")
    lines.append(f"  z = sec(N°)^(1/d) = exp((ln|sec|+i*pi)/d)  [sec<0]")
    lines.append(f"  q1 = GaussIntNearest( d / (ln|sec| + i*pi) )")

    lines += ["", "=== Verify closed form vs file (P70, P115, P130) ==="]
    for n in (70, 115, 130):
        if n not in keys or n not in cfs:
            continue
        d = keys[n].d
        pred_r = int(round(d * c_rd))
        pred_i = int(round(-d * pi / (ln * ln + pi * pi)))
        q1 = cfs[n][1]
        lines.append(
            f"  P{n}  pred=({pred_r}, {pred_i})  file=({int(q1.real)}, {int(q1.imag)})"
        )

    lines += ["", "=== P135+ prediction (unsolved d: CF collapses to [1; q1] only) ==="]
    lines.append(
        "  When priv d is known: q1_real = round(d * 0.14719115239541897)"
    )
    lines.append(
        "                    q1_imag = round(-d * pi / (ln^2+pi^2))"
    )
    lines.append(f"  CF length ~2 for d >> 10^38 (|z-1| ~ 1/d)")
    for n in [70, 115, 120, 125, 130]:
        if n not in cfs or n not in keys:
            continue
        d = keys[n].d
        q1 = cfs[n][1]
        qr = int(q1.real)
        lines.append(f"  P{n}:")
        lines.append(f"    q1_real / d = {Decimal(qr) / Decimal(d)}")
        lines.append(f"    q1_real * d / N = {Decimal(qr) * Decimal(d) / Decimal(N)}")
        lines.append(f"    q1_real / 2^n = {Decimal(qr) / Decimal(2**n)}")
        lines.append(f"    q1_real / 2^(n-1) = {Decimal(qr) / Decimal(2**(n-1))}")

    out = ROOT / "ARCHIVE" / "hurwitz_cf_analysis.txt"
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    print(f"\nwrote {out}", flush=True)


if __name__ == "__main__":
    main()
