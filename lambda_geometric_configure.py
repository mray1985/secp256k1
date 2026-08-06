#!/usr/bin/env python3
"""Configure lambda two ways from public Px, rx, Py, ry — and relate to P = d*G.

Layer A (bridge, Complexity_Simplified):
  Lambda_x = Px * rx^-1 mod p
  lambda_y = Py * ry^-1 mod p

Layer B (geometric doubling slope — "lambda of the face"):
  lam_double(P) = (3*Px^2) * (2*Py)^-1 mod p
  At G: lam_1 transitions face 1G -> 2G

P = d*G is the EC identity (solved check). Geometric lambda does NOT equal Px/rx;
it is the group-law slope at that face, not a discrete-log ratio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ECDLP"))

from hashkeys_rsz import N, PUZZLE_RSZ, p, recover_r_point_from_sig, y_roots_from_x
from puzzle_keys_53125 import parse_53125

try:
    from ecdsa import SECP256k1, SigningKey

    def pubkey_from_scalar(d: int) -> tuple[int, int]:
        sk = SigningKey.from_secret_exponent(d % N, curve=SECP256k1)
        pt = sk.get_verifying_key().pubkey.point
        return int(pt.x()), int(pt.y())

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False
    pubkey_from_scalar = None  # type: ignore

# Complexity_Simplified triples (epsilon row = index 2 for P135 target Px3)
DEFAULT_PX = [
    51866120889717641461810659005716431188799022756838843706514074509901265629059,
    54715131853151445691733189261594605794679177894602772031317532630299444965014,
    9210836494447108270027136741376870869791784014198948301625976867708124077590,
]
DEFAULT_RX = [
    114930704126154877082883546730544079307369404418439078397954295509919169851219,
    90653255469745952335985143920649543885181555095025199315947044135806663628368,
    26000218878731561428273279366182192513989009817816850365013828370091835863739,
]
DEFAULT_PY = 46351506704828816385393879789131775975171267756561783641521771795450741674800
DEFAULT_RY = 49714739208247555872780528359092797866261457510155690641636464864972500227644

OUT_JSON = ROOT / "lambda_geometric_configure_report.json"
OUT_TXT = ROOT / "02_Research" / "notes" / "Complexity_Simplified_lambda_geometric_block.txt"
ROOT_TXT = ROOT / "Complexity_Simplified_p_lambda_geometric_append.txt"

# Complexity_Simplified slot 2 = secp256k1 generator x
GX_GEN = 55066263022277343669578718895168534326250603453777594175500187360389116729240
BRIDGE_LAMBDA_P135 = 97451685862885086182458552040892158509924235661624603229050850812487253689501
LAM_1_EXPECTED = 91914383230618135761690975197207778399550061809281766160147273830617914855857


def y_from_pubkey(x: int, compressed: str) -> int:
    yp, yn = y_roots_from_x(x)
    return yp if compressed.startswith("02") else yn


def y_even(x: int) -> int:
    yp, yn = y_roots_from_x(x)
    return yp if yp % 2 == 0 else yn


def lam_double(x: int, y: int) -> int:
    return (3 * x * x * pow(2 * y, -1, p)) % p


def double_point(x: int, y: int, lam: int) -> tuple[int, int]:
    x2 = (lam * lam - 2 * x) % p
    y2 = (lam * (x - x2) - y) % p
    return x2, y2


def bridge_lambda_x(px: int, rx: int) -> int:
    return (px * pow(rx, -1, p)) % p


def bridge_lambda_y(py: int, ry: int) -> int:
    return (py * pow(ry, -1, p)) % p


def complexity_row(px: int) -> int | None:
    try:
        return DEFAULT_PX.index(px)
    except ValueError:
        return None


def configure_puzzle(n: int, keys: dict) -> dict | None:
    if n not in PUZZLE_RSZ:
        return None
    rsz = PUZZLE_RSZ[n]
    px = int(rsz.pub_compressed[2:], 16)
    py = y_from_pubkey(px, rsz.pub_compressed)
    r_pt = recover_r_point_from_sig(rsz.r)
    if not r_pt:
        return None
    rx_sig, ry_sig = r_pt

    row = complexity_row(px)
    if row is not None:
        rx_bridge = DEFAULT_RX[row]
        ry_bridge = y_even(DEFAULT_RX[row]) if row != 2 else DEFAULT_RY
        py_bridge = DEFAULT_PY if row == 2 else py
        bridge_source = f"complexity_row_{row}_rx"
    else:
        rx_bridge, ry_bridge, py_bridge = rx_sig, ry_sig, py
        bridge_source = "hashkeys_r_sig"

    gx, gy = GX_GEN, y_even(GX_GEN)
    lam_g = lam_double(gx, gy)
    lam_p = lam_double(px, py)
    lam_r_sig = lam_double(rx_sig, ry_sig)
    lam_x_bridge = bridge_lambda_x(px, rx_bridge)
    lam_x_sig = bridge_lambda_x(px, rx_sig)
    lam_y_bridge = bridge_lambda_y(py_bridge, ry_bridge)

    row = {
        "puzzle": n,
        "public": {
            "Px": px,
            "Py": py,
            "rx_sig": rx_sig,
            "ry_sig": ry_sig,
            "rx_bridge": rx_bridge,
            "ry_bridge": ry_bridge,
            "r_sig": rsz.r,
            "Gx": gx,
            "Gy": gy,
        },
        "bridge": {
            "source": bridge_source,
            "Lambda_x_Px_over_rx": lam_x_bridge,
            "Lambda_x_Px_over_r_sig": lam_x_sig,
            "lambda_y_Py_over_ry": lam_y_bridge,
            "Lambda_x_eq_lambda_y": lam_x_bridge == lam_y_bridge,
            "is_complexity_Lambda": lam_x_bridge == BRIDGE_LAMBDA_P135 if n == 135 else None,
        },
        "geometric": {
            "lam_1_at_G": lam_g,
            "lam_double_at_P": lam_p,
            "lam_double_at_R_sig": lam_r_sig,
            "lam_1_matches_expected": lam_g == LAM_1_EXPECTED,
        },
        "compare": {
            "lam_g_eq_bridge_Lambda": lam_g == lam_x_bridge,
            "lam_p_eq_bridge_Lambda": lam_p == lam_x_bridge,
            "lam_p_eq_lam_g_mod_p": (lam_p * pow(lam_g, -1, p)) % p,
            "bridge_sig_is_Lambda1_cube_root": lam_x_sig == 37643865109859786597771480714430795265672370613336709366230557028248558914645,
        },
        "Px_eq_dG": None,
        "d": None,
        "band": {"lo": 1 << (n - 1), "hi": (1 << n) - 1},
    }

    if n in keys and keys[n].d > 0 and _HAS_ECDSA:
        d = keys[n].d
        dpx, dpy = pubkey_from_scalar(d)
        row["d"] = d
        row["Px_eq_dG"] = dpx == px and dpy == py
        row["dG"] = {"x": dpx, "y": dpy}
        row["ec_identity"] = f"P = {d} * G_gen"

    # doubling chain at G
    x2, y2 = double_point(gx, gy, lam_g)
    lam_2 = lam_double(x2, y2)
    x4, y4 = double_point(x2, y2, lam_2)
    row["chain_at_G"] = {
        "G": [gx, gy],
        "2G": [x2, y2],
        "4G": [x4, y4],
        "lam_1": lam_g,
        "lam_at_2G": lam_2,
    }

    return row


def format_block(rows: list[dict]) -> str:
    lines = [
        "",
        "=" * 72,
        "GEOMETRIC LAMBDA CONFIGURATION (append)",
        "Two layers — do not conflate:",
        "  BRIDGE:  Lambda = Px/rx,  lambda_y = Py/ry  (Complexity_Simplified collapse)",
        "  GEOMETRIC: lam_1 = (3Gx^2)(2Gy)^-1 at G; lam_P = (3Px^2)(2Py)^-1 at P",
        "  EC IDENTITY: P = d*G  (face of body d); geometric lam is slope G->2G or P->2P",
        "=" * 72,
        "",
        f"G_gen (Gx2) = {GX_GEN}",
        f"Gy (even)   = {y_even(GX_GEN)}",
        f"lam_1 (1G->2G) = {LAM_1_EXPECTED}",
        "",
    ]
    for row in rows:
        n = row["puzzle"]
        lines.append(f"--- Puzzle {n} ---")
        lines.append(f"  BRIDGE Lambda_x = Px/rx_bridge = {row['bridge']['Lambda_x_Px_over_rx']}  ({row['bridge']['source']})")
        lines.append(f"  BRIDGE Px/r_sig only = {row['bridge']['Lambda_x_Px_over_r_sig']}")
        lines.append(f"  BRIDGE lambda_y = Py/ry = {row['bridge']['lambda_y_Py_over_ry']}")
        lines.append(f"  GEOM lam_1 at G (1G->2G) = {row['geometric']['lam_1_at_G']}")
        lines.append(f"  GEOM lam_double(P)     = {row['geometric']['lam_double_at_P']}")
        lines.append(f"  lam_P == bridge Lambda? {row['compare']['lam_p_eq_bridge_Lambda']}")
        lines.append(f"  lam_1 == bridge Lambda? {row['compare']['lam_g_eq_bridge_Lambda']}")
        if row.get("ec_identity"):
            lines.append(f"  EC: {row['ec_identity']}  verified={row['Px_eq_dG']}")
        lines.append("")
    p135 = next((r for r in rows if r["puzzle"] == 135), None)
    if p135:
        b = p135["bridge"]["Lambda_x_Px_over_rx"]
        bs = p135["bridge"]["Lambda_x_Px_over_r_sig"]
        lines.append("P135 anchor:")
        lines.append(f"  Complexity Lambda (Px3/rx3) = {BRIDGE_LAMBDA_P135}")
        lines.append(f"  recomputed rx_bridge       = {b}  match={b == BRIDGE_LAMBDA_P135}")
        lines.append(f"  Px/r_sig alone             = {bs}  (= Lambda1 cube-root branch, NOT Lambda)")
        lines.append(f"  lam_1 at G                 = {LAM_1_EXPECTED}")
        lines.append("  Three distinct lambdas: lam_1 (doubling), Lambda (bridge), Lambda1 (Px/rx2)")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    keys = parse_53125()
    puzzles = sorted(PUZZLE_RSZ)
    rows = [configure_puzzle(n, keys) for n in puzzles]
    rows = [r for r in rows if r]

    report = {
        "title": "Lambda configured: bridge (Px/rx) vs geometric (doubling slope)",
        "facts": {
            "G_gen": GX_GEN,
            "lam_1_expected": LAM_1_EXPECTED,
            "bridge_Lambda_P135": BRIDGE_LAMBDA_P135,
            "puzzle_count": len(rows),
        },
        "key_point": (
            "Px = d*G means pubkey (Px,Py) is the elliptic-curve point for scalar d times generator. "
            "Bridge Lambda = Px/rx ratios two faces (P and R). "
            "Geometric lam_P is the doubling slope at face P (P -> 2P), not d and not Px/rx."
        ),
        "aggregate": {
            "lam_p_never_eq_bridge": sum(1 for r in rows if not r["compare"]["lam_p_eq_bridge_Lambda"]),
            "lam_g_never_eq_bridge": sum(1 for r in rows if not r["compare"]["lam_g_eq_bridge_Lambda"]),
            "Px_eq_dG_verified": sum(1 for r in rows if r.get("Px_eq_dG")),
            "solved_with_d": sum(1 for r in rows if r.get("d")),
        },
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    block = format_block(rows)
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text(block, encoding="utf-8")
    ROOT_TXT.write_text(block, encoding="utf-8")

    print(block)
    print(f"JSON: {OUT_JSON}")
    print(f"TXT:  {OUT_TXT}")


if __name__ == "__main__":
    main()
