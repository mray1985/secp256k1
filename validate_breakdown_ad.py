#!/usr/bin/env python3
import re
from pathlib import Path

D = {
    1: 1, 2: 3, 3: 7, 4: 8, 5: 21, 6: 49, 7: 76, 8: 224, 9: 467, 10: 514,
    11: 1155, 12: 2683, 13: 5216, 14: 10544, 15: 26867, 16: 51510, 17: 95823,
    18: 198669, 19: 357535, 20: 863317, 21: 1811764, 22: 3007503, 23: 5598802,
    24: 14428676, 25: 33185509, 26: 54538862, 27: 111949941, 28: 227634408,
    29: 400708894, 30: 1033162084, 31: 2102388551, 32: 3093472814,
    33: 7137437912, 34: 14133072157,
}
V2N = {v: n for n, v in D.items()}
OP_RE = re.compile(r"([AD])\((\d+)\)")
ARITH = re.compile(r"^(\d+)\s*=\s*(.+)$")


def val(op: str, m: int) -> int:
    return D[m] if op == "A" else 2 * D[m]


def load_records(path: Path) -> list[dict]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    records: list[dict] = []
    i = 0
    while i < len(lines):
        m = ARITH.match(lines[i])
        if not m:
            i += 1
            continue
        target = int(m.group(1))
        if i + 1 < len(lines) and OP_RE.search(lines[i + 1]):
            ad = lines[i + 1]
            ops = [(g, int(idx)) for g, idx in OP_RE.findall(ad)]
            i += 2
            records.append({"n": V2N.get(target), "target": target, "ad": ad, "ops": ops})
        else:
            i += 1
    return sorted([r for r in records if r["n"]], key=lambda x: x["n"])


def main() -> None:
    path = Path(r"F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN.txt")
    records = load_records(path)
    prev_end: str | None = None
    for r in records:
        n, ops, ad = r["n"], r["ops"], r["ad"]
        issues: list[str] = []
        for j in range(1, len(ops)):
            if ops[j][0] == ops[j - 1][0]:
                issues.append(f"AA/DD at {j}: {ops[j-1]} then {ops[j]}")
        if prev_end and ops[0][0] == prev_end:
            issues.append(f"cross: starts {ops[0][0]} after prev ended {prev_end}")
        s = sum(val(o, m) for o, m in ops)
        if s != r["target"]:
            issues.append(f"sum {s} != {r['target']} (delta {r['target'] - s})")
        tag = "OK" if not issues else "BAD"
        print(f"P{n:2d} {tag}  start={ops[0][0]} end={ops[-1][0]}  sum={s}")
        for iss in issues:
            print(f"     {iss}")
            if "AA/DD" in iss or "cross" in iss:
                print(f"     AD: {ad}")
        prev_end = ops[-1][0] if ops else prev_end


if __name__ == "__main__":
    main()
