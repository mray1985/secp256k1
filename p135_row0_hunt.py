#!/usr/bin/env python3
"""Deprecated wrapper — use solve_batch.py (runs all P135–P160)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from solve_batch import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
