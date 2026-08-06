#!/usr/bin/env python3
"""
Fetch ECDSA R,S,Z from blockchain spend transactions.

Sources: blockstream.info API + hashkeys.space frozen table (P135 etc.).
Cache: ARCHIVE/puzzle_rsz_cache.json
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from hashkeys_rsz import HASHKEYS_TXID, PUZZLE_RSZ
from puzzle_catalog import PuzzleCatalogEntry, load_catalog

ROOT = Path(__file__).resolve().parent
CACHE_PATH = ROOT / "ARCHIVE" / "puzzle_rsz_cache.json"
BLOCKSTREAM = "https://blockstream.info/api"


@dataclass
class PuzzleRSZRecord:
    puzzle: int
    source: str
    txid: str
    input_index: int
    r: int
    s: int
    z: int
    pub_compressed: str
    k: int | None = None
    note: str = ""


def _hash160(pub_hex: str) -> str:
    pub = bytes.fromhex(pub_hex)
    return hashlib.new("ripemd160", hashlib.sha256(pub).digest()).hexdigest()


def _get_rs(sig_hex: str) -> tuple[str, str]:
    rlen = int(sig_hex[2:4], 16)
    r = sig_hex[4 : 4 + rlen * 2]
    s = sig_hex[8 + rlen * 2 :]
    return r, s


def _split_sig_pieces(script: str) -> tuple[str, str, str]:
    sig_len = int(script[2:4], 16)
    sig = script[2 + 2 : 2 + sig_len * 2]
    r, s = _get_rs(sig[4:])
    pub_len = int(script[4 + sig_len * 2 : 4 + sig_len * 2 + 2], 16)
    pub = script[4 + sig_len * 2 + 2 :]
    return r, s, pub


def _parse_tx(rawtx: str) -> tuple[str, list[list[str]], str]:
    if rawtx[8:12] == "0001":
        raise ValueError("segwit tx not supported for legacy RSZ parser")
    inp_nu = int(rawtx[8:10], 16)
    first = rawtx[0:10]
    cur = 10
    inp_list: list[list[str]] = []
    for _ in range(inp_nu):
        prev_out = rawtx[cur : cur + 64]
        var0 = rawtx[cur + 64 : cur + 64 + 8]
        cur = cur + 64 + 8
        script_len = int(rawtx[cur : cur + 2], 16)
        script = rawtx[cur : 2 + cur + 2 * script_len]
        r, s, pub = _split_sig_pieces(script)
        seq = rawtx[2 + cur + 2 * script_len : 10 + cur + 2 * script_len]
        inp_list.append([prev_out, var0, r, s, pub, seq])
        cur = 10 + cur + 2 * script_len
    rest = rawtx[cur:]
    return first, inp_list, rest


def _signable_txn(parsed: tuple[str, list[list[str]], str]) -> list[tuple[str, str, str, str]]:
    first, inp_list, rest = parsed
    tot = len(inp_list)
    out: list[tuple[str, str, str, str]] = []
    for one in range(tot):
        e = first
        for i in range(tot):
            e += inp_list[i][0]
            e += inp_list[i][1]
            if one == i:
                h160 = _hash160(inp_list[one][4])
                e += "1976a914" + h160 + "88ac"
            else:
                e += "00"
            e += inp_list[i][5]
        e += rest + "01000000"
        z = hashlib.sha256(hashlib.sha256(bytes.fromhex(e)).digest()).hexdigest()
        out.append((inp_list[one][2], inp_list[one][3], z, inp_list[one][4]))
    return out


def _api_get(path: str) -> bytes:
    url = f"{BLOCKSTREAM}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "secp256k1-puzzle-rsz/1.0"})
    return urllib.request.urlopen(req, timeout=45).read()


def _rawtx_hex(txid: str) -> str:
    return _api_get(f"tx/{txid}/hex").decode().strip()


def _address_txs(address: str, limit: int = 25) -> list[dict]:
    data = json.loads(_api_get(f"address/{address}/txs"))
    return data[:limit]


def rsz_from_rawtx(rawtx: str, want_pubkey: str | None = None) -> list[PuzzleRSZRecord]:
    parsed = _parse_tx(rawtx)
    rows = _signable_txn(parsed)
    out: list[PuzzleRSZRecord] = []
    for i, (r, s, z, pub) in enumerate(rows):
        if want_pubkey and pub.lower() != want_pubkey.lower():
            continue
        out.append(
            PuzzleRSZRecord(
                puzzle=0,
                source="blockchain",
                txid="",
                input_index=i,
                r=int(r, 16),
                s=int(s, 16),
                z=int(z, 16),
                pub_compressed=pub,
            )
        )
    return out


def rsz_from_txid(txid: str, want_pubkey: str | None = None) -> list[PuzzleRSZRecord]:
    raw = _rawtx_hex(txid)
    rows = rsz_from_rawtx(raw, want_pubkey)
    for row in rows:
        row.txid = txid
    return rows


def find_spend_rsz(entry: PuzzleCatalogEntry, sleep_s: float = 0.35) -> PuzzleRSZRecord | None:
    """Find RSZ from a spend tx matching puzzle pubkey."""
    if not entry.public_key:
        return None
    time.sleep(sleep_s)
    try:
        txs = _address_txs(entry.address)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    want = entry.public_key.lower()
    for tx in txs:
        txid = tx["txid"]
        try:
            time.sleep(sleep_s)
            for row in rsz_from_txid(txid, want):
                row.puzzle = entry.n
                row.source = "blockstream spend tx"
                return row
        except (ValueError, urllib.error.URLError, json.JSONDecodeError):
            continue
    return None


_HASHKEYS_PARSED: list[tuple[str, str, str, str]] | None = None


def _hashkeys_rows() -> list[tuple[str, str, str, str]]:
    global _HASHKEYS_PARSED
    if _HASHKEYS_PARSED is None:
        raw = _rawtx_hex(HASHKEYS_TXID)
        _HASHKEYS_PARSED = _signable_txn(_parse_tx(raw))
    return _HASHKEYS_PARSED


def rsz_from_hashkeys(n: int) -> PuzzleRSZRecord | None:
    rsz = PUZZLE_RSZ.get(n)
    if rsz is None:
        return None
    want = rsz.pub_compressed.lower()
    z = rsz.z
    idx = 0
    for i, (r, s, zhex, pub) in enumerate(_hashkeys_rows()):
        if pub.lower() == want:
            z = int(zhex, 16)
            idx = i
            break
    return PuzzleRSZRecord(
        puzzle=n,
        source="hashkeys.space partial spend",
        txid=HASHKEYS_TXID,
        input_index=idx,
        r=rsz.r,
        s=rsz.s,
        z=z,
        pub_compressed=rsz.pub_compressed,
        k=rsz.k,
        note="hashkeys frozen r,s; z from blockchain tx parse",
    )


def get_rsz(n: int, entry: PuzzleCatalogEntry, cache: dict) -> PuzzleRSZRecord | None:
    key = str(n)
    if key in cache:
        d = cache[key]
        return PuzzleRSZRecord(**d) if d else None
    # P135: hashkeys is authoritative per user
    if n in PUZZLE_RSZ:
        rec = rsz_from_hashkeys(n)
        cache[key] = asdict(rec) if rec else None
        return rec
    if entry.solved and entry.public_key:
        rec = find_spend_rsz(entry)
        cache[key] = asdict(rec) if rec else None
        return rec
    cache[key] = None
    return None


def build_cache(puzzles: list[int] | None = None, refresh: bool = False) -> dict[str, dict | None]:
    catalog = load_catalog()
    cache: dict[str, dict | None] = {}
    if CACHE_PATH.exists() and not refresh:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    targets = puzzles or list(range(1, 161))
    for n in targets:
        if str(n) in cache and not refresh:
            continue
        entry = catalog[n]
        get_rsz(n, entry, cache)
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        print(f"  puzzle {n:3d}  rsz={'yes' if cache.get(str(n)) else 'no'}")
    return cache


if __name__ == "__main__":
    import sys

    refresh = "--refresh" in sys.argv
    subset = [int(x) for x in sys.argv[1:] if x.isdigit()]
    build_cache(subset or None, refresh=refresh)
