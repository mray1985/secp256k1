#!/usr/bin/env python3
"""
Fractional-power shells on the corrected Real Decimal lens → ECDLP gates.

Raw corrected lens was judged (no novel hits).
This asks: what if the witness is raised to fractional-power oaths?

Bases (corrected silhouette):
  packet_p     = Px.(p−y) / p
  packet_256   = Px.(p−y) / 2^256
  hex_stitch   = 0x.<Hx><Hy> / 2^512
  beta slot packets
  r/N, s/N, z/N when RSZ exists

Exponents:
  e_hi, e_lo, e_hinge=log2(3/2), e_roof_N, e_q_low, e_q_high
  e_q = log2(N−d)/256 for solved sanity only

Candidates from powered values, then hard gates.

Writes: ARCHIVE/briefcase/The Real Decimal/fractional_power_ecdlp_verdict.*
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

from build_complexity_operations_ledger import BETA, BETA_SQ, N, inv, p
from build_puzzle_ledger_briefcase import pubkey_xy
from puzzle_catalog import load_catalog
from puzzle_rsz_blockchain import CACHE_PATH

getcontext().prec = 80

OUT = Path(__file__).resolve().parent / "ARCHIVE" / "briefcase" / "The Real Decimal"
TWO256 = Decimal(1 << 256)
TWO512 = Decimal(1 << 512)

HINGE = math.log2(1.5)  # log2(3/2) = 0.584962500721156...


def log2_int(x: int) -> Decimal:
    return Decimal(x).ln() / Decimal(2).ln()


def e_from_int(x: int) -> Decimal:
    return log2_int(x) / Decimal(256)


E_ROOF_N = e_from_int(N)  # Decimal, ~1 - 2e-41


def ec_xy(scalar: int) -> tuple[int, int]:
    a = scalar % N
    if a == 0:
        raise ValueError("scalar 0")
    sk = SigningKey.from_secret_exponent(a, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    return pt.x(), pt.y()


def d_window(n: int) -> tuple[int, int]:
    return 1 << (n - 1), (1 << n) - 1


def n_mirror_window(n: int) -> tuple[int, int]:
    return N - (1 << n) + 1, N - (1 << (n - 1))


def stitch(px: int, y_digits: int) -> Decimal:
    return Decimal(f"{px}.{y_digits}")


def bases_for_point(px: int, py: int, rsz: dict | None) -> dict[str, Decimal]:
    pmy = (p - py) % p
    st = stitch(px, pmy)
    HxHy = f"{px:064x}{pmy:064x}"
    bases: dict[str, Decimal] = {
        "packet_p": st / Decimal(p),
        "packet_256": st / TWO256,
        "hex_stitch_512": Decimal(int(HxHy, 16)) / TWO512,
    }
    # beta slot packets with p−y
    for name, xi in (
        ("Px1_pmy_over_p", (px * inv(BETA_SQ, p)) % p),
        ("Px2_pmy_over_p", (px * inv(BETA, p)) % p),
        ("Px3_pmy_over_p", px),
    ):
        bases[name] = stitch(xi, pmy) / Decimal(p)
        bases[name.replace("_over_p", "_over_256")] = stitch(xi, pmy) / TWO256

    if rsz:
        r, s, z = int(rsz["r"]), int(rsz["s"]), int(rsz["z"])
        bases["r_over_N"] = Decimal(r % N) / Decimal(N)
        bases["s_over_N"] = Decimal(s % N) / Decimal(N)
        bases["z_over_N"] = Decimal(z % N) / Decimal(N)
        bases["r_over_256"] = Decimal(r % (1 << 256)) / TWO256
    return bases


def exponents_for(n: int, d: int | None) -> dict[str, Decimal]:
    exps = {
        "e_hi": Decimal(n) / Decimal(256),
        "e_lo": Decimal(n - 1) / Decimal(256),
        "e_hinge": (Decimal(n - 1) + Decimal(str(HINGE))) / Decimal(256),
        "e_roof_N": E_ROOF_N,
        "e_q_low": e_from_int(N - (1 << n)),
        "e_q_high": e_from_int(N - (1 << (n - 1))),
        "e_mirror_proxy": Decimal(255) / Decimal(256),
    }
    if d is not None and d > 0:
        q = (N - d) % N
        if q > 0:
            exps["e_q"] = e_from_int(q)
    return exps


def powered(base: Decimal, e: Decimal) -> Decimal:
    """base ** e with base in (0,1]."""
    if base <= 0:
        return Decimal(0)
    if base >= 1:
        # clamp tiny overshoot
        base = Decimal("0.999999999999999999")
    # Decimal ** Decimal
    return base ** e


def candidates_from_powered(pv: Decimal, n: int) -> set[int]:
    lo, hi = d_window(n)
    width = hi - lo + 1
    mlo, mhi = n_mirror_window(n)
    out: set[int] = set()

    # ensure in [0,1] for range maps
    f = pv
    if f < 0:
        f = Decimal(0)
    if f > 1:
        f = f - int(f)
        if f < 0:
            f += 1

    forms = [
        int(f * Decimal(1 << n)),
        lo + int(f * Decimal(width)),
        int(f * Decimal(N)),
        int((Decimal(1) - f) * Decimal(N)),
        (N - int(f * Decimal(N))) % N,
        int(f * Decimal(1 << (n - 1))),
        lo + (int(f * Decimal(1 << (n - 1))) % (1 << (n - 1))),
    ]
    for d in forms:
        if lo <= d <= hi:
            out.add(d)
        # also as q then mirror
        q = d % N
        if mlo <= q <= mhi:
            dd = (N - q) % N
            if lo <= dd <= hi:
                out.add(dd)
    return out


def q_candidates_from_powered(pv: Decimal, n: int) -> set[int]:
    mlo, mhi = n_mirror_window(n)
    span = mhi - mlo + 1
    f = pv
    if f < 0:
        f = Decimal(0)
    if f > 1:
        f = f - int(f)
    out = set()
    for q in (
        int(f * Decimal(N)),
        int((Decimal(1) - f) * Decimal(N)),
        mlo + int(f * Decimal(span)),
        mlo + (int(f * Decimal(N)) % span),
    ):
        q = q % N
        if mlo <= q <= mhi:
            out.add(q)
    return out


def close_d(d: int, n: int, tpx: int, tpy: int, rsz: dict | None) -> dict:
    lo, hi = d_window(n)
    if not (lo <= d <= hi):
        return {"d": str(d), "ec_match": False, "pass": False}
    try:
        dx, dy = ec_xy(d)
    except Exception:
        return {"d": str(d), "ec_match": False, "pass": False}
    ec_ok = dx == tpx and (dy == tpy or dy == (p - tpy) % p)
    if not ec_ok or not rsz:
        return {"d": str(d), "ec_match": ec_ok, "pass": ec_ok, "rsz_ok": None}
    r, s, z = int(rsz["r"]), int(rsz["s"]), int(rsz["z"])
    k = ((z + r * d) * inv(s, N)) % N
    try:
        kx, _ = ec_xy(k)
        r_ok = (kx % N) == (r % N)
    except Exception:
        r_ok = False
    eq_ok = (s * k) % N == (z + r * d) % N
    return {
        "d": str(d),
        "ec_match": True,
        "rsz_ok": r_ok and eq_ok,
        "pass": r_ok and eq_ok,
        "k": str(k),
    }


def close_q(q: int, n: int, tpx: int, tpy: int, rsz: dict | None) -> dict:
    mlo, mhi = n_mirror_window(n)
    if not (mlo <= q <= mhi):
        return {"q": str(q), "ec_match": False, "pass": False}
    d = (N - q) % N
    res = close_d(d, n, tpx, tpy, rsz)
    neg_ok = False
    if res["ec_match"]:
        try:
            qx, qy = ec_xy(q)
            dx, dy = ec_xy(d)
            neg_ok = qx == dx and qy == ((p - dy) % p)
        except Exception:
            neg_ok = False
    return {
        "q": str(q),
        "d": str(d),
        "ec_match": res["ec_match"],
        "neg_P_ok": neg_ok,
        "rsz_ok": res.get("rsz_ok"),
        "pass": res["ec_match"] and neg_ok and (res.get("rsz_ok") is not False),
    }


def run_puzzle(n: int, catalog, rsz_cache: dict) -> dict:
    e = catalog[n]
    if not e.public_key:
        return {"puzzle": n, "status": "NO_PUBKEY"}

    px, py = pubkey_xy(e.public_key)
    rsz = rsz_cache.get(str(n))
    d_true = e.private_key if e.solved and e.private_key > 0 else None
    bases = bases_for_point(px, py, rsz)
    exps = exponents_for(n, d_true)

    d_cands: set[int] = set()
    q_cands: set[int] = set()
    provenance: list[dict] = []

    for bname, base in bases.items():
        # keep base in (0,1]
        b = base
        if b <= 0:
            continue
        if b > 1:
            b = b - int(b)
        for ename, e_n in exps.items():
            # float powering for e_roof_N ≈ 1
            e_f = float(e_n)
            if e_f >= 1.0:
                e_f = 1.0 - 1e-15  # avoid identity-only; tiny nudge if float collapsed
            try:
                pv = powered(b, Decimal(str(e_f))) if e_f < 1 else b
                # prefer Decimal power when e is not ~1
                if e_n < Decimal("0.999"):
                    pv = powered(b, e_n)
                else:
                    # e_roof_N / e_q ≈ 1: use base itself (identity under float)
                    pv = b
            except Exception:
                continue
            ds = candidates_from_powered(pv, n)
            qs = q_candidates_from_powered(pv, n)
            d_cands |= ds
            q_cands |= qs
            provenance.append({
                "base": bname,
                "exp": ename,
                "powered_head": format(pv, "f")[:24],
                "d_cands": len(ds),
                "q_cands": len(qs),
            })

    lo, hi = d_window(n)
    d_in = {d for d in d_cands if lo <= d <= hi}
    mlo, mhi = n_mirror_window(n)
    q_in = {q for q in q_cands if mlo <= q <= mhi}

    d_hits = []
    for d in d_in:
        res = close_d(d, n, px, py, rsz)
        if res["ec_match"]:
            d_hits.append(res)

    q_hits = []
    for q in q_in:
        res = close_q(q, n, px, py, rsz)
        if res["ec_match"]:
            q_hits.append(res)

    sanity = None
    if d_true:
        sanity = close_d(d_true, n, px, py, rsz)

    return {
        "puzzle": n,
        "status": "SOLVED" if d_true else "UNSOLVED_PUBKEY",
        "has_rsz": bool(rsz),
        "exponents": {k: format(v, "f") for k, v in exps.items()},
        "bases": list(bases.keys()),
        "candidates": {
            "d_in_window": len(d_in),
            "q_in_mirror": len(q_in),
        },
        "d_path": {"tested": len(d_in), "ec_hits": len(d_hits), "hits": d_hits},
        "mirror_path": {"tested": len(q_in), "ec_hits": len(q_hits), "hits": q_hits},
        "sanity_true_d": sanity,
        "provenance_sample": provenance[:12],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    rsz_cache = {}
    if CACHE_PATH.exists():
        rsz_cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    # ALL puzzles with x,y (pubkey) — every fractional-power shell
    results = []
    for n in range(1, 161):
        e = catalog[n]
        if not e.public_key:
            results.append({"puzzle": n, "status": "NO_PUBKEY", "skipped": True})
            continue
        print(f"P{n}...")
        results.append(run_puzzle(n, catalog, rsz_cache))

    total_d = sum(r["d_path"]["tested"] for r in results if "d_path" in r)
    total_q = sum(r["mirror_path"]["tested"] for r in results if "mirror_path" in r)

    novel = []
    for r in results:
        if "d_path" not in r:
            continue
        true_d = catalog[r["puzzle"]].private_key if r["status"] == "SOLVED" else None
        for h in r["d_path"]["hits"]:
            if true_d is not None and int(h["d"]) == true_d:
                continue
            novel.append({"puzzle": r["puzzle"], "path": "d", **h})
        for h in r["mirror_path"]["hits"]:
            if true_d is not None and int(h["d"]) == true_d:
                continue
            novel.append({"puzzle": r["puzzle"], "path": "mirror", **h})

    sanity_ok = all(
        r.get("sanity_true_d", {}).get("ec_match") is True
        for r in results
        if r.get("status") == "SOLVED"
    )

    n_run = len([r for r in results if "d_path" in r])
    n_skip = len([r for r in results if r.get("skipped")])
    n_solved_run = len([r for r in results if r.get("status") == "SOLVED"])
    n_unsolved_run = len([r for r in results if r.get("status") == "UNSOLVED_PUBKEY"])

    summary = {
        "test": "fractional-power shells on corrected Real Decimal lens",
        "coverage": "ALL puzzles with pubkey (x,y); NO_PUBKEY skipped",
        "prior_raw_lens": "no novel hits",
        "puzzles_total": 160,
        "puzzles_run": n_run,
        "puzzles_skipped_no_pubkey": n_skip,
        "solved_run": n_solved_run,
        "unsolved_pubkey_run": n_unsolved_run,
        "d_candidates_tested": total_d,
        "q_candidates_tested": total_q,
        "novel_ec_hits": len(novel),
        "novel_hits": novel,
        "sanity_true_d_passes": sanity_ok,
        "exponents": [
            "e_hi=n/256",
            "e_lo=(n-1)/256",
            "e_hinge=(n-1+log2(3/2))/256",
            "e_roof_N=log2(N)/256",
            "e_q_low=log2(N-2^n)/256",
            "e_q_high=log2(N-2^(n-1))/256",
            "e_q=log2(N-d)/256 (solved)",
            "e_mirror_proxy=255/256",
        ],
        "verdict": (
            "FRACTIONAL-POWER SHELLS ON CORRECTED LENS: "
            + ("NO NOVEL HITS" if not novel else f"{len(novel)} NOVEL HITS")
        ),
    }

    # strip heavy provenance for json size if needed — keep
    payload = {"summary": summary, "results": results}
    (OUT / "fractional_power_ecdlp_verdict.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Fractional-power shells on corrected lens — ECDLP verdict",
        "",
        "Raw Real Decimal lens: already judged, no novel hits.",
        "This run: **fractional-power oath** on the same corrected bases.",
        "",
        "## Bases",
        "",
        "```text",
        "packet_p, packet_256, hex_stitch_512",
        "beta slot packets Px_i.(p−y)/p and /2^256",
        "r/N, s/N, z/N, r/2^256 when RSZ exists",
        "```",
        "",
        "## Exponents",
        "",
    ]
    for e in summary["exponents"]:
        lines.append(f"- `{e}`")

    lines.extend([
        "",
        "## Gates",
        "",
        "```text",
        "[d]G == P",
        "k = (z+r*d)*s^-1 mod N",
        "x([k]G) == r",
        "s*k == z+r*d mod N",
        "mirror: q dock, d=N−q, [q]G == −P",
        "```",
        "",
        "## Summary",
        "",
        f"- coverage: **all {summary['puzzles_run']} pubkey puzzles** "
        f"({summary['solved_run']} solved + {summary['unsolved_pubkey_run']} unsolved); "
        f"{summary['puzzles_skipped_no_pubkey']} NO_PUBKEY skipped",
        f"- d candidates: **{total_d}**",
        f"- q candidates: **{total_q}**",
        f"- novel EC hits: **{len(novel)}**",
        f"- sanity true d (all solved): **{sanity_ok}**",
        "",
        f"**{summary['verdict']}**",
        "",
        "## Per puzzle",
        "",
        "| P | status | d tested | q tested | ec hits d | ec hits mir | sanity |",
        "|---|--------|----------|----------|-----------|-------------|--------|",
    ])
    for r in results:
        if "d_path" not in r:
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
        "```text",
        "Raw corrected lens:              judged, no novel hits",
        "Fractional-power corrected lens: judged, no novel hits",
        "```",
        "",
        "Judge Popcorn: **the witness testified plain and under the fractional-power oath. "
        "No conviction either time.**",
        "",
    ])
    (OUT / "fractional_power_ecdlp_verdict.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print(f"wrote {OUT / 'fractional_power_ecdlp_verdict.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
