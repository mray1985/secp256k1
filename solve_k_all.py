#!/usr/bin/env python3
"""
Solve nonce k from ECDSA for all solved puzzles with hashkeys RSZ:

    s*k = z + r*d  (mod N)
    k = s^-1 * (z + r*d)  (mod N)

Verifies against published nonce on hashkeys where present, and k*G vs R from r.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from hashkeys_rsz import PUZZLE_RSZ, p, recover_r_point_from_sig, y_roots_from_x
from puzzle_keys_53125 import parse_53125

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
LOG = ROOT / "ARCHIVE" / "cloud_pages" / "solve_k_all.log"
CSV = ROOT / "ARCHIVE" / "cloud_pages" / "solve_k_all.csv"


def pt_scalar(s: int) -> tuple[int, int]:
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_secret_exponent(s % N, curve=SECP256k1)
    pt = sk.get_verifying_key().pubkey.point
    return int(pt.x()), int(pt.y())


def solve_k(r: int, s: int, z: int, d: int) -> int:
    return (pow(s, -1, N) * (z + r * d)) % N


def r_point_candidates(r_sig: int) -> list[tuple[int, int, str]]:
    """All affine R candidates from signature r (both y roots per valid x lift)."""
    out: list[tuple[int, int, str]] = []
    xs: list[int] = []
    for x in (r_sig % N, (r_sig % N) + N):
        if 0 < x < p and x not in xs:
            xs.append(x)
    for x in xs:
        y_sq = (pow(x, 3, p) + 7) % p
        if pow(y_sq, (p - 1) // 2, p) != 1:
            continue
        y_pos, y_neg = y_roots_from_x(x)
        for y in (y_pos, y_neg):
            label = "y_even" if y % 2 == 0 else "y_odd"
            out.append((x, y, label))
    return out


def match_kG_to_r_candidates(kG: tuple[int, int], r_sig: int) -> tuple[bool, str, bool]:
    """Return (matches_any_branch, branch_label, prefer_even_match)."""
    kG_pt = kG
    prefer_even = recover_r_point_from_sig(r_sig)
    prefer_even_match = prefer_even is not None and kG_pt == prefer_even
    for x, y, label in r_point_candidates(r_sig):
        if (x, y) == kG_pt:
            return True, label, prefer_even_match
    return False, "", prefer_even_match


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    keys = parse_53125()
    rows: list[dict] = []

    log("=== Solve k = s^-1(z + r*d) mod N for all RSZ + solved d ===")
    log("")

    for n in sorted(PUZZLE_RSZ):
        rsz = PUZZLE_RSZ[n]
        pk = keys.get(n)
        d = pk.d if pk and pk.d > 0 else None
        if d is None:
            log(f"P{n}: RSZ present, d unknown — k not solvable from ECDSA")
            rows.append(
                {
                    "n": n,
                    "d_known": False,
                    "k_solved": "",
                    "k_hex": "",
                    "k_bits": "",
                    "published_k": rsz.nonce_hex or "",
                    "match_published": "",
                    "ecdsa_ok": "",
                    "kG_x_eq_r": "",
                    "kG_eq_R_any_branch": "",
                    "kG_y_branch": "",
                    "kG_eq_R_prefer_even": "",
                }
            )
            continue

        k = solve_k(rsz.r, rsz.s, rsz.z, d)
        ecdsa_ok = (rsz.s * k) % N == (rsz.z + rsz.r * d) % N
        pub_k = rsz.k
        match_pub = pub_k is not None and k == pub_k
        kx, ky = pt_scalar(k)
        r_x_match = (kx % N) == (rsz.r % N) or kx == rsz.r
        kG_any, y_branch, kG_prefer_even = match_kG_to_r_candidates((kx, ky), rsz.r)

        rows.append(
            {
                "n": n,
                "d_known": True,
                "k_solved": str(k),
                "k_hex": f"{k:064x}",
                "k_bits": k.bit_length(),
                "published_k": rsz.nonce_hex or "",
                "match_published": match_pub if pub_k else "n/a",
                "ecdsa_ok": ecdsa_ok,
                "kG_x_eq_r": r_x_match,
                "kG_eq_R_any_branch": kG_any,
                "kG_y_branch": y_branch,
                "kG_eq_R_prefer_even": kG_prefer_even,
            }
        )

        pub_note = f"match_hashkeys={match_pub}" if pub_k else "no published k"
        log(
            f"P{n}: k={k} ({k.bit_length()}b)  ECDSA={ecdsa_ok}  "
            f"{pub_note}  kG==R_any={kG_any} ({y_branch})  prefer_even={kG_prefer_even}"
        )
        log(f"     k_hex = {k:064x}")

    log("")
    solved = [r for r in rows if r["d_known"]]
    with_pub = [r for r in solved if r["published_k"]]
    log(f"Solved k: {len(solved)} puzzles")
    log(f"ECDSA verify: {sum(1 for r in solved if r['ecdsa_ok'])}/{len(solved)}")
    log(
        f"Match hashkeys published k: "
        f"{sum(1 for r in with_pub if r['match_published'] is True)}/{len(with_pub)}"
    )
    log(
        f"k*G == R (any y branch): "
        f"{sum(1 for r in solved if r['kG_eq_R_any_branch'])}/{len(solved)}"
    )
    log(
        f"k*G == R (prefer_even_y only): "
        f"{sum(1 for r in solved if r['kG_eq_R_prefer_even'])}/{len(solved)}"
    )

    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log(f"CSV {CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
