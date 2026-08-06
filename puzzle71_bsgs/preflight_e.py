#!/usr/bin/env python3
"""Check E: is writable and has enough space for P71 BSGS baby build."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from paths import BABY_DIR, BSGS_ROOT, GIANT_DIR, LOG_DIR

M = 1 << 35
H160_BYTES = 25 * M
X_BYTES = 36 * M
FULL_BOTH = H160_BYTES + X_BYTES


def main() -> int:
    root = str(BSGS_ROOT)
    print(f"BSGS root: {BSGS_ROOT}")
    if not os.path.exists(root):
        print(f"FAIL: {root} does not exist — run setup_e_drive_admin.bat as Admin")
        return 1

    test = BSGS_ROOT / "_write_test.tmp"
    try:
        test.write_text("ok", encoding="utf-8")
        test.unlink()
    except OSError as e:
        print(f"FAIL: cannot write to {root}: {e}")
        print("Run setup_e_drive_admin.bat as Administrator")
        return 1

    free = shutil.disk_usage(root).free
    print(f"Free space: {free / 1e9:.2f} GB")
    print(f"Need ~{FULL_BOTH / 1e9:.0f} GB for full h160 + x library")
    if free < FULL_BOTH * 1.05:
        print("WARN: may not fit full library — build h160-only or use chunks")

    for d in (BABY_DIR, GIANT_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
    print("OK: E: writable, folders ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
