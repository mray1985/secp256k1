#!/usr/bin/env python3
"""Phase 3: pairwise h160 + RSZ formulas + complement-window EC sweep for P160."""

from __future__ import annotations

import hashlib
import re
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, puzzle_band, pubkey_from_scalar, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ, rsz_bridge_features  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "p160_rsz_h160_phase3.txt"

NP1 = N + 1
D_LO, D_HI = 1 << 159, 1 << 160
lo, hi, _ = puzzle_band(160)
width = hi - lo
STEP_57 = 2**57
M_BASE = 2**96

P160_PUB = (
    ROOT / "puzzle160_keyhunt_bsgs" / "P160_compressed.pub"
).read_text(encoding="ascii").strip().splitlines()[0].strip()
P160_X = int(P160_PUB[2:], 16)

RSZ160 = PUZZLE_RSZ[160]
R160, S160, Z160 = RSZ160.r, RSZ160.s, RSZ160.z
SINV160 = pow(S160, -1, N)
RINV160 = pow(R160, -1, N)

ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ADDR_ONLY = {
    71: "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU",
    72: "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR",
    74: "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv",
    76: "1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF",
}

SHOOT_CENTERS = [
    ("comp_013_f6245", 1126542888683233323254665949792539221572272567387),
    ("comp_008_f5292", 1054601304886752241697263831605029951669396806916),
    ("comp_011_f6411", 1139617642013975815235187587466624157313351302882),
    ("comp_014_f6807", 1171311781543178512062158975163829804131433351107),
    ("comp_018_f7220", 1205362177380791960866532459524416203030698514661),
    ("comp_016_f4468", 996025653554917077713473378695473340804626027395),
    ("h160_self", None),  # filled at runtime
    ("h160_P40+P65", None),
    ("bf_08167", None),
]

# complement .bat hex midpoints from manifest
BAT_CENTERS_HEX = [
    ("bat_008", "b8b9f542a914e924756cc8ca757c8efd06879d04", "b8b9f542a914e924756cc8ca757c9efd06879d04"),
    ("bat_011", "c79e38f2b64cee0cb8c3d4fee67669a6822c3ee2", "c79e38f2b64cee0cb8c3d4fee67679a6822c3ee2"),
    ("bat_013", "c553ee2403f18ef6913d1ffcd9c995880c08b45b", "c553ee2403f18ef6913d1ffcd9c9a5880c08b45b"),
]


def b58decode_check(addr: str) -> bytes:
    n = 0
    for ch in addr:
        n = n * 58 + ALPH.index(ch)
    full = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(addr) - len(addr.lstrip("1"))
    full = b"\x00" * pad + full
    chk = hashlib.sha256(hashlib.sha256(full[:-4]).digest()).digest()[:4]
    if chk != full[-4:]:
        raise ValueError(addr)
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
    pubs[160] = P160_PUB
    hmap = {n: h160_from_pub(p) for n, p in pubs.items()}
    for n, addr in ADDR_ONLY.items():
        hmap[n] = int.from_bytes(b58decode_check(addr)[1:21], "big")
    return hmap


def in_band(d: int) -> bool:
    return D_LO <= d < D_HI


def check_d_g(d: int) -> bool:
    if not in_band(d):
        return False
    x, y = pubkey_from_scalar(d)
    return x == P160_X and (P160_PUB[:2] == "02") == (y % 2 == 0)


def d_from_k_rsz(k: int, r: int, s: int, z: int) -> int:
    """d = r^-1 (s*k - z) mod N."""
    return (pow(r, -1, N) * ((s * k) % N - z)) % N


def k_from_d_rsz(d: int, r: int, s: int, z: int) -> int:
    return (pow(s, -1, N) * (z + r * d)) % N


def band_from_frac(f: float) -> int:
    f = max(0.0, min(1.0 - 1e-18, f))
    return lo + int(f * (width - 1))


# --- worker for window scan ---
_g_pub_x = P160_X
_g_pub_pref = P160_PUB[:2]


def _ec_worker(d: int) -> int | None:
    if not (D_LO <= d < D_HI):
        return None
    from ecdlp_full_pipeline import pubkey_from_scalar as pfs

    x, y = pfs(d)
    if x == _g_pub_x and (_g_pub_pref == "02") == (y % 2 == 0):
        return d
    return None


def scan_window(label: str, center: int, half: int, step: int = 1) -> tuple[str, int | None, int]:
    lo_w = max(D_LO, center - half)
    hi_w = min(D_HI - 1, center + half)
    ds = list(range(lo_w, hi_w + 1, step))
    total = len(ds)
    workers = max(1, min(cpu_count(), 8))
    with Pool(workers) as pool:
        for hit in pool.imap_unordered(_ec_worker, ds, chunksize=512):
            if hit is not None:
                pool.terminate()
                return label, hit, total
    return label, None, total


def phase_rsz_h160(hmap: dict[int, int]) -> tuple[list[str], list[tuple[str, int]]]:
    lines: list[str] = ["=== Phase A: RSZ + h160 pairwise formulas ==="]
    hits: list[tuple[str, int]] = []
    seen: set[int] = set()

    def try_d(label: str, d: int) -> None:
        d %= N
        if d in seen:
            return
        seen.add(d)
        if check_d_g(d):
            hits.append((label, d))
            lines.append(f"  HIT {label}  d={d}")

    keys = sorted(hmap.keys())
    rsz_nums = sorted(PUZZLE_RSZ.keys())

    # --- A1: P160 RSZ, k := h160 / RSZ mixes ---
    k_bases: list[tuple[str, int]] = []
    for m in keys:
        h = hmap[m]
        k_bases.append((f"h160(P{m})", h))
    for i, a in enumerate(keys):
        for b in keys[i:]:
            ha, hb = hmap[a], hmap[b]
            k_bases.append((f"h160({a})+h160({b})", (ha + hb) % N))
            k_bases.append((f"h160({a})^h160({b})", ha ^ hb))
    for name, val in rsz_bridge_features(160):
        k_bases.append((name, val))
    for name, val in rsz_bridge_features(135):
        k_bases.append((f"P135_{name}", val))

    for klab, k in k_bases:
        d = d_from_k_rsz(k, R160, S160, Z160)
        try_d(f"P160_RSZ k={klab}", d)
        # k variants with RSZ scalars
        for tag, kv in [
            ("k+h160(P160)", (k + hmap[160]) % N),
            ("k^r", k ^ R160),
            ("k+z", (k + Z160) % N),
            ("k*r", (k * R160) % N),
            ("s*k", (S160 * k) % N),
        ]:
            try_d(f"P160_RSZ k={klab} {tag}", d_from_k_rsz(kv, R160, S160, Z160))

    lines.append(f"  k-base variants: {len(k_bases)}  unique d tried: {len(seen)}  hits: {len(hits)}")

    # --- A2: cross-RSZ pairwise with h160 as d directly ---
    seen2: set[int] = set()
    for a in rsz_nums:
        ra, sa, za = PUZZLE_RSZ[a].r, PUZZLE_RSZ[a].s, PUZZLE_RSZ[a].z
        for b in keys:
            h = hmap[b]
            combos = [
                (f"d=h160({b})", h),
                (f"d=h160({b})+z160", (h + Z160) % N),
                (f"d=h160({b})+r160", (h + R160) % N),
                (f"d=h160({b})+z_a", (h + za) % N),
                (f"d=h160({b})+r_a", (h + ra) % N),
                (f"d=(h160({b})*r_a)", (h * ra) % N),
                (f"d=s_a*h160({b})", (sa * h) % N),
            ]
            for lab, d in combos:
                d %= N
                if d in seen2:
                    continue
                seen2.add(d)
                try_d(f"cross P{a} {lab}", d)

    # --- A3: known k from other puzzles -> d via P160 RSZ ---
    for a in rsz_nums:
        rsz = PUZZLE_RSZ[a]
        if rsz.k is None:
            continue
        for b in keys:
            h = hmap[b]
            for klab, k in [
                (f"k_pub_{a}", rsz.k),
                (f"k_{a}+h160({b})", (rsz.k + h) % N),
                (f"k_{a}^h160({b})", rsz.k ^ h),
                (f"h160({b})", h),
            ]:
                try_d(f"P160_RSZ from P{a} {klab}", d_from_k_rsz(k, R160, S160, Z160))

    # --- A4: m-bridge h160 -> m -> d = (N+1)/m ---
    for b in keys:
        h = hmap[b]
        m_cands = [
            M_BASE + (h % STEP_57),
            M_BASE + ((h >> 96) % STEP_57),
            M_BASE + (int(h % (2**40))),
            2**96 + (h % (2**97 - 2**96)),
            h if 2**96 <= h < 2**97 else 0,
        ]
        for mi, m in enumerate(m_cands):
            if m <= 0 or m >= 2**97:
                continue
            q, rem = divmod(NP1, m)
            if in_band(q):
                try_d(f"m-leg P{b} m{mi} d=NP1//m", q)
            if rem > 0 and in_band(q + 1):
                try_d(f"m-leg P{b} m{mi} d=NP1//m+1", q + 1)

    lines.append(f"  total RSZ+h160 hits: {len(hits)}")
    return lines, hits


def phase_complement_windows(hmap: dict[int, int]) -> tuple[list[str], list[tuple[str, int]]]:
    lines: list[str] = ["", "=== Phase B: complement / h160 window EC sweep ==="]
    hits: list[tuple[str, int]] = []

    centers: list[tuple[str, int]] = []
    h40p65 = (hmap.get(40, 0) + hmap.get(65, 0)) % N
    if in_band(h40p65):
        centers.append(("h160_P40+P65", h40p65))
    centers.append(("h160_P160", hmap[160]))
    centers.append(("bf_08167", band_from_frac(0.8167)))
    centers.extend((name, c) for name, c in SHOOT_CENTERS if c is not None)
    for name, lo_h, hi_h in BAT_CENTERS_HEX:
        centers.append((name, (int(lo_h, 16) + int(hi_h, 16)) // 2))

    # dedupe centers
    uniq: dict[str, int] = {}
    for name, c in centers:
        if in_band(c):
            uniq[name] = c
    lines.append(f"  window centers: {len(uniq)}")

    # B1: spot check exact centers
    for name, c in sorted(uniq.items(), key=lambda x: x[1]):
        if check_d_g(c):
            hits.append((f"center:{name}", c))
            lines.append(f"  HIT center {name} d={c}")

    # B2: dense ±2^16 step 1 on all centers
    half_dense = 1 << 16
    for name, c in sorted(uniq.items(), key=lambda x: -x[1])[:12]:
        t0 = time.time()
        lab, hit, n = scan_window(f"dense_{name}", c, half_dense, step=1)
        dt = time.time() - t0
        lines.append(f"  dense ±2^16 {name} center={c} checked~{n} in {dt:.1f}s")
        if hit:
            hits.append((lab, hit))
            lines.append(f"    HIT {lab} d={hit}")

    # B3: wide stepped ±2^24 step 2^12 on top 5 centers
    half_wide = 1 << 24
    step_wide = 1 << 12
    top5 = sorted(uniq.items(), key=lambda x: abs((x[1] - lo) / width - 0.8147))[:5]
    for name, c in top5:
        t0 = time.time()
        lab, hit, n = scan_window(f"wide_{name}", c, half_wide, step=step_wide)
        dt = time.time() - t0
        lines.append(
            f"  wide ±2^24 step2^12 {name} bf={(c-lo)/width:.4f} "
            f"checked~{n} in {dt:.1f}s"
        )
        if hit:
            hits.append((lab, hit))
            lines.append(f"    HIT {lab} d={hit}")

    lines.append(f"  window phase hits: {len(hits)}")
    return lines, hits


def retrospective_rsz_h160(hmap: dict[int, int]) -> list[str]:
    """On solved RSZ puzzles: does d_true = d_from_k(h160(other))?"""
    lines = ["", "=== Retrospective (solved RSZ): d_true vs h160 cross ==="]
    keys = {n: k.d for n, k in parse_53125().items() if k.d}
    matches = 0
    for n in sorted(PUZZLE_RSZ.keys()):
        if n not in keys:
            continue
        rsz = PUZZLE_RSZ[n]
        d_true = keys[n]
        for m, h in hmap.items():
            if m == n:
                continue
            d_pred = d_from_k_rsz(h, rsz.r, rsz.s, rsz.z)
            if d_pred == d_true:
                matches += 1
                lines.append(f"  P{n} d == d_from_k(h160(P{m}))")
    lines.append(f"  retrospective matches: {matches}")
    return lines


def main() -> None:
    t0 = time.time()
    hmap = load_hmap()
    lines = [
        "P160 Phase 3: RSZ + h160 pairwise + complement windows",
        f"P160 RSZ r={R160:x}",
        f"band [{lo}, {hi})",
        "",
    ]

    a_lines, a_hits = phase_rsz_h160(hmap)
    lines.extend(a_lines)

    b_lines, b_hits = phase_complement_windows(hmap)
    lines.extend(b_lines)

    lines.extend(retrospective_rsz_h160(hmap))

    all_hits = a_hits + b_hits
    lines.append("")
    lines.append(f"=== TOTAL HITS: {len(all_hits)} ===")
    for lab, d in all_hits:
        lines.append(f"  {lab}  d={d}  hex={d:064x}")

    lines.append(f"\nelapsed {time.time()-t0:.1f}s")
    text = "\n".join(lines) + "\n"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
