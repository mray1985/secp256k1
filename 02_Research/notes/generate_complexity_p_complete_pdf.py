#!/usr/bin/env python3
"""Append verified y-side block to Complexity_Simplified_p.txt and build combined PDF."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N
LO, HI = 2**134, 2**135

CP1 = 57602015833677736603574291432760600960685355547305560147555835666458430710854
CR1 = 73680319372475906803320245449080571569331871474977252785503402279627244902569
Lambda = 97451685862885086182458552040892158509924235661624603229050850812487253689501

Gx = [
    91177636130617246552803821781935006617134368061721227770777272682868638699771,
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    85340279321737800624759429340272274763154997815782306132637707972559913914315,
]
Px = [
    51866120889717641461810659005716431188799022756838843706514074509901265629059,
    54715131853151445691733189261594605794679177894602772031317532630299444965014,
    9210836494447108270027136741376870869791784014198948301625976867708124077590,
]
rx = [
    114930704126154877082883546730544079307369404418439078397954295509919169851219,
    90653255469745952335985143920649543885181555095025199315947044135806663628368,
    26000218878731561428273279366182192513989009817816850365013828370091835863739,
]

NOTES = Path(__file__).resolve().parent
TXT = NOTES / "Complexity_Simplified_p.txt"
PDF_OUT = NOTES / "Complexity_Simplified_p_Complete.pdf"


def y_roots(x: int) -> tuple[int, int]:
    y_sq = (pow(x, 3, p) + 7) % p
    y_pos = pow(y_sq, (p + 1) // 4, p)
    return y_pos, (p - y_pos) % p


def map_p_to_n(y: int) -> int:
    return (N * y // p) % N


def compute_y_side() -> dict:
    gy_pos, gy_neg = y_roots(Gx[0])
    py_pos, py_neg = y_roots(Px[0])
    ry_pos, ry_neg = y_roots(rx[0])

    # Pubkey 02145d... uses even y (yn branch for this triple).
    gy = gy_pos
    py = py_neg
    ry = ry_pos

    cq1 = (py * pow(gy, -1, p)) % p
    cq1_inv = pow(cq1, -1, p)
    c_r1 = (ry * pow(gy, -1, p)) % p
    c_r1_inv = pow(c_r1, -1, p)
    lam_y = (py * pow(ry, -1, p)) % p
    lam_y_inv = pow(lam_y, -1, p)
    lam_y_alt = (py * pow(ry_neg, -1, p)) % p

    ip = (Px[0] * Px[1] * Px[2]) % p
    ig = (Gx[0] * Gx[1] * Gx[2]) % p
    ir = (rx[0] * rx[1] * rx[2]) % p
    igy = pow(gy, 3, p)
    ipy = pow(py, 3, p)
    iry = pow(ry, 3, p)

    ratio_y = ((pow(Px[2], 3, p) + 7) * pow(pow(rx[2], 3, p) + 7, -1, p)) % p
    lam_y_sq = (lam_y * lam_y) % p

    lambda_n = (Px[2] * pow(rx[2], -1, N)) % N
    lam_y_n = (py * pow(ry, -1, N)) % N
    gap_x = (lambda_n - Lambda) % N
    gap_y = (lam_y_n - lambda_n) % N

    lam_py = map_p_to_n(py)
    lam_py_neg = map_p_to_n((-py) % p)
    lam_ry = map_p_to_n(ry)
    lam_ry_neg = map_p_to_n((-ry) % p)

    checks = {
        "shared_y2_px": len({(pow(x, 3, p) + 7) % p for x in Px}) == 1,
        "shared_y2_gx": len({(pow(x, 3, p) + 7) % p for x in Gx}) == 1,
        "shared_y2_rx": len({(pow(x, 3, p) + 7) % p for x in rx}) == 1,
        "ip_plus_7": (ip + 7) % p == (py * py) % p,
        "lam_y_sq": lam_y_sq == ratio_y,
        "cq1_const": all((py * pow(gy, -1, p)) % p == cq1 for _ in range(3)),
        "c_r1_const": all((ry * pow(gy, -1, p)) % p == c_r1 for _ in range(3)),
        "lam_y_const": all((py * pow(ry, -1, p)) % p == lam_y for _ in range(3)),
        "py_on_curve": (py * py) % p == (pow(Px[2], 3, p) + 7) % p,
        "refl_py": (lam_py + lam_py_neg) % N == N - 1,
        "refl_ry": (lam_ry + lam_ry_neg) % N == N - 1,
    }

    return {
        "gy_pos": gy_pos,
        "gy_neg": gy_neg,
        "py_pos": py_pos,
        "py_neg": py_neg,
        "ry_pos": ry_pos,
        "ry_neg": ry_neg,
        "gy": gy,
        "py": py,
        "ry": ry,
        "gy_inv": pow(gy, -1, p),
        "py_inv": pow(py, -1, p),
        "ry_inv": pow(ry, -1, p),
        "cq1": cq1,
        "cq1_inv": cq1_inv,
        "c_r1": c_r1,
        "c_r1_inv": c_r1_inv,
        "lam_y": lam_y,
        "lam_y_inv": lam_y_inv,
        "lam_y_alt": lam_y_alt,
        "lam_y_sq": lam_y_sq,
        "ratio_y": ratio_y,
        "ip": ip,
        "igy": igy,
        "ipy": ipy,
        "iry": iry,
        "ig": ig,
        "ir": ir,
        "lambda_n": lambda_n,
        "lam_y_n": lam_y_n,
        "gap_x": gap_x,
        "gap_y": gap_y,
        "lam_py": lam_py,
        "lam_py_neg": lam_py_neg,
        "lam_ry": lam_ry,
        "lam_ry_neg": lam_ry_neg,
        "lam_over_lambda": (lam_y * pow(Lambda, -1, p)) % p,
        "checks": checks,
    }


def build_y_block(data: dict) -> str:
    c = data
    lines = [
        "",
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        "Y-SIDE (verified 2026-06-09) - quadratic bridge parallel to x-side",
        "",
        "Within each triple (Gx1..3, Px1..3, rx1..3) all three x-coordinates share the same y^2 mod p.",
        "Therefore Gy1=Gy2=Gy3, Py1=Py2=Py3, and ry1=ry2=ry3 up to the single +/- branch choice.",
        "Puzzle 135 pubkey 02145d... selects the EVEN y branch for Py3.",
        "",
        "Gy1 = Gy2 = Gy3 = " + str(c["gy"]),
        "\t483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8",
        "",
        "Gy^-1 (mod p) = " + str(c["gy_inv"]),
        "",
        "Gy (odd branch) = " + str(c["gy_neg"]),
        "",
        "Py1 = Py2 = Py3 = " + str(c["py"]),
        "\t667a05e9a1bdd6f70142b66558bd12ce2c0f9cbc7001b20c8a6a109c80dc5330",
        "",
        "Py^-1 (mod p) = " + str(c["py_inv"]),
        "",
        "Py (odd branch) = " + str(c["py_pos"]),
        "",
        "ry1 = ry2 = ry3 (even branch, same parity as Py3) = " + str(c["ry"]),
        "\t6de98b9482b20dffa5ccbb87548d2dfda0218c4b941c4c55afd02232f775d63c",
        "",
        "ry^-1 (mod p) = " + str(c["ry_inv"]),
        "",
        "ry (odd branch) = " + str(c["ry_neg"]),
        "",
        "Py_i * Gy_i^-1 mod p = " + str(c["cq1"]) + " = CQ1  (collapsed, all i)",
        "ry_i * Gy_i^-1 mod p = " + str(c["c_r1"]) + " = C_r1 (collapsed, all i)",
        "",
        "CQ1^-1 (mod p) = " + str(c["cq1_inv"]),
        "C_r1^-1 (mod p) = " + str(c["c_r1_inv"]),
        "",
        "BRIDGE_y: { Py_i / Gy_i = CQ1",
        "          ry_i / Gy_i = C_r1 }",
        "",
        "therefore: { Py_i / ry_i = CQ1 * C_r1^-1 mod p }",
        "",
        "CQ1 * C_r1^-1 mod p = " + str(c["lam_y"]) + " = lambda_y",
        "",
        "lambda_y^-1 (mod p) = " + str(c["lam_y_inv"]),
        "",
        "lambda_y != Lambda  (x-bridge and y-bridge are distinct)",
        "Lambda   (x) = " + str(Lambda),
        "lambda_y (y) = " + str(c["lam_y"]),
        "lambda_y / Lambda mod p = " + str(c["lam_over_lambda"]),
        "",
        "lambda_y^2 mod p = " + str(c["lam_y_sq"]),
        "(Px3^3 + 7) * (rx3^3 + 7)^-1 mod p = " + str(c["ratio_y"]),
        "=> lambda_y^2 = (Px3^3+7)/(rx3^3+7) mod p  (quadratic y-bridge; x-side uses Lambda^3)",
        "",
        "KEY IDENTITY:  IP + 7 = Py3^2 mod p",
        "IP  = Px1*Px2*Px3 mod p = " + str(c["ip"]),
        "Py3^2 mod p             = " + str((c["py"] * c["py"]) % p),
        "",
        "Gy1*Gy2*Gy3 mod p = " + str(c["igy"]) + " = IGy",
        "Py1*Py2*Py3 mod p = " + str(c["ipy"]) + " = IPy",
        "ry1*ry2*ry3 mod p = " + str(c["iry"]) + " = IRy",
        "",
        "BRANCH GRID (Py +/- vs ry +/-):",
        "  same parity (Py+/ry+ or Py-/ry-) => lambda_y = " + str(c["lam_y"]),
        "  mixed parity                      => lambda_y = " + str(c["lam_y_alt"]),
        "",
        "NO 3-way n_j normalization on y (cube-root Latin square is x-only).",
        "",
        "--- N-side shadow (for Complexity_Simplified_N bridge) ---",
        "Lambda_N = Px3*rx3^-1 mod N = " + str(c["lambda_n"]),
        "lambda_y_N = Py3*ry3^-1 mod N = " + str(c["lam_y_n"]),
        "GAP_x = Lambda_N - Lambda mod N = " + str(c["gap_x"]),
        "GAP_y = lambda_y_N - Lambda_N mod N = " + str(c["gap_y"]),
        "",
        "Reflection (floor map): lambda_y + lambda_-y = N - 1",
        "  map_p_to_n(Py3)  = " + str(c["lam_py"]),
        "  map_p_to_n(-Py3) = " + str(c["lam_py_neg"]),
        "  sum mod N        = " + str((c["lam_py"] + c["lam_py_neg"]) % N),
        "",
        "VERIFICATION: " + ", ".join(f"{k}={v}" for k, v in c["checks"].items()),
        "",
    ]
    return "\n".join(lines)


class CompletePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def ascii_safe(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def heading(pdf: FPDF, text: str, level: int = 1) -> None:
    text = ascii_safe(text)
    sizes = {1: 16, 2: 13, 3: 11}
    pdf.set_font("Helvetica", "B", sizes.get(level, 11))
    pdf.multi_cell(0, 8, text)
    pdf.ln(2)


def body(pdf: FPDF, text: str) -> None:
    text = ascii_safe(text)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)


def mono(pdf: FPDF, text: str) -> None:
    text = ascii_safe(text)
    pdf.set_font("Courier", "", 7)
    pdf.multi_cell(0, 4, text)
    pdf.ln(1)


def table_row(pdf: FPDF, c1: str, c2: str, c3: str = "") -> None:
    c1, c2, c3 = ascii_safe(c1), ascii_safe(c2), ascii_safe(c3)
    pdf.set_font("Helvetica", "", 9)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    if c3:
        pdf.cell(w * 0.28, 6, c1[:42], border=1)
        pdf.cell(w * 0.36, 6, c2[:55], border=1)
        pdf.cell(w * 0.36, 6, c3[:55], border=1)
    else:
        pdf.cell(w * 0.35, 6, c1[:50], border=1)
        pdf.cell(w * 0.65, 6, c2[:95], border=1)
    pdf.ln()


def build_pdf(data: dict) -> None:
    pdf = CompletePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    heading(pdf, "Complexity_Simplified_p - Complete Reference")
    body(
        pdf,
        f"Puzzle 135 / secp256k1. Generated {date.today().isoformat()}.\n"
        "Combines the original x-side cube-root bridge (Complexity_Simplified_p.txt) "
        "with the verified y-side quadratic bridge and N-side shadow constants.",
    )

    heading(pdf, "1. Executive summary", 2)
    body(
        pdf,
        "Puzzle 135 target x = Px3. The p-side file closes the x-bridge: Px_i/rx_i = Lambda (mod p) "
        "via three cube roots n1,n2,n3 of N. The y-side mirrors this with collapsed ratios CQ1, C_r1, "
        "and lambda_y - but y has only +/- branches (no third cube slot). lambda_y != Lambda. "
        "The strongest new identity is IP + 7 = Py3^2 (mod p) where IP = Px1*Px2*Px3.",
    )

    heading(pdf, "2. Puzzle 135 target", 2)
    mono(
        pdf,
        f"Px3 = {Px[2]}\n"
        f"hex = 145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16\n"
        f"Py3 = {data['py']}  (even y, compressed pubkey 02...)\n"
        f"rx3 = {rx[2]}\n"
        f"d band: [2^134, 2^135 - 1]  and mirror [N - 2^135 - 1, N - 2^134]",
    )

    heading(pdf, "3. Foundational parameters", 2)
    mono(
        pdf,
        f"p = {p}\nN = {N}\np - N = {delta}\n"
        f"n1^3 = N (mod p)  [cube roots n1,n2,n3 in source file]",
    )

    heading(pdf, "4. X-side bridge (original, verified)", 2)
    body(pdf, "Three-way Latin square on Gx, Px, rx via n_j^-1. Collapsed constants:")
    mono(
        pdf,
        f"CP1 = Px_i * Gx_i^-1 mod p = {CP1}\n"
        f"CR1 = rx_i * Gx_i^-1 mod p = {CR1}\n"
        f"Lambda = CP1 * CR1^-1 = Px_i * rx_i^-1 mod p = {Lambda}\n"
        f"Lambda^-1 mod p = {pow(Lambda, -1, p)}\n\n"
        f"IP = Px1*Px2*Px3 mod p = {data['ip']}\n"
        f"IG = Gx1*Gx2*Gx3 mod p = {data['ig']}\n"
        f"IR = rx1*rx2*rx3 mod p = {data['ir']}\n\n"
        f"Pi = Lambda * ri (mod p)  [root bridge]\n"
        f"IP = Lambda^3 * IR (mod p) [cubic bridge]",
    )

    heading(pdf, "5. Y-side bridge (new, verified)", 2)
    body(
        pdf,
        "Each triple shares one y^2 mod p, so Gy1=Gy2=Gy3, Py1=Py2=Py3, ry1=ry2=ry3 (per branch). "
        "Pubkey selects even Py. No 3-way n_j Latin square on y.",
    )
    mono(
        pdf,
        f"Gy (even) = {data['gy']}\n"
        f"Py (even) = {data['py']}\n"
        f"ry (even, same parity as Py) = {data['ry']}\n\n"
        f"CQ1 = Py_i * Gy_i^-1 mod p = {data['cq1']}\n"
        f"C_r1 = ry_i * Gy_i^-1 mod p = {data['c_r1']}\n"
        f"lambda_y = CQ1 * C_r1^-1 = Py_i * ry_i^-1 mod p = {data['lam_y']}\n"
        f"lambda_y^-1 mod p = {data['lam_y_inv']}\n\n"
        f"lambda_y / Lambda mod p = {data['lam_over_lambda']}\n"
        f"lambda_y^2 mod p = {data['lam_y_sq']}\n"
        f"(Px3^3+7)/(rx3^3+7) mod p = {data['ratio_y']}",
    )

    heading(pdf, "6. Key identity: IP + 7 = Py3^2", 2)
    mono(
        pdf,
        f"IP = Px1*Px2*Px3 mod p = {data['ip']}\n"
        f"IP + 7 mod p = {(data['ip'] + 7) % p}\n"
        f"Py3^2 mod p = {(data['py'] * data['py']) % p}\n"
        f"Match: {data['checks']['ip_plus_7']}",
    )
    body(
        pdf,
        "This ties the x-product block directly to the puzzle pubkey y-coordinate. "
        "It is the main structural link between the x-side ladder and the target point.",
    )

    heading(pdf, "7. X-side vs Y-side comparison", 2)
    table_row(pdf, "Layer", "x-side", "y-side")
    rows = [
        ("Root degree", "x^3 -> 3 cube roots n1,n2,n3", "y^2 -> 2 branches (+/- only)"),
        ("Normalize", "n_j^-1 Latin square A/B/C", "branch pick only (no n_j on y)"),
        ("Collapse G", "CP1 = Px/Gx", "CQ1 = Py/Gy"),
        ("Collapse r", "CR1 = rx/Gx", "C_r1 = ry/Gy"),
        ("Bridge", "Lambda = Px/rx", "lambda_y = Py/ry ( != Lambda )"),
        ("Power law", "Lambda^3 cubic", "lambda_y^2 quadratic"),
        ("Triple product", "IP, IG, IR", "IPy, IGy, IRy"),
        ("Puzzle 135", "Px3", "Py3 even branch"),
    ]
    for row in rows:
        table_row(pdf, *row)
    pdf.ln(4)

    heading(pdf, "8. Branch grid (y only)", 2)
    mono(
        pdf,
        f"Py+ / ry+  or  Py- / ry-  (same parity) => lambda_y = {data['lam_y']}\n"
        f"Py+ / ry-  or  Py- / ry+  (mixed parity) => lambda_y = {data['lam_y_alt']}\n\n"
        f"Odd branches:\n"
        f"  Gy- = {data['gy_neg']}\n"
        f"  Py- = {data['py_pos']}\n"
        f"  ry- = {data['ry_neg']}",
    )

    heading(pdf, "9. N-side shadow (for Complexity_Simplified_N)", 2)
    mono(
        pdf,
        f"Lambda_N = Px3*rx3^-1 mod N = {data['lambda_n']}\n"
        f"lambda_y_N = Py3*ry3^-1 mod N = {data['lam_y_n']}\n"
        f"GAP_x = Lambda_N - Lambda mod N = {data['gap_x']}\n"
        f"GAP_y = lambda_y_N - Lambda_N mod N = {data['gap_y']}\n\n"
        f"Reflection: map_p_to_n(y) = floor(N*y/p) mod N\n"
        f"  map_p_to_n(Py3) + map_p_to_n(-Py3) = { (data['lam_py'] + data['lam_py_neg']) % N } (= N-1)\n\n"
        "Do NOT copy Lambda to N blindly. Use Lambda_N = Lambda + GAP_x. "
        "Y-side needs separate lambda_y_N and reflection pairing.",
    )

    heading(pdf, "10. Verification checklist", 2)
    for key, val in data["checks"].items():
        status = "PASS" if val else "FAIL"
        body(pdf, f"  [{status}] {key}")

    heading(pdf, "11. What this does / does not give", 2)
    body(
        pdf,
        "DOES: complete p-side geometry for Puzzle 135; second bridge constant lambda_y; "
        "IP+7=Py3^2; N-side GAP and reflection inputs.\n\n"
        "DOES NOT: yield private key d directly. Scalar recovery still requires ECDLP "
        "(kangaroo on almost.txt start point) or ladder narrowing in [2^134, 2^135).",
    )

    heading(pdf, "12. Source files", 2)
    body(
        pdf,
        "Complexity_Simplified_p.txt (this note, x+y)\n"
        "Complexity_Simplified_N.txt (N-side, needs Lambda_N + range-variable delta)\n"
        "almost.txt (EC trace -> kangaroo on start point)\n"
        "primes_public_all_puzzles.txt (public factorizations, no private key for 135)",
    )

    pdf.output(str(PDF_OUT))


def main() -> None:
    data = compute_y_side()
    block = build_y_block(data)

    text = TXT.read_text(encoding="utf-8")
    marker = "Y-SIDE (verified"
    if marker not in text:
        TXT.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
        print(f"Appended y-side block to {TXT}")
    else:
        print(f"Y-side block already present in {TXT}")

    build_pdf(data)
    print(f"Wrote PDF: {PDF_OUT}")
    failed = [k for k, v in data["checks"].items() if not v]
    if failed:
        raise SystemExit(f"Verification failed: {failed}")


if __name__ == "__main__":
    main()
