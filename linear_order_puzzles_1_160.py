#!/usr/bin/env python3
"""Linear-order rankings for puzzles 1..160.

Always (all 160 with catalog fields):
  n, band floors, hash160/rmd160, address payload, sha256_vh, sha256_chk, checksum4

When compressed pubkey known:
  Px, Py, Pmy, sha256_pubkey, and (if solved+rsz) r,s,z,Ry,d,log2d

Sort each series ascending by numeric value; tag source puzzle_n.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from puzzle_catalog import load_catalog
from scan_log_ratio_cross_puzzle import load_rows, recover_xy_from_pubkey, P

OUT = Path("logs/log_ratio_scan")
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + ALPHABET.index(ch)
    # restore leading zeros (Base58 '1')
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    h = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    return b"\x00" * pad + h


@dataclass
class Row160:
    n: int
    address: str
    hash160_hex: str
    hash160_int: int
    addr_payload_int: int  # 25-byte 00||h160||checksum as int
    sha256_vh_int: int  # SHA256(0x00||h160)
    sha256_chk_int: int  # SHA256(sha256_vh)
    checksum4_int: int  # first 4 bytes of sha256_chk
    # optional
    public_key: str
    d: int | None
    log2d: float | None
    Px: int | None
    Py: int | None
    Pmy: int | None
    neg_y: int | None  # (-Py) mod p  (== Pmy when 0 < Py < p)
    y2_mod_p: int | None  # y^2 mod p (reference only; erases carry)
    x3_plus_7_mod_p: int | None  # x^3 + 7 mod p (reference only)
    y2_full: int | None  # y^2 unreduced
    x3plus7_full: int | None  # x^3 + 7 unreduced
    p_carry: int | None  # C = (X - Y) / p
    # formal analogues (NOT on-curve identities): treat rmd160 / address_payload as field elements
    rmd160_cubed_plus_7_mod_p: int  # rmd160^3 + 7 mod p
    address_payload_sq_mod_p: int  # address_payload^2 mod p
    rmd160_sq_mod_p: int  # rmd160^2 mod p
    address_payload_cubed_plus_7_mod_p: int  # address_payload^3 + 7 mod p
    sha256_pubkey_int: int | None
    r: int | None
    s: int | None
    z: int | None
    Ry: int | None


def build_rows() -> list[Row160]:
    cat = load_catalog()
    rsz_by_n = {r.n: r for r in load_rows()}

    rows: list[Row160] = []
    for n in range(1, 161):
        e = cat[n]
        h160 = bytes.fromhex(e.hash160)
        assert len(h160) == 20
        vh = b"\x00" + h160
        sha_vh = hashlib.sha256(vh).digest()
        sha_chk = hashlib.sha256(sha_vh).digest()
        checksum4 = sha_chk[:4]
        payload = vh + checksum4
        # verify address if present
        addr = e.address

        d = e.private_key if e.private_key > 0 else None
        px = py = pmy = None
        neg_y = y2 = rhs = None
        sha_pub = None
        r = s = z = ry = None

        pub = e.public_key
        if pub:
            px, py = recover_xy_from_pubkey(pub)
            pmy = P - py
            pref = bytes.fromhex(pub[:2])
            body = bytes.fromhex(pub[2:])
            comp = pref + body
            sha_pub = int.from_bytes(hashlib.sha256(comp).digest(), "big")

        rr = rsz_by_n.get(n)
        if rr is not None:
            r, s, z, ry = rr.r, rr.s, rr.z, rr.Ry
            if d is None and rr.d:
                d = rr.d
            if px is None and rr.Px:
                px, py, pmy = rr.Px, rr.Py, rr.Pmy

        if px is not None and py is not None:
            neg_y = (-py) % P
            y2 = (py * py) % P
            rhs = (pow(px, 3, P) + 7) % P
            y2_full = py * py
            x3_full = px * px * px + 7
            diff = x3_full - y2_full
            if diff % P != 0:
                raise RuntimeError(f"P{n}: unreduced X-Y not divisible by p")
            p_carry = diff // P
        else:
            y2_full = x3_full = p_carry = None

        h160_int = int.from_bytes(h160, "big")
        payload_int = int.from_bytes(payload, "big")
        rmd160_cube7 = (pow(h160_int, 3, P) + 7) % P
        addr_sq = pow(payload_int, 2, P)
        rmd160_sq = pow(h160_int, 2, P)
        addr_cube7 = (pow(payload_int, 3, P) + 7) % P

        rows.append(
            Row160(
                n=n,
                address=addr,
                hash160_hex=e.hash160,
                hash160_int=h160_int,
                addr_payload_int=payload_int,
                sha256_vh_int=int.from_bytes(sha_vh, "big"),
                sha256_chk_int=int.from_bytes(sha_chk, "big"),
                checksum4_int=int.from_bytes(checksum4, "big"),
                public_key=pub or "",
                d=d,
                log2d=(math.log2(d) if d else None),
                Px=px,
                Py=py,
                Pmy=pmy,
                neg_y=neg_y,
                y2_mod_p=y2,
                x3_plus_7_mod_p=rhs,
                y2_full=y2_full,
                x3plus7_full=x3_full,
                p_carry=p_carry,
                rmd160_cubed_plus_7_mod_p=rmd160_cube7,
                address_payload_sq_mod_p=addr_sq,
                rmd160_sq_mod_p=rmd160_sq,
                address_payload_cubed_plus_7_mod_p=addr_cube7,
                sha256_pubkey_int=sha_pub,
                r=r,
                s=s,
                z=z,
                Ry=ry,
            )
        )
    return rows


def rank_series(
    rows: list[Row160], name: str, getter
) -> list[dict]:
    triples = []
    for row in rows:
        v = getter(row)
        if v is None:
            continue
        triples.append((v, row.n, row.d))
    triples.sort(key=lambda t: t[0])
    out = []
    for rank, (val, puzzle_n, d) in enumerate(triples, start=1):
        out.append(
            {
                "linear_rank": rank,
                "puzzle_n": puzzle_n,
                "value": val if not isinstance(val, float) else val,
                "value_repr": repr(val) if isinstance(val, float) else str(val),
                "d": d,
            }
        )
    return out


def main() -> None:
    rows = build_rows()
    OUT.mkdir(parents=True, exist_ok=True)

    series_spec = [
        ("n", lambda r: r.n),
        ("d", lambda r: r.d),
        ("log2d", lambda r: r.log2d),
        ("Px", lambda r: r.Px),
        ("Py", lambda r: r.Py),
        ("Pmy", lambda r: r.Pmy),
        ("neg_y", lambda r: r.neg_y),  # (-y) mod p
        ("y2_mod_p", lambda r: r.y2_mod_p),  # y^2 mod p (erases carry)
        ("x3_plus_7_mod_p", lambda r: r.x3_plus_7_mod_p),  # x^3+7 mod p
        ("y2_full", lambda r: r.y2_full),
        ("x3plus7_full", lambda r: r.x3plus7_full),
        ("p_carry", lambda r: r.p_carry),
        ("rmd160_cubed_plus_7_mod_p", lambda r: r.rmd160_cubed_plus_7_mod_p),
        ("address_payload_sq_mod_p", lambda r: r.address_payload_sq_mod_p),
        ("rmd160_sq_mod_p", lambda r: r.rmd160_sq_mod_p),
        ("address_payload_cubed_plus_7_mod_p", lambda r: r.address_payload_cubed_plus_7_mod_p),
        ("r", lambda r: r.r),
        ("s", lambda r: r.s),
        ("z", lambda r: r.z),
        ("Ry", lambda r: r.Ry),
        ("rmd160", lambda r: r.hash160_int),
        ("address_payload", lambda r: r.addr_payload_int),
        ("address_base58_lex", lambda r: r.address),  # lexicographic string order
        ("sha256_pubkey", lambda r: r.sha256_pubkey_int),
        ("sha256_vh", lambda r: r.sha256_vh_int),  # SHA256(0x00||rmd160)
        ("sha256_chk", lambda r: r.sha256_chk_int),  # SHA256(sha256_vh)
        ("checksum4", lambda r: r.checksum4_int),
    ]

    ordered: dict[str, list[dict]] = {}
    for name, getter in series_spec:
        # address_base58_lex needs special: sort by string
        if name == "address_base58_lex":
            items = [(r.address, r.n, r.d) for r in rows]
            items.sort(key=lambda t: t[0])
            ordered[name] = [
                {
                    "linear_rank": i,
                    "puzzle_n": n,
                    "value": addr,
                    "value_repr": addr,
                    "d": d,
                }
                for i, (addr, n, d) in enumerate(items, start=1)
            ]
        else:
            ordered[name] = rank_series(rows, name, getter)

    # coverage summary
    coverage = {name: len(v) for name, v in ordered.items()}

    json_path = OUT / "linear_order_puzzles_1_160.json"
    json_path.write_text(
        json.dumps(
            {
                "cohort": "puzzles 1..160",
                "coverage": coverage,
                "notes": {
                    "rmd160": "RIPEMD160(SHA256(compressed_pubkey)) as big-endian int; all 160 from catalog",
                    "address_payload": "int(0x00||rmd160||checksum4); numeric address body",
                    "address_base58_lex": "Base58 string lexicographic order",
                    "sha256_pubkey": "SHA256(compressed pubkey); only when pubkey known",
                    "sha256_vh": "SHA256(0x00||rmd160); all 160",
                    "sha256_chk": "SHA256(sha256_vh); all 160",
                    "checksum4": "first 4 bytes of sha256_chk as uint32; all 160",
                    "limbs": "Px/Py/Pmy/r/s/z/Ry only when pubkey and/or rsz available",
                    "neg_y": "(-Py) mod p; equals Pmy for affine points on the curve",
                    "y2_mod_p": "Py^2 mod p (erases Cp carry — reference only)",
                    "x3_plus_7_mod_p": "Px^3 + 7 mod p (erases Cp carry — reference only)",
                    "y2_full": "Py^2 unreduced",
                    "x3plus7_full": "Px^3 + 7 unreduced",
                    "p_carry": "C=(X-Y)/p so X-Y-Cp=0",
                    "rmd160_cubed_plus_7_mod_p": "hash160^3 + 7 mod p (formal analogue; not a curve law)",
                    "address_payload_sq_mod_p": "(00||rmd160||checksum4)^2 mod p (formal analogue)",
                    "rmd160_sq_mod_p": "hash160^2 mod p (flipped formal analogue)",
                    "address_payload_cubed_plus_7_mod_p": "address_payload^3 + 7 mod p (flipped formal analogue)",
                },
                "series": ordered,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # Full text + sequences
    txt_path = OUT / "LINEAR_ORDER_PUZZLES_1_160.txt"
    with txt_path.open("w", encoding="utf-8") as fh:
        fh.write("Puzzles 1..160 linear order (ascending value)\n")
        fh.write("columns: linear_rank  puzzle_n  value\n\n")
        fh.write("coverage:\n")
        for k, v in coverage.items():
            fh.write(f"  {k}: {v}\n")
        fh.write("\n")

        for name, _ in series_spec:
            ents = ordered[name]
            fh.write("=" * 72 + "\n")
            fh.write(f"{name}  (n={len(ents)})\n")
            fh.write("=" * 72 + "\n")
            for e in ents:
                v = e["value"]
                if isinstance(v, float):
                    vs = f"{v:.15g}"
                else:
                    vs = str(v)
                fh.write(f"{e['linear_rank']:3d}  n={e['puzzle_n']:3d}  {vs}\n")
            seq = ",".join(str(e["puzzle_n"]) for e in ents)
            fh.write(f"\npuzzle_n sequence (small->large {name}):\n{seq}\n\n")

    # Console: sequences only
    print("coverage:", coverage)
    print()
    for name, _ in series_spec:
        seq = ",".join(str(e["puzzle_n"]) for e in ordered[name])
        print(f"{name} ({coverage[name]}):")
        print(seq)
        print()
    print(f"wrote {json_path}")
    print(f"wrote {txt_path}")


if __name__ == "__main__":
    main()
