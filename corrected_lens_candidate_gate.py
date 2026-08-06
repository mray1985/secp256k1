#!/usr/bin/env python3
"""
Corrected-lens ECDLP candidate-close pipeline.

Uses The Real Decimal silhouette:
  stitched = Px.(p−y)   (decimal placement)
  packet_p = stitched / p
  packet_256 = stitched / 2^256

Generates candidates from the corrected lens, then closes:

  d-path:
    1. d in [2^(n-1), 2^n)
    2. [d]G == P
    3. k = (z + r*d) * s^-1 mod N   (if RSZ)
    4. x([k]G) == r
    5. s*k == z + r*d mod N

  mirror-path:
    1. q in [N-2^n+1, N-2^(n-1)]
    2. d = N - q
    3. [d]G == P
    4. [q]G == -P  (x same, y flipped)
    5. RSZ close with k

Writes: ARCHIVE/briefcase/The Real Decimal/corrected_lens_ecdlp_verdict.*
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import BETA, BETA_SQ, DELTA, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

getcontext().prec = 80

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ARCHIVE" / "briefcase" / "The Real Decimal"
TWO256 = Decimal(1 << 256)

# Focus: unsolved pubkey puzzles + sanity on a few solved
FOCUS_UNSOLVED = [135, 140, 145, 150, 155, 160]
SANITY_SOLVED = [1, 65, 75, 100, 130]


def ec_xy(scalar: int) -> tuple[int, int]:
    a = scalar % N
    if a == 0:
        raise ValueError("scalar 0")
    sk = SigningKey.from_secret_exponent(a, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    return pt.x(), pt.y()


def map_p_to_n(x: int) -> int:
    return (N * x) // p


def d_window(n: int) -> tuple[int, int]:
    return 1 << (n - 1), (1 << n) - 1


def n_mirror_window(n: int) -> tuple[int, int]:
    return N - (1 << n) + 1, N - (1 << (n - 1))


def stitch(px: int, y_digits: int) -> Decimal:
    return Decimal(f"{px}.{y_digits}")


def generate_candidates(n: int, px: int, py: int) -> dict[str, set[int]]:
    """Candidates from corrected lens only."""
    lo, hi = d_window(n)
    width = hi - lo + 1
    pmy = (p - py) % p
    st = stitch(px, pmy)
    pkt_p = st / Decimal(p)
    pkt_256 = st / TWO256
    floor_n = int(pkt_p * Decimal(N))
    floor_n_256 = int(pkt_256 * Decimal(N))
    m_px = map_p_to_n(px)
    m_pmy = map_p_to_n(pmy)
    px1 = (px * inv(BETA_SQ, p)) % p
    px2 = (px * inv(BETA, p)) % p

    d_cands: set[int] = set()
    q_cands: set[int] = set()

    # --- direct d from range projection of corrected fractions ---
    for frac in (pkt_p, pkt_256, Decimal(px) / Decimal(p), Decimal(pmy) / Decimal(p)):
        # frac may be > 1 for stitch/2^256? no stitch/2^256 < 1 typically
        f = frac - int(frac)  # frac part in [0,1)
        if f < 0:
            f += 1
        d_cands.add(lo + int(f * Decimal(width)))
        d_cands.add(lo + int(f * Decimal(width)) % width)

    # --- congruence-class landings from lens integers ---
    ints = [
        px, pmy, py, px1, px2,
        m_px, m_pmy,
        floor_n, floor_n_256,
        int(st),  # integer part of stitch = Px
        int(pkt_p * Decimal(1 << n)),
        int(pkt_256 * Decimal(1 << n)),
        int(pkt_p * Decimal(1 << (n - 1))),
        int(pkt_256 * Decimal(1 << (n - 1))),
        (px * inv(DELTA % p, p)) % p,
        (m_px * inv(DELTA % N, N)) % N,
    ]
    for v in ints:
        d_cands.add(lo + (v % width))
        d_cands.add(lo + (abs(v) % (1 << (n - 1))))
        # low bits of v as offset from floor
        d_cands.add(lo + (v & ((1 << (n - 1)) - 1)))

    # hinge landing
    from decimal import Decimal as D
    HINGE = D("0.58496250072115618145373894394781650876")
    d_cands.add(lo + int(D(width) * HINGE))

    # --- mirror path: q candidates in N-mirror → d = N - q ---
    q_ints = [
        m_px, m_pmy, floor_n, floor_n_256,
        map_p_to_n(px1), map_p_to_n(px2),
        (floor_n + DELTA) % N,
        (m_px + DELTA) % N,
        (N - px % N) % N,
        int(pkt_p * Decimal(N)),
        int(pkt_256 * Decimal(N)),
    ]
    mlo, mhi = n_mirror_window(n)
    for q in q_ints:
        q = q % N
        q_cands.add(q)
        # also project q into mirror window by congruence
        span = mhi - mlo + 1
        q_cands.add(mlo + (q % span))

    # convert mirror q → d
    for q in list(q_cands):
        if mlo <= q <= mhi:
            d = (N - q) % N
            d_cands.add(d)

    # keep only in d-window for d-path reporting
    d_in = {d for d in d_cands if lo <= d <= hi}
    q_in = {q for q in q_cands if mlo <= q <= mhi}

    return {
        "d_raw": d_cands,
        "d_in_window": d_in,
        "q_raw": q_cands,
        "q_in_mirror": q_in,
    }


def close_d(
    d: int,
    n: int,
    tpx: int,
    tpy: int,
    rsz: dict | None,
) -> dict:
    lo, hi = d_window(n)
    gates = []
    gates.append({"gate": "range", "pass": lo <= d <= hi})

    try:
        dx, dy = ec_xy(d)
        ec_ok = dx == tpx and (dy == tpy or dy == (p - tpy) % p)
    except Exception as exc:
        return {"d": str(d), "pass": False, "gates": [{"gate": "ec", "pass": False, "err": str(exc)}]}

    gates.append({"gate": "ec_dG", "pass": ec_ok})

    rsz_ok = None
    k = None
    if rsz and ec_ok:
        r, s, z = int(rsz["r"]), int(rsz["s"]), int(rsz["z"])
        k = ((z + r * d) * inv(s, N)) % N
        try:
            kx, _ = ec_xy(k)
            r_ok = kx == (r % N) or kx == r  # r is x-coordinate
            # r from ECDSA is x(R) mod N; compare to kx mod N
            r_ok = (kx % N) == (r % N)
        except Exception:
            r_ok = False
        eq_ok = (s * k) % N == (z + r * d) % N
        gates.append({"gate": "rsz_x_kG", "pass": r_ok, "k": str(k)})
        gates.append({"gate": "rsz_equation", "pass": eq_ok})
        rsz_ok = r_ok and eq_ok
    elif rsz:
        gates.append({"gate": "rsz_x_kG", "pass": False, "skip": "ec failed"})
        gates.append({"gate": "rsz_equation", "pass": False, "skip": "ec failed"})

    return {
        "d": str(d),
        "pass": ec_ok and (rsz_ok is not False),
        "ec_match": ec_ok,
        "rsz_ok": rsz_ok,
        "k": str(k) if k is not None else None,
        "gates": gates,
    }


def close_mirror_q(
    q: int,
    n: int,
    tpx: int,
    tpy: int,
    rsz: dict | None,
) -> dict:
    mlo, mhi = n_mirror_window(n)
    gates = [{"gate": "q_in_N_mirror", "pass": mlo <= q <= mhi}]
    d = (N - q) % N
    lo, hi = d_window(n)
    gates.append({"gate": "d_from_q_in_range", "pass": lo <= d <= hi})

    try:
        dx, dy = ec_xy(d)
        ec_ok = dx == tpx and (dy == tpy or dy == (p - tpy) % p)
    except Exception as exc:
        return {"q": str(q), "d": str(d), "pass": False, "gates": gates + [{"gate": "ec", "pass": False, "err": str(exc)}]}

    gates.append({"gate": "ec_dG", "pass": ec_ok})

    # [q]G == -P  (same x, opposite y)
    try:
        qx, qy = ec_xy(q)
        neg_ok = qx == tpx and (qy == (p - tpy) % p or qy == tpy)
        # properly -P has y = p - Py when P has y = Py
        neg_ok = qx == tpx and qy == ((p - tpy) % p if ec_ok and dy == tpy else (p - dy) % p)
        # simpler: qG + dG = N*G = O, so qG = -dG = -P
        neg_ok = qx == dx and qy == ((p - dy) % p)
    except Exception:
        neg_ok = False
    gates.append({"gate": "ec_qG_is_neg_P", "pass": neg_ok})

    # RSZ on d
    rsz_part = close_d(d, n, tpx, tpy, rsz)
    for g in rsz_part["gates"]:
        if g["gate"].startswith("rsz"):
            gates.append(g)

    return {
        "q": str(q),
        "d": str(d),
        "pass": ec_ok and neg_ok and (rsz_part.get("rsz_ok") is not False),
        "ec_match": ec_ok,
        "neg_P_ok": neg_ok,
        "gates": gates,
    }


def run_puzzle(n: int, catalog, rsz_cache: dict) -> dict:
    e = catalog[n]
    if not e.public_key:
        return {"puzzle": n, "status": "NO_PUBKEY"}

    px, py = pubkey_xy(e.public_key)
    rsz = rsz_cache.get(str(n))
    cands = generate_candidates(n, px, py)

    # d-path
    d_hits = []
    d_tested = 0
    for d in sorted(cands["d_in_window"]):
        d_tested += 1
        res = close_d(d, n, px, py, rsz)
        if res["ec_match"]:
            d_hits.append(res)

    # mirror-path
    q_hits = []
    q_tested = 0
    for q in sorted(cands["q_in_mirror"]):
        q_tested += 1
        res = close_mirror_q(q, n, px, py, rsz)
        if res["ec_match"]:
            q_hits.append(res)

    # sanity: if solved, true d must pass
    sanity = None
    if e.solved and e.private_key > 0:
        sanity = close_d(e.private_key, n, px, py, rsz)

    return {
        "puzzle": n,
        "status": "SOLVED" if e.solved else "UNSOLVED_PUBKEY",
        "has_rsz": bool(rsz),
        "candidates": {
            "d_raw": len(cands["d_raw"]),
            "d_in_window": len(cands["d_in_window"]),
            "q_raw": len(cands["q_raw"]),
            "q_in_mirror": len(cands["q_in_mirror"]),
        },
        "d_path": {
            "tested": d_tested,
            "ec_hits": len(d_hits),
            "hits": d_hits,
        },
        "mirror_path": {
            "tested": q_tested,
            "ec_hits": len(q_hits),
            "hits": q_hits,
        },
        "sanity_true_d": sanity,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz_cache = {}
    if CACHE_PATH.exists():
        rsz_cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    results = []
    puzzles = list(dict.fromkeys(FOCUS_UNSOLVED + SANITY_SOLVED))
    for n in puzzles:
        print(f"P{n}...")
        results.append(run_puzzle(n, catalog, rsz_cache))

    # also run all remaining unsolved pubkey puzzles
    for n in range(1, 161):
        e = catalog[n]
        if n in puzzles:
            continue
        if e.public_key and not e.solved:
            print(f"P{n}...")
            results.append(run_puzzle(n, catalog, rsz_cache))

    total_d = sum(r["d_path"]["tested"] for r in results if "d_path" in r)
    total_q = sum(r["mirror_path"]["tested"] for r in results if "mirror_path" in r)
    total_ec_hits = sum(
        r["d_path"]["ec_hits"] + r["mirror_path"]["ec_hits"]
        for r in results
        if "d_path" in r
    )
    # exclude sanity true-d from "new hits" for solved
    new_hits = []
    for r in results:
        if r.get("status") == "NO_PUBKEY":
            continue
        for h in r["d_path"]["hits"]:
            if r["status"] == "SOLVED" and r.get("sanity_true_d", {}).get("d") == h["d"]:
                continue
            # for solved, true d might be in candidate set
            if r["status"] == "SOLVED":
                true_d = catalog[r["puzzle"]].private_key
                if int(h["d"]) == true_d:
                    continue
            new_hits.append({"puzzle": r["puzzle"], "path": "d", **h})
        for h in r["mirror_path"]["hits"]:
            if r["status"] == "SOLVED":
                true_d = catalog[r["puzzle"]].private_key
                if int(h["d"]) == true_d:
                    continue
            new_hits.append({"puzzle": r["puzzle"], "path": "mirror", **h})

    sanity_ok = all(
        r.get("sanity_true_d", {}).get("ec_match") is True
        for r in results
        if r.get("status") == "SOLVED"
    )

    summary = {
        "lens": "corrected Real Decimal — stitch Px.(p-y), /p and /2^256",
        "puzzles_run": len([r for r in results if "d_path" in r]),
        "d_candidates_tested": total_d,
        "q_candidates_tested": total_q,
        "ec_hits_total_including_true_d_if_generated": total_ec_hits,
        "novel_ec_hits": len(new_hits),
        "novel_hits": new_hits,
        "sanity_true_d_passes_gate": sanity_ok,
        "verdict": (
            "CORRECTED LENS RUN THROUGH ECDLP GATES: "
            + ("NO NOVEL HITS" if not new_hits else f"{len(new_hits)} NOVEL HITS")
        ),
    }

    payload = {"summary": summary, "results": results}
    (OUT / "corrected_lens_ecdlp_verdict.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Corrected-lens ECDLP verdict",
        "",
        "Sworn witnesses from **The Real Decimal** (stitched `Px.(p−y)`, `/p`, `/2^256`).",
        "",
        "## Gates",
        "",
        "```text",
        "d-path:  range → [d]G==P → k=(z+r*d)*s^-1 → x([k]G)==r → s*k==z+r*d",
        "mirror:  q in N-mirror → d=N-q → [d]G==P → [q]G==-P → RSZ",
        "```",
        "",
        "## Summary",
        "",
        f"- puzzles run: **{summary['puzzles_run']}**",
        f"- d candidates tested: **{total_d}**",
        f"- q (mirror) candidates tested: **{total_q}**",
        f"- novel EC hits: **{len(new_hits)}**",
        f"- sanity (true d passes on solved): **{sanity_ok}**",
        "",
        f"**{summary['verdict']}**",
        "",
        "## Per puzzle",
        "",
        "| P | status | d tested | q tested | ec hits (d) | ec hits (mirror) | sanity |",
        "|---|--------|----------|----------|-------------|------------------|--------|",
    ]
    for r in results:
        if "d_path" not in r:
            lines.append(f"| {r['puzzle']} | {r['status']} | — | — | — | — | — |")
            continue
        san = r.get("sanity_true_d")
        san_s = san["ec_match"] if san else "—"
        lines.append(
            f"| {r['puzzle']} | {r['status']} | {r['d_path']['tested']} | "
            f"{r['mirror_path']['tested']} | {r['d_path']['ec_hits']} | "
            f"{r['mirror_path']['ec_hits']} | {san_s} |"
        )

    lines.extend([
        "",
        "## Ruling",
        "",
        "Old lens: already judged, no hits.",
        "Corrected lens: now judged through ECDLP candidate-close gates.",
        f"Result: **{'no novel hits' if not new_hits else 'see novel_hits'}**.",
        "",
        "Judge Popcorn: **corrected witnesses sworn in and cross-examined. "
        "No conviction.**",
        "",
    ])
    (OUT / "corrected_lens_ecdlp_verdict.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print(f"wrote {OUT / 'corrected_lens_ecdlp_verdict.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
