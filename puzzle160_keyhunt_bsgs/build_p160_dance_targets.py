#!/usr/bin/env python3
"""Build multi-target uncompressed pubkeys around P160 for keyhunt BSGS dance.

Every target T has a known recovery: if keyhunt returns k with k*G == T, then
d = recover(k) and d*G == P160.

Only include targets whose discrete log lies in the Puzzle-160 band
[2^159, 2^160) whenever the true d does (so -b 160 / dance can hit them).
"""

from __future__ import annotations

import json
from pathlib import Path

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = SECP256k1.generator
CURVE = SECP256k1.curve

# Puzzle 160
PX = 0xE0A8B039282FAF6FE0FD769CFBC4B6B4CF8758BA68220EAC420E32B91DDFA673
PY = 0xC2D9690945DD98F6E0E45D4A1F760C9E85ED5AE5FFEEDA74E121EE0D836A7C86
P160 = Point(CURVE, PX, PY, N)

LO = 1 << 159
HI = 1 << 160  # exclusive end used by keyhunt -b 160
BAND_MID = LO + (HI - LO) // 2  # 3 << 158
# reflection center for d' = 2*BAND_MID - d = 3*2^159 - d
REFLECT_C = 3 * LO  # 3 << 159

OUT_DIR = Path(__file__).resolve().parent
PUB_OUT = OUT_DIR / "P160_dance_multitarget.pub"
MAP_OUT = OUT_DIR / "P160_dance_multitarget_recover.json"
WORKDIR_PUB = Path(r"C:\Users\mitch\source\repos\keyhunt\P160_dance_multitarget.pub")

# Barcode / complement centers (d-band hypotheses)
CENTERS: dict[str, int] = {
    "py_w15": 803505878170136640646881328233715742298136844352,
    "px_w0": 1016161246378405429915312532485865240202132152583,
    "y2_w21": 1279319893184270309653638302331043709986753761686,
    "rmd_wrap2": 999836400474710041910519435328613735285013260936,
    # complement bat midpoints (start of each narrow window ≈ seed)
    "comp_clean_0": 0xE8D8EB910DC0725D6336EF2F469A656A194260F4,
    "comp_clean_1": 0xF82271433A9E4D7ED743E4A5AA52F16725B9F8CB,
    "comp_clean_2": 0x9F13E7956AD917D51CB73E3A45B36906023871EA,
    "comp_clean_3": 0xA79CC60BF686D5FA7343E4E285C045FF6C15D55B,
    "comp_clean_4": 0x8CEADCD0AAD31F0548F191E9C3835EAD9B72EA72,
    "comp_clean_5": 0x84872DC45CBAE18988CA2D1839D892F4620CFE0E,
    "comp_clean_6": 0xB8B9F542A914E924756CC8CA757C8EFD06879D04,
    "comp_clean_7": 0x90C63FE8D01AAA47BC2D850A5EA73854EB5B5043,
    "comp_clean_8": 0xE16CA6879D9DD79BCFB5FE42D18D029DA1E12303,
    "comp_clean_9": 0xC79E38F2B64CEE0CB8C3D4FEE67669A6822C3EE2,
    "comp_clean_10": 0xAAD1899B113449B00E9E0AF154588F1667AF55CD,
    "comp_clean_11": 0xC553EE2403F18EF6913D1FFCD9C995880C08B45B,
    "comp_rem_0": 0xFB0FFBFC84B30BC0FDA44ADE1B5D983B91597103,
    "comp_rem_1": 0x87455393126687AAECD8D14994EB82CE58283489,
    "comp_rem_3": 0xD3224F3383D29E2DD2483D3210BFC065B4C9D8E5,
    "comp_rem_4": 0xAE7755C291D82B50DB71813BC4224CF23F2A9383,
    "comp_rem_5": 0xCD2B6FD3A394CB5240B1742A4DC8FDC20D4887C3,
    "comp_rem_6": 0xEB6B615357E63C2BACBC36E2E1497DF01D51BDF0,
    "comp_rem_7": 0xA8245AE3380C1E4BBD5962F594DA5992276F6661,
}


def pub_hex(pt: Point) -> str:
    return f"04{pt.x():064x}{pt.y():064x}".upper()


def add_G(pt: Point, k: int) -> Point:
    """pt + k*G (k may be negative)."""
    k %= N
    return pt + (k * G)


def main() -> None:
    rows: list[dict] = []
    pubs: list[str] = []
    seen: set[str] = set()

    def add(name: str, pt: Point, recover: str, formula: str) -> None:
        h = pub_hex(pt)
        if h in seen:
            return
        seen.add(h)
        pubs.append(h)
        rows.append({"name": name, "pub": h, "recover": recover, "formula": formula})

    # 1) base
    add("P160", P160, "d = k", "target = d*G")

    # 2) band reflection: d' = REFLECT_C - d  (same band when d is)
    #    Q = d'*G = REFLECT_C*G - P
    Q_ref = (REFLECT_C * G) + (-P160)
    add(
        "band_reflect",
        Q_ref,
        f"d = {REFLECT_C} - k",
        "d' = 3*2^159 - d; target = d'*G",
    )

    # 3) center-offset targets: T = P - (c - LO)*G = (d - c + LO)*G
    #    when d≈c, DL(T)≈LO (bottom of dance band)
    for name, c in CENTERS.items():
        if not (LO <= c < HI):
            continue
        delta = (c - LO) % N
        T = add_G(P160, -delta)
        add(
            f"center_{name}",
            T,
            f"d = k + ({c} - {LO})",
            f"T=(d-c+2^159)G; center={c}",
        )
        # also reflection of that centered key back into band via same reflect map on target
        # T_ref = REFLECT_C*G - T  => DL = REFLECT_C - (d-c+LO) => d = REFLECT_C - k - LO + c
        T_ref = (REFLECT_C * G) + (-T)
        add(
            f"center_{name}_reflect",
            T_ref,
            f"d = {REFLECT_C} - k - {LO} + {c}",
            "reflect of center-offset target",
        )

    # 4) small power-of-two shifts (still in-band except near edges)
    for i in list(range(0, 48)) + [64, 80, 96, 112, 128, 144]:
        off = 1 << i
        add(
            f"P_plus_2^{i}",
            add_G(P160, off),
            f"d = k - 2^{i}",
            "T=(d+2^i)G",
        )
        add(
            f"P_minus_2^{i}",
            add_G(P160, -off),
            f"d = k + 2^{i}",
            "T=(d-2^i)G",
        )

    # 5) known mod-N factor images that STILL land in-band only for special d —
    #    skip random f*P (DL leaves the band). Keep inv(2) half-scalar as optional
    #    159-bit companion (document only; not added to -b 160 file).
    half_note = {
        "note": (
            "[inv(2)]P has DL = d*inv(2) mod N (~159-bit if d even). "
            "Not included in -b 160 dance file; run a separate -b 159 job if desired."
        ),
        "inv2_mod_N": (N + 1) // 2,
    }

    PUB_OUT.write_text("\n".join(pubs) + "\n", encoding="utf-8")
    payload = {
        "n_targets": len(pubs),
        "band": [LO, HI],
        "reflect_c": REFLECT_C,
        "half_scalar_note": half_note,
        "targets": rows,
    }
    MAP_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # also drop into keyhunt bloom CWD if present
    try:
        WORKDIR_PUB.parent.mkdir(parents=True, exist_ok=True)
        WORKDIR_PUB.write_text("\n".join(pubs) + "\n", encoding="utf-8")
        workdir_written = str(WORKDIR_PUB)
    except OSError:
        workdir_written = None

    print(f"wrote {PUB_OUT}  ({len(pubs)} pubs)")
    print(f"wrote {MAP_OUT}")
    if workdir_written:
        print(f"wrote {workdir_written}")


if __name__ == "__main__":
    main()
