#!/usr/bin/env python3
"""
Inverted RSZ-first P160 search:
  Pick k from low-entropy / spend-geometry families
  d = r^-1 (s*k - z) mod N
  Gate: d in [2^159,2^160), d*G==P160, optionally k*G==R
"""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band, pubkey_from_scalar, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, recover_r_point_from_sig  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_inverted_ksz_scan.txt"

D_LO, D_HI = 1 << 159, 1 << 160
lo, hi, _ = puzzle_band(160)
STEP_57 = 2**57
M_BASE = 2**96
TWO32 = 4294967296
TWO32M1 = TWO32 - 1

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)
P160_Y_EVEN = P160_PUB.startswith("02")

rsz = PUZZLE_RSZ[160]
R, S, Z = rsz.r, rsz.s, rsz.z
RINV = pow(R, -1, N)
R_POINT = recover_r_point_from_sig(R)


def d_from_k(k: int) -> int:
    return (RINV * ((S * (k % N) - Z) % N)) % N


def h160_pub(pub: str) -> int:
    raw = bytes.fromhex(pub)
    x = int(pub[2:], 16)
    yp, yn = y_roots(x)
    y = yp if (raw[0] == 2) == (yp % 2 == 0) else yn
    pref = b"\x02" if y % 2 == 0 else b"\x03"
    return int.from_bytes(
        hashlib.new("ripemd160", hashlib.sha256(pref + x.to_bytes(32, "big")).digest()).digest(),
        "big",
    )


def check_d_p160(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (y % 2 == 0) == P160_Y_EVEN


def check_k_r(k: int) -> bool:
    if R_POINT is None:
        return False
    return pubkey_from_scalar(k) == R_POINT


def load_hmap() -> dict[int, int]:
    pubs: dict[int, str] = {}
    for n, row in parse_53125().items():
        if row.px:
            pubs[n] = ("02" if row.py % 2 == 0 else "03") + format(row.px, "064x")
    for n, r in PUZZLE_RSZ.items():
        if n not in pubs and r.pub_compressed:
            pubs[n] = r.pub_compressed
    pubs[160] = P160_PUB
    return {n: h160_pub(p) for n, p in pubs.items()}


def build_k_candidates(hmap: dict[int, int]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    seen: set[int] = set()

    def add(name: str, k: int) -> None:
        k %= N
        if k in seen:
            return
        seen.add(k)
        out.append((name, k))

    # RSZ scalars
    for name, v in [("r", R), ("s", S), ("z", Z), ("r^s", (R * S) % N), ("z+r", (Z + R) % N)]:
        add(name, v)

    # published k from other puzzles
    for n, row in PUZZLE_RSZ.items():
        if row.k is not None:
            add(f"k_pub_P{n}", row.k)

    # h160 family
    for n, h in hmap.items():
        add(f"h160_P{n}", h)

    # complement-scale k ladder  m ~ k hypothesis: k = 2^96 + j*2^57
    for j in range(0, 50_001):
        add(f"mleg_{j}", M_BASE + j * STEP_57)

    # k near r (spend geometry) — small window
    for delta in range(-4096, 4097):
        add(f"r+{delta}", R + delta)

    # 2^i ladder
    for i in range(1, 161):
        add(f"2^{i}", 1 << i)

    # small integers
    for c in list(range(1, 256)) + [512, 1024, 2048, 4096, 76, 42, 159, 160]:
        add(f"c_{c}", c)

    # 2^32 lane
    add("2^32", TWO32)
    add("2^32-1", TWO32M1)
    add("P_SHIFT", 5_457_912_602)

    return out


def main() -> None:
    t0 = time.time()
    hmap = load_hmap()
    k_cands = build_k_candidates(hmap)

    lines = [
        "P160 inverted RSZ-first: k candidate -> d = r^-1(sk-z)",
        f"k candidates: {len(k_cands)}",
        f"R point: {R_POINT}",
        "",
    ]

    in_band = 0
    hits: list[str] = []
    k_r_only: list[str] = []

    for name, k in k_cands:
        d = d_from_k(k)
        if not (D_LO <= d < D_HI):
            continue
        in_band += 1
        ok_d = check_d_p160(d)
        ok_k = check_k_r(k)
        if ok_d and ok_k:
            hits.append(f"DUAL HIT {name} k={k} d={d}")
        elif ok_d:
            hits.append(f"d_HIT {name} k={k} d={d} (k*G==R? {ok_k})")
        elif ok_k:
            k_r_only.append(f"k_HIT {name} d_in_band bf={(d-lo)/(hi-lo):.4f}")

    lines.append(f"in-band d from k scan: {in_band}")
    lines.append(f"full hits: {len([h for h in hits if h.startswith('DUAL')])}")
    lines.append(f"d*G==P (any k): {len([h for h in hits if 'd_HIT' in h or 'DUAL' in h])}")
    lines.extend(hits[:20] if hits else ["  (no d*G==P hits)"])
    if k_r_only:
        lines.append(f"k*G==R with d in band but wrong P: {len(k_r_only)}")
        lines.extend(k_r_only[:5])

    # Phase 2: m-leg k ladder only, finer rem on resulting d
    lines.append("")
    lines.append("=== Phase 2: m-leg k ladder (j=0..200k) band hits ===")
    mleg_band: list[tuple[int, int, int, bool, bool]] = []
    for j in range(0, 200_001):
        k = M_BASE + j * STEP_57
        d = d_from_k(k)
        if D_LO <= d < D_HI:
            mleg_band.append(
                (j, d, (d - lo) // TWO32, check_d_p160(d), check_k_r(k))
            )
    lines.append(f"  in-band count: {len(mleg_band)}")
    if mleg_band:
        # show closest to h160 bf 0.8147
        tgt = 0.8147
        best = sorted(mleg_band, key=lambda x: abs((x[1] - lo) / (hi - lo) - tgt))[:8]
        lines.append("  nearest bf to 0.8147:")
        for j, d, q, od, ok in best:
            lines.append(
                f"    j={j} bf={(d-lo)/(hi-lo):.4f} dG={od} kG==R={ok}"
            )
        dual = [x for x in mleg_band if x[3] and x[4]]
        lines.append(f"  dual gate in m-leg: {len(dual)}")

    lines.append(f"\nelapsed {time.time()-t0:.1f}s")
    text = "\n".join(lines) + "\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
