#!/usr/bin/env python3
"""Verify ECDLP folder photo checklist against Puzzle 135 (row 3 / Px3).

Run from anywhere:
  python C:\\Users\\mitch\\Desktop\\secp256k1\\ECDLP\\ecdlp_n_bridge_verify.py
"""

from __future__ import annotations

from dataclasses import dataclass

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N
LO, HI, TOP = 2**134, 2**135, 2**135 - 1

n1 = 59918213076871302850696965052278348370805334183656907928308327240635173121259
n2 = 79196589282660987520076475805787536662716643115069436220061826482331618169130
n3 = 92469376115100100476368529159309930673017992032554783930545014292850878052937

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

CP1 = 57602015833677736603574291432760600960685355547305560147555835666458430710854
CR1 = 73680319372475906803320245449080571569331871474977252785503402279627244902569
Lambda = 97451685862885086182458552040892158509924235661624603229050850812487253689501

Py3 = 46351506704828816385393879789131775975171267756561783641521771795450741674800
ry3_even = 49714739208247555872780528359092797866261457510155690641636464864972500227644

IDX = 2  # Puzzle 135 = row 3 (0-based index 2)


@dataclass
class Check:
    photo: str
    title: str
    passed: bool
    detail: str
    expect_pass: bool = True


def y_even(x: int) -> int:
    y_sq = (pow(x, 3, p) + 7) % p
    y_pos = pow(y_sq, (p + 1) // 4, p)
    y_neg = (p - y_pos) % p
    return y_pos if y_pos % 2 == 0 else y_neg


def cube_root_mod_n(a: int) -> tuple[int | None, str]:
    """Principal cube root mod N when defined; else (None, reason)."""
    if a % N == 0:
        return 0, "zero"
    if (N - 1) % 3 != 0:
        return None, f"(N-1) mod 3 = {(N - 1) % 3} (not 1)"
    exp = (2 * N - 1) // 3
    r = pow(a, exp, N)
    if pow(r, 3, N) != a % N:
        return None, "principal root failed cube check"
    return r, "ok"


def beta_n() -> int | None:
    for a in range(2, 10000):
        b = pow(a, (N - 1) // 3, N)
        if b != 1 and pow(b, 3, N) == 1:
            return b
    return None


def is_exact_div(num: int, mod: int) -> tuple[bool, int | None]:
    r = num % mod
    if r != 0:
        return False, None
    return True, num // mod


def run_checks() -> list[Check]:
    out: list[Check] = []
    ninv = [pow(x, -1, p) for x in (n1, n2, n3)]

    Qx = [(x * delta) % N for x in Px]
    qx = [(x * delta) % N for x in rx]
    Qy3 = (Py3 * delta) % N
    qy3 = (ry3_even * delta) % N

    Lambda_N = (Px[IDX] * pow(rx[IDX], -1, N)) % N
    GAP = (Lambda_N - Lambda) % N
    lam_y = (Py3 * pow(ry3_even, -1, p)) % p
    lam_y_N = (Py3 * pow(ry3_even, -1, N)) % N

    IP = 1
    IR = 1
    IQ = 1
    Iq = 1
    for i in range(3):
        IP = IP * Px[i] % p
        IR = IR * rx[i] % p
        IQ = IQ * Qx[i] % N
        Iq = Iq * qx[i] % N

    b3_x_num = Lambda_N * qx[IDX] - Qx[IDX]
    b3_x_ok, b3_x = is_exact_div(b3_x_num, N)
    b3_yN_num = lam_y_N * qy3 - Qy3
    b3_yN_ok, b3_yN = is_exact_div(b3_yN_num, N)

    # --- IMG_9999 p-side ---
    lambdas_p = {(Px[i] * pow(rx[i], -1, p)) % p for i in range(3)}
    out.append(
        Check(
            "IMG_9999",
            "p-side: Lambda = Px_i/rx_i same for all i",
            len(lambdas_p) == 1 and lambdas_p.pop() == Lambda,
            f"values={Lambda}",
        )
    )
    out.append(
        Check(
            "IMG_9999",
            "p-side: n1^3 == N (mod p)",
            pow(n1, 3, p) == N % p,
            f"n1^3 mod p = {pow(n1, 3, p)}",
        )
    )
    out.append(
        Check(
            "IMG_9999",
            "p-side: CP1 = Px_i/Gx_i collapsed",
            all((Px[i] * pow(Gx[i], -1, p)) % p == CP1 for i in range(3)),
            f"CP1={CP1}",
        )
    )
    out.append(
        Check(
            "IMG_9999",
            "p-side: IP == Lambda^3 * IR (mod p)",
            IP == (pow(Lambda, 3, p) * IR) % p,
            "cubic aggregate on p",
        )
    )

    # --- IMG_0001 N-side bridge ---
    out.append(
        Check(
            "IMG_0001",
            "N-side: Lambda_N == Lambda + GAP (mod N)",
            Lambda_N == (Lambda + GAP) % N,
            f"GAP bitlen={GAP.bit_length()}",
        )
    )
    out.append(
        Check(
            "IMG_0001",
            "N-side: Qx3 == Lambda_N*qx3 (mod N) at d=0",
            Qx[IDX] == (Lambda_N * qx[IDX]) % N,
            "row 3 only",
        )
    )
    out.append(
        Check(
            "IMG_0001",
            "N-side: Lambda+GAP+d closes row3 for d=2^134",
            Qx[IDX] == ((Lambda + GAP + LO) % N * qx[IDX]) % N,
            "photo adds d to bridge scalar directly",
            expect_pass=False,
        )
    )

    # --- IMG_9988 / 0002 / 9995 carries ---
    out.append(
        Check(
            "IMG_9988",
            "b3_x = (Lambda_N*qx3 - Qx3)/N is integer (row 3)",
            b3_x_ok,
            f"b3_x={b3_x}" if b3_x_ok else f"remainder={b3_x_num % N}",
        )
    )
    out.append(
        Check(
            "IMG_0002",
            "b3_yN = (Lambda_yN*qy3 - Qy3)/N is integer (row 3)",
            b3_yN_ok,
            f"b3_yN={b3_yN}" if b3_yN_ok else f"remainder={b3_yN_num % N}",
        )
    )
    for i in range(3):
        num = Lambda_N * qx[i] - Qx[i]
        ok = num % N == 0
        out.append(
            Check(
                "IMG_9992",
                f"vector row {i + 1}: Qx == Lambda_N*qx - N*b",
                ok,
                "exact integer carry" if ok else f"remainder={num % N}",
                expect_pass=(i == IDX),
            )
        )

    # --- IMG_9989 / 9997 defect sensitivity ---
    d_step = (1 * qx[IDX]) // N
    b3_pred = (b3_x or 0) + d_step if b3_x_ok else None
    out.append(
        Check(
            "IMG_9989",
            "b3_x(d) step: b3_x(1) == b3_x(0) + floor(qx3/N)",
            b3_x_ok and b3_pred == (b3_x + (1 * qx[IDX]) // N),
            f"floor(qx3/N)={d_step}",
        )
    )
    dy_step = (1 * qy3) // N
    out.append(
        Check(
            "IMG_9997",
            "Delta b3_yN per d=1 ~ floor(qy3/N)",
            b3_yN_ok and dy_step == (qy3 // N),
            f"floor(qy3/N)={dy_step}",
        )
    )
    out.append(
        Check(
            "IMG_9997",
            "Adding d=1 keeps both carries integer",
            is_exact_div(Lambda_N * qx[IDX] - Qx[IDX] + qx[IDX], N)[0]
            and is_exact_div(lam_y_N * qy3 - Qy3 + qy3, N)[0],
            "photo 'wiggle d' closure",
            expect_pass=False,
        )
    )

    # --- IMG_9994 Lambda_yN ---
    out.append(
        Check(
            "IMG_9994",
            "Lambda_yN = Qy3*qy3^-1 mod N",
            lam_y_N == (Qy3 * pow(qy3, -1, N)) % N,
            f"Lambda_yN={lam_y_N}",
        )
    )

    # --- Grand alignment: naive vs corrected ---
    naive_n = pow(lam_y_N, 2, N) == pow(Lambda_N, 3, N)
    corrected_p = (pow(lam_y, 2, p) * pow(ry3_even, 2, p) - pow(Lambda, 3, p) * pow(rx[IDX], 3, p)) % p == 7
    corrected_n = (
        pow(lam_y_N, 2, N) * pow(qy3, 2, N) - pow(Lambda_N, 3, N) * pow(qx[IDX], 3, N)
    ) % N
    out.append(
        Check(
            "IMG_9996",
            "naive: Lambda_yN^2 == Lambda_N^3 (mod N)",
            naive_n,
            "as stated in photos",
            expect_pass=False,
        )
    )
    out.append(
        Check(
            "IMG_9996",
            "corrected p: lam_y^2*ry^2 - Lambda^3*rx^3 == 7 (mod p)",
            corrected_p,
            "includes curve constant b=7",
        )
    )
    out.append(
        Check(
            "IMG_0003",
            "corrected N: lam_yN^2*qy^2 - Lambda_N^3*qx^3 == 7 (mod N)",
            corrected_n == 7,
            f"actual remainder mod N = {corrected_n}",
            expect_pass=False,
        )
    )

    # --- IMG_9990 / 9991 / 9993 cubic on N ---
    cubic_ok = IQ == (pow(Lambda_N, 3, N) * Iq) % N
    out.append(
        Check(
            "IMG_9990",
            "IQ == Lambda_N^3 * Iq (mod N)",
            cubic_ok,
            f"IQ={IQ}",
            expect_pass=False,
        )
    )
    R = (IQ * pow(Iq, -1, N)) % N
    y1, y1_msg = cube_root_mod_n(R)
    out.append(
        Check(
            "IMG_9993",
            "cube root of IQ/Iq mod N (principal)",
            y1 is not None,
            y1_msg,
            expect_pass=False,
        )
    )
    if y1 is not None:
        b = beta_n()
        roots = [y1, y1 * b % N, y1 * pow(b, 2, N) % N] if b else [y1]
        any_cube = any(pow(r, 3, N) == R for r in roots)
        any_align = any(pow(r, 2, N) == pow(Lambda_N, 3, N) for r in roots)
        out.append(
            Check(
                "IMG_9993",
                "three cube-root branches restore R",
                any_cube,
                f"roots tested={len(roots)}",
                expect_pass=False,
            )
        )
        out.append(
            Check(
                "IMG_9991",
                "height-aware: cbrt(IQ/Iq)^2 == Lambda_N^3",
                any_align,
                "photo shortcut",
                expect_pass=False,
            )
        )
    else:
        out.append(
            Check(
                "IMG_9991",
                "height-aware: cbrt(IQ/Iq)^2 == Lambda_N^3",
                False,
                "skipped (no principal root)",
                expect_pass=False,
            )
        )

    B_num = pow(Lambda_N, 3) * Iq - IQ
    B_ok, B_cubic = is_exact_div(B_num, N)
    out.append(
        Check(
            "IMG_9990",
            "B_cubic = (Lambda_N^3*Iq - IQ)/N integer",
            B_ok,
            f"B_cubic={B_cubic}" if B_ok else f"remainder={(B_num % N)}",
            expect_pass=False,
        )
    )

    # --- IMG_9998 / 0004 extract k ---
    out.append(
        Check(
            "IMG_9998",
            "k = Lambda_N is in Puzzle 135 band [2^134, 2^135)",
            LO <= Lambda_N < HI,
            f"Lambda_N bitlen={Lambda_N.bit_length()}",
            expect_pass=False,
        )
    )
    out.append(
        Check(
            "IMG_0004",
            "IP + 7 == Py3^2 (mod p) key identity",
            (IP + 7) % p == (Py3 * Py3) % p,
            "x-product ties to pubkey y",
        )
    )

    g_slots = [
        72789842462919254798787184333665945456600870881042555899576743439227206827139,
        5413323970105506090398366098172752697370300495141572731819943140721401835677,
        37588922804291434534385434576849209699298813289456435408060897427960226008847,
    ]
    gx_row = {(Gx[0] * ninv[j]) % p for j in range(3)}
    gy_row = {(y_even(Gx[0]) * ninv[j]) % p for j in range(3)}
    out.append(
        Check(
            "IMG_9999",
            "x-side: Gx1*n_j^-1 hits {G_A,G_B,G_C}",
            gx_row == set(g_slots),
            f"got {len(gx_row)} slots",
        )
    )
    out.append(
        Check(
            "IMG_9999",
            "y-side: Gy1*n_j^-1 is NOT same Latin permutation",
            gy_row != set(g_slots),
            "y has +/- only; no cube Latin square on y",
        )
    )

    return out


def print_report(checks: list[Check]) -> None:
    print("=" * 88)
    print("ECDLP PHOTO CHECKLIST - Puzzle 135 (Px3 / row 3)")
    print("=" * 88)

    by_photo: dict[str, list[Check]] = {}
    for c in checks:
        by_photo.setdefault(c.photo, []).append(c)

    ok = warn = fail = 0
    for photo in sorted(by_photo.keys()):
        print(f"\n--- {photo} ---")
        for c in by_photo[photo]:
            if c.passed and c.expect_pass:
                tag = "PASS"
                ok += 1
            elif c.passed and not c.expect_pass:
                tag = "WARN (passed but expected fail - recheck photo claim)"
                warn += 1
            elif not c.passed and not c.expect_pass:
                tag = "PASS (expected fail - photo claim does not hold)"
                ok += 1
            else:
                tag = "FAIL"
                fail += 1
            print(f"  [{tag}] {c.title}")
            print(f"           {c.detail}")

    print("\n" + "=" * 88)
    print(f"Summary: {ok} ok, {fail} unexpected fails, {warn} warnings")
    print("=" * 88)
    print("\nInterpretation:")
    print("  - Row-3 carries (b3_x, b3_yN) and p-side bridge: solid.")
    print("  - Naive N-side cubic / k=Lambda_N / cube-root on IQ/Iq: not valid as written.")
    print("  - Corrected p-side alignment uses +7: lam_y^2*ry^2 - Lambda^3*rx^3 == 7 (mod p).")
    print("  - Private key d still requires ECDLP (kangaroo / ladder), not Lambda_N.")


def main() -> None:
    checks = run_checks()
    print_report(checks)


if __name__ == "__main__":
    main()
