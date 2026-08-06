#!/usr/bin/env python3
"""Compare a carry remainder (N*s mod r) against P160 bridge carry family."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ECDLP"))

from ecdlp_full_pipeline import N, compute_order_in_the_court, p  # noqa: E402

P160_ROW1 = {
    "rx": [
        2058256938737534441052364174182103859798018828298390488211196700026657501931,
        73166243711482150095739218900420001340047970263222419524399021938933427175712,
        40567588587096510886779401934085802653423995574119754026847365368948749994020,
    ],
    "ry": 93506999776394773977012568374000894735649274226096876119078636851803903807856,
    "Px": [
        99685974423659554164545805763816838248496097325140083731055710648889920816643,
        101616124637840542991531253248586524020213215258338643076214814468447630501491,
        30282079413132293691064911004972453437830656747802401271644642898480118025192,
    ],
    "Py": 88132823371574229813684435207239348220522140366126834573803505878170136640646,
    "bx": 45007068078951775493665366593068225830383104709624889150671119680370932167439,
    "byN": 25521455940944530174129280783626801324832048577090320769791998327429762137874,
    "b3y": 25679081129138390705925832301664113077781168814058443227772887373585962647910,
    "rem_bx2": 43720250250513757717226302143127507522607577809063170077781439267918635988149,
    "rem_bx3": 14239552606443953505304430449267592133211590458257850537298680824115920299660,
    "GAP": 19109611754471202442933391846413867149547903901773638386705602529405636680319,
    "defect_lo": 730750819097871845667502073210562376218639448814,
    "defect_hi": 1461501637763323304769344489568703886046605720301,
}

P160_RSZ = {
    "r_sig": int("2cb230880dd2dcb03c8dbf0674c372a5b65b4583c30b45ad9eccd7c0232c425f", 16),
    "s_sig": int("aa9b5f47c69338130fc9e949ef9965379d5f99652acaa660142f6d9a290d1154", 16),
}


def lo_distance(a: int, b: int, lo: int) -> int:
    d = (a - b) % lo
    return min(d, lo - d)


def build_carry_family(lo: int) -> dict[str, int]:
    d = P160_ROW1
    delta = p - N
    qx = [(d["Px"][i] * delta) % N for i in range(3)]
    qy = (d["Py"] * delta) % N
    lambda_ns = [(qx[i] * pow(d["rx"][i], -1, N)) % N for i in range(3)]
    lam_y_n = (d["Py"] * pow(d["ry"], -1, N)) % N
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=d["rx"],
        qy=d["ry"],
        qx_scaled=qx,
        qy_scaled=qy,
        lambda_ns=lambda_ns,
        lam_y_n=lam_y_n,
    )
    return {
        "bx_row1": d["bx"],
        "byN": d["byN"],
        "b3y": d["b3y"],
        "rem_bx_row2": d["rem_bx2"],
        "rem_bx_row3": d["rem_bx3"],
        "GAP": d["GAP"],
        "shelf2": oitc.shelf2,
        "shelf3": oitc.shelf3,
        "shelf_y": oitc.shelf_y,
        "defect_lo": d["defect_lo"],
        "defect_hi": d["defect_hi"],
        "d_cube_lift2": oitc.d_cube_lift2,
        "d_cube_lift3": oitc.d_cube_lift3,
    }


def report(rem: int, lo: int, delta: int, label: str) -> None:
    family = build_carry_family(lo)
    base = rem % lo
    print(f"\n=== {label} ===")
    print(f"rem bitlen={rem.bit_length()}")
    print(f"rem mod LO     = {base}")
    print(f"rem mod delta  = {rem % delta}")
    print(f"rem // delta   = {rem // delta}")
    print(f"delta gap      = {(delta - (rem % delta)) % delta}")

    ranked = sorted(
        ((lo_distance(v, rem, lo), name, v % lo) for name, v in family.items()),
        key=lambda t: t[0],
    )
    print("\nClosest carry residues mod LO:")
    for dist, name, residue in ranked[:8]:
        mark = " EXACT" if dist == 0 else ""
        print(f"  {name:14} dist={dist}{mark}")
        if dist == 0:
            print(f"    -> exact match: {name}")

    print("\nN*s mod r presets (mod LO distance to rem):")
    presets: list[tuple[str, int, int]] = []
    for s_name, s in [("ry", P160_ROW1["ry"]), ("s_ecdsa", P160_RSZ["s_sig"])]:
        for i, r in enumerate(P160_ROW1["rx"], 1):
            presets.append((f"N*{s_name} mod rx{i}", N * s, r))
        presets.append((f"N*{s_name} mod r_sig", N * s, P160_RSZ["r_sig"]))
    preset_rank = []
    for name, ns, r in presets:
        candidate = ns % r
        preset_rank.append((lo_distance(candidate, rem, lo), name, candidate % lo))
    for dist, name, residue in sorted(preset_rank)[:5]:
        print(f"  {name:22} dist={dist}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rem", type=int, help="remainder integer")
    parser.add_argument("--s", type=int, help="s multiplier (with --r computes rem = N*s mod r)")
    parser.add_argument("--r", type=int, help="r divisor")
    parser.add_argument("--bits", type=int, default=160, help="puzzle bits for LO=2^(bits-1)")
    args = parser.parse_args()

    lo = 1 << (args.bits - 1)
    delta = p - N

    if args.s is not None and args.r is not None:
        rem = (N * args.s) % args.r
        q = (N * args.s) // args.r
        print(f"Computed: N*s = q*r + rem")
        print(f"  q bitlen={q.bit_length()}")
        print(f"  rem={rem}")
        print(f"  f=rem/r={rem / args.r}")
        report(rem, lo, delta, "computed remainder")
        return

    if args.rem is None:
        # user handoff values from session
        args.rem = 22200967118453308410035035011649497046083380657293281447464993331821717914202

    report(args.rem, lo, delta, "supplied remainder")


if __name__ == "__main__":
    main()
