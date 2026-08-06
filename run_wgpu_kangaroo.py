#!/usr/bin/env python3
"""Run kangaroo_wgpu on Puzzle 135 candidate ranges sequentially.

Usage:
  python run_wgpu_kangaroo.py                    # run 2^65 candidates from 1..806
  python run_wgpu_kangaroo.py --start 10 --end 20 # run a slice
  python run_wgpu_kangaroo.py --bits 68           # use 2^68 candidates
"""

import subprocess, sys, time, re, csv, json
from pathlib import Path

KANGAROO = Path(r"C:\Users\mitch\Desktop\secp256k1\kangaroo_wgpu\target\release\kangaroo.exe")
ROOT = Path(r"C:\Users\mitch\Desktop\secp256k1")
OUT = ROOT / "wgpu_kangaroo_results"
OUT.mkdir(exist_ok=True)

PUBKEY = "02145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16"

def load_candidates(bits: int) -> list[dict]:
    tsv_path = ROOT / f"135kanga_2p{bits}_candidates.tsv"
    results = []
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            idx = int(row["idx"])
            # Kangaroo wgpu uses --start and --range (range in bits)
            lo_hex = row["lo_hex"].strip().upper()
            lo_int = int(lo_hex, 16)
            width_bits = int(row["width_bits"])
            results.append({
                "idx": idx,
                "label": row["label"],
                "start_hex": lo_hex,
                "start_int": lo_int,
                "range_bits": width_bits,
                "center_int": int(row["center_hex"], 16),
            })
    return results

def run_kangaroo(candidate: dict, timeout_min: int = 1440) -> str | None:
    """Run kangaroo_wgpu on a single candidate. Returns the private key hex if found."""
    start_hex = candidate["start_hex"]
    rbits = candidate["range_bits"]
    label = candidate["label"]
    idx = candidate["idx"]
    out_file = OUT / f"candidate_{idx:04d}_{label}.txt"

    if out_file.exists():
        content = out_file.read_text().strip()
        if content and not content.startswith("Not found"):
            return content

    cmd = [
        str(KANGAROO),
        "--pubkey", PUBKEY,
        "--start", start_hex,
        "--range", str(rbits),
        "--output", str(out_file),
        "--backend", "vulkan",
        "--max-ops", "0",
    ]

    print(f"[{idx}] {label}: start=0x{start_hex}, range={rbits} bits")
    print(f"    cmd: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_min * 60)
        out_file.write_text(result.stdout + "\n---STDERR---\n" + result.stderr)
        # Check for key in output
        for line in result.stdout.split("\n"):
            if "Key found" in line or "Privkey" in line or "SOLVED" in line:
                # Extract hex key
                m = re.search(r'[0-9a-fA-F]{64}', line)
                if m:
                    key = m.group(0)
                    print(f"*** [{idx}] KEY FOUND: {key} ***")
                    (OUT / "FOUND.txt").write_text(key)
                    return key
        print(f"[{idx}] No key found (exited code {result.returncode})")
        return None
    except subprocess.TimeoutExpired:
        print(f"[{idx}] Timeout after {timeout_min}min")
        out_file.write_text(f"TIMEOUT after {timeout_min}min")
        return None
    except Exception as e:
        print(f"[{idx}] Error: {e}")
        out_file.write_text(f"ERROR: {e}")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=806)
    parser.add_argument("--bits", type=int, default=65, choices=[65, 68])
    parser.add_argument("--timeout", type=int, default=1440, help="Timeout per candidate in minutes")
    args = parser.parse_args()

    candidates = load_candidates(args.bits)
    selected = [c for c in candidates if args.start <= c["idx"] <= args.end]
    print(f"Loaded {len(candidates)} candidates, running {len(selected)} (idx {args.start}..{args.end})")

    for cand in selected:
        found = run_kangaroo(cand, timeout_min=args.timeout)
        if found:
            print(f"\n*** SOLVED! Private key: {found} ***")
            (OUT / "SOLVED.txt").write_text(found)
            sys.exit(0)

    print("All candidates processed. No key found.")

if __name__ == "__main__":
    main()
