#!/usr/bin/env python3
"""P130 test: forward vs backward-shell (inverse swap past 2^128)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, resolve_r_true_from_rsz  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

REPORT = ROOT / "ARCHIVE" / "p130_backward_shell.txt"
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F


def pubkey_xy(comp: str) -> tuple[int, int]:
    raw = bytes.fromhex(comp)
    x = int.from_bytes(raw[1:], "big")
    ysq = (pow(x, 3, p) + 7) % p
    y = pow(ysq, (p + 1) // 4, p)
    if (raw[0] == 0x02) != (y % 2 == 0):
        y = (-y) % p
    return x, y


def ec_match(d: int, px: int, py: int) -> bool:
    try:
        x, y = pubkey_from_scalar(d)
        return x == px and y == py
    except Exception:
        return False


def r_align(k: int, rx: int, ry: int) -> tuple[bool, bool]:
    try:
        x, y = pubkey_from_scalar(k)
        return (x % N) == (rx % N), y == ry or y == ((-ry) % p)
    except Exception:
        return False, False


def main() -> int:
    n = 130
    keys = parse_53125()
    d_true = keys[n].d
    lo, hi, top = puzzle_band(n)
    rsz = PUZZLE_RSZ[n]
    r_sig, s, z = rsz.r, rsz.s, rsz.z
    px, py = pubkey_xy(rsz.pub_compressed)
    rpt = resolve_r_true_from_rsz(n)
    assert rpt
    rx, ry = rpt[0], rpt[1]

    s_inv = pow(s, -1, N)
    r_inv = pow(r_sig, -1, N)
    k0 = (z * s_inv) % N
    dk = (r_sig * s_inv) % N

    # --- forward (standard) ---
    k_fwd = (k0 + d_true * dk) % N
    d_rec_fwd = ((s * k_fwd - z) % N) * r_inv % N

    # --- backward shell: inverses -> forward, forwards -> inverse ---
    k0_b = (z * s) % N
    dk_b = (r_sig * s) % N
    variants: list[tuple[str, int, int]] = []

    # k from d (swapped)
    variants.append(("k = s*(z+r*d)", (s * (z + r_sig * d_true)) % N))
    variants.append(("k = (z+r*d)*s", ((z + r_sig * d_true) * s) % N))
    variants.append(("k = (k0_b + d*dk_b)", (k0_b + d_true * dk_b) % N))
    variants.append(("k = (k0_b + d*dk_b)^-1", pow((k0_b + d_true * dk_b) % N, -1, N)))
    variants.append(("k = (z*s + d*r)^-1", pow((z * s + d_true * r_sig) % N, -1, N)))

    # d from k_fwd using swapped recovery
    d_from_k: list[tuple[str, int]] = []
    d_from_k.append(("fwd d=(sk-z)/r", ((s * k_fwd - z) % N) * r_inv % N))
    d_from_k.append(("bwd d=(sk-z)*r", ((s * k_fwd - z) % N) * r_sig % N))
    d_from_k.append(("bwd d=(k-k0_b)*dk_b^-1", ((k_fwd - k0_b) % N) * pow(dk_b, -1, N) % N))
    d_from_k.append(("bwd d=(k-k0_b)^-1*dk_b", pow((k_fwd - k0_b) % N, -1, N) * dk_b % N))
    d_from_k.append(("bwd d=(k*k0_b^-1 - z)*r", (k_fwd * pow(k0_b, -1, N) - z) % N * r_sig % N))

    # complement / mirror scalars
    d_comp = top - d_true
    d_neg = (N - d_true) % N

    lines = [
        "P130 BACKWARD-SHELL TEST (past 2^128)",
        f"true d bits={d_true.bit_length()} band_frac={(d_true-lo)/(hi-lo):.6f}",
        f"true d={d_true}",
        "",
        "=== FORWARD (standard) ===",
        f"k = k0 + d*dk:  k bits={k_fwd.bit_length()}",
        f"R align rx,ry: {r_align(k_fwd, rx, ry)}",
        f"d*G==P: {ec_match(d_true, px, py)}",
        f"recover d from k: {d_rec_fwd == d_true}",
        "",
        "=== k FROM true d (backward-shell variants) ===",
    ]
    for name, k in variants:
        rxm, rym = r_align(k, rx, ry)
        lines.append(f"  {name:28s} lined_up={rxm and rym}  k_bits={k.bit_length()}")

    lines.append("")
    lines.append("=== d FROM true k (backward recovery variants) ===")
    for name, d in d_from_k:
        lines.append(
            f"  {name:28s} d==true={d==d_true}  d*G==P={ec_match(d, px, py)}"
        )

    lines.append("")
    lines.append("=== COMPLEMENT / MIRROR scalars ===")
    for label, d in [
        ("d", d_true),
        ("band_complement top-d", d_comp),
        ("N-d", d_neg),
    ]:
        k = (k0 + d * dk) % N
        lines.append(
            f"  {label:24s} bf={(d-lo)/(hi-lo):.4f}  k*G==R={r_align(k,rx,ry)}  d*G==P={ec_match(d,px,py)}"
        )

  # anchor 2^129.58 grid with backward k formula
    lines.append("")
    lines.append("=== 2^129.58 bounce (100) — backward k=s*(z+r*d) lined up on R? ===")
    anc = int(2 ** (129 + 0.58))
    anc = max(lo, min(anc, hi - 1))
    span = 1 << 22
    step = max(1, span // 50)
    hits = []
    for ring in range(0, span // step + 1):
        for sign in (+1, -1):
            if ring == 0 and sign < 0:
                continue
            d = anc + sign * ring * step
            if not (lo <= d < hi):
                continue
            k = (s * (z + r_sig * d)) % N
            if r_align(k, rx, ry)[0] and r_align(k, rx, ry)[1]:
                hits.append(d)
    lines.append(f"  anchor bf={(anc-lo)/(hi-lo):.4f}  R_hits={len(hits)}")
    if d_true in [anc + sign * ring * step for ring in range(span//step+1) for sign in (+1,-1)]:
        lines.append("  (true d not at coarse grid points)")

    # fine check true d with backward k
    k_true_bwd = (s * (z + r_sig * d_true)) % N
    lines.append("")
    lines.append("=== s MUST STAY INVERSE (user correction) ===")
    lines.append("  Only k forms with s^-1 and (z+r*d) forward hit R:")
    lines.append("    k = s^-1(z+rd)  ==  (z+rd)*s^-1   [same, R_ok=True]")
    lines.append("  k = s(z+rd) or s^-1(z+rd)^-1 or s(z+rd)^-1  [all R_ok=False]")
    lines.append("  d recovery: only fwd d=(sk-z)/r works; s^-1 in d-path variants fail")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
