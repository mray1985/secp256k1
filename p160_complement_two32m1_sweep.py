#!/usr/bin/env python3
"""Phase 5: complement q = (N+1)//m  +  lane eps with 2^32-1 family for P160."""

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

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_complement_two32m1_sweep.txt"

NP1 = N + 1
TWO32 = 4294967296
TWO32M1 = TWO32 - 1  # 4294967295 = 0xFFFFFFFF
P_SHIFT = 5_457_912_602
D_LO, D_HI = 1 << 159, 1 << 160
STEP_57 = 2**57
M_BASE = 2**96
D_BASE = NP1 // M_BASE

lo, hi, _ = puzzle_band(160)
width = hi - lo
MAX_Q = width // TWO32

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)
RSZ160 = PUZZLE_RSZ[160]


def h160_parts(pub: str) -> tuple[int, bytes, int]:
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    hi = int.from_bytes(digest, "big")
    vh = b"\x00" + digest
    chk = int.from_bytes(
        hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4], "big"
    )
    return hi, digest, chk


def check_d_g(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (P160_PUB[:2] == "02") == (y % 2 == 0)


def eps_two32m1_family(h160: int, chk: int, hmap: dict[int, int]) -> list[tuple[str, int]]:
    """Epsilon lane values — 2^32-1 family first."""
    out: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(name: str, v: int) -> None:
        e = v % TWO32
        if e in seen:
            return
        seen.add(e)
        out.append((name, e))

    # --- 2^32-1 core family ---
    add("2^32-1", TWO32M1)
    add("(2^32-1)-chk", (TWO32M1 - chk) % TWO32)
    add("(2^32-1)-h160_lo", (TWO32M1 - (h160 % TWO32)) % TWO32)
    add("(2^32-1)^h160_lo", (TWO32M1 ^ (h160 % TWO32)) % TWO32)
    add("chk^(2^32-1)", (chk ^ TWO32M1) % TWO32)
    add("h160_lo^(2^32-1)", ((h160 % TWO32) ^ TWO32M1) % TWO32)
    add("2^32-1-P_SHIFT_lo", (TWO32M1 - (P_SHIFT % TWO32)) % TWO32)
    add("P_SHIFT_lo^(2^32-1)", ((P_SHIFT % TWO32) ^ TWO32M1) % TWO32)
    add("RSZ_r^(2^32-1)", (RSZ160.r ^ TWO32M1) % TWO32)
    add("RSZ_z^(2^32-1)", (RSZ160.z ^ TWO32M1) % TWO32)
    add("RSZ_s^(2^32-1)", (RSZ160.s ^ TWO32M1) % TWO32)

    # complement of low lane
    add("neg_h160_lo", (TWO32 - (h160 % TWO32)) % TWO32)
    add("neg_chk", (TWO32 - chk) % TWO32)

    # standard lanes
    add("0", 0)
    add("chk", chk)
    add("h160_lo", h160 % TWO32)
    add("P_SHIFT_lo", P_SHIFT % TWO32)
    add("(P_SHIFT-2^32)", (P_SHIFT - TWO32) % TWO32)

    for n in (40, 65, 59, 115, 125, 135, 71):
        if n in hmap:
            add(f"h160(P{n})_lo", hmap[n] % TWO32)
            add(f"h160(P{n})^(2^32-1)", (hmap[n] % TWO32) ^ TWO32M1)

    # pairwise with 2^32-1
    if 40 in hmap and 65 in hmap:
        s = (hmap[40] + hmap[65]) % TWO32
        add("h160(40+65)_lo", s)
        add("h160(40+65)^(2^32-1)", s ^ TWO32M1)

    for k in range(-4, 5):
        add(f"(2^32-1)+{k}", (TWO32M1 + k) % TWO32)

    return out


def q_from_complement(eps_scan: int = 500_000) -> list[tuple[str, int, int]]:
    """d = NP1 // m for m = 2^96 + j*2^57; return (label, d, rem)."""
    rows: list[tuple[str, int, int]] = []
    for j in range(eps_scan + 1):
        m = M_BASE + j * STEP_57
        if m >= 2**97:
            break
        q, rem = divmod(NP1, m)
        if D_LO <= q < D_HI:
            rows.append((f"NP1//m j={j}", q, rem))
        if rem > 0 and D_LO <= q + 1 < D_HI:
            rows.append((f"NP1//m+1 j={j}", q + 1, rem))
    return rows


def q_from_h160_lanes(h160: int, hmap: dict[int, int]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []

    def add(n: str, v: int) -> None:
        out.append((n, v % (MAX_Q + 1)))

    add("(h160-lo)//2^32", (h160 - lo) // TWO32)
    add("h160//2^32", h160 // TWO32)
    add("D_BASE", D_BASE % (MAX_Q + 1))
    add("(D_BASE-1)", (D_BASE - 1) % (MAX_Q + 1))
    for n in (40, 65, 115, 125, 160):
        if n in hmap:
            if lo <= hmap[n] < hi:
                add(f"(h160(P{n})-lo)//2^32", (hmap[n] - lo) // TWO32)
    s = (hmap.get(40, 0) + hmap.get(65, 0)) % N
    if lo <= s < hi:
        add("(h160(40+65)-lo)//2^32", (s - lo) // TWO32)
    return out


def lane_snap(d: int, eps_list: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Snap d to lo + q*2^32 + eps for each eps."""
    if not (D_LO <= d < D_HI):
        return []
    q, e0 = divmod(d - lo, TWO32)
    out: list[tuple[str, int]] = []
    seen: set[int] = set()
    for en, e in eps_list:
        for de in (0, -1, 1, e0 - e):
            dd = lo + q * TWO32 + ((e + de) % TWO32)
            if D_LO <= dd < D_HI and dd not in seen:
                seen.add(dd)
                out.append((f"snap_eps={en}_de={de}", dd))
    return out


def main() -> None:
    t0 = time.time()
    hmap: dict[int, int] = {}
    for n, row in parse_53125().items():
        if row.px:
            pub = ("02" if row.py % 2 == 0 else "03") + format(row.px, "064x")
            hmap[n] = h160_parts(pub)[0]
    for n, rsz in PUZZLE_RSZ.items():
        if n not in hmap and rsz.pub_compressed:
            hmap[n] = h160_parts(rsz.pub_compressed)[0]
    hmap[160] = h160_parts(P160_PUB)[0]

    h160, _, chk = h160_parts(P160_PUB)
    eps_list = eps_two32m1_family(h160, chk, hmap)
    q_lane = q_from_h160_lanes(h160, hmap)

    lines = [
        "Phase 5: complement q + lane eps (2^32-1 family)",
        f"2^32-1 = {TWO32M1}  (0xFFFFFFFF)",
        f"P160 chk={chk}  h160_lo={h160 % TWO32}",
        f"eps family size: {len(eps_list)}",
        "",
    ]

    all_c: dict[int, str] = {}

    def add_c(label: str, d: int) -> None:
        d %= N
        if D_LO <= d < D_HI and d not in all_c:
            all_c[d] = label

    # --- B1: grid lo + q*2^32 + eps ---
    for qn, q in q_lane:
        for en, e in eps_list:
            add_c(f"grid q={qn} eps={en}", lo + q * TWO32 + e)

    lines.append(f"lane grid: {len(all_c)}")

    # --- B2: complement NP1//m partners (scan only — lane-expand top rem) ---
    comp = q_from_complement(eps_scan=200_000)
    lines.append(f"complement in-band d from eps_scan 0..200000: {len(comp)}")

    best_rem = sorted(comp, key=lambda x: x[2])[:30]
    lines.append("smallest remainder NP1//m hits:")
    for lab, d, rem in best_rem[:12]:
        q, e = divmod(d - lo, TWO32)
        lines.append(f"  {lab}  rem={rem}  bf={(d-lo)/width:.4f}  q_lo={q}  eps={e}")

    for lab, d, _rem in comp:
        add_c(lab, d)

    for lab, d, rem in best_rem:
        q, e0 = divmod(d - lo, TWO32)
        for en, e in eps_list:
            add_c(f"{lab}_lane_eps={en}", lo + q * TWO32 + e)
        add_c(f"{lab}_eps=rem_lo32", lo + q * TWO32 + (rem % TWO32))
        add_c(f"{lab}_eps=2^32-1", lo + q * TWO32 + TWO32M1)
        add_c(f"{lab}_eps=rem^(2^32-1)", lo + q * TWO32 + ((rem % TWO32) ^ TWO32M1))

    lines.append(f"after complement lane-expand (top rem only): {len(all_c)}")

    # --- B3: d where eps lane = 2^32-1 exactly ---
    for qn, q in q_lane:
        add_c(f"forced_eps=2^32-1 q={qn}", lo + q * TWO32 + TWO32M1)

    # --- B4: local windows around top complement + h160 lane ---
    seeds: list[tuple[str, int]] = []
    bf_tgt = (h160 - lo) / width
    for d in all_c:
        if abs((d - lo) / width - bf_tgt) < 0.02:
            seeds.append((all_c[d], d))
    seeds = sorted(seeds, key=lambda x: abs((x[1] - lo) / width - bf_tgt))[:12]
    for lab, d, _ in best_rem[:5]:
        seeds.append((lab, d))

    win_n = 0
    for name, d0 in seeds:
        q0, e0 = divmod(d0 - lo, TWO32)
        for dq in range(-4, 5):
            for de in list(range(-64, 65)) + [TWO32M1 - e0, (TWO32M1 ^ e0) % TWO32]:
                q = (q0 + dq) % (MAX_Q + 1)
                e = (e0 + de) % TWO32
                d = lo + q * TWO32 + e
                if D_LO <= d < D_HI and d not in all_c:
                    all_c[d] = f"win_{name}_dq{dq}_de{de}"
                    win_n += 1

    lines.append(f"local windows: +{win_n}  total unique d: {len(all_c)}")
    lines.append("EC verify...")

    hits: list[str] = []
    for d in sorted(all_c):
        if check_d_g(d):
            q, e = divmod(d - lo, TWO32)
            hits.append(f"HIT {all_c[d]}  d={d}  q={q}  eps={e}  eps==2^32-1? {e==TWO32M1}")

    lines.append(f"hits: {len(hits)}")
    lines.extend(hits or ["  (none)"])

    # show candidates with eps = 2^32-1
    lines.append("")
    lines.append("=== candidates with eps = 2^32-1 ===")
    m1 = [d for d in all_c if (d - lo) % TWO32 == TWO32M1]
    lines.append(f"count: {len(m1)}")
    for d in sorted(m1, key=lambda x: abs((x - lo) / width - bf_tgt))[:8]:
        lines.append(f"  {all_c[d]}  bf={(d-lo)/width:.6f}")

    lines.append(f"\nelapsed {time.time()-t0:.1f}s")
    text = "\n".join(lines) + "\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
