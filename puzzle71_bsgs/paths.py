"""Puzzle 71 BSGS storage paths — E: if healthy, else C:."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

M_FULL = 1 << 35
H160_RECORD = 25


def _drive_ok(root: Path, min_free: int) -> bool:
    drive = f"{root.drive}\\"
    if not root.drive or not os.path.exists(drive):
        return False
    try:
        return shutil.disk_usage(drive).free >= min_free
    except OSError:
        return False


def pick_bsgs_root() -> Path:
    env = os.environ.get("PUZZLE71_BSGS_ROOT")
    if env:
        return Path(env)
    need = M_FULL * H160_RECORD
    for root in (Path(r"E:\puzzle71_bsgs"), Path(r"C:\puzzle71_bsgs")):
        if _drive_ok(root, need):
            return root
    if _drive_ok(Path(r"C:\puzzle71_bsgs"), H160_RECORD * (1 << 33)):
        return Path(r"C:\puzzle71_bsgs")
    return Path(r"C:\puzzle71_bsgs")


BSGS_ROOT = pick_bsgs_root()
BABY_DIR = BSGS_ROOT / "baby"
GIANT_DIR = BSGS_ROOT / "giant"
LOG_DIR = BSGS_ROOT / "logs"
