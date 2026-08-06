#!/usr/bin/env python3
"""P160 left5=13260 band-bias test with empirical null + growth profile."""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from puzzle_catalog import load_catalog  # noqa: E402

P160_LEFT5 = 13260
THRESHOLDS = [5, 10, 50, 100]
N_MAX = 20_000
LEFT5_SPACE = 90_000


def hash160_compressed(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    x, y = pub[:32], pub[32:]
    comp = (b"\x02" if (y[-1] & 1) == 0 else b"\x03") + x
    h = hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()
    return int.from_bytes(h, "big")


def build_left5_array(n_max: int) -> list[int]:
    print(f"Building left5[1..{n_max}]...", flush=True)
    arr = [0] * (n_max + 1)
    for d in range(1, n_max + 1):
        arr[d] = int(str(hash160_compressed(d))[:5])
        if d % 5000 == 0:
            print(f"  d={d}", flush=True)
    return arr


def count_near(arr: list[int], lo: int, hi: int, anchor: int, tol: int) -> int:
    return sum(1 for d in range(lo, hi + 1) if abs(arr[d] - anchor) <= tol)


def uniform_expected(n: int, tol: int) -> float:
    return n * (2 * tol + 1) / LEFT5_SPACE


def empirical_expected(arr: list[int], lo: int, hi: int, anchor: int, tol: int) -> float:
    """Fraction of sample within tol of anchor, applied to block size (local rate)."""
    n = hi - lo + 1
    rate = count_near(arr, lo, hi, anchor, tol) / n
    return rate * n  # same as obs for same window; for cross-anchor use global rate


def global_rate(arr: list[int], n_max: int, anchor: int, tol: int) -> float:
    return count_near(arr, 1, n_max, anchor, tol) / n_max


def poisson_tail(obs: int, exp: float) -> float:
    if obs == 0:
        return 1.0
    if exp <= 0:
        return 0.0
    if exp > 50 or obs > 50:
        z = (obs - exp) / math.sqrt(exp)
        return 0.5 * math.erfc(z / math.sqrt(2))
    s = 0.0
    for k in range(obs):
        s += math.exp(-exp) * (exp**k) / math.factorial(k)
    return min(1.0, max(0.0, 1.0 - s))


def main() -> None:
    cat = load_catalog()
    p160_h = int.from_bytes(
        hashlib.new(
            "ripemd160",
            hashlib.sha256(bytes.fromhex(cat[160].public_key)).digest(),
        ).digest(),
        "big",
    )
    print("P160 hash160:", p160_h)
    print("P160 left5:", P160_LEFT5)
    print()

    arr = build_left5_array(N_MAX)

    # --- uniform null cumulative ---
    print("=== CUMULATIVE d=1..20000 vs UNIFORM null ===")
    for tol in THRESHOLDS:
        obs = count_near(arr, 1, N_MAX, P160_LEFT5, tol)
        exp = uniform_expected(N_MAX, tol)
        print(
            f"  tol<={tol:3d}: obs={obs:3d}  uniform_exp={exp:6.2f}  "
            f"ratio={obs/exp:.2f}x  p~={poisson_tail(obs, exp):.2e}"
        )

    # --- empirical: average rate at 100 random anchors ---
    print()
    print("=== CONTROL: mean obs for 100 random anchors (same d=1..20000) ===")
    import random

    random.seed(42)
    anchors = random.sample(range(10000, 100000), 100)
    for tol in THRESHOLDS:
        counts = [count_near(arr, 1, N_MAX, a, tol) for a in anchors]
        mean_c = sum(counts) / len(counts)
        obs = count_near(arr, 1, N_MAX, P160_LEFT5, tol)
        print(
            f"  tol<={tol:3d}: P160_obs={obs:3d}  random_mean={mean_c:.1f}  "
            f"P160/rand={obs/mean_c if mean_c else 0:.2f}x"
        )

    # fixed controls
    controls = [
        ("d=1 left5", arr[1]),
        ("d=1000 left5", arr[1000]),
        ("mirror 86739", 99999 - P160_LEFT5 + 10000),  # not real mirror
        ("13xxx mid", 13500),
        ("66xxx d1 class", 66863),
    ]
    print()
    print("=== FIXED ANCHOR CONTROLS tol<=50 ===")
    for name, anchor in controls:
        obs = count_near(arr, 1, N_MAX, anchor, 50)
        exp_u = uniform_expected(N_MAX, 50)
        print(f"  {name:16s} anchor={anchor:5d}  obs={obs:3d}  uniform_exp={exp_u:.2f}  ratio={obs/exp_u:.2f}x")

    # --- growth: per 1000 block rate ---
    print()
    print("=== RATE per 1000-block (tol<=50): obs, uniform_exp, ratio ===")
    for start in range(1, N_MAX + 1, 1000):
        end = min(start + 999, N_MAX)
        n = end - start + 1
        obs = count_near(arr, start, end, P160_LEFT5, 50)
        exp = uniform_expected(n, 50)
        print(f"  d={start:5d}-{end:5d}: obs={obs:2d} exp={exp:.2f} ratio={obs/exp if exp else 0:.2f}x")

    # --- nearest hits ---
    print()
    print("=== NEAREST 15 scalars to P160 left5 (d=1..20000) ===")
    nearest = sorted(
        ((d, arr[d], abs(arr[d] - P160_LEFT5)) for d in range(1, N_MAX + 1)),
        key=lambda t: (t[2], t[0]),
    )[:15]
    for d, l5, dist in nearest:
        print(f"  d={d:5d}  left5={l5}  dist={dist}")

    # --- does ratio grow with d? linear regression on block ratios ---
    blocks = []
    for start in range(1, N_MAX + 1, 1000):
        end = min(start + 999, N_MAX)
        n = end - start + 1
        obs = count_near(arr, start, end, P160_LEFT5, 50)
        exp = uniform_expected(n, 50)
        blocks.append((start, obs / exp if exp else 0))
    ratios = [b[1] for b in blocks]
    print()
    print(f"=== GROWTH: block ratios tol<=50 min/mean/max = {min(ratios):.2f}/{sum(ratios)/len(ratios):.2f}/{max(ratios):.2f}")
    first5 = sum(ratios[:5]) / 5
    last5 = sum(ratios[-5:]) / 5
    print(f"  first 5 blocks avg ratio={first5:.2f}  last 5 blocks avg ratio={last5:.2f}")
    if last5 > first5 * 1.5:
        print("  -> ratio INCREASES with d (possible band steering)")
    elif abs(last5 - first5) < 1.0:
        print("  -> ratio FLAT with d (no steering; static density bias)")
    else:
        print("  -> ratio mixed; no clear d-growth signal")


if __name__ == "__main__":
    main()
