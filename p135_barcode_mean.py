#!/usr/bin/env python3
"""P135 barcode sum/mean analysis — puzzle71-style convergence center."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))
sys.path.insert(0, str(ROOT / "puzzle135_bucket_bsgs"))

from ecdlp_full_pipeline import y_roots  # noqa: E402
from hashkeys_rsz import PUZZLE_RSZ  # noqa: E402
from p135_common import G, scalar_mult  # noqa: E402

LO, HI = 2**134, 2**135
N_BAND = HI - LO

px135 = int(PUZZLE_RSZ[135].pub_compressed[2:], 16)
yp, yn = y_roots(px135)
py135 = yp if yp % 2 == 0 else yn

MAIN = {
    "barcode135_px": 9210836494447108270027136741376870869791784014198948301625976867708124077590,
    "barcode2_135": 339313561024031265435986695011695739557734064934,
    "barcode3_135": 1457340647687514555129058036566359538903001312758743383575,
    "barcode4_135": 15509729875763924304053419655647994379903175655107184284998698212653288468986,
}

CHUNKS41 = [
    36494447108270027136741376870869791784014,
    27002713674137687086979178401419894830162,
    27136741376870869791784014198948301625976,
    36741376870869791784014198948301625976867,
    41376870869791784014198948301625976867708,
    37687086979178401419894830162597686770812,
    33931356102403126543598669501169573955773,
    39313561024031265435986695011695739557734,
    31356102403126543598669501169573955773406,
    35610240312654359866950116957395577340649,
    34064768751455512905803656635953890300131,
    40647687514555129058036566359538903001312,
    29875763924304053419655647994379903175655,
    39243040534196556479943799031756551071842,
    24304053419655647994379903175655107184284,
    43040534196556479943799031756551071842849,
    30405341965564799437990317565510718428499,
    40534196556479943799031756551071842849986,
    34196556479943799031756551071842849986982,
    41965564799437990317565510718428499869821,
    43799031756551071842849986982126532884689,
    37990317565510718428499869821265328846898,
]

B2134 = {
    "barcode_2^134_px": 92137904221004991822640747341747548945462418389173665085162488592935043663263,
    "barcode2_2^134": 311245721786421917988725031832311708252044887614,
    "barcode3_2^134": 1336790196092596834619168108456337743020426117426948522536,
    "product_2^134": 21778071482940061661655974875633165533184,
}

PROD_2_134 = 21778071482940061661655974875633165533184


def band_pos(d: int) -> float:
    return 100.0 * (d - LO) / N_BAND


def dec_lead_match(a: int, b: int) -> int:
    sa, sb = str(a), str(b)
    k = 0
    for x, y in zip(sa, sb):
        if x == y:
            k += 1
        else:
            break
    return k


def verify(label: str, d: int) -> str:
    if d <= 0:
        return f"{label}: invalid d<=0"
    in_band = LO <= d < HI
    bits = d.bit_length()
    if not in_band:
        return f"{label}: bits={bits} in_band=False d...{str(d)[-10:]}"
    pt = scalar_mult(d, G)
    if pt and pt[0] == px135 and pt[1] == py135:
        return f"{label}: *** SOLVED d={d} ***"
    dec_lead = dec_lead_match(px135, pt[0]) if pt else 0
    return (
        f"{label}: bits={bits} pos={band_pos(d):.3f}% "
        f"dec_px_lead={dec_lead} d...{str(d)[-12:]}"
    )


def stats(vals: list[int], name: str) -> tuple[int, int]:
    s = sum(vals)
    n = len(vals)
    mean = s // n
    print(f"\n=== {name} (n={n}) ===")
    print(f"  sum  : {len(str(s))} dec digits, {s.bit_length()} bits")
    print(f"  mean : {len(str(mean))} dec digits, {mean.bit_length()} bits")
    print(f"  pos  : {band_pos(mean):.4f}% of band")
    print(f"  {verify(name + '_mean', mean)}")
    return s, mean


def main() -> int:
    print("P135 BARCODE SUM / MEAN ANALYSIS")
    print(f"band [{LO}, {HI})  Px135 dec starts: {str(px135)[:12]}...")
    print()

    print("Main barcodes:")
    for k, v in MAIN.items():
        ib = LO <= v < HI
        print(f"  {k:16s} {v.bit_length():3d} bits  in_band={ib}")

    in_band_chunks = [c for c in CHUNKS41 if LO <= c < HI]
    print(f"\n41-digit chunks: {len(CHUNKS41)} total, {len(in_band_chunks)} in band")

    _, m41 = stats(CHUNKS41, "chunks41")
    _, m4 = stats(list(MAIN.values()), "main4")
    s41, _ = stats(CHUNKS41, "chunks41_sum_only")
    stats(list(MAIN.values()) + CHUNKS41, "main4+chunks41")
    _, m_aux = stats(
        [MAIN["barcode2_135"], MAIN["barcode3_135"], MAIN["barcode4_135"]], "aux3"
    )
    _, m_b2134 = stats(list(B2134.values()), "2^134_barcodes")

    print("\n=== MEAN COMBINATIONS ===")
    combos = [
        ("mean41 + product_2^134", m41 + PROD_2_134),
        ("mean41 - product_2^134", m41 - PROD_2_134),
        ("mean41 + mean_aux", m41 + m_aux),
        ("mean41 + mean_2^134_barcodes", m41 + m_b2134),
        ("(mean41 + mean_aux) // 2", (m41 + m_aux) // 2),
        ("LO + (mean41 % band)", LO + (m41 % N_BAND)),
        ("mean41 ^ product_2^134", m41 ^ PROD_2_134),
        ("sum41 // 22 + LO", LO + (s41 // len(CHUNKS41)) % N_BAND),
    ]
    for label, d in combos:
        print(f"  {verify(label, d)}")

    print("\n=== DECIMAL SIMILARITY (mean41 vs Px135) ===")
    print(f"  mean41 leading match to Px135: {dec_lead_match(px135, m41)} digits")
    print(f"  mean41 / Px135 = {m41 / px135:.12f}")
    print(f"  mean41 decimal: ...{str(m41)[:30]}...")
    print(f"  Px135  decimal: ...{str(px135)[:30]}...")

    print("\n=== PUZZLE71-STYLE: mean of top in-band cluster ===")
    # sort chunks by decimal overlap with Px135
    ranked = sorted(
        in_band_chunks,
        key=lambda c: dec_lead_match(px135, c),
        reverse=True,
    )
    top3 = ranked[:3]
    center = sum(top3) // len(top3)
    print(f"  top3 by Px dec overlap: {[str(x)[:12] for x in top3]}")
    print(f"  {verify('top3_cluster_mean', center)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
