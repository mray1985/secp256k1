"""Parse integer.x/N.y/N decimal forms and compare to page/d."""
from decimal import Decimal, getcontext

getcontext().prec = 250

N = int(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
Nd = Decimal(N)

from puzzle_keys_53125 import parse_53125
from puzzle_echo_ratio_scan import PAGE


def fracs(x: int, y: int) -> tuple[str, str, int]:
    xN = Decimal(x) / Nd
    yN = Decimal(y) / Nd
    fx = format(xN, "f").split(".")[1]
    fy = format(yN, "f").split(".")[1]
    qi = int(xN)
    return fx, fy, qi


def forms(x: int, y: int) -> dict[str, str]:
    fx, fy, qi = fracs(x, y)
    B = x * N + y
    qB, _ = divmod(B, N)
    return {
        "0.fx+fy": f"0.{fx}{fy}",
        "0.fx.fy": f"0.{fx}.{fy}",
        "qi.fx+fy": f"{qi}.{fx}{fy}",
        "qi.fx.fy": f"{qi}.{fx}.{fy}",
        "Px.fy (B/N)": f"{x}.{fy}",
        "Px.fx.fy": f"{x}.{fx}.{fy}",
        "B/N": format(Decimal(B) / Nd, "f"),
    }


def show(n: int, x: int, y: int, pg: int | None, d: int | None) -> None:
    print(f"\n=== P{n} ===")
    if pg:
        print(f"page={pg} ({len(str(pg))} digits)")
    if d:
        print(f"d={d} ({len(str(d))} digits)")
    for name, s in forms(x, y).items():
        print(f"  [{name}]")
        print(f"    top41: {s[:41]}")
        print(f"    42-82: {s[41:82]}")


keys = parse_53125()
for n in [120, 125, 130]:
    k = keys[n]
    show(n, k.px, k.py, PAGE[n], k.d)

Px = 9210836494447108270027136741376870869791784014198948301625976867708124077590
Py = 46351506704828816385393879789131775975171267756561783641521771795450741674800
show(135, Px, Py, None, None)
LO, HI = 2**134, 2**135 - 1
print(f"\nP135 page band: [{LO//60}, {HI//60}]")
