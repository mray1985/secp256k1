#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import math
from decimal import Decimal, ROUND_FLOOR, getcontext
from datetime import datetime, timezone, timedelta

# Optional packages
try:
    import base58 as pybase58
except ImportError:
    pybase58 = None

try:
    import gmpy2
except ImportError:
    gmpy2 = None

# ----------------------------
# Fixed inputs from the prompt
# ----------------------------
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
E_LITERAL_STR = "2.718281828459045"
ADDRESS = "16RGFo6y25rW5Lw7gEaBwBwDmb2MubHiyj"
R = 9210836494447108270027136741376870869791784014198948301625976867708124077590

LAMBDAS = [
    18550647013200406789286060994475703560416436121766183371493072993703432094758,
    36793031382526386630822426321733144812287525987490732260894675548311548513972,
    60448410841589402003462497692479059480133602169817988750217414599503180885607,
]

# Experimental checksum branch from earlier exploration
EXPERIMENTAL_FULL_HEX = "0DDF227D"
EXPERIMENTAL_SUFFIX_HEX = "227D"
EXPERIMENTAL_UNIT_SCALAR = 227  # "227D" as 227 with unit symbol D

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


# ----------------------------
# Base58 helpers
# ----------------------------
def b58decode_raw(s: str) -> bytes:
    if pybase58 is not None:
        return pybase58.b58decode(s)

    n = 0
    for ch in s:
        n = n * 58 + ALPHABET.index(ch)
    leading = len(s) - len(s.lstrip("1"))
    payload = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * leading + payload


def b58encode_raw(data: bytes) -> str:
    if pybase58 is not None:
        out = pybase58.b58encode(data)
        return out.decode() if isinstance(out, bytes) else out

    n = int.from_bytes(data, "big")
    chars = []
    while n > 0:
        n, rem = divmod(n, 58)
        chars.append(ALPHABET[rem])
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + ("".join(reversed(chars)) if chars else "")


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


# ----------------------------
# Formatting helpers
# ----------------------------
def hex_of(data: bytes) -> str:
    return data.hex()

def escaped_bytes(data: bytes) -> str:
    parts = []
    for b in data:
        if 32 <= b <= 126:
            parts.append(chr(b))
        else:
            parts.append(f"\\x{b:02x}")
    return "".join(parts)

def utc_from_timestamp(value: int) -> str:
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    except Exception as exc:
        return f"<timestamp conversion failed: {exc}>"

def invert_mod(x: int, mod: int) -> int:
    if math.gcd(x, mod) != 1:
        raise ValueError(f"{x} has no inverse modulo N")
    if gmpy2 is not None:
        return int(gmpy2.invert(gmpy2.mpz(x), gmpy2.mpz(mod)))
    return pow(x, -1, mod)

def resonance_fraction(date_modulation: int, time_phase_dec: Decimal) -> Decimal:
    return (Decimal(date_modulation) / time_phase_dec) % 1

def wrap_distance(frac: Decimal) -> Decimal:
    return min(frac, Decimal(1) - frac)


# ----------------------------
# Main computations
# ----------------------------
def decode_address(address: str) -> dict:
    decoded = b58decode_raw(address)
    if len(decoded) < 5:
        raise ValueError("Decoded Base58 data is too short to contain version/payload/checksum")

    version = decoded[:1]
    payload = decoded[1:-4]
    extracted_checksum = decoded[-4:]
    recomputed_checksum = sha256d(decoded[:-4])[:4]
    return {
        "decoded": decoded,
        "version": version,
        "payload": payload,
        "extracted_checksum": extracted_checksum,
        "recomputed_checksum": recomputed_checksum,
        "is_valid_base58check": extracted_checksum == recomputed_checksum,
    }

def checksum_interpretations(raw_checksum: bytes) -> dict:
    actual_hex = raw_checksum.hex().upper()
    actual_int = int.from_bytes(raw_checksum, "big")

    exp_full_bytes = bytes.fromhex(EXPERIMENTAL_FULL_HEX)
    exp_full_int = int.from_bytes(exp_full_bytes, "big")

    exp_suffix_bytes = bytes.fromhex(EXPERIMENTAL_SUFFIX_HEX)
    exp_suffix_int = int.from_bytes(exp_suffix_bytes, "big")

    return {
        "actual": {
            "hex": actual_hex,
            "int": actual_int,
            "base58_raw": b58encode_raw(raw_checksum),
            "bytes_escaped": escaped_bytes(raw_checksum),
            "timestamp_utc": utc_from_timestamp(actual_int),
        },
        "experimental_full": {
            "hex": EXPERIMENTAL_FULL_HEX,
            "int": exp_full_int,
            "base58_raw": b58encode_raw(exp_full_bytes),
            "bytes_escaped": escaped_bytes(exp_full_bytes),
            "timestamp_utc": utc_from_timestamp(exp_full_int),
        },
        "experimental_suffix_bytes": {
            "hex": EXPERIMENTAL_SUFFIX_HEX,
            "int": exp_suffix_int,
            "base58_raw": b58encode_raw(exp_suffix_bytes),
            "bytes_escaped": escaped_bytes(exp_suffix_bytes),
            "timestamp_utc": utc_from_timestamp(exp_suffix_int),
        },
        "experimental_unit_scalar": {
            "scalar": EXPERIMENTAL_UNIT_SCALAR,
            "days_seconds": EXPERIMENTAL_UNIT_SCALAR * 24 * 60 * 60,
            "days_hours": EXPERIMENTAL_UNIT_SCALAR * 24,
            "days_weeks": EXPERIMENTAL_UNIT_SCALAR / 7,
            "circle_radius": EXPERIMENTAL_UNIT_SCALAR / 2,
            "circle_circumference_formula": f"{EXPERIMENTAL_UNIT_SCALAR}π",
            "circle_area_formula": f"{EXPERIMENTAL_UNIT_SCALAR**2}π/4",
            "sphere_surface_formula": f"{EXPERIMENTAL_UNIT_SCALAR**2}π",
            "sphere_volume_formula": f"{EXPERIMENTAL_UNIT_SCALAR**3}π/6",
            "labels": ["days", "diameter", "Delisle", "debye", "darcy"],
        },
    }

def build_time_phases(e_scale: int = 80) -> dict:
    getcontext().prec = max(120, e_scale + 50)

    # Python float path exactly as written in ordinary Python code
    e_float = float(E_LITERAL_STR)
    time_phase_float = R * e_float

    # Decimal path using the literal string as exact decimal digits
    e_decimal_literal = Decimal(E_LITERAL_STR)
    time_phase_decimal_literal = Decimal(R) * e_decimal_literal

    # Higher-precision rational path: floor(e * 10^k) / 10^k
    e_true = Decimal(1).exp()
    scale = Decimal(10) ** e_scale
    e_scaled_num = int((e_true * scale).to_integral_value(rounding=ROUND_FLOOR))
    e_scaled_den = 10 ** e_scale
    time_phase_scaled = Decimal(R * e_scaled_num) / Decimal(e_scaled_den)

    return {
        "float_literal": {
            "E_repr": repr(e_float),
            "time_phase": time_phase_float,
        },
        "decimal_literal": {
            "E_repr": str(e_decimal_literal),
            "time_phase": time_phase_decimal_literal,
        },
        "scaled_true_e": {
            "e_scale": e_scale,
            "E_num": e_scaled_num,
            "E_den": e_scaled_den,
            "time_phase": time_phase_scaled,
        },
    }

def build_modular_checksum_scalars(actual_checksum_int: int) -> dict:
    inv1169 = invert_mod(1169, N)
    inv1406 = invert_mod(1406, N)

    c_ratio_24_1169 = (24 * inv1169) % N
    c_ratio_6_1406 = (6 * inv1406) % N

    return {
        "address_extracted_checksum": actual_checksum_int,
        "candidate_full_0x0DDF227D": int(EXPERIMENTAL_FULL_HEX, 16),
        "ratio_24_over_1169_modN": c_ratio_24_1169,
        "ratio_6_over_1406_modN": c_ratio_6_1406,
        "verification": {
            "gcd(1169, N)": math.gcd(1169, N),
            "gcd(1406, N)": math.gcd(1406, N),
            "inv1169": inv1169,
            "inv1406": inv1406,
            "1169 * ratio_24_over_1169_modN mod N": (1169 * c_ratio_24_1169) % N,
            "1406 * ratio_6_over_1406_modN mod N": (1406 * c_ratio_6_1406) % N,
        },
    }

def build_t_micro(checksum_scalars: dict) -> dict:
    out = {}
    for name, scalar in checksum_scalars.items():
        if name == "verification":
            continue
        out[name] = (R * scalar) % N
    return out

def lambda_resonances(actual_checksum_int: int, time_phases: dict) -> dict:
    date_modulations = [(L * actual_checksum_int) % N for L in LAMBDAS]

    result = {
        "date_modulations": date_modulations,
        "float_literal": [],
        "decimal_literal": [],
        "scaled_true_e": [],
    }

    tp_float = time_phases["float_literal"]["time_phase"]
    tp_dec = time_phases["decimal_literal"]["time_phase"]
    tp_scaled = time_phases["scaled_true_e"]["time_phase"]

    for dm in date_modulations:
        frac_float = (dm / tp_float) % 1
        frac_dec = resonance_fraction(dm, tp_dec)
        frac_scaled = resonance_fraction(dm, tp_scaled)

        result["float_literal"].append(frac_float)
        result["decimal_literal"].append(frac_dec)
        result["scaled_true_e"].append(frac_scaled)

    return result

def maybe_plot(resonances_scaled: list[Decimal], path: str = "resonance_plot.png") -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] matplotlib not installed; skipping plot")
        return

    labels = [f"Lambda_{i}" for i in range(1, len(resonances_scaled) + 1)]
    values = [float(x) for x in resonances_scaled]

    plt.figure(figsize=(8, 4))
    plt.bar(labels, values)
    plt.ylim(0, 1)
    plt.ylabel("Resonance fraction")
    plt.title("Checksum-date / r·E resonance")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    print(f"[+] Saved plot: {path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Checksum-as-date and r·E-as-time model")
    parser.add_argument("--e-scale", type=int, default=80, help="Digits for scaled true-e rational path")
    parser.add_argument("--plot", action="store_true", help="Save a matplotlib resonance chart")
    args = parser.parse_args()

    addr = decode_address(ADDRESS)
    checks = checksum_interpretations(addr["extracted_checksum"])
    phases = build_time_phases(e_scale=args.e_scale)
    c_scalars = build_modular_checksum_scalars(checks["actual"]["int"])
    t_micro = build_t_micro(c_scalars)
    lamb = lambda_resonances(checks["actual"]["int"], phases)

    print("\n=== ADDRESS DECODE ===")
    print("decoded_hex              =", hex_of(addr["decoded"]))
    print("version                  =", hex_of(addr["version"]))
    print("payload_hash160          =", hex_of(addr["payload"]))
    print("extracted_checksum       =", hex_of(addr["extracted_checksum"]))
    print("recomputed_checksum      =", hex_of(addr["recomputed_checksum"]))
    print("is_valid_base58check     =", addr["is_valid_base58check"])

    print("\n=== CHECKSUM INTERPRETATIONS ===")
    for key, value in checks.items():
        print(f"\n[{key}]")
        for k, v in value.items():
            print(f"  {k:24} = {v}")

    print("\n=== TIME PHASES ===")
    print("[float_literal]")
    print("  E_repr                  =", phases["float_literal"]["E_repr"])
    print("  time_phase              =", format(phases["float_literal"]["time_phase"], ".17e"))

    print("\n[decimal_literal]")
    print("  E_repr                  =", phases["decimal_literal"]["E_repr"])
    print("  time_phase              =", phases["decimal_literal"]["time_phase"])

    print("\n[scaled_true_e]")
    print("  e_scale                 =", phases["scaled_true_e"]["e_scale"])
    print("  E_num                   =", phases["scaled_true_e"]["E_num"])
    print("  E_den                   =", phases["scaled_true_e"]["E_den"])
    print("  time_phase              =", phases["scaled_true_e"]["time_phase"])

    print("\n=== MODULAR CHECKSUM SCALARS ===")
    for key, value in c_scalars.items():
        if key == "verification":
            continue
        print(f"  {key:28} = {value}")

    print("\n=== MODULAR INVERSE CHECKS ===")
    for key, value in c_scalars["verification"].items():
        print(f"  {key:28} = {value}")

    print("\n=== T_micro = (r * C_checksum) mod N ===")
    for key, value in t_micro.items():
        print(f"  {key:28} = {value}")

    print("\n=== LAMBDA DATE MODULATIONS ===")
    for i, dm in enumerate(lamb["date_modulations"], 1):
        print(f"  Lambda_{i}_date_modulation      = {dm}")

    print("\n=== RESONANCES ===")
    for i in range(3):
        frac_scaled = lamb["scaled_true_e"][i]
        print(f"  Lambda_{i+1}_float              = {lamb['float_literal'][i]!r}")
        print(f"  Lambda_{i+1}_decimal_literal    = {lamb['decimal_literal'][i]}")
        print(f"  Lambda_{i+1}_scaled_true_e      = {frac_scaled}")
        print(f"  Lambda_{i+1}_wrap_distance      = {wrap_distance(frac_scaled)}")

    if args.plot:
        maybe_plot(lamb["scaled_true_e"])

if __name__ == "__main__":
    main()
