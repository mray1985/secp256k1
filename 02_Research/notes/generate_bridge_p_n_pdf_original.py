#!/usr/bin/env python3
"""Generate ORIGINAL PDF (first version, 11 sections). Do not overwrite expanded."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N
Lambda = 0xD773B315F9871CF943F6F886AD1243BBE9D2130DB214DD8EF0504CFEDAE1049D
Px3 = 9210836494447108270027136741376870869791784014198948301625976867708124077590
rx3 = 26000218878731561428273279366182192513989009817816850365013828370091835863739
LO, HI = 2**134, 2**135
MIRROR_LO = N - (HI + 1)

ratio_p = (Px3 * pow(rx3, -1, p)) % p
ratio_n = (Px3 * pow(rx3, -1, N)) % N
GAP = (ratio_n - Lambda) % N
Lambda_N = ratio_n
a3 = (Lambda * rx3 - Px3) // p

Qx3 = (Px3 * delta) % N
qx3 = (rx3 * delta) % N
Gx3 = 85340279321737800624759429340272274763154997815782306132637707972559913914315
gx3 = (Gx3 * delta) % N

OUT = Path(__file__).resolve().parent / "BRIDGE_p_to_N_Gap_Analysis.pdf"


class BridgePDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def heading(pdf: FPDF, text: str, level: int = 1) -> None:
    sizes = {1: 16, 2: 13, 3: 11}
    pdf.set_font("Helvetica", "B", sizes.get(level, 11))
    pdf.multi_cell(0, 8, text)
    pdf.ln(2)


def body(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)


def mono(pdf: FPDF, text: str) -> None:
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(0, 4, text)
    pdf.ln(1)


def table_row(pdf: FPDF, col1: str, col2: str, col3: str = "") -> None:
    pdf.set_font("Helvetica", "", 9)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    if col3:
        pdf.cell(w * 0.28, 6, col1[:42], border=1)
        pdf.cell(w * 0.36, 6, col2[:55], border=1)
        pdf.cell(w * 0.36, 6, col3[:55], border=1)
    else:
        pdf.cell(w * 0.35, 6, col1[:50], border=1)
        pdf.cell(w * 0.65, 6, col2[:95], border=1)
    pdf.ln()


def build() -> Path:
    pdf = BridgePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    heading(pdf, "Bridge Gap: Complexity_Simplified_p to Complexity_Simplified_N")
    body(
        pdf,
        f"Puzzle 135 / secp256k1 research note. Generated {date.today().isoformat()}.\n"
        "This document records what the p-side file completes, what the N-side file assumes, "
        "and the missing closure (Lambda_N, range-variable delta, carry, cubic aggregate).",
    )

    heading(pdf, "1. Executive summary", 2)
    body(
        pdf,
        "Complexity_Simplified_p closes the bridge on the field side: Px_i / rx_i = Lambda (mod p). "
        "Complexity_Simplified_N copies the same numeric Lambda but the live N-side ratio is "
        "Lambda_N = Lambda + GAP, not Lambda. Until N-file uses Lambda_N and range-variable defect(d), "
        "the two files do not meet.",
    )

    heading(pdf, "2. Side-by-side completion map", 2)
    table_row(pdf, "Layer", "p-file", "N-file")
    rows = [
        ("Root", "n^3 = N (mod p)", "p^3 = p (mod N)"),
        ("Normalize", "G/P/r x n_i^-1 -> Latin square", "G/P/r x p_i^-1 (no collapse)"),
        ("Collapse", "CP1, CR1 constants", "MISSING CQ1, Cq1"),
        ("Point bridge", "Px/rx = Lambda (mod p) OK", "Assumes Lambda; Px/rx mod N FAILS"),
        ("Scaled bridge", "(n/a)", "Qx = Px*d; Qx = Lambda_N*qx OK"),
        ("Cubic aggregate", "IP/IR = Lambda^3 (mod p) OK", "IQ/Iq = Lambda^3 (mod N) FAILS"),
        ("Carry", "a3 = (Lambda*rx3-Px3)//p", "MISSING b3 on N"),
        ("Range delta", "fixed p-N", "only global Lambda*(p-N)"),
    ]
    for r in rows:
        table_row(pdf, *r)
    pdf.ln(4)

    heading(pdf, "3. Core constants", 2)
    mono(
        pdf,
        f"delta = p - N = {delta}\n\n"
        f"Lambda (p-side bridge) = {Lambda}\n\n"
        f"Lambda_N = Px3/rx3 mod N = {Lambda_N}\n\n"
        f"GAP = Lambda_N - Lambda mod N = {GAP}\n\n"
        f"Px3/rx3 mod p == Lambda ? {ratio_p == Lambda}\n"
        f"Px3/rx3 mod N == Lambda ? {ratio_n == Lambda}\n"
        f"Qx3 == Lambda*qx3 mod N ? {Qx3 == (Lambda * qx3) % N}\n"
        f"Qx3 == Lambda_N*qx3 mod N ? {Qx3 == (Lambda_N * qx3) % N}",
    )

    heading(pdf, "4. N-side BRIDGE block (to add)", 2)
    mono(
        pdf,
        "BRIDGE_N:\n"
        "  Qx_i / qx_i = CQ1/Cq1 = Lambda_N   (mod N)\n"
        "  Qx_i = Lambda_N * qx_i             (mod N)\n\n"
        "Where:\n"
        "  Qx = Px * delta,   qx = rx * delta,   delta = p - N\n"
        "  Lambda_N = Lambda + GAP\n"
        "  GAP = Px3*rx3^-1 - Lambda            (mod N)\n\n"
        "NOT Lambda alone. The p constant is the shadow; Lambda_N is the live N bridge.",
    )

    heading(pdf, "5. Three corner deltas (Puzzle 135 lane)", 2)
    body(
        pdf,
        "Dual bands: d in [2^134, 2^135-1]; mirror [N-(2^135+1), N-2^134]. Mirror ceiling is +2 below "
        "naive N-(2^135-1). No delta at N+2^134 (outside the lane; that anchor is not used).",
    )
    mono(
        pdf,
        f"delta_B = p - (N - 2^135)       = {p - (N - HI)}\n"
        f"delta_C = p - (N - 2^134)       = {p - (N - LO)}\n"
        f"delta_D = p - (N - (2^135+1))   = {p - (N - (HI + 1))}\n\n"
        f"G_low  = (N - 2^134) - 2^134 = N - 2^135 = {(N - LO) - LO}\n"
        f"G_high = mirror_lo - TOP = N - 2^136 = {MIRROR_LO - (HI - 1)}\n\n"
        "Interior (if d known):\n"
        "  defect(d) = delta + d = p - (N - d)\n"
        "  new_N(d) = N - d\n\n"
        "Relative offset (gap delta minus defect):\n"
        "  at floor d=2^134: offset = 2^134\n"
        "  at ceiling via G_high: offset = 2^135 + 1\n"
        "  delta_D - defect(TOP) = 2 (mirror +2)",
    )

    heading(pdf, "6. Heaven carry (p) and N gap", 2)
    mono(
        pdf,
        f"p-side carry:\n"
        f"  a3 = (Lambda*rx3 - Px3) // p = {a3}\n"
        f"  Lambda*rx3 - Px3 = a3 * p exactly (mod p residue 0)\n\n"
        "N-side carry (not yet in N-file):\n"
        "  b3 = (Lambda_N*qx3 - Qx3) // N   [to be computed at puzzle height]\n\n"
        "The integer lift across p is what lets the p-bridge close; N needs the parallel lift.",
    )

    heading(pdf, "7. Cubic aggregate failure on N", 2)
    Px = [
        51866120889717641461810659005716431188799022756838843706514074509901265629059,
        54715131853151445691733189261594605794679177894602772031317532630299444965014,
        Px3,
    ]
    rx = [
        114930704126154877082883546730544079307369404418439078397954295509919169851219,
        90653255469745952335985143920649543885181555095025199315947044135806663628368,
        rx3,
    ]
    Qx = [(x * delta) % N for x in Px]
    qx = [(x * delta) % N for x in rx]
    IP = Px[0] * Px[1] * Px[2] % p
    IR = rx[0] * rx[1] * rx[2] % p
    IQ = Qx[0] * Qx[1] * Qx[2] % N
    Iq = qx[0] * qx[1] * qx[2] % N
    mono(
        pdf,
        f"IP/IR mod p == Lambda^3 mod p ? {(IP * pow(IR, -1, p)) % p == pow(Lambda, 3, p)}\n"
        f"IQ/Iq mod N == Lambda^3 mod N ? {(IQ * pow(Iq, -1, N)) % N == pow(Lambda, 3, N)}\n"
        f"IQ/Iq mod N == Lambda_N^3 mod N ? {(IQ * pow(Iq, -1, N)) % N == pow(Lambda_N, 3, N)}\n\n"
        "N-file lists Lambda^3*(p-N) but never closes IQ/Iq. Cubic on N needs a range-aware "
        "replacement, not a direct copy of p-side Lambda^3.",
    )

    heading(pdf, "8. Orphans in N-file (unconnected)", 2)
    Cq = 3820628127091453859030266576898546114566560342084415068589713593856641559477
    p3 = 92991331307360483616382958948483650923668592306718313881520244192640870034108
    C3 = (Px3 * pow(p3, -1, N)) % N
    mono(
        pdf,
        f"Cq = RQ*Rq^-1 mod N = {Cq}\n"
        f"  equals Lambda? {Cq == Lambda}\n"
        f"  equals GAP? {Cq == GAP}\n"
        f"  equals Lambda_N? {Cq == Lambda_N}\n\n"
        f"p3 defect root branch: C3 = Px3/p3 mod N = {C3}\n\n"
        "These aggregates exist in N-file but are not wired to Lambda_N or to d in [2^134,2^135).",
    )

    heading(pdf, "9. Scalar reduction (tool note)", 2)
    body(
        pdf,
        "Separate from the bridge files but relevant to multiplier checks: correct rule is (k mod N)*G. "
        "Example k = 16*(N+1) = 16N+16 has k mod N = 16, so k*G = 16G. Tools that treat k>=N as "
        "infinity in widening blocks (2N,4N,8N,16N) are wrong; only multiples of N exactly map to O.",
    )

    heading(pdf, "10. Closure sentence", 2)
    mono(
        pdf,
        "p-side:  Px = Lambda * rx           (mod p)     Lambda fixed\n"
        "N-side:  Qx = Lambda_N * qx         (mod N)     Lambda_N = Lambda + GAP\n"
        "Height:  defect(d) = delta + d,     new_N(d) = N - d\n"
        "Scalar:  only (k mod N) matters;    16(N+1) -> residue 16",
    )

    heading(pdf, "11. Priority actions", 2)
    actions = [
        "1. Add BRIDGE_N section to Complexity_Simplified_N with Lambda_N and GAP.",
        "2. Add four corner deltas and defect(d) = delta + d for Puzzle 135 lane.",
        "3. Derive N-side carry b3 parallel to p-side a3.",
        "4. Fix or replace cubic aggregate on N (IQ/Iq); do not assume Lambda^3.",
        "5. Wire p3 branch (C3, D3) through Lambda_N, not global Lambda.",
        "6. Regenerate search anchors from Lambda_N + relative offset, not fixed p-file Lambda.",
    ]
    for a in actions:
        body(pdf, a)

    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
