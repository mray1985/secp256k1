#!/usr/bin/env python3
"""Generate PDF: missing bridge between Complexity_Simplified_p and _N."""

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
PUBKEY_Y = 0x667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330


def find_y_from_x(x: int) -> tuple[int, int]:
    """Return both y roots for y^2 = x^3 + 7 on secp256k1."""
    y_sq = (pow(x, 3, p) + 7) % p
    if pow(y_sq, (p - 1) // 2, p) != 1:
        raise ValueError(f"x={x} not on curve")
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    c = pow(z, q, p)
    x_r = pow(y_sq, (q + 1) // 2, p)
    t = pow(y_sq, q, p)
    m = s
    while t != 1:
        temp = t
        i = 0
        while temp != 1 and i < m:
            temp = pow(temp, 2, p)
            i += 1
        if i == m:
            raise ValueError("Tonelli-Shanks failed")
        b = pow(c, 1 << (m - i - 1), p)
        x_r = (x_r * b) % p
        t = (t * b * b) % p
        c = (b * b) % p
        m = i
    return x_r, p - x_r


Py_pos, Py_neg = find_y_from_x(Px3)
ry_pos, ry_neg = find_y_from_x(rx3)

ratio_p = (Px3 * pow(rx3, -1, p)) % p
ratio_n = (Px3 * pow(rx3, -1, N)) % N
GAP = (ratio_n - Lambda) % N
Lambda_N = ratio_n
a3 = (Lambda * rx3 - Px3) // p

Qx3 = (Px3 * delta) % N
qx3 = (rx3 * delta) % N
Gx3 = 85340279321737800624759429340272274763154997815782306132637707972559913914315
gx3 = (Gx3 * delta) % N

ratio_power_p = ((pow(Px3, 3, p) + 7) * pow(pow(rx3, 3, p) + 7, -1, p)) % p
lam_x_cube_plus_7 = (pow(Lambda, 3, p) + 7) % p
naive_power_n = (pow(Lambda_N, 3, N) + 7) % N
ratio_power_n = ((pow(Qx3, 3, N) + 7) * pow(pow(qx3, 3, N) + 7, -1, N)) % N


def map_p_to_n(y: int) -> int:
    return (N * y // p) % N


def reflection_row(label: str, y: int) -> dict:
    neg_y = (-y) % p
    lam_y = map_p_to_n(y)
    lam_neg_y = map_p_to_n(neg_y)
    total = lam_y + lam_neg_y
    return {
        "label": label,
        "y": y,
        "neg_y": neg_y,
        "lam_y": lam_y,
        "lam_neg_y": lam_neg_y,
        "sum": total,
        "passes": total in (N - 1, N, N + 1),
    }


def branch_row(py_label: str, py: int, ry_label: str, ry: int) -> dict:
    lam_y = (py * pow(ry, -1, p)) % p
    lam_y_n = (py * pow(ry, -1, N)) % N
    b3 = (lam_y * ry - py) // p
    return {
        "py_label": py_label,
        "ry_label": ry_label,
        "py": py,
        "ry": ry,
        "same_parity": (py % 2) == (ry % 2),
        "lam_y": lam_y,
        "lam_y_n": lam_y_n,
        "power_ok_p": (lam_y * lam_y) % p == ratio_power_p,
        "b3_y": b3,
    }


REFLECTION_P = reflection_row("P (Px3)", Py_pos)
REFLECTION_R = reflection_row("r (rx3)", ry_pos)
BRANCH_GRID = [
    branch_row("Py+", Py_pos, "ry+", ry_pos),
    branch_row("Py+", Py_pos, "ry-", ry_neg),
    branch_row("Py-", Py_neg, "ry+", ry_pos),
    branch_row("Py-", Py_neg, "ry-", ry_neg),
]
DISTINCT_LAM_Y = {row["lam_y"] for row in BRANCH_GRID}
EXAMPLE = next(r for r in BRANCH_GRID if r["py"] == PUBKEY_Y and r["ry"] == ry_pos)
Lambda_y_example = EXAMPLE["lam_y"]
Lambda_y_N_example = EXAMPLE["lam_y_n"]
b3_y_example = EXAMPLE["b3_y"]
lam_y_sq_p = (Lambda_y_example * Lambda_y_example) % p
lam_y_sq_n = (Lambda_y_N_example * Lambda_y_N_example) % N
k_y_over_x = (Lambda_y_example * pow(Lambda, -1, p)) % p

OUT = Path(__file__).resolve().parent / "BRIDGE_p_to_N_Gap_Analysis_expanded.pdf"


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
        "Complexity_Simplified_p closes the x-bridge: Px_i / rx_i = Lambda (mod p) via three cube-root "
        "branches (x^3). y follows the same make-up but with only two square-root branches (y^2), "
        "coupled by reflection (lambda_y + lambda_-y = N). N-file must use Lambda_N = Lambda + GAP "
        "and range-variable defect(d), not a blind copy of p-side Lambda or Lambda^3.",
    )

    heading(pdf, "2. Side-by-side completion map", 2)
    table_row(pdf, "Layer", "p-file", "N-file")
    rows = [
        ("Root", "n^3 = N (mod p)", "p^3 = p (mod N)"),
        ("Normalize x", "n^3 roots -> 3-way Latin square", "p^3 roots -> no collapse"),
        ("Normalize y", "y^2 -> 2 branches (+/- only)", "reflection pair (not 3-way)"),
        ("Collapse x", "CP1, CR1 -> Lambda", "MISSING CQ1, Cq1"),
        ("Point bridge x", "Px/rx = Lambda (mod p) OK", "Qx = Lambda_N*qx OK (scaled)"),
        ("Point bridge y", "Py/ry = lambda_y (2-fold)", "lambda_y + lambda_-y = N"),
        ("Power law", "lam_y^2=(Px^3+7)/(rx^3+7) OK", "Ratio + naive forms FAIL mod N"),
        ("Cubic aggregate", "IP/IR = Lambda^3 (mod p) OK", "IQ/Iq = Lambda^3 (mod N) FAILS"),
        ("Carry", "a3 (x), b3_y (y) on p", "MISSING b3_x, b3_yN on N"),
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
        f"G_low  = (N - 2^134) - 2^134 = N - 2^135 = { (N - LO) - LO}\n"
        f"G_high = mirror_lo - TOP = N - 2^136 = {MIRROR_LO - (HI - 1)}\n\n"
        "Interior (if d known):\n"
        "  defect(d) = delta + d = p - (N - d)\n"
        "  new_N(d) = N - d\n\n"
        "Relative offset (gap delta minus defect):\n"
        "  at floor d=2^134: offset = 2^134\n"
        "  at ceiling via G_high: offset = 2^135 + 1\n"
        "  delta_D - defect(TOP) = 2 (mirror +2)",
    )

    heading(pdf, "6. Same make-up: x^3 (3 branches) vs y^2 (2 branches)", 2)
    body(
        pdf,
        "The bridge follows the same normalization pattern on x and y, but the algebraic degree "
        "fixes the branch count. x^3 gives three cube-root slots (n1, n2, n3) and the A/B/C Latin "
        "square. y^2 gives only two square-root branches (y and -y). There is no third y slot "
        "analogous to n3.",
    )
    mono(
        pdf,
        "x-side (cubic, 3 branches):\n"
        "  n^3 = N (mod p)  ->  n1, n2, n3\n"
        "  Gx_i * n_j^-1, Px_i * n_j^-1, rx_i * n_j^-1  ->  Latin square A/B/C\n"
        "  Px3 * n1^-1 = P_B,  rx3 * n1^-1 = r_B  (branch-3 slot pinned)\n"
        "  Px3/rx3 = Lambda  (one x-ratio, collapsed)\n\n"
        "y-side (quadratic, 2 branches only):\n"
        "  y^2 = x^3 + 7 (mod p)  ->  exactly (y, -y) per x\n"
        "  NO Py3 from n3 normalization  ->  only (Py+, Py-) and (ry+, ry-)\n"
        "  Complexity files define Px3 and rx3 only; y is not a collapsed constant like Lambda",
    )
    body(
        pdf,
        "External anchor (not from complexity file): published puzzle pubkey picks one Py branch "
        f"(0x667a05e9... even y). That does not create a third cube root; it only selects one "
        "member of the +/- pair.",
    )

    heading(pdf, "7. Reflection pairing (y bridge rule)", 2)
    body(
        pdf,
        "y branches are coupled, not independent. The reflection bridge maps one y branch to N "
        "and pairs it with its negation:",
    )
    mono(
        pdf,
        "p-side:  y + (-y) = p\n"
        "N-side:  lambda_y = floor(N * y / p) mod N\n"
        "         lambda_{-y} = floor(N * (-y) / p) mod N\n"
        "         lambda_y + lambda_{-y} = N (or N-1 / N+1 from floor)",
    )
    for row in (REFLECTION_P, REFLECTION_R):
        mono(
            pdf,
            f"{row['label']}:\n"
            f"  y+      = {row['y']}\n"
            f"  y-      = {row['neg_y']}\n"
            f"  lam_y   = {row['lam_y']}\n"
            f"  lam_-y  = {row['lam_neg_y']}\n"
            f"  sum     = {row['sum']}\n"
            f"  PASS    = {row['passes']}",
        )
    body(
        pdf,
        "Reflection fixes the partner branch: choose y, then -y is determined. This is the y-side "
        "analog of x-side collapse, but with 2 branches instead of 3.",
    )

    heading(pdf, "8. Lambda_x / Lambda_y and 2x2 branch table", 2)
    body(
        pdf,
        "lambda_x = Px3/rx3 = Lambda (unique, from cubic lane). lambda_y = Py/ry depends on which "
        "square-root branch is taken on each side. Four pairings collapse to two distinct lambda_y values.",
    )
    body(
        pdf,
        "Naive (WRONG):  lambda_x^3 + 7 = lambda_y^2 (mod p)\n"
        "Correct:        lambda_y^2 = (Px^3 + 7) / (rx^3 + 7) (mod p)",
    )
    table_row(pdf, "Pairing", "lambda_y (mod p)", "same parity?")
    for row in BRANCH_GRID:
        table_row(
            pdf,
            f"{row['py_label']} x {row['ry_label']}",
            str(row["lam_y"]),
            "yes" if row["same_parity"] else "no",
        )
    pdf.ln(2)
    mono(
        pdf,
        f"Distinct lambda_y values across 4 pairings: {len(DISTINCT_LAM_Y)} (not 4)\n"
        f"Opposite-parity pairings share one value; same-parity share the other.\n\n"
        f"Example (pubkey Py+ x ry+):\n"
        f"  lambda_y = {Lambda_y_example}\n"
        f"  lambda_y == Lambda ? {Lambda_y_example == Lambda}\n"
        f"  k = lambda_y/lambda_x mod p = {k_y_over_x}\n\n"
        f"POWER (mod p), any pairing:\n"
        f"  lambda_y^2 == (Px^3+7)/(rx^3+7) ? True for all 4 pairings\n"
        f"  lambda_x^3 + 7 == lambda_y^2     ? {lam_x_cube_plus_7 == lam_y_sq_p}\n\n"
        f"N-side (example pairing, mod N):\n"
        f"  Qx3 == Lambda_N * qx3 ? {Qx3 == (Lambda_N * qx3) % N}\n"
        f"  lambda_yN^2 == (Qx^3+7)/(qx^3+7) ? {lam_y_sq_n == ratio_power_n}\n"
        f"  lambda_xN^3 + 7 == lambda_yN^2     ? {naive_power_n == lam_y_sq_n}",
    )
    body(
        pdf,
        "IP/IR = Lambda^3 is an x/cubic artifact only. y needs its own ratio lambda_y per branch "
        "pairing plus reflection. Lambda^3 cube roots do not transfer to N.",
    )

    heading(pdf, "9. Heaven carry (p) and N gap", 2)
    mono(
        pdf,
        f"p-side x carry:\n"
        f"  a3 = (Lambda*rx3 - Px3) // p = {a3}\n\n"
        f"p-side y carry (per branch pairing, example Py+ x ry+):\n"
        f"  b3_y = (lambda_y*ry - Py) // p = {b3_y_example}\n"
        f"  Lambda*ry+ - Py+ divisible by p ? {(Lambda * ry_pos - Py_pos) % p == 0}\n"
        f"  lambda_y*ry+ - Py+ divisible by p ? {(Lambda_y_example * ry_pos - Py_pos) % p == 0}\n\n"
        "N-side carry (not yet in N-file):\n"
        "  b3_x = (Lambda_N*qx3 - Qx3) // N\n"
        "  b3_yN = (lambda_yN*q(ry) - q(y)) // N   [per chosen y branch]\n\n"
        "Integer lift across p closes x; y needs parallel lift per (+/-) pairing.",
    )

    heading(pdf, "10. Cubic aggregate failure on N", 2)
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
        "replacement, not a direct copy of p-side Lambda^3.\n\n"
        "Why Lambda^3 cube roots do not transfer:\n"
        "  - x cubic IP/IR = Lambda^3 uses only lambda_x\n"
        "  - y ratio lambda_y != lambda_x; power law is (Px^3+7)/(rx^3+7), not lambda_x^3+7\n"
        "  - mod N, even the ratio power law fails on scaled coords until defect(d) is applied",
    )

    heading(pdf, "11. Orphans in N-file (unconnected)", 2)
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

    heading(pdf, "12. Scalar reduction (tool note)", 2)
    body(
        pdf,
        "Separate from the bridge files but relevant to multiplier checks: correct rule is (k mod N)*G. "
        "Example k = 16*(N+1) = 16N+16 has k mod N = 16, so k*G = 16G. Tools that treat k>=N as "
        "infinity in widening blocks (2N,4N,8N,16N) are wrong; only multiples of N exactly map to O.",
    )

    heading(pdf, "13. Closure sentence", 2)
    mono(
        pdf,
        "x: 3 branches (x^3, n1/n2/n3) -> Lambda = Px/rx (mod p), Lambda_N (mod N)\n"
        "y: 2 branches (y^2) -> (Py+, Py-), (ry+, ry-); lambda_y + lambda_-y = N\n"
        "y power: lambda_y^2 = (Px^3+7)/(rx^3+7), NOT lambda_x^3+7\n"
        "Height: defect(d) = delta + d, new_N(d) = N - d\n"
        "Scalar: only (k mod N) matters; 16(N+1) -> residue 16",
    )

    heading(pdf, "14. Priority actions", 2)
    actions = [
        "1. Add BRIDGE_N with Lambda_N (x) and reflection pair lambda_y / lambda_-y (y).",
        "2. Document x^3 (3-way) vs y^2 (2-way) branch structure in Complexity_Simplified_N.",
        "3. Add three corner deltas (B/C/D) and defect(d) = delta + d for Puzzle 135 lane.",
        "4. Record a3 (x carry) and b3_y per (+/-) pairing; derive b3_x and b3_yN on N.",
        "5. Use ratio power law (Px^3+7)/(rx^3+7); reject naive lambda_x^3+7.",
        "6. Do not copy Lambda^3 cube-root tree to N; IQ/Iq needs height-aware replacement.",
        "7. Regenerate anchors from Lambda_N + reflection pairing + relative offset.",
    ]
    for a in actions:
        body(pdf, a)

    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
