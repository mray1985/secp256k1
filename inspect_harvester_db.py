#!/usr/bin/env python3
import json
import os
import plistlib
import sqlite3
from pathlib import Path

BASE = Path(r"C:\Users\mitch\Desktop\harvester\AppDomain-com.jbmobile.Harvester")
DB = BASE / "Library" / "Application Support" / "BitcoinModel.sqlite"
PLIST = BASE / "Library" / "Preferences" / "com.jbmobile.Harvester.plist"
OUT = Path(r"C:\Users\mitch\Desktop\secp256k1\ARCHIVE\harvester_appdomain_inspect.txt")

lines: list[str] = []
lines.append(f"AppDomain: {BASE}")
lines.append("")

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
lines.append("=== TABLES ===")
for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [c[1] for c in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    n = cur.fetchone()[0]
    lines.append(f"  {t}: {n} rows  cols={cols}")

for t in tables:
    lines.append(f"\n=== SAMPLE {t} (first 8) ===")
    cur.execute(f"PRAGMA table_info({t})")
    cols = [c[1] for c in cur.fetchall()]
    cur.execute(f"SELECT * FROM {t} LIMIT 8")
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        for k, v in list(d.items()):
            if isinstance(v, (bytes, bytearray)):
                d[k] = f"<bytes {len(v)}>"
            elif isinstance(v, str) and len(v) > 120:
                d[k] = v[:120] + "..."
        lines.append(f"  {d}")

with PLIST.open("rb") as f:
    prefs = plistlib.load(f)
lines.append("\n=== PLIST ===")
for k, v in prefs.items():
    if isinstance(v, (str, int, float, bool)):
        lines.append(f"  {k}: {v}")
    elif isinstance(v, dict):
        lines.append(f"  {k}: dict keys={list(v.keys())[:20]}")
    elif isinstance(v, list):
        lines.append(f"  {k}: list len={len(v)}")
    else:
        lines.append(f"  {k}: {type(v).__name__}")

text = "\n".join(lines)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(text + "\n", encoding="utf-8")
print(text)
print(f"\nwrote {OUT}")
