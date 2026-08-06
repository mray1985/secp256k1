#!/usr/bin/env python3
"""Sweep d = f(h160(P_k), eps) for Puzzle 160 — structured index + offset grid."""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band, pubkey_from_scalar, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

D_LO = 1 << 159
D_HI = 1 << 160
OFFSET_96 = 2**56 - 1
P_SHIFT = 5_457_912_602
STEP_56 = 2**56
STEP_57 = 2**57

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)


def check_d_g(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (P160_PUB[:2] == "02") == (y % 2 == 0)

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_h160_eps_sweep.txt"

P160 = 160
lo, hi, top = puzzle_band(P160)
width = hi - lo

H_FRAC = 0.345702
H_HALF = 0.172851
SHOOT_FRACS = (0.6245, 0.5292, 0.6411, 0.6807, 0.7220, 0.4468, 0.8147, 0.642, 0.58)

ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ADDR_ONLY = {
    71: "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU",
    72: "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR",
    73: "12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4",
    74: "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv",
    76: "1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF",
    77: "1Bxk4CQdqL9p22JEtDfdXMsng1XacifUtE",
    78: "15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb",
    79: "1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8",
}

# Index rules: mirror, RSZ spine, band_frac neighbors, high-n pubkeys
K_CANDIDATES = sorted(
    {
        160,
        135,
        125,
        115,
        130,
        150,
        140,
        71,
        72,
        74,
        76,
        59,
        9,
        40,
        51,
        80,
        67,
        65,
        70,
        75,
        80,
        85,
        90,
        100,
        155,
        145,
        # mirror partners
        160 - 135,
        160 - 125,
        160 - 115,
        160 - 71,
        160 - 59,
    }
)


def b58decode_check(addr: str) -> bytes:
    n = 0
    for ch in addr:
        n = n * 58 + ALPH.index(ch)
    full = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = 0
    for ch in addr:
        if ch == "1":
            pad += 1
        else:
            break
    full = b"\x00" * pad + full
    chk = hashlib.sha256(hashlib.sha256(full[:-4]).digest()).digest()[:4]
    if chk != full[-4:]:
        raise ValueError(f"bad checksum {addr}")
    return full[:-4]


def h160_from_pub(pub: str) -> int:
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    return int.from_bytes(digest, "big")


def load_hmap() -> dict[int, int]:
    pubs: dict[int, str] = {}
    for n, row in parse_53125().items():
        if row.px:
            pubs[n] = ("02" if row.py % 2 == 0 else "03") + format(row.px, "064x")
    for n, rsz in PUZZLE_RSZ.items():
        if n not in pubs and rsz.pub_compressed:
            pubs[n] = rsz.pub_compressed
    p160_pub = ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
    if p160_pub.is_file():
        pubs[P160] = p160_pub.read_text(encoding="ascii").strip().splitlines()[0].strip()

    hmap = {n: h160_from_pub(p) for n, p in pubs.items()}
    for n, addr in ADDR_ONLY.items():
        hmap[n] = int.from_bytes(b58decode_check(addr)[1:21], "big")
    return hmap


def band_frac(v: int) -> float:
    if lo <= v < hi:
        return (v - lo) / width
    # treat as fraction of 2^160 for out-of-band anchors
    return (v % (1 << 160)) / float(1 << 160)


def band_from_frac(f: float) -> int:
    f = max(0.0, min(1.0 - 1e-18, f))
    return lo + int(f * (width - 1))


def band_mirror(v: int) -> int:
    """Reflect v's in-band position: bf -> 1-bf."""
    if lo <= v < hi:
        bf = (v - lo) / width
    else:
        bf = band_frac(v)
    return band_from_frac(1.0 - bf)


def small_offsets(k: int) -> list[int]:
    offs = {
        0,
        1,
        -1,
        42,
        -42,
        49,
        76,
        21,
        k,
        -k,
        P160 - k,
        -(P160 - k),
        P160,
        -P160,
        OFFSET_96,
        -OFFSET_96,
        P_SHIFT,
        -P_SHIFT,
        STEP_56,
        -STEP_56,
        STEP_57,
        -STEP_57,
        int(H_FRAC * width),
        int(H_HALF * width),
        -int(H_FRAC * width),
        -int(H_HALF * width),
    }
    for i in range(0, 24):
        offs.add(1 << i)
        offs.add(-(1 << i))
    for i in (32, 40, 48, 56, 57, 58, 59, 96, 128, 155, 158, 159):
        offs.add(1 << i)
        offs.add(-(1 << i))
    return sorted(offs)


def generate_candidates(k: int, h: int, hmap: dict[int, int]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(label: str, d: int) -> None:
        d %= N
        if not (D_LO <= d < D_HI):
            return
        if d in seen:
            return
        seen.add(d)
        out.append((f"P{k}:{label}", d))

    # --- base transforms on h ---
    add("h160", h)
    add("N-h", (N - h) % N)
    add("h|2^159", h | (1 << 159))
    add("h^2^159", h ^ (1 << 159))
    add("band_mirror", band_mirror(h))
    add("lo+frac(h)", band_from_frac(band_frac(h)))

    bf_h = band_frac(h)
    for j, tag in enumerate(("H", "H/2")):
        f = H_FRAC if j == 0 else H_HALF
        add(f"lo+{tag}", band_from_frac(f))
        add(f"lo+{tag}+bf_h", band_from_frac(min(1.0, f + bf_h * 0.1)))

    # shoot window fracs
    for i, f in enumerate(SHOOT_FRACS):
        add(f"shoot_{i}_{f:.4f}", band_from_frac(f))
        add(f"shoot_{i}+bf_h", band_from_frac(min(1.0 - 1e-18, f + (bf_h - 0.5) * 0.02)))

    # lock band_frac from related puzzles
    for j in (P160 - k, k, 59, 125, 135, 115, 71):
        if j in hmap and j != k:
            add(f"bf_lock_P{j}", band_from_frac(band_frac(hmap[j])))

    # --- epsilon grid around h ---
    for eps in small_offsets(k):
        add(f"h+{eps}", h + eps)

    # coarse ladder multiples
    for mult in range(-32, 33):
        if mult == 0:
            continue
        add(f"h+{mult}*STEP56", h + mult * STEP_56)
        add(f"h+{mult}*STEP57", h + mult * STEP_57)

    return out


def main() -> None:
    t0 = time.time()
    hmap = load_hmap()
    lines: list[str] = [
        "P160 sweep: d = f(h160(P_k), eps)",
        f"band [{lo}, {hi})",
        f"index candidates k: {len(K_CANDIDATES)}",
        "",
    ]

    all_cands: list[tuple[str, int]] = []
    for k in K_CANDIDATES:
        if k not in hmap:
            lines.append(f"  skip P{k} (no h160)")
            continue
        h = hmap[k]
        cands = generate_candidates(k, h, hmap)
        all_cands.extend(cands)
        in_band = lo <= h < hi
        lines.append(
            f"  P{k:3d}  h160_bits={h.bit_length()}  in_band={in_band}  "
            f"bf={band_frac(h):.6f}  cands={len(cands)}"
        )

    lines.append("")
    lines.append(f"total unique in-band candidates: {len(all_cands)}")
    lines.append("EC verify (d*G == P160)...")

    hits: list[str] = []
    checked = 0
    for label, d in all_cands:
        checked += 1
        if check_d_g(d):
            hits.append(f"HIT  {label}  d={d}  hex={d:064x}")

    elapsed = time.time() - t0
    lines.append(f"checked {checked} in {elapsed:.1f}s")
    lines.append("")
    lines.append(f"=== HITS: {len(hits)} ===")
    lines.extend(hits or ["  (none)"])

    # nearest to h160(P160) bf for diagnostics
    h160_self = hmap.get(160, 0)
    target_bf = band_frac(h160_self) if h160_self else 0.8147
    ranked = sorted(
        ((abs(band_frac(d) - target_bf), label, d) for label, d in all_cands),
        key=lambda x: x[0],
    )[:12]
    lines.append("")
    lines.append(f"=== closest band_frac to h160(P160)={target_bf:.4f} ===")
    for diff, label, d in ranked:
        lines.append(f"  {label:30s} bf={band_frac(d):.6f}  diff={diff:.6f}")

    text = "\n".join(lines) + "\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
