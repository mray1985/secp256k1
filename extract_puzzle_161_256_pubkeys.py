#!/usr/bin/env python3
"""Extract puzzle 161-256 pubkeys from genesis tx spend on mempool.space."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

GENESIS = "08389f34c98c606322740c0be6a7125d9860bb8d5cb182c02f98461e5fa6cd15"
BASE = "https://mempool.space/api"
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "ARCHIVE" / "briefcase" / "puzzlepubkeys"


def fetch_json(url: str, retries: int = 5) -> dict | list:
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "puzzle-extractor/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1 + i)
    raise RuntimeError("unreachable")


def extract_pubkey_from_scriptsig(scriptsig: str) -> str | None:
    """P2PKH scriptsig: <sig> <pubkey>. Return compressed/uncompressed hex pubkey."""
    sig = scriptsig.lower()
    # push 33-byte compressed key: 21 + 02/03 + 32 bytes = 66 hex chars after opcode
    for prefix in ("21", "41"):
        m = re.search(rf"{prefix}((0[23][0-9a-f]{{64}})|(0[4-9a-f][0-9a-f]{{128}}))", sig)
        if m:
            pk = m.group(1)
            if len(pk) == 66 and pk[:2] in ("02", "03"):
                return pk
            if len(pk) == 130 and pk[:2] == "04":
                return pk
    # fallback: last push in scriptsig
    pushes = re.findall(r"(?:21|41)([0-9a-f]{66,130})", sig)
    if pushes:
        pk = pushes[-1]
        if len(pk) in (66, 130):
            return pk
    return None


def hash160_hex(data: bytes) -> str:
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).hexdigest()


def compressed_from_uncompressed(u: str) -> str:
    if len(u) != 130 or not u.startswith("04"):
        return u
    x = u[2:66]
    y = int(u[66:], 16)
    return ("02" if y % 2 == 0 else "03") + x


def main() -> None:
    print("Fetching genesis tx...")
    genesis = fetch_json(f"{BASE}/tx/{GENESIS}")
    outspends = fetch_json(f"{BASE}/tx/{GENESIS}/outspends")

    vouts = genesis["vout"]
    assert len(vouts) == 256, f"expected 256 outputs, got {len(vouts)}"

    puzzles: dict[int, dict] = {}
    for i, vout in enumerate(vouts):
        n = i + 1
        puzzles[n] = {
            "puzzle": n,
            "vout": i,
            "value_sats": vout["value"],
            "address": vout.get("scriptpubkey_address"),
            "hash160": vout["scriptpubkey"][6:46] if vout["scriptpubkey"].startswith("76a914") else None,
            "spent": outspends[i].get("spent", False),
            "spend_txid": outspends[i].get("txid"),
            "spend_vin": outspends[i].get("vin"),
        }

    # Group spend txs needed for 161-256
    spend_map: dict[str, list[tuple[int, int]]] = {}  # txid -> [(puzzle_n, genesis_vout), ...]
    for n in range(161, 257):
        p = puzzles[n]
        if not p["spent"]:
            print(f"WARNING: P{n} not marked spent")
            continue
        txid = p["spend_txid"]
        spend_map.setdefault(txid, []).append((n, p["vout"]))

    print(f"Unique spend txs for 161-256: {len(spend_map)}")
    for txid, items in spend_map.items():
        print(f"  {txid[:16]}... -> {len(items)} puzzles")

    results: dict[int, dict] = {}
    for txid, items in spend_map.items():
        print(f"Fetching spend tx {txid}...")
        stx = fetch_json(f"{BASE}/tx/{txid}")
        # map genesis vout -> vin index in spend tx
        vin_by_prev = {}
        for vin_i, vin in enumerate(stx["vin"]):
            if vin.get("txid") == GENESIS:
                vin_by_prev[vin["vout"]] = vin_i

        for puzzle_n, genesis_vout in items:
            vin_i = vin_by_prev.get(genesis_vout)
            if vin_i is None:
                # try direct vin from outspends
                vin_i = puzzles[puzzle_n].get("spend_vin")
            if vin_i is None:
                print(f"  P{puzzle_n}: could not locate vin")
                continue
            vin = stx["vin"][vin_i]
            scriptsig = vin.get("scriptsig", "")
            pk = extract_pubkey_from_scriptsig(scriptsig)
            if not pk:
                print(f"  P{puzzle_n}: no pubkey in scriptsig {scriptsig[:40]}...")
                continue
            comp = compressed_from_uncompressed(pk) if pk.startswith("04") else pk
            pk_bytes = bytes.fromhex(comp)
            h160 = hash160_hex(pk_bytes)
            expected = puzzles[puzzle_n]["hash160"]
            ok = h160 == expected
            results[puzzle_n] = {
                "puzzle": puzzle_n,
                "address": puzzles[puzzle_n]["address"],
                "hash160": expected,
                "pubkey_compressed": comp,
                "pubkey_full": "04" + comp[2:] + "?" if comp.startswith(("02", "03")) else pk,
                "hash160_match": ok,
                "spend_txid": txid,
                "genesis_vout": genesis_vout,
            }
            if not ok:
                print(f"  P{puzzle_n}: HASH160 MISMATCH got {h160} expected {expected}")

    print(f"\nExtracted {len(results)}/96 pubkeys for puzzles 161-256")

    # write outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "puzzle_161_256_pubkeys.csv"
    json_path = OUT_DIR / "puzzle_161_256_pubkeys.json"
    txt_path = OUT_DIR / "puzzle_161_256_pubkeys.txt"

    rows = [results[n] for n in sorted(results)]
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8") as f:
        f.write("puzzle,address,pubkey_compressed,hash160,spend_txid,hash160_match\n")
        for r in rows:
            f.write(
                f"{r['puzzle']},{r['address']},{r['pubkey_compressed']},"
                f"{r['hash160']},{r['spend_txid']},{r['hash160_match']}\n"
            )

    with txt_path.open("w", encoding="utf-8") as f:
        f.write(f"# Bitcoin puzzle pubkeys 161-256 from genesis spend\n")
        f.write(f"# Genesis: {GENESIS}\n\n")
        for r in rows:
            f.write(f"puzzle {r['puzzle']}\n")
            f.write(f"  address: {r['address']}\n")
            f.write(f"  pubkey:  {r['pubkey_compressed']}\n")
            f.write(f"  hash160: {r['hash160']}\n\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {txt_path}")

    # sample
    for n in [161, 200, 256]:
        if n in results:
            print(f"P{n}: {results[n]['pubkey_compressed']}")


if __name__ == "__main__":
    main()
