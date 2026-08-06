#!/usr/bin/env python3
"""P135 shifted-shell diagram: G (gap), K = N - G, splits mod p vs mod N."""

from __future__ import annotations

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
Px1 = 51866120889717641461810659005716431188799022756838843706514074509901265629059
Px2 = 54715131853151445691733189261594605794679177894602772031317532630299444965014

K_USER = 31193737104849324896427298504706271360388477943930185831958733572697429308310


def gap(mod: int) -> int:
    return (pow(Py, 2, mod) - pow(Px, 3, mod)) % mod


def shell(mod: int, y_shift: int, x_const: int) -> tuple[int, int, int]:
    lhs = (pow(Py, 2, mod) - y_shift) % mod
    rhs = (pow(Px, 3, mod) + x_const) % mod
    return lhs, rhs, (lhs - rhs) % mod


def main() -> None:
    G_p = gap(p)
    G_n = gap(N)
    K = (N - G_n) % N

    lines = [
        "=" * 72,
        "P135 SHIFTED SHELL - G (gap) and K",
        "=" * 72,
        "",
        "LOCK POINT: Px3 (row 3), Py",
        f"  Px = {Px}",
        f"  Py = {Py}",
        "",
        "+---------------------------------------------------------------------+",
        "|  CURVE SHELL (concept)          |  mod p (on-curve) |  mod N (off)   |",
        "+---------------------------------+-------------------+----------------+",
        "|  y^2 - x^3  =  G                |  G = 7            |  G ~ 256 bits  |",
        "|  y^2       =  x^3 + G           |  closes           |  identity      |",
        "|  K        =  N - G              |  (wrap)           |  your constant |",
        "|  y^2 + K   =  x^3   (mod N)     |                   |  TRUE          |",
        "|  y^2       =  x^3 + K           |                   |  FALSE (sign)  |",
        "+---------------------------------------------------------------------+",
        "",
        "-- G (gap) --",
        f"  G mod p = {G_p}   (bits {G_p.bit_length()})  <- the sacred 7 on F_p",
        f"  G mod N = {G_n}",
        f"            bits {G_n.bit_length()}",
        "",
        "-- K --",
        f"  K (computed)  = N - G  = {K}",
        f"  K (your value)           = {K_USER}",
        f"  match: {K == K_USER}",
        f"  bits: {K.bit_length()}",
        "",
        "-- Identities (run) --",
        "  Py^2 - Px^3 == G (mod N):  " + str((pow(Py,2,N)-pow(Px,3,N))%N == G_n),
        "  Py^2 == Px^3 + G (mod N):  " + str((pow(Px,3,N)+G_n)%N == pow(Py,2,N)),
        "  Py^2 == Px^3 + K (mod N):  " + str((pow(Px,3,N)+K)%N == pow(Py,2,N)) + "  <- FALSE",
        "  Py^2 + K == Px^3 (mod N):  " + str((pow(Py,2,N)+K)%N == pow(Px,3,N)) + "  <- TRUE",
        f"  G + K == 0 (mod N):      {(G_n+K)%N == 0}",
        "",
        "-- Gomez split: y^2 - a = x^3 + (G - a)  at lock --",
        "",
        "  mod p:",
        "    a   y_shift  x_const  remainder (lhs-rhs)",
    ]
    for a in (0, 1, 2, 3, 4, 5, 6, 7):
        _, _, r = shell(p, a, G_p - a)
        mark = " <- exact" if r == 0 else (" <- remainder 1" if r == 1 else "")
        lines.append(f"    {a}   {a:>7}  {G_p-a:>7}  {r}{mark}")

    lines += [
        "",
        "  mod N (same split labels; G is big, not 7):",
        "    a   y_shift  x_const  remainder",
    ]
    for a in (0, 4):
        _, _, r = shell(N, a, (G_n - a) % N)
        lines.append(f"    {a}   {a:>7}  {(G_n-a)%N}  tail={r % 10**8}  (bits {r.bit_length()})")

    lines += [
        "",
        "  your probes:",
        "    mod p:  Py^2-4 vs Px^3+3  remainder 0",
        "    mod p:  Py^2-4 vs Px^3+2  remainder 1",
    ]
    _, _, r43 = shell(p, 4, 3)
    _, _, r42 = shell(p, 4, 2)
    lines.append(f"    check p  (4,3): {r43}")
    lines.append(f"    check p  (4,2): {r42}")

    IP = (Px1 * Px2 * Px) % p
    lines += [
        "",
        "-- PRODUCT COLLAPSE mod p (IP = Px1*Px2*Px3) --",
        f"  IP + 7  == Py^2: {(IP+7)%p == pow(Py,2,p)}",
        f"  IP + 3  == Py^2-4: {(IP+3)%p == (pow(Py,2,p)-4)%p}",
        f"  IP + 2  == Py^2-4: {(IP+2)%p == (pow(Py,2,p)-4)%p}  (short by 1)",
        f"  Py^2 - IP - 7 = {(pow(Py,2,p)-IP-7)%p}",
        "",
        "-- ASCII FLOW --",
        "",
        "   mod p                         mod N",
        "   -----                         -----",
        "   Py^2 ------------+               Py^2 ------------+",
        "                    |                                |",
        "                    v                                v",
        "   Px^3 + 7 <-- G=7               Px^3 + G <-- G=Py^2-Px^3",
        "                    |                                |",
        "   split a=4:                      split a=4:",
        "   Py^2-4 = Px^3+3 OK              Py^2-4 = Px^3+(G-4)",
        "                                   (same algebra)",
        "                                                    ",
        "   K unused on p                   K = N - G",
        "                                   Py^2 + K = Px^3",
        "                                   (wrap of -G)",
        "",
        "=" * 72,
    ]

    report = "\n".join(lines) + "\n"
    from pathlib import Path

    out = Path(__file__).resolve().parent / "ARCHIVE" / "p135_K_shell_diagram.txt"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")
    print(f"K = N - G  match_user={K == K_USER}")
    print(f"Py^2 == Px^3 + G (mod N): {(pow(Px,3,N)+G_n)%N == pow(Py,2,N)}")
    print(f"Py^2 + K == Px^3 (mod N): {(pow(Py,2,N)+K)%N == pow(Px,3,N)}")


if __name__ == "__main__":
    main()
