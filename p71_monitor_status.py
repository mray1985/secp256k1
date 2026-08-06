#!/usr/bin/env python3
"""Lightweight Puzzle 71 status check (pubkey exposure / solved).

Fetches btcpuzzle.info puzzle/71 when network is available.
Does not scan keys. Does not reopen pattern lanes.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "logs" / "p71_monitor"
ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
URL = "https://btcpuzzle.info/puzzle/71"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    status = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": URL,
        "expected_addr": ADDR,
        "engine": "linear_HASH160",
        "kangaroo_trigger": False,
    }
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "p71-monitor/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        status["http_ok"] = True
        status["addr_present"] = ADDR in html
        # Heuristics
        unsolved = bool(re.search(r"Unsolved", html, re.I))
        solved = bool(re.search(r"\bSolved\b", html, re.I)) and not unsolved
        # Pubkey exposure often shows 02/03 + 64 hex near puzzle pages
        pubkey_like = re.findall(r"\b0[23][0-9a-fA-F]{64}\b", html)
        status["page_says_unsolved"] = unsolved
        status["page_says_solved"] = solved
        status["pubkey_hex_candidates_on_page"] = pubkey_like[:5]
        status["pubkey_exposed_suspected"] = len(pubkey_like) > 0
        if solved or status["pubkey_exposed_suspected"]:
            status["alert"] = "ENGINE_SWITCH_REVIEW: solved and/or pubkey-like hex on page"
            status["recommended_engine"] = "review — kangaroo only if spend exposes pubkey"
        else:
            status["alert"] = None
            status["recommended_engine"] = "linear_HASH160"
    except Exception as exc:
        status["http_ok"] = False
        status["error"] = str(exc)
        status["alert"] = "fetch_failed"

    path = OUT / "P71_status_latest.json"
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    # append history
    hist = OUT / "P71_status_history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(status) + "\n")
    print(json.dumps(status, indent=2))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
