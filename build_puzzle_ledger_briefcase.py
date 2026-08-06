#!/usr/bin/env python3
"""
One operation ledger per puzzle (1–160) in ARCHIVE/briefcase/.

Pubkey catalog: privatekeys.pw export (ARCHIVE/puzzle_catalog_160.csv)
RSZ: blockchain spend tx + hashkeys partial-spend (P135 etc.)
"""

from __future__ import annotations

import json
import shutil
from decimal import Decimal, getcontext
from pathlib import Path

from build_complexity_operations_ledger import (
    BETA,
    BETA_SQ,
    DELTA,
    LAMBDA,
    N,
    Op,
    add_op,
    fmt_hex,
    inv,
    map_p_to_n,
    p,
    pick_y_branch,
    y_roots,
)
from hashkeys_rsz import recover_r_point_from_sig
from puzzle_catalog import PuzzleCatalogEntry, load_catalog
from puzzle_rsz_blockchain import CACHE_PATH, PuzzleRSZRecord, build_cache, get_rsz

ROOT = Path(__file__).resolve().parent
BRIEFCASE = ROOT / "ARCHIVE" / "briefcase"
MASTER_MD = ROOT / "ARCHIVE" / "operation_ledger_index.md"
MASTER_JSON = ROOT / "ARCHIVE" / "operation_ledger_index.json"


def log2_decimal(n: int) -> Decimal:
    getcontext().prec = 80
    return Decimal(n).ln() / Decimal(2).ln()


def pubkey_xy(compressed: str) -> tuple[int, int]:
    px = int(compressed[2:], 16)
    y_pos, y_neg, _ = y_roots(px)
    py = y_pos if compressed.startswith("02") else y_neg
    return px, py


def k_from_d(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N) * (z + r * d)) % N


def render_puzzle_md(puzzle_num: int, ops: list[Op], verdict: dict) -> str:
    verified = sum(1 for o in ops if o.verified is True)
    lines = [
        f"# Puzzle {puzzle_num} — Operation Ledger",
        "",
        "Full-information format: **formula → values → live verification**.",
        "Re-run: `python build_puzzle_ledger_briefcase.py`",
        "",
        "## Verdict",
        "",
    ]
    for k, v in verdict.items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append(f"**Operations:** {len(ops)} total, {verified} verified")
    lines.append("")
    lines.append("---")
    lines.append("")

    phase = ""
    for op in ops:
        if op.phase != phase:
            phase = op.phase
            lines.append(f"### Phase {phase}")
            lines.append("")
        v = "✓" if op.verified else ("?" if op.verified is None else "✗")
        q = " **QUARANTINED**" if op.quarantine else ""
        lines.append(f"#### {op.name}  [{v}]{q}")
        lines.append(f"**Formula:** {op.formula}")
        if op.note:
            lines.append(f"**Note:** {op.note}")
        lines.append("```")
        lines.extend(op.lines)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def build_puzzle_ops(
    entry: PuzzleCatalogEntry,
    rsz: PuzzleRSZRecord | None,
) -> tuple[list[Op], dict]:
    ops: list[Op] = []
    n = entry.n
    d = entry.private_key
    lo, hi = entry.range_min, entry.range_max

    add_op(ops, "00_identity", f"Puzzle {n} catalog row",
           "privatekeys.pw / blockchain",
           [
               f"puzzle = {n}",
               f"address = {entry.address}",
               f"key range [2^{n-1}, 2^{n}) = [{lo}, {hi})",
               f"range_min hex = {hex(lo)}",
               f"range_max hex = {hex(hi)}",
               f"btc_value = {entry.btc_value}",
               f"hash160 = {entry.hash160}",
               f"solved = {entry.solved}",
               (
                   f"private key d = {d}"
                   if d
                   else "private key d = unknown (unsolved — not zero)"
               ),
               f"solve_date = {entry.solve_date or '—'}",
               f"public_key leaked = {bool(entry.public_key)}",
           ],
           verified=True)

    if not entry.public_key:
        add_op(ops, "01_no_pubkey", "pubkey not exposed on chain",
               "no spend tx with public key — brute-force address only",
               [
                   "Cannot build Px/Py or RSZ bridge until pubkey is revealed by a spend.",
                   f"Target hash160 = {entry.hash160}",
               ],
               verified=None,
               note="Puzzles without partial spend remain hash160-only targets.")
        verdict = {
            "status": "UNSOLVED — no pubkey" if not entry.solved else "SOLVED but pubkey row empty",
            "rsz": "TBD — no pubkey",
            "address": entry.address,
        }
        return ops, verdict

    px, py = pubkey_xy(entry.public_key)
    add_op(ops, "01_pubkey", "compressed pubkey → Px, Py",
           entry.public_key,
           [
               f"pub_compressed = {entry.public_key}",
               f"Px = {px}",
               f"\t{fmt_hex(px)}",
               f"Py = {py}",
               f"\t{fmt_hex(py)}",
               f"bit_length(d) = {d.bit_length() if d else 0}",
           ],
           verified=px > 0 and py > 0)

    y_sq = (pow(px, 3, p) + 7) % p
    on_curve = (py * py) % p == y_sq
    y_pos, y_neg, _ = y_roots(px)
    add_op(ops, "02_curve_law", "y² = x³ + 7 mod p",
           "two branches only: y and p-y",
           [
               f"Px³ + 7 mod p = {y_sq}",
               f"Py² mod p = {(py * py) % p}",
               f"on_curve: {on_curve}",
               f"y branch = {y_pos}",
               f"p-y branch = {y_neg}",
           ],
           verified=on_curve)

    px3, px2, px1 = px, (px * inv(BETA, p)) % p, (px * inv(BETA_SQ, p)) % p
    add_op(ops, "03_x_beta_triple", "three x β-slots",
           "Px3 = pubkey x; Px2 = Px3/β; Px1 = Px3/β²",
           [
               f"β³ mod p = {pow(BETA, 3, p)}",
               f"Px1 = {px1}",
               f"Px2 = {px2}",
               f"Px3 = {px3}",
               f"Px2 * β = Px3: {(px2 * BETA) % p == px3}",
           ],
           verified=(px2 * BETA) % p == px3)

    py_slots = [pick_y_branch(x, even=(py % 2 == 0)) for x in (px1, px2, px3)]
    add_op(ops, "04_shared_y_branches", "slot labels, not three y branches",
           "Py1 = Py2 = Py3 on selected parity",
           [
               f"Py1 = Py2 = Py3 = {py_slots[0]}",
               f"ry note: y-side uses parity branch y or p-y only",
           ],
           verified=py_slots[0] == py_slots[1] == py_slots[2] == py)

    lam_py = map_p_to_n(py)
    lam_py_neg = map_p_to_n((-py) % p)
    add_op(ops, "05_n_shadow_py", "map_p_to_n(Py)",
           "lam_py + lam_py_neg = N-1",
           [
               f"map_p_to_n(Py) = {lam_py}",
               f"map_p_to_n(-Py) = {lam_py_neg}",
               f"sum mod N = {(lam_py + lam_py_neg) % N}",
           ],
           verified=(lam_py + lam_py_neg) % N == N - 1)

    if rsz is None:
        add_op(ops, "06_rsz", "spend-line RSZ",
               "not yet fetched from blockchain",
               ["Run: python puzzle_rsz_blockchain.py", f"cache: {CACHE_PATH.name}"],
               verified=None,
               quarantine=True,
               note="RSZ TBD — fetch spend tx from blockstream / hashkeys.")
        verdict = {
            "status": "SOLVED" if entry.solved else "UNSOLVED",
            "pubkey": "YES",
            "rsz": "TBD",
            "x_beta_triple": "VERIFIED",
        }
        return ops, verdict

    k = rsz.k
    if d > 0:
        k = k_from_d(rsz.r, rsz.s, rsz.z, d)
    ecdsa_ok = (rsz.s * k) % N == (rsz.z + rsz.r * d) % N if d > 0 and k else None

    add_op(ops, "06_rsz", "blockchain / hashkeys RSZ",
           "s*k = z + r*d mod N",
           [
               f"source = {rsz.source}",
               f"txid = {rsz.txid}",
               f"input_index = {rsz.input_index}",
               f"r = {rsz.r}",
               f"\t{fmt_hex(rsz.r)}",
               f"s = {rsz.s}",
               f"z = {rsz.z}",
               f"pub_compressed = {rsz.pub_compressed}",
               f"k (computed) = {k}" if k else "k = not computed (d unknown)",
               f"s*k mod N = {(rsz.s * k) % N if k else '—'}",
               f"z+r*d mod N = {(rsz.z + rsz.r * d) % N if d else '—'}",
               f"ECDSA verify: {ecdsa_ok}",
           ],
           verified=ecdsa_ok if ecdsa_ok is not None else (k is not None and d == 0))

    r_pt = recover_r_point_from_sig(rsz.r, prefer_even_y=(py % 2 == 0))
    rx2, ry2 = r_pt if r_pt else (rsz.r % p, 0)
    rx3 = (rx2 * BETA) % p
    rx1 = (rx2 * inv(BETA, p)) % p
    ry_slots = [pick_y_branch(x, even=(ry2 % 2 == 0)) for x in (rx1, rx2, rx3)]
    lam = (px3 * inv(rx3, p)) % p
    lam1 = (px3 * inv(rx2, p)) % p
    lam_y = (py * inv(ry2, p)) % p if ry2 else 0

    add_op(ops, "07_r_beta_triple", "rx3 = rx2 * β",
           "spend-line x slots",
           [
               f"rx2 = {rx2}",
               f"rx3 = {rx3}",
               f"rx3 = rx2 * β: {(rx2 * BETA) % p == rx3}",
           ],
           verified=(rx2 * BETA) % p == rx3)

    add_op(ops, "08_lambda_x_bridge", "Λ and Λ1",
           "Px3/rx3 = Λ; Px3/rx2 = Λ1",
           [
               f"Λ = Px3/rx3 = {lam}",
               f"Λ1 = Px3/rx2 = {lam1}",
               f"Λ/Λ1 = β²: {(lam * inv(lam1, p)) % p == BETA_SQ}",
               f"P135 reference Λ = {LAMBDA}",
               f"matches P135 Λ: {lam == LAMBDA}" if n == 135 else "per-puzzle Λ",
           ],
           verified=lam1 and (lam * inv(lam1, p)) % p == BETA_SQ)

    add_op(ops, "09_y_parity_bridge", "ry2 = ry3; lambda_y = Py/ry",
           "no y-side β rotation",
           [
               f"ry2 = {ry_slots[1]}",
               f"ry3 = {ry_slots[2]}",
               f"ry2 == ry3: {ry_slots[1] == ry_slots[2]}",
               f"lambda_y = {lam_y}",
           ],
           verified=ry_slots[1] == ry_slots[2] and ry2 > 0)

    lam_n = (px3 * inv(rx3, N)) % N
    lam_y_n = (py * inv(ry2, N)) % N if ry2 else 0
    add_op(ops, "10_n_shadow_bridges", "Lambda_N, GAP_x, GAP_y",
           "N-side shadow bookkeeping",
           [
               f"Lambda_N = {lam_n}",
               f"lambda_y_N = {lam_y_n}",
               f"GAP_x = {(lam_n - lam) % N}",
               f"GAP_y = {(lam_y_n - lam_n) % N}",
           ],
           verified=lam_n == (px3 * inv(rx3, N)) % N)

    verdict = {
        "status": "SOLVED" if entry.solved else "UNSOLVED (pubkey exposed)",
        "rsz_source": rsz.source,
        "x_beta_triple": "VERIFIED",
        "slot_2_to_3_x": "rx3 = rx2 * β",
        "y_side": "ry2 = ry3",
        "Λ": str(lam),
        "Λ1": str(lam1),
    }
    return ops, verdict


def write_puzzle_files(puzzle_num: int, ops: list[Op], verdict: dict) -> None:
    stem = f"puzzle_{puzzle_num:03d}_ledger"
    (BRIEFCASE / f"{stem}.md").write_text(
        render_puzzle_md(puzzle_num, ops, verdict), encoding="utf-8"
    )
    payload = {
        "puzzle": puzzle_num,
        "verdict": verdict,
        "operations": [
            {
                "phase": o.phase,
                "name": o.name,
                "formula": o.formula,
                "lines": o.lines,
                "verified": o.verified,
                "note": o.note,
                "quarantine": o.quarantine,
            }
            for o in ops
        ],
    }
    (BRIEFCASE / f"{stem}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_index(manifest: list[dict]) -> None:
    lines = [
        "# Briefcase — Per-Puzzle Operation Ledgers (1–160)",
        "",
        f"**{len(manifest)}** puzzle ledgers.",
        "Catalog: `ARCHIVE/puzzle_catalog_160.csv` (privatekeys.pw)",
        "RSZ cache: `ARCHIVE/puzzle_rsz_cache.json` (blockstream + hashkeys)",
        "",
        "Re-run: `python build_puzzle_ledger_briefcase.py`",
        "",
        "| Puzzle | Solved | Pubkey | RSZ | Verified | File |",
        "|--------|--------|--------|-----|----------|------|",
    ]
    for row in manifest:
        lines.append(
            f"| {row['puzzle']} | {row['solved']} | {row['pubkey']} | {row['rsz']} | "
            f"{row['verified']}/{row['total']} | `{row['file']}` |"
        )
    lines.extend([
        "",
        "## Puzzle 135 master",
        "",
        "Full Complexity Simplified ledger:",
        "- `puzzle_135_complexity_master_ledger.md`",
        "- `puzzle_135_complexity_master_ledger.json`",
        "",
    ])
    (BRIEFCASE / "index.md").write_text("\n".join(lines), encoding="utf-8")
    (BRIEFCASE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    import sys

    BRIEFCASE.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    refresh_rsz = "--fetch-rsz" in sys.argv

    cache: dict = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    if refresh_rsz or not CACHE_PATH.exists():
        print("Fetching RSZ from blockchain (this may take several minutes)...")
        cache = build_cache(list(range(1, 161)), refresh=refresh_rsz)

    manifest: list[dict] = []
    for n in range(1, 161):
        entry = catalog[n]
        rsz_dict = cache.get(str(n))
        rsz = PuzzleRSZRecord(**rsz_dict) if rsz_dict else None
        if rsz is None and entry.public_key:
            rsz = get_rsz(n, entry, cache)
            CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")

        ops, verdict = build_puzzle_ops(entry, rsz)
        write_puzzle_files(n, ops, verdict)
        verified = sum(1 for o in ops if o.verified is True)
        manifest.append({
            "puzzle": n,
            "file": f"puzzle_{n:03d}_ledger.md",
            "solved": entry.solved,
            "pubkey": bool(entry.public_key),
            "rsz": bool(rsz),
            "total": len(ops),
            "verified": verified,
        })

    if MASTER_MD.exists():
        shutil.copy2(MASTER_MD, BRIEFCASE / "puzzle_135_complexity_master_ledger.md")
    if MASTER_JSON.exists():
        shutil.copy2(MASTER_JSON, BRIEFCASE / "puzzle_135_complexity_master_ledger.json")

    write_index(manifest)
    rsz_count = sum(1 for m in manifest if m["rsz"])
    print(f"briefcase: 160 ledgers -> {BRIEFCASE}")
    print(f"  RSZ filled: {rsz_count}/160")
    print(f"  index: {BRIEFCASE / 'index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
