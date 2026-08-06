#!/usr/bin/env python3
"""Show coordinate shell vs ratio shell: mod p (+7) vs mod N (+G)."""

from __future__ import annotations

from pathlib import Path

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
rx = 26000218878731561428273279366182192513989009817816850365013828370091835863739
ry = 49714739208247555872780528359092797866261457510155690641636464864972500227644


def main() -> None:
    lam_x_p = (Px * pow(rx, -1, p)) % p
    lam_y_p = (Py * pow(ry, -1, p)) % p
    lam_x_n = (Px * pow(rx, -1, N)) % N
    lam_y_n = (Py * pow(ry, -1, N)) % N

    G_p = (pow(Py, 2, p) - pow(Px, 3, p)) % p
    G_n = (pow(Py, 2, N) - pow(Px, 3, N)) % N
    K_n = (N - G_n) % N

    w_p = (pow(lam_y_p, 2, p) * pow(ry, 2, p) - pow(lam_x_p, 3, p) * pow(rx, 3, p)) % p
    w_n = (pow(lam_y_n, 2, N) * pow(ry, 2, N) - pow(lam_x_n, 3, N) * pow(rx, 3, N)) % N

    bare_p = (pow(lam_y_p, 2, p) - pow(lam_x_p, 3, p)) % p
    bare_n = (pow(lam_x_n, 3, N) - pow(lam_y_n, 2, N)) % N

    law_p = pow(lam_y_p, 2, p) == ((pow(Px, 3, p) + 7) * pow(pow(rx, 3, p) + 7, -1, p)) % p
    law_x = pow(lam_x_p, 3, p) == ((pow(Py, 2, p) - 7) * pow(pow(ry, 2, p) - 7, -1, p)) % p

    lines = [
        "=" * 72,
        "P135 LAMBDA SHELL vs COORDINATE SHELL",
        "=" * 72,
        "",
        "LOCK: Px3, Py, rx3, ry  (epsilon row)",
        "",
        "+---------------------------+---------------------------+",
        "|  COORDINATES (Px, Py)    |  RATIOS (Lambda, lambda_y)|",
        "+---------------------------+---------------------------+",
        "|  Py^2 - Px^3  =  GAP      |  lam_y^2 * ry^2           |",
        "|                           |    - lam_x^3 * rx^3 = GAP |",
        "+---------------------------+---------------------------+",
        "",
        "------------------------------------------------------------------------",
        " mod p (on-curve)                         mod N (off-curve)",
        "------------------------------------------------------------------------",
        f"  Py^2 - Px^3        = {G_p}",
        f"  weighted lambda    = {w_p}",
        f"  match?             {G_p == w_p == 7}",
        "",
        f"  Py^2 - Px^3        = G  ({G_n})",
        f"                       bits {G_n.bit_length()}",
        f"  weighted lambda    = G? {w_n == G_n}",
        f"  equals 7 mod N?    {w_n == 7}",
        "",
        "------------------------------------------------------------------------",
        " WRONG on bare ratios (what does NOT work)",
        "------------------------------------------------------------------------",
        f"  lam_y^2 == lam_x^3 + 7   mod p?  {pow(lam_y_p,2,p) == (pow(lam_x_p,3,p)+7)%p}",
        f"  lam_y^2 == lam_x^3 + 7   mod N?  {pow(lam_y_n,2,N) == (pow(lam_x_n,3,N)+7)%N}",
        f"  lam_x^3 - lam_y^2 == G   mod N?  {bare_n == G_n}",
        f"  lam_x^3 - lam_y^2        = {bare_n}",
        f"  (not G, not K, not 7)",
        "",
        "------------------------------------------------------------------------",
        " RIGHT ratio laws (separate layers)",
        "------------------------------------------------------------------------",
        f"  LAW-P:  lam_y^2 == (Px^3+7)/(rx^3+7)   mod p?  {law_p}",
        f"  LAW-X:  lam_x^3 == (Py^2-7)/(ry^2-7)   mod p?  {law_x}",
        "",
        "  Expand LAW-P:",
        f"    lam_y^2 * (rx^3+7) = Px^3+7",
        f"    check mod p: {(pow(lam_y_p,2,p)*((pow(rx,3,p)+7)%p))%p == (pow(Px,3,p)+7)%p}",
        "",
        "  Expand LAW-X:",
        f"    lam_x^3 * (ry^2-7) = Py^2-7",
        f"    check mod p: {(pow(lam_x_p,3,p)*((pow(ry,2,p)-7)%p))%p == (pow(Py,2,p)-7)%p}",
        "",
        "------------------------------------------------------------------------",
        " WEIGHTED GLUE (why +7 appears)",
        "------------------------------------------------------------------------",
        "",
        "  lam_y = Py/ry   =>  lam_y^2 * ry^2 = Py^2",
        "  lam_x = Px/rx   =>  lam_x^3 * rx^3 = Px^3",
        "",
        "  lam_y^2*ry^2 - lam_x^3*rx^3",
        "       = Py^2 - Px^3",
        "       = 7           (mod p)",
        "       = G           (mod N)",
        "",
        f"  mod p value: {w_p}",
        f"  mod N value: {w_n}",
        f"  K = N-G:     {K_n}",
        f"  Py^2 + K == Px^3 mod N? {(pow(Py,2,N)+K_n)%N == pow(Px,3,N)}",
        "",
        "------------------------------------------------------------------------",
        " FLOW",
        "------------------------------------------------------------------------",
        "",
        "   mod p                          mod N",
        "   -----                          -----",
        "   Py^2 = Px^3 + 7                Py^2 = Px^3 + G",
        "        |                              |",
        "   divide by ry^2, rx^3           same algebra",
        "        |                              |",
        "   lam_y^2*ry^2                   lam_y^2*ry^2",
        "     - lam_x^3*rx^3 = 7             - lam_x^3*rx^3 = G",
        "                                     (NOT 7)",
        "",
        "   Bare lam_y^2 - lam_x^3  is a different object (no rx, ry).",
        "   GAP = Lambda_N - Lambda_p  is the p->N x-class shift (separate).",
        "",
        "=" * 72,
    ]

    report = "\n".join(lines) + "\n"
    out = Path(__file__).resolve().parent / "ARCHIVE" / "p135_lambda_shell_show.txt"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
