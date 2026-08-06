#!/usr/bin/env python3
"""Compare left-5 hash160 duplicate spread pattern: d=1..1000 vs d=1001..2000."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

from ecdsa import SECP256k1, SigningKey

ROOT = Path(__file__).resolve().parent


def hash160_compressed(d: int) -> int:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    x, y = pub[:32], pub[32:]
    comp = (b"\x02" if (y[-1] & 1) == 0 else b"\x03") + x
    h = hashlib.new("ripemd160", hashlib.sha256(comp).digest()).digest()
    return int.from_bytes(h, "big")


def analyze_range(lo: int, hi: int) -> dict:
    left5 = {d: str(hash160_compressed(d))[:5] for d in range(lo, hi + 1)}
    by_pref: dict[str, list[int]] = defaultdict(list)
    for d, p in left5.items():
        by_pref[p].append(d)

    dups = {p: sorted(ds) for p, ds in by_pref.items() if len(ds) > 1}
    spreads: list[int] = []
    rows: list[tuple[str, int, int, int]] = []
    for p, ds in sorted(dups.items()):
        for i in range(len(ds) - 1):
            s = ds[i + 1] - ds[i]
            spreads.append(s)
            rows.append((p, ds[i], ds[i + 1], s))

    left5_ints = [int(left5[d]) for d in range(lo, hi + 1)]
    diffs = [left5_ints[i + 1] - left5_ints[i] for i in range(len(left5_ints) - 1)]
    fd: dict[str, int] = defaultdict(int)
    for d in range(lo, hi + 1):
        fd[left5[d][0]] += 1

    return {
        "lo": lo,
        "hi": hi,
        "n": hi - lo + 1,
        "left5": left5,
        "unique": len(by_pref),
        "dup_prefixes": len(dups),
        "dup_scalars": sum(len(v) for v in dups.values()),
        "spreads": spreads,
        "rows": rows,
        "diff_min": min(diffs),
        "diff_max": max(diffs),
        "diff_mean": sum(diffs) / len(diffs),
        "first_digit": dict(sorted(fd.items())),
        "left5_min": min(left5_ints),
        "left5_max": max(left5_ints),
    }


def bucket(spreads: list[int]) -> dict[str, int]:
    b = {"1-50": 0, "51-100": 0, "101-200": 0, "201-400": 0, "401+": 0}
    for s in spreads:
        if s <= 50:
            b["1-50"] += 1
        elif s <= 100:
            b["51-100"] += 1
        elif s <= 200:
            b["101-200"] += 1
        elif s <= 400:
            b["201-400"] += 1
        else:
            b["401+"] += 1
    return b


def summarize(name: str, r: dict) -> None:
    sp = r["spreads"]
    print(f"=== {name} (d={r['lo']}..{r['hi']}) ===")
    print(f"  unique left5: {r['unique']} / {r['n']}")
    print(f"  duplicate prefixes: {r['dup_prefixes']}  (scalars involved: {r['dup_scalars']})")
    if sp:
        med = sorted(sp)[len(sp) // 2]
        print(f"  spread min/mean/median/max: {min(sp)} / {sum(sp)/len(sp):.1f} / {med} / {max(sp)}")
        print(f"  spread buckets: {bucket(sp)}")
    else:
        print("  no duplicates")
    print(f"  left5 int range: {r['left5_min']} .. {r['left5_max']}")
    print(f"  consecutive left5 diff min/mean/max: {r['diff_min']} / {r['diff_mean']:.1f} / {r['diff_max']}")
    print(f"  first-digit counts: {r['first_digit']}")
    print()


def main() -> None:
    r1 = analyze_range(1, 1000)
    r2 = analyze_range(1001, 2000)

    summarize("BLOCK A", r1)
    summarize("BLOCK B", r2)

    print("=== BLOCK B duplicate detail ===")
    for p, a, b, s in r2["rows"]:
        print(f"  {p}  d={a:4d}, {b:4d}  spread={s:4d}")

    set_a = set(r1["left5"].values())
    set_b = set(r2["left5"].values())
    cross = sorted(set_a & set_b)
    print()
    print(f"Cross-block same left5 (A intersect B): {len(cross)}")
    for p in cross[:20]:
        da = [d for d, v in r1["left5"].items() if v == p]
        db = [d for d, v in r2["left5"].items() if v == p]
        print(f"  {p}  A:{da}  B:{db}  scalar_gap={db[0]-da[0]}")

    out = ROOT / "ARCHIVE" / "secp256k1_hash160_left5_1001_2000.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("# d=1001..2000 left5 hash160_decimal\n")
        for d in range(1001, 2001):
            h = hash160_compressed(d)
            f.write(f"{d}\t{str(h)[:5]}\t{h}\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
