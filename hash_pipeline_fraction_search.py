#!/usr/bin/env python3
"""
Hash pipeline bucket search — SHA256 #1, SHA256(vh), SHA256d, checksum, payload.

Tests fractional relations vs log2(d)/log2(N), log_pos, frac_d across solved puzzles.
Inspired by address pipeline steps 2/5/6/7/8 in user notes.
"""

from __future__ import annotations

import hashlib
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from ecdlp_full_pipeline import N, pubkey_from_scalar, puzzle_band, y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from puzzle_keys_53125 import parse_53125  # noqa: E402

ARCHIVE = ROOT / "ARCHIVE"
REPORT = ARCHIVE / "hash_pipeline_fraction_search.txt"

getcontext().prec = 60
LOG2_N = float(Decimal(N).ln() / Decimal(2).ln())


def pipeline_ints(px: int, py: int) -> dict[str, int]:
    comp = (b"\x02" if py % 2 == 0 else b"\x03") + px.to_bytes(32, "big")
    sha1 = hashlib.sha256(comp).digest()
    h160 = hashlib.new("ripemd160", sha1).digest()
    vh = b"\x00" + h160
    sha_vh = hashlib.sha256(vh).digest()  # step 5 in notes
    sha2d = hashlib.sha256(sha_vh).digest()  # step 6
    chk = sha2d[:4]
    payload = vh + chk
    return {
        "sha1": int.from_bytes(sha1, "big"),
        "h160": int.from_bytes(h160, "big"),
        "sha_vh": int.from_bytes(sha_vh, "big"),
        "sha2d": int.from_bytes(sha2d, "big"),
        "chk": int.from_bytes(chk, "big"),
        "payload": int.from_bytes(payload, "big"),
        "sha1_hex": sha1.hex(),
        "sha_vh_hex": sha_vh.hex(),
        "sha2d_hex": sha2d.hex(),
        "chk_hex": chk.hex(),
        "d_hex_head2": None,
    }


def frac_mod(x: int, mod: int) -> float:
    return (x % mod) / mod if mod else 0.0


def main() -> int:
    keys = parse_53125()
    rows = []
    for n, pk in sorted(keys.items()):
        if pk.d <= 0:
            continue
        lo, hi, _ = puzzle_band(n)
        if not (lo <= pk.d < hi):
            continue
        ints = pipeline_ints(pk.px, pk.py)
        d = pk.d
        dhex = format(d, "x")
        ints["d_hex_head2"] = dhex[:2]
        log_pos = math.log2(d) - (n - 1)
        y_d = math.log2(d) / LOG2_N
        frac_d = (d - lo) / lo
        rows.append(
            {
                "n": n,
                "d": d,
                "lo": lo,
                "log_pos": log_pos,
                "y_d": y_d,
                "frac_d": frac_d,
                **ints,
            }
        )

    lines = [
        "HASH PIPELINE FRACTION SEARCH",
        f"puzzles: {len(rows)}",
        "",
        "Pipeline steps: sha1=SHA256(pub), sha_vh=SHA256(00||h160), sha2d=SHA256(sha_vh), chk=sha2d[:4]",
        "",
    ]

    # digit head matches (user note)
    lines.append("=== first-2-hex-digit matches (private d) ===")
    for step in ("sha1_hex", "sha_vh_hex", "sha2d_hex", "chk_hex"):
        m2 = m4 = 0
        for r in rows:
            hx = r[step]
            dh = format(r["d"], "x")
            if hx[:2] == dh[:2]:
                m2 += 1
            if hx[:4] == dh[:4]:
                m4 += 1
        lines.append(f"  {step[:6]} head2==d head2: {m2}/{len(rows)}  head4: {m4}/{len(rows)}")
    lines.append("")

    # build predictors
    predictors: dict[str, list[float]] = {}
    for r in rows:
        lo, n = r["lo"], r["n"]
        for name, val in [
            ("sha1/N", r["sha1"] / N),
            ("sha_vh/N", r["sha_vh"] / N),
            ("sha2d/N", r["sha2d"] / N),
            ("sha1/2^256", r["sha1"] / (2**256)),
            ("sha_vh/2^256", r["sha_vh"] / (2**256)),
            ("sha2d/2^256", r["sha2d"] / (2**256)),
            ("chk/2^32", r["chk"] / (2**32)),
            ("payload/2^200", r["payload"] / (2**200)),
            ("h160/2^160", r["h160"] / (2**160)),
            ("sha1 mod lo / lo", frac_mod(r["sha1"], lo)),
            ("sha_vh mod lo / lo", frac_mod(r["sha_vh"], lo)),
            ("sha2d mod lo / lo", frac_mod(r["sha2d"], lo)),
            ("h160 mod lo / lo", frac_mod(r["h160"], lo)),
            ("d mod lo / lo", frac_mod(r["d"], lo)),
            ("log2(sha_vh)/log2(N)", math.log2(r["sha_vh"]) / LOG2_N if r["sha_vh"] else 0),
            ("log2(sha1)/log2(N)", math.log2(r["sha1"]) / LOG2_N),
            ("n/256", n / 256),
        ]:
            predictors.setdefault(name, []).append(val)

    targets = {
        "log_pos": [r["log_pos"] for r in rows],
        "frac_d": [r["frac_d"] for r in rows],
        "y_d - n/256": [r["y_d"] - r["n"] / 256 for r in rows],
    }

    for tname, ys in targets.items():
        lines.append(f"=== predict {tname} (best buckets) ===")
        inv = []
        corrs = []
        my = sum(ys) / len(ys)
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        for k, xs in predictors.items():
            if len(xs) != len(ys):
                continue
            mx = sum(xs) / len(xs)
            dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
            if dx > 1e-15 and dy > 1e-15:
                r = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(ys))) / (dx * dy)
                corrs.append((abs(r), r, k))
            diffs = [ys[i] - xs[i] for i in range(len(ys))]
            mu = sum(diffs) / len(diffs)
            std = math.sqrt(sum((d - mu) ** 2 for d in diffs) / len(diffs))
            inv.append((std, mu, k))
        corrs.sort(reverse=True)
        inv.sort()
        for _, r, k in corrs[:12]:
            lines.append(f"  r={r:+.4f}  {k}")
        lines.append(f"  best invariant std={inv[0][0]:.5f} mean={inv[0][1]:+.5f}  {inv[0][2]}")
        lines.append("")

    # user note style: sha_vh / 2^255 as percent
    lines.append("=== user-note style: sha_vh / 2^(n-1) vs band percent ===")
    for r in rows[:5]:
        pct = 100 * r["sha_vh"] / (2 ** (r["n"] - 1))
        pct_d = 100 * r["frac_d"]
        lines.append(
            f"  P{r['n']:3d} sha_vh/2^{r['n']-1} %={pct:.2f}  frac_d%={pct_d:.2f}  diff={abs(pct-pct_d):.2f}"
        )
    errs = [abs(100 * r["sha_vh"] / (2 ** (r["n"] - 1)) - 100 * r["frac_d"]) for r in rows]
    lines.append(f"  mean abs diff %: {sum(errs)/len(errs):.2f}")
    lines.append("")

    # P135
    lines.append("=== P135 predictions ===")
    rsz = PUZZLE_RSZ[135]
    px = int(rsz.pub_compressed[2:], 16)
    yp, yn = y_roots(px)
    py = yp if yp % 2 == 0 else yn
    lo135, hi135, _ = puzzle_band(135)
    p135 = pipeline_ints(px, py)
    preds135 = {
        "sha_vh mod lo / lo": frac_mod(p135["sha_vh"], lo135),
        "sha2d mod lo / lo": frac_mod(p135["sha2d"], lo135),
        "h160 mod lo / lo": frac_mod(p135["h160"], lo135),
        "sha_vh/2^256": p135["sha_vh"] / (2**256),
        "chk/2^32": p135["chk"] / (2**32),
    }
    lines.append(f"  addr pipeline sha_vh head={p135['sha_vh_hex'][:8]} chk={p135['chk_hex']}")
    hits = []
    for name, pred in preds135.items():
        d_est = int(lo135 * (1 + pred))
        if lo135 <= d_est < hi135:
            gx, gy = pubkey_from_scalar(d_est)
            ok = gx == px and gy == py
            lines.append(f"  lo*(1+{name}): ec={ok} tail...{str(d_est)[-6:]}")
            if ok:
                hits.append(name)

    # best invariant for log_pos from prior scan
    best_k = "sha_vh mod lo / lo"
    diffs = []
    for r in rows:
        pred = frac_mod(r["sha_vh"], r["lo"])
        diffs.append(r["log_pos"] - pred)
    mu = sum(diffs) / len(diffs)
    lp = preds135[best_k] + mu
    d135 = int(lo135 * (2**lp))
    if lo135 <= d135 < hi135:
        gx, gy = pubkey_from_scalar(d135)
        ok = gx == px and gy == py
        lines.append(f"  log_pos invariant {best_k}: lp={lp:.6f} d ec={ok}")
        if ok:
            hits.append("log_pos inv")

    lines.append("")
    lines.append(f"VERDICT: EC hits {len(hits)}")

    text = "\n".join(lines)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
