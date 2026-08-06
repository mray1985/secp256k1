"""Puzzle 135 BSGS storage paths."""

from __future__ import annotations

import os
from pathlib import Path


def _disk_free(path: Path) -> int:
    import shutil

    root = str(path.drive + "\\") if path.drive else str(path.anchor)
    return shutil.disk_usage(root).free


def _drive_ok(path: Path, need: int = 0) -> bool:
    try:
        drive = path.drive or str(path.anchor)
        if drive and not os.path.exists(drive + "\\"):
            return False
        if need and _disk_free(path) < need:
            return False
        return True
    except OSError:
        return False


def pick_bsgs_root() -> Path:
    env = os.environ.get("PUZZLE135_BSGS_ROOT")
    if env:
        return Path(env)
    for root in (Path(r"E:\puzzle135_bsgs"), Path(r"C:\puzzle135_bsgs")):
        if _drive_ok(root):
            return root
    return Path(r"C:\puzzle135_bsgs")


BSGS_ROOT = pick_bsgs_root()
BABY_DIR = BSGS_ROOT / "baby"
GIANT_DIR = BSGS_ROOT / "giant"
LOG_DIR = BSGS_ROOT / "logs"
