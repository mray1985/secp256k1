#!/usr/bin/env python3
"""Dual-domain wrap tracer for secp256k1 affine arithmetic.

Locked separation:

  coordinates reduce modulo p
  scalars reduce modulo N

This is an *operation ledger* for a chosen affine formula path.
It does not remove key bits. Intermediate quotients are
implementation-path dependent (affine vs Jacobian vs rearranged
equivalents can differ while returning the same final point).

N-wrap is recorded only when scalar provenance (a, b) is known.
You cannot infer N-wrap from coordinates alone.
A coordinate with x >= N is NOT an N-scalar wrap — it is only
a field element in the shelf [N, p).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# secp256k1
P_MOD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N_MOD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Generator (affine)
G_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
G_Y = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (G_X, G_Y)


@dataclass(frozen=True)
class Reduction:
    """v = quotient * modulus + residue, with 0 <= residue < modulus (Python divmod)."""

    raw: int
    quotient: int
    residue: int
    modulus: int
    domain: str  # "p" | "N"

    @property
    def crossed(self) -> bool:
        return self.quotient != 0

    @property
    def wrap_kind(self) -> str:
        q = self.quotient
        if q == 0:
            return "none"
        if q == 1:
            return "upward_once"
        if q == -1:
            return "downward_once"
        if q > 1:
            return "multiple_upward"
        return "multiple_downward"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["crossed"] = self.crossed
        d["wrap_kind"] = self.wrap_kind
        return d


def reduce_with_trace(value: int, modulus: int, *, domain: str) -> Reduction:
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    if domain not in ("p", "N"):
        raise ValueError("domain must be 'p' or 'N'")
    quotient, residue = divmod(value, modulus)
    return Reduction(
        raw=value,
        quotient=quotient,
        residue=residue,
        modulus=modulus,
        domain=domain,
    )


def reduce_p(value: int) -> Reduction:
    return reduce_with_trace(value, P_MOD, domain="p")


def reduce_n(value: int) -> Reduction:
    return reduce_with_trace(value, N_MOD, domain="N")


def negate_point(point: tuple[int, int]) -> tuple[int, int]:
    x, y = point
    return (x % P_MOD, (-y) % P_MOD)


def on_curve(point: tuple[int, int] | None) -> bool:
    if point is None:
        return True  # infinity
    x, y = point
    return (y * y - (x * x * x + 7)) % P_MOD == 0


@dataclass(frozen=True)
class FieldWrapEvent:
    """Signed p-quotients for one affine add/double step.

    For addition of distinct points:
      (q_Δx, q_Δy, q_λ, q_x, q_y)

    For doubling, Δx/Δy are replaced by the doubling numerator/denominator
    reductions (3x² and 2y), still logged under q_dx / q_dy slots.
    """

    q_dx: int
    q_dy: int
    q_lambda: int
    q_x: int
    q_y: int

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (self.q_dx, self.q_dy, self.q_lambda, self.q_x, self.q_y)


def add_points_with_trace(
    point_a: tuple[int, int],
    point_b: tuple[int, int],
) -> dict[str, Any]:
    """Affine point addition/doubling with p-domain wrap ledger.

    Formulas (implementation path — not an intrinsic point label):

      Δx_raw = x2 - x1,  Δy_raw = y2 - y1
      λ = Δy * inv(Δx)  (mod p)   [product logged unreduced]
      x3 from λ² - x1 - x2
      y3 from λ(x1 - x3) - y1
    """
    x1, y1 = point_a[0] % P_MOD, point_a[1] % P_MOD
    x2, y2 = point_b[0] % P_MOD, point_b[1] % P_MOD

    # P + (-P) = O
    if x1 == x2 and (y1 + y2) % P_MOD == 0:
        return {
            "special_case": "point_at_infinity",
            "operation": "addition" if (x1, y1) != (x2, y2) else "doubling_degenerate",
            "result": None,
            "p_wrap_event": None,
            "n_wrap": None,
            "note": "N-wrap not inferable from coordinates alone",
            "result_coordinate_shelf": None,
        }

    if (x1, y1) == (x2, y2):
        # doubling: λ = (3 x1²) / (2 y1)
        numerator = reduce_p(3 * x1 * x1)
        denominator = reduce_p(2 * y1)
        operation = "doubling"
    else:
        numerator = reduce_p(y2 - y1)  # Δy_raw
        denominator = reduce_p(x2 - x1)  # Δx_raw
        operation = "addition"

    if denominator.residue == 0:
        raise ZeroDivisionError("Slope denominator is zero modulo p.")

    inverse = pow(denominator.residue, -1, P_MOD)

    # L = Δy * (Δx)^{-1}  (unreduced product of already-reduced limbs)
    lambda_product = reduce_p(numerator.residue * inverse)
    slope = lambda_product.residue

    x_raw = reduce_p(slope * slope - x1 - x2)
    x3 = x_raw.residue

    y_raw = reduce_p(slope * (x1 - x3) - y1)
    y3 = y_raw.residue

    event = FieldWrapEvent(
        q_dx=denominator.quotient,
        q_dy=numerator.quotient,
        q_lambda=lambda_product.quotient,
        q_x=x_raw.quotient,
        q_y=y_raw.quotient,
    )

    return {
        "special_case": None,
        "operation": operation,
        "formula_path": "affine_secp256k1",
        "numerator": numerator.to_dict(),
        "denominator": denominator.to_dict(),
        "denominator_inverse": inverse,
        "lambda_product": lambda_product.to_dict(),
        "x3_reduction": x_raw.to_dict(),
        "y3_reduction": y_raw.to_dict(),
        "p_wrap_event": {
            "q_dx": event.q_dx,
            "q_dy": event.q_dy,
            "q_lambda": event.q_lambda,
            "q_x": event.q_x,
            "q_y": event.q_y,
            "tuple": list(event.as_tuple()),
        },
        "n_wrap": None,
        "note": (
            "N-wrap omitted: scalar provenance unknown. "
            "Coordinate shelf x>=N is NOT an N-scalar wrap."
        ),
        "result": (x3, y3),
        "result_on_curve": on_curve((x3, y3)),
        "result_coordinate_shelf": {
            "x_ge_N": x3 >= N_MOD,
            "y_ge_N": y3 >= N_MOD,
            "x_in_N_to_p_shelf": N_MOD <= x3 < P_MOD,
            "y_in_N_to_p_shelf": N_MOD <= y3 < P_MOD,
            "x_ge_p": False,  # always false after reduction
            "y_ge_p": False,
        },
    }


def subtract_points_with_trace(
    point_a: tuple[int, int],
    point_b: tuple[int, int],
) -> dict[str, Any]:
    """P - Q = P + (-Q) with p-wrap trace on the addition path."""
    out = add_points_with_trace(point_a, negate_point(point_b))
    out["operation"] = (
        "subtraction_via_negation"
        if out.get("operation") == "addition"
        else out.get("operation")
    )
    out["negated_q"] = negate_point(point_b)
    return out


def scalar_add_with_trace(a: int, b: int) -> Reduction:
    """a + b = q_N * N + r_N. Requires known scalars."""
    return reduce_n(a + b)


def scalar_subtract_with_trace(a: int, b: int) -> Reduction:
    """a - b = q_N * N + r_N. Requires known scalars."""
    return reduce_n(a - b)


def add_with_optional_scalars(
    point_a: tuple[int, int],
    point_b: tuple[int, int],
    *,
    scalar_a: int | None = None,
    scalar_b: int | None = None,
    op: str = "add",
) -> dict[str, Any]:
    """Point op with p-trace; attach N-trace only if both scalars are known."""
    if op == "add":
        out = add_points_with_trace(point_a, point_b)
        if scalar_a is not None and scalar_b is not None:
            nred = scalar_add_with_trace(scalar_a, scalar_b)
            out["n_wrap"] = nred.to_dict()
            out["note"] = (
                "N-wrap from known scalars: P+Q = [a+b mod N]G. "
                "Not recoverable from coordinates alone."
            )
            out["scalar_result_mod_N"] = nred.residue
    elif op == "sub":
        out = subtract_points_with_trace(point_a, point_b)
        if scalar_a is not None and scalar_b is not None:
            nred = scalar_subtract_with_trace(scalar_a, scalar_b)
            out["n_wrap"] = nred.to_dict()
            out["note"] = (
                "N-wrap from known scalars: P-Q = [a-b mod N]G. "
                "Not recoverable from coordinates alone."
            )
            out["scalar_result_mod_N"] = nred.residue
    else:
        raise ValueError("op must be 'add' or 'sub'")
    return out


def scalar_mul_g(k: int) -> tuple[int, int]:
    """Naive double-and-add for demos/tests (not constant-time)."""
    k = k % N_MOD
    if k == 0:
        raise ValueError("infinity not represented as affine pair")
    result: tuple[int, int] | None = None
    addend = G
    while k:
        if k & 1:
            result = addend if result is None else add_points_with_trace(result, addend)["result"]
        addend = add_points_with_trace(addend, addend)["result"]
        k >>= 1
        assert result is None or on_curve(result)
        assert on_curve(addend)
    assert result is not None
    return result


def _self_check() -> list[dict[str, Any]]:
    """Sanity: G+G, G+(2G), shelf vs N-wrap, known-scalar N carry."""
    from ecdsa import SECP256k1

    checks: list[dict[str, Any]] = []
    eg = SECP256k1.generator

    # 1) doubling G matches library
    tr = add_points_with_trace(G, G)
    two_pt = eg * 2
    two_g = (two_pt.x(), two_pt.y())
    checks.append(
        {
            "name": "double_G_matches_ecdsa",
            "pass": tr["result"] == two_g and tr["result_on_curve"],
            "p_wrap_event": tr["p_wrap_event"],
            "n_wrap": tr["n_wrap"],
        }
    )

    # 2) G + 2G = 3G
    three = add_with_optional_scalars(G, two_g, scalar_a=1, scalar_b=2, op="add")
    three_pt = eg * 3
    three_lib = (three_pt.x(), three_pt.y())
    checks.append(
        {
            "name": "G_plus_2G_with_N_trace",
            "pass": three["result"] == three_lib and three["n_wrap"]["quotient"] == 0,
            "p_wrap_event": three["p_wrap_event"],
            "n_wrap": three["n_wrap"],
        }
    )

    # 3) Scalar wrap across N: (N-1) + 2 = 1 mod N, q_N = 1
    n_add = scalar_add_with_trace(N_MOD - 1, 2)
    checks.append(
        {
            "name": "scalar_add_crosses_N",
            "pass": n_add.quotient == 1 and n_add.residue == 1,
            "n_wrap": n_add.to_dict(),
        }
    )

    # 4) Coordinate shelf is not N-wrap: find a point with x >= N if easy,
    #    else document that shelf flag is independent of n_wrap.
    p2 = two_g
    shelf = add_points_with_trace(p2, p2)  # 4G
    checks.append(
        {
            "name": "shelf_flag_independent_of_n_wrap",
            "pass": shelf["n_wrap"] is None and "x_ge_N" in shelf["result_coordinate_shelf"],
            "shelf": shelf["result_coordinate_shelf"],
            "note": "x_ge_N does not imply scalar N-wrap",
        }
    )

    # 5) Subtraction: 3G - G = 2G with N-trace
    sub = add_with_optional_scalars(three_lib, G, scalar_a=3, scalar_b=1, op="sub")
    checks.append(
        {
            "name": "sub_3G_minus_G",
            "pass": sub["result"] == two_g and sub["n_wrap"]["residue"] == 2,
            "p_wrap_event": sub["p_wrap_event"],
            "n_wrap": sub["n_wrap"],
        }
    )

    # 6) Canonical field add/sub quotient sets
    a, b = P_MOD - 5, 10
    s = reduce_p(a + b)
    d = reduce_p(a - b)
    checks.append(
        {
            "name": "field_add_sub_quotient_sets",
            "pass": s.quotient in (0, 1) and d.quotient in (-1, 0),
            "add": s.to_dict(),
            "sub": d.to_dict(),
        }
    )

    return checks


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description="Dual-domain (p / N) wrap tracer")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--demo", action="store_true", help="trace G+G and (N-1)+2 scalars")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "tool": "dual_domain_wrap_tracer",
        "domains": {
            "coordinates": "mod p",
            "scalars": "mod N",
        },
        "warning": (
            "p-wrap quotients are formula-path dependent; "
            "N-wrap requires known scalars; "
            "x>=N is a coordinate shelf, not an N-wrap; "
            "0 verified key bits."
        ),
        "constants": {
            "p_hex": hex(P_MOD),
            "N_hex": hex(N_MOD),
            "N_lt_p": N_MOD < P_MOD,
        },
    }

    run_check = args.self_check or not args.demo
    if run_check:
        checks = _self_check()
        payload["self_check"] = checks
        payload["self_check_pass"] = all(c["pass"] for c in checks)
        for c in checks:
            print(f"  {c['name']}: {'PASS' if c['pass'] else 'FAIL'}")
        print(f"self_check: {'PASS' if payload['self_check_pass'] else 'FAIL'}")

    if args.demo:
        demo = {
            "double_G": add_points_with_trace(G, G),
            "scalar_N_minus_1_plus_2": scalar_add_with_trace(N_MOD - 1, 2).to_dict(),
            "known_scalar_add_1_plus_2": add_with_optional_scalars(
                G, scalar_mul_g(2), scalar_a=1, scalar_b=2, op="add"
            ),
        }
        payload["demo"] = demo
        ev = demo["double_G"]["p_wrap_event"]
        print(f"demo G+G p_wrap_event tuple: {ev['tuple']}")
        print(f"demo scalar (N-1)+2: q_N={demo['scalar_N_minus_1_plus_2']['quotient']}")

    out = args.output
    if out is None:
        out = (
            Path(__file__).resolve().parent
            / "logs"
            / "wrap_tracer"
            / "dual_domain_self_check.json"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_jsonable(payload), indent=2), encoding="utf-8")
    print(f"wrote {out}")
    if payload.get("self_check_pass") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
