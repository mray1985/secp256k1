#!/usr/bin/env python3
"""Phase 4: d = lo + q*2^32 + eps  (32-bit lane sweep) for Puzzle 160."""

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
REPORT = ARCHIVE / "p160_lane_two32_sweep.txt"

TWO32 = 4294967296
P_SHIFT = 5_457_912_602
NP1 = N + 1
D_LO, D_HI = 1 << 159, 1 << 160

lo, hi, top = puzzle_band(160)
width = hi - lo

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)

RSZ160 = PUZZLE_RSZ[160]
STEP_57 = 2**57
M_BASE = 2**96
D_BASE = NP1 // M_BASE

SHOOT_CENTERS = [
    1126542888683233323254665949792539221572272567387,
    1054601304886752241697263831605029951669396806916,
    1139617642013975815235187587466624157313351302882,
    1171311781543178512062158975163829804131433351107,
    1205362177380791960866532459524416203030698514661,
    996025653554917077713473378695473340804626027395,
]

ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def h160_from_pub(pub: str) -> tuple[int, bytes]:
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    digest = hashlib.new(
        "ripemd160",
        hashlib.sha256(pref + x.to_bytes(32, "big")).digest(),
    ).digest()
    return int.from_bytes(digest, "big"), digest


def payload_checksum(h160: bytes) -> int:
    vh = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
    return int.from_bytes(chk, "big")


def check_d_g(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (P160_PUB[:2] == "02") == (y % 2 == 0)


def lane_pack(q: int, eps: int) -> int:
    return lo + (q % (width // TWO32 + 1)) * TWO32 + (eps % TWO32)


def load_hmap() -> dict[int, int]:
    pubs: dict[int, str] = {}
    for n, row in parse_53125().items():
        if row.px:
            pubs[n] = ("02" if row.py % 2 == 0 else "03") + format(row.px, "064x")
    for n, rsz in PUZZLE_RSZ.items():
        if n not in pubs and rsz.pub_compressed:
            pubs[n] = rsz.pub_compressed
    pubs[160] = P160_PUB
    return {n: h160_from_pub(p)[0] for n, p in pubs.items()}


def q_anchors(hmap: dict[int, int], h160_b: bytes, chk: int) -> list[tuple[str, int]]:
    anchors: list[tuple[str, int]] = []
    h = int.from_bytes(h160_b, "big")

    def add(name: str, val: int) -> None:
        anchors.append((name, val % (1 << 128)))

    add("h160//2^32", h // TWO32)
    add("(h160-lo)//2^32", (h - lo) // TWO32 if h >= lo else h // TWO32)
    add("chk", chk)
    add("P_SHIFT", P_SHIFT)
    add("P_SHIFT//2^32", P_SHIFT // TWO32)

    for n in (40, 65, 59, 71, 115, 125, 135, 150, 160):
        if n not in hmap:
            continue
        hi_n = hmap[n]
        add(f"h160(P{n})//2^32", hi_n // TWO32)
        if lo <= hi_n < hi:
            add(f"(h160(P{n})-lo)//2^32", (hi_n - lo) // TWO32)

    ha, hb = hmap.get(40, 0), hmap.get(65, 0)
    if ha and hb:
        s = (ha + hb) % N
        add("h160(40+65)//2^32", s // TWO32)
        if lo <= s < hi:
            add("(h160(40+65)-lo)//2^32", (s - lo) // TWO32)

    for i, c in enumerate(SHOOT_CENTERS):
        add(f"shoot_{i}", (c - lo) // TWO32)

    add("D_BASE//2^32", D_BASE // TWO32)
    add("floor_1.5x", int(1.5 * lo) // TWO32)

    # retrospective: solved d lane q at same band scale (scaled)
    keys = parse_53125()
    for n in (59, 80, 125, 130):
        if n not in keys or not keys[n].d:
            continue
        lo_n, hi_n, _ = puzzle_band(n)
        off = keys[n].d - lo_n
        add(f"P{n}_d_lane_q", off // TWO32)

    return anchors


def eps_family(h160_b: bytes, chk: int, hmap: dict[int, int]) -> list[tuple[str, int]]:
    h = int.from_bytes(h160_b, "big")
    eps: list[tuple[str, int]] = []

    def add(name: str, v: int) -> None:
        eps.append((name, v % TWO32))

    add("0", 0)
    add("chk_P160", chk)
    add("h160_lo32", h % TWO32)
    add("P_SHIFT_lo32", P_SHIFT % TWO32)
    add("P_SHIFT", P_SHIFT % TWO32)
    add("(P_SHIFT-2^32)", (P_SHIFT - TWO32) % TWO32)
    add("newfound_5457912602_lo", 5457912602 % TWO32)
    add("RSZ_r_lo", RSZ160.r % TWO32)
    add("RSZ_s_lo", RSZ160.s % TWO32)
    add("RSZ_z_lo", RSZ160.z % TWO32)

    for n in (40, 65, 59, 115, 125, 135, 71, 75):
        if n in hmap:
            add(f"h160(P{n})_lo32", hmap[n] % TWO32)

    # pairwise low-lane mixes
    for a, b in ((40, 65), (125, 160), (115, 160), (59, 160)):
        if a in hmap and b in hmap:
            add(f"h160({a}+{b})_lo32", (hmap[a] + hmap[b]) % TWO32)
            add(f"h160({a})^h160({b})_lo32", (hmap[a] ^ hmap[b]) % TWO32)

    # small ticks (positional ladder feel)
    for k in range(-8, 9):
        add(f"tick_{k}", k % TWO32)
    for bit in (1, 2, 4, 8, 16, 42, 76, 128, 256, 512, 1024):
        add(f"+{bit}", bit)

    return eps


def build_candidates(
    q_anchors: list[tuple[str, int]],
    eps_list: list[tuple[str, int]],
    hmap_local: dict[int, int],
    h160_bytes: bytes,
) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    seen: set[int] = set()
    max_q = width // TWO32

    for qn, q in q_anchors:
        q_mod = q % (max_q + 1)
        for en, e in eps_list:
            d = lo + q_mod * TWO32 + e
            if not (D_LO <= d < D_HI):
                # try carry into next q bucket
                d2 = lo + ((q_mod + 1) % (max_q + 1)) * TWO32 + e
                if D_LO <= d2 < D_HI:
                    d = d2
                else:
                    continue
            if d in seen:
                continue
            seen.add(d)
            out.append((f"q={qn} eps={en}", d))

    # also: d from full centers snapped to lane grid
    centers = [
        ("h160_P160", int.from_bytes(h160_bytes, "big")),
        ("h160_40+65", (hmap_local.get(40, 0) + hmap_local.get(65, 0)) % N),
    ]
    for name, c in centers:
        if not (D_LO <= c < D_HI):
            continue
        q, e = divmod(c - lo, TWO32)
        for de in range(-16, 17):
            d = lo + q * TWO32 + ((e + de) % TWO32)
            if D_LO <= d < D_HI and d not in seen:
                seen.add(d)
                out.append((f"snap_{name}_de={de}", d))

    return out


def sweep_local_windows(
    seeds: list[tuple[str, int]], half_q: int = 4, half_e: int = 512
) -> list[tuple[str, int]]:
    """±q buckets and ±eps around top seeds."""
    out: list[tuple[str, int]] = []
    seen: set[int] = set()
    max_q = width // TWO32
    for name, d0 in seeds:
        q0, e0 = divmod(d0 - lo, TWO32)
        for dq in range(-half_q, half_q + 1):
            for de in range(-half_e, half_e + 1):
                q = (q0 + dq) % (max_q + 1)
                e = (e0 + de) % TWO32
                d = lo + q * TWO32 + e
                if not (D_LO <= d < D_HI) or d in seen:
                    continue
                seen.add(d)
                out.append((f"win_{name}_dq{dq}_de{de}", d))
    return out


def main() -> None:
    t0 = time.time()
    hmap = load_hmap()
    h160_int, h160_b = h160_from_pub(P160_PUB)
    chk = payload_checksum(h160_b)

    q_list = q_anchors(hmap, h160_b, chk)
    e_list = eps_family(h160_b, chk, hmap)

    lines = [
        "Phase 4: d = lo + q*2^32 + eps  (P160 lane sweep)",
        f"band lo = {lo}",
        f"max_q buckets = {width // TWO32}  (~2^127)",
        f"P160 checksum = {chk}  h160 mod 2^32 = {h160_int % TWO32}",
        f"P_SHIFT = {P_SHIFT}  (P_SHIFT mod 2^32 = {P_SHIFT % TWO32})",
        f"q anchors: {len(q_list)}  eps family: {len(e_list)}",
        "",
    ]

    cands = build_candidates(q_list, e_list, hmap, h160_b)
    lines.append(f"grid candidates: {len(cands)}")

    # top seeds by band_frac near h160
    bf_tgt = (h160_int - lo) / width
    ranked = sorted(cands, key=lambda x: abs((x[1] - lo) / width - bf_tgt))[:8]
    lines.append(f"target band_frac ~ {bf_tgt:.6f}")
    lines.append("top grid seeds:")
    for lab, d in ranked:
        q, e = divmod(d - lo, TWO32)
        lines.append(f"  {lab}  bf={(d-lo)/width:.6f}  q={q}  eps={e}")

    win = sweep_local_windows(ranked, half_q=8, half_e=1024)
    lines.append(f"local windows around top seeds: +{len(win)}")
    all_c = {d: lab for lab, d in cands}
    for lab, d in win:
        if d not in all_c:
            all_c[d] = lab

    lines.append(f"total unique d: {len(all_c)}")
    lines.append("EC verify...")

    hits: list[str] = []
    for d, lab in sorted(all_c.items(), key=lambda x: x[0]):
        if check_d_g(d):
            q, e = divmod(d - lo, TWO32)
            hits.append(f"HIT {lab}  d={d}  q={q}  eps={e}")

    lines.append(f"hits: {len(hits)}")
    lines.extend(hits or ["  (none)"])

    # retrospective: lane formula on solved P125/P130
    lines.append("")
    lines.append("=== Retrospective lane hit on solved (same eps set) ===")
    retro = 0
    keys = parse_53125()
    for n in sorted(keys):
        if not keys[n].d or n not in hmap:
            continue
        lo_n, _, _ = puzzle_band(n)
        d = keys[n].d
        q, e = divmod(d - lo_n, TWO32)
        for en, ev in e_list:
            if e == ev:
                retro += 1
                lines.append(f"  P{n} true d matches eps={en}")
                break
    lines.append(f"  puzzles matching any eps in family: {retro}")

    lines.append(f"\nelapsed {time.time()-t0:.1f}s")
    text = "\n".join(lines) + "\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
