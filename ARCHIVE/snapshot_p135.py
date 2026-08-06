#!/usr/bin/env python3
"""Daily/hourly P135 + secp256k1 research snapshot. Copies tracked files + live constants."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = Path(__file__).resolve().parent
SNAPSHOTS = ARCHIVE / "snapshots"
MANIFEST_PATH = ARCHIVE / "tracked_files.json"
LOG_PATH = ARCHIVE / "snapshot_log.jsonl"

# Relative to ROOT — add paths here when new important artifacts appear.
TRACKED = [
    "p135_carry_remainder_report.py",
    "p135_carry_remainder_report.txt",
    "p135_phase_band_scan.py",
    "p135_k_lane_band_scan.py",
    "p135_resumable_search.py",
    "carry_remainder_check.py",
    "02_Research/notes/Complexity_Simplified_p.txt",
    "02_Research/notes/Complexity_Simplified_N.txt",
    "00_Projects/patent/717.txt",
    "ECDLP/kangaroo_infiles/p135_meta.txt",
    "ECDLP/kangaroo_infiles/p135_band_lo_125bit.txt",
    "ECDLP/kangaroo_infiles/p135_shelf2_125bit.txt",
    "ARCHIVE/MASTER_STATE.md",
    "ARCHIVE/constants_frozen.json",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def live_constants() -> dict[str, str]:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "ECDLP"))
    from p135_carry_remainder_report import build_p135_bridge

    bridge = build_p135_bridge(puzzle_row=2)
    out: dict[str, str] = {k: str(v) for k, v in bridge.items()}
    out["N"] = "115792089237316195423570985008687907852837564279074904382605163141518161494337"
    out["p"] = "115792089237316195423570985008687907853269984665640564039457584007908834671663"
    out["delta"] = str(int(out["p"]) - int(out["N"]))
    out["LO_2_134"] = str(2**134)
    out["HI_2_135"] = str(2**135)
    out["Lambda_p_row3"] = "97451685862885086182458552040892158509924235661624603229050850812487253689501"
    out["s_barcode"] = "15509729875763924304053419655647994379903175655107184284998698212653288468986"
    out["z_barcode"] = "66278737796829840734606014530466656889790152192829793669891337810330530090951"
    out["r_tx_rx2"] = "90653255469745952335985143920649543885181555095025199315947044135806663628368"
    out["k_Px_pipeline"] = "19089036453356401353257357002647987614981495902151757130742235757133693952525"
    out["k_Py_pipeline"] = "90508964219557991953548570402867934097841441951106365697884749206559245429888"
    return out


def snapshot(label: str | None = None) -> Path:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    dest = SNAPSHOTS / (f"{stamp}_{label}" if label else stamp)
    dest.mkdir(parents=True, exist_ok=False)

    entries: list[dict] = []
    for rel in TRACKED:
        src = ROOT / rel
        if not src.is_file():
            entries.append({"rel": rel, "status": "missing"})
            continue
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        entries.append(
            {
                "rel": rel,
                "status": "copied",
                "bytes": src.stat().st_size,
                "sha256": sha256_file(src),
            }
        )

    const = live_constants()
    const_path = dest / "constants_live.json"
    const_path.write_text(json.dumps(const, indent=2) + "\n", encoding="utf-8")
    (ARCHIVE / "constants_live.json").write_text(
        json.dumps(const, indent=2) + "\n", encoding="utf-8"
    )

    meta = {
        "utc": now.isoformat(),
        "stamp": stamp,
        "label": label,
        "root": str(ROOT),
        "files": entries,
        "constants_live": str(const_path.relative_to(ARCHIVE)),
    }
    (dest / "snapshot_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (ARCHIVE / "LATEST.txt").write_text(dest.name + "\n", encoding="utf-8")

    log_line = json.dumps({"utc": now.isoformat(), "dir": dest.name, "copied": sum(1 for e in entries if e["status"] == "copied")})
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    MANIFEST_PATH.write_text(json.dumps({"tracked": TRACKED, "updated_utc": now.isoformat()}, indent=2) + "\n", encoding="utf-8")
    return dest


def prune_old(keep: int = 90) -> int:
    dirs = sorted(SNAPSHOTS.iterdir(), key=lambda p: p.name, reverse=True)
    removed = 0
    for d in dirs[keep:]:
        if d.is_dir():
            shutil.rmtree(d)
            removed += 1
    return removed


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="P135 research snapshot")
    ap.add_argument("--label", default=None, help="optional tag e.g. session-end")
    ap.add_argument("--prune-keep", type=int, default=90, help="keep N newest snapshot dirs")
    args = ap.parse_args()
    dest = snapshot(args.label)
    pruned = prune_old(args.prune_keep)
    print(f"snapshot: {dest}")
    print(f"pruned: {pruned} old dirs (keep {args.prune_keep})")


if __name__ == "__main__":
    main()
