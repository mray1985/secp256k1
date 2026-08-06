#!/usr/bin/env python3
"""All 160 Bitcoin puzzle addresses from privatekeys.pw export."""

from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG_CSV = ROOT / "ARCHIVE" / "puzzle_catalog_160.csv"
EXPORT_URL = "https://privatekeys.pw/puzzles/bitcoin-puzzle-tx/export?status=all"


@dataclass(frozen=True)
class PuzzleCatalogEntry:
    n: int
    range_min: int
    range_max: int
    address: str
    btc_value: float
    hash160: str
    public_key: str  # compressed hex, empty if not leaked
    private_key: int  # 0 if unsolved
    solve_date: str

    @property
    def solved(self) -> bool:
        return self.private_key > 0

    @property
    def has_pubkey(self) -> bool:
        return bool(self.public_key)


def download_catalog(dest: Path = CATALOG_CSV) -> str:
    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": "Mozilla/5.0"})
    text = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return text


def load_catalog(path: Path = CATALOG_CSV) -> dict[int, PuzzleCatalogEntry]:
    if not path.exists():
        download_catalog(path)
    text = path.read_text(encoding="utf-8")
    out: dict[int, PuzzleCatalogEntry] = {}
    for row in csv.DictReader(io.StringIO(text)):
        n = int(row["bits"])
        priv_hex = (row.get("private_key") or "").strip()
        priv = int(priv_hex, 16) if priv_hex else 0
        out[n] = PuzzleCatalogEntry(
            n=n,
            range_min=int(row["range_min"], 16) if row["range_min"] else 0,
            range_max=int(row["range_max"], 16) if row["range_max"] else 0,
            address=row["address"],
            btc_value=float(row["btc_value"]),
            hash160=row["hash160_compressed"],
            public_key=(row.get("public_key") or "").strip(),
            private_key=priv,
            solve_date=(row.get("solve_date") or "").strip(),
        )
    return out


if __name__ == "__main__":
    cat = load_catalog()
    print(f"catalog: {len(cat)} puzzles, solved={sum(1 for e in cat.values() if e.solved)}")
