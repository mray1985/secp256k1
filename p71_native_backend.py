#!/usr/bin/env python3
"""P71 native backend bridge — BitCrack (CUDA/OpenCL) and KeyHunt (CPU).

Locked path verification (independent of scanner):
  d → [d]G → compressed SEC → SHA256 → RIPEMD160

Compares 20-byte HASH160. Base58 only for human reporting after a verified hit.

Backends:
  bitcrack  — cuBitCrack / clBitCrack (OpenCL experimental per BitCrack docs)
  keyhunt   — albertobsd keyhunt compressed address mode (CPU / WSL)

P71-S03 calibration:
  --expect-private <hex|int>   require this exact key; verify HASH160 independently
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import signal
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ecdsa import SECP256k1

G = SECP256k1.generator

P71_ADDR = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
P71_H160 = bytes.fromhex("F6F5431D25BBF7B12E8ADD9AF5E3475C44A0A5B8")
P71_D_MIN = 1 << 70
P71_D_MAX = (1 << 71) - 1

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# BitCrack: "10.33 MKey/s (1,244,659,712 total)" or "1.23 GKey/s"
# KeyHunt:  "~4 Mkeys/s (4427483 keys/s)"
_RATE_RE = re.compile(
    r"(?P<rate>\d+(?:\.\d+)?)\s*(?P<unit>[kKmMgGtT]?)\s*(?:keys|Keys|Key|key|Kkey|MKey|GKey|TKey)\s*/\s*s",
    re.I,
)
_TOTAL_RE = re.compile(
    r"(?:Total\s+)?(?P<total>[\d,]+)\s*keys\b|\((?P<total2>[\d,]+)\s*total\)",
    re.I,
)
# privkey lines: hex, sometimes with address (do not match "pubkey:")
_PRIV_HEX_RE = re.compile(
    r"(?:Hit!\s*)?(?:Private\s*key|Priv(?:ate)?(?:\s*key)?)\s*[:=]\s*(?:0x)?([0-9a-fA-F]{1,64})",
    re.I,
)
_BARE_HEX_RE = re.compile(r"\b([0-9a-fA-F]{16,64})\b")


@dataclass
class NativeRunResult:
    backend: str
    binary: str
    command: list[str]
    target_address: str
    target_h160: str
    start: int
    end: int  # inclusive
    R_peak: float | None
    R_sustained: float | None
    rate_samples: list[float]
    keys_tested_reported: int | None
    wall_s: float
    found_private_keys: list[str]
    verified_hits: list[dict[str, Any]]
    rejected_hits: list[dict[str, Any]]
    expect_private: str | None
    expect_match: bool | None
    returncode: int | None
    timed_out: bool
    stdout_tail: str
    stderr_tail: str
    notes: list[str] = field(default_factory=list)
    device_notes: str = ""
    started_at_utc: str = ""
    finished_at_utc: str = ""


def parse_int(s: str) -> int:
    s = s.strip().lower().replace("_", "")
    if s.startswith("0x"):
        return int(s, 16)
    # bare hex if has a-f
    if any(c in s for c in "abcdef"):
        return int(s, 16)
    # Long digit-only strings are keyspace hex (e.g. 400000000000000000 = 2^70),
    # not decimal — decimal would under-shoot the P71 band.
    if len(s) >= 16 and all(c in "0123456789" for c in s):
        return int(s, 16)
    return int(s, 10)


def to_hex(n: int) -> str:
    return format(n, "x")


def hash160_compressed(d: int) -> bytes:
    P = d * G
    pref = b"\x02" if (P.y() % 2 == 0) else b"\x03"
    sec = pref + int(P.x()).to_bytes(32, "big")
    return hashlib.new("ripemd160", hashlib.sha256(sec).digest()).digest()


def address_p2pkh(h160: bytes) -> str:
    payload = b"\x00" + h160
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    raw = payload + chk
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    pad = sum(1 for b in raw if b == 0)
    # only leading zeros
    pad = 0
    for b in raw:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + out


def decode_address_h160(addr: str) -> bytes:
    n = 0
    for c in addr:
        n = n * 58 + ALPHABET.index(c)
    raw = n.to_bytes(25, "big")
    if raw[0] != 0:
        raise ValueError(f"not P2PKH mainnet: version={raw[0]}")
    payload, chk = raw[:21], raw[21:]
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != chk:
        raise ValueError("bad address checksum")
    return payload[1:]


def rate_to_keys_per_s(rate: float, unit: str) -> float:
    u = unit.lower()
    mult = {"": 1, "k": 1e3, "m": 1e6, "g": 1e9, "t": 1e12}.get(u, 1)
    return rate * mult


def parse_rates(text: str) -> list[float]:
    rates: list[float] = []
    for m in _RATE_RE.finditer(text):
        rates.append(rate_to_keys_per_s(float(m.group("rate")), m.group("unit") or ""))
    return rates


def parse_totals(text: str) -> list[int]:
    out: list[int] = []
    for m in _TOTAL_RE.finditer(text):
        raw = m.group("total") or m.group("total2")
        if raw:
            out.append(int(raw.replace(",", "")))
    return out


def extract_priv_candidates(text: str) -> list[int]:
    found: list[int] = []
    seen: set[int] = set()
    for m in _PRIV_HEX_RE.finditer(text):
        v = int(m.group(1), 16)
        if v not in seen and v > 0:
            seen.add(v)
            found.append(v)
    # Drop KeyHunt "Base key:" and BitCrack keyspace banner lines before bare-hex
    # scan (Ending at: …0020 is not a reported hit).
    text_bare = re.sub(r"Base\s*key:\s*[0-9a-fA-F]+", "", text, flags=re.I)
    text_bare = re.sub(
        r"(?:Starting at|Ending at|Counting by)\s*:\s*[0-9a-fA-F]+",
        "",
        text_bare,
        flags=re.I,
    )
    # BitCrack found file: address + 64-char priv hex. Skip 40-char HASH160 lines.
    for m in _BARE_HEX_RE.finditer(text_bare):
        hx = m.group(1)
        if len(hx) < 16 or len(hx) == 40:
            continue
        v = int(hx, 16)
        if v not in seen and v > 0:
            seen.add(v)
            found.append(v)
    return found


def verify_hit(
    d: int,
    *,
    target_h160: bytes,
    start: int,
    end: int,
) -> dict[str, Any]:
    """Independent recomputation — reject false / out-of-range hits."""
    rec: dict[str, Any] = {
        "d": d,
        "d_hex": to_hex(d),
        "in_range": start <= d <= end,
    }
    if not rec["in_range"]:
        rec["accepted"] = False
        rec["reason"] = "out_of_range"
        return rec
    try:
        h160 = hash160_compressed(d)
    except Exception as exc:
        rec["accepted"] = False
        rec["reason"] = f"ec_error:{exc}"
        return rec
    rec["h160"] = h160.hex()
    rec["address"] = address_p2pkh(h160)
    if h160 != target_h160:
        rec["accepted"] = False
        rec["reason"] = "hash160_mismatch"
        return rec
    rec["accepted"] = True
    rec["reason"] = "hash160_match"
    return rec


def build_bitcrack_cmd(
    binary: Path,
    target: str,
    start: int,
    end: int,
    *,
    found_file: Path | None,
    checkpoint: Path | None,
    compressed: bool = True,
    blocks: int | None = None,
    threads: int | None = None,
    points: int | None = None,
    device: int | None = None,
) -> list[str]:
    cmd = [str(binary)]
    if device is not None:
        cmd.extend(["-d", str(device)])
    if blocks is not None:
        cmd.extend(["-b", str(blocks)])
    if threads is not None:
        cmd.extend(["-t", str(threads)])
    if points is not None:
        cmd.extend(["-p", str(points)])
    if compressed:
        cmd.append("-c")
    else:
        cmd.append("-u")
    cmd.extend(["--keyspace", f"{to_hex(start)}:{to_hex(end)}"])
    if checkpoint is not None:
        cmd.extend(["--continue", str(checkpoint)])
    if found_file is not None:
        cmd.extend(["-o", str(found_file)])
    cmd.append(target)
    return cmd


def is_linux_elf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def win_to_wsl_path(path: Path) -> str:
    """Map C:\\foo\\bar → /mnt/c/foo/bar for WSL invocation."""
    p = path.resolve()
    s = str(p)
    if len(s) >= 2 and s[1] == ":":
        drive = s[0].lower()
        rest = s[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return s.replace("\\", "/")


def build_keyhunt_cmd(
    binary: Path,
    target: str,
    start: int,
    end: int,
    *,
    threads: int,
    address_file: Path,
    compressed: bool = True,
) -> list[str]:
    """albertobsd keyhunt: -m address -f file -r start:end -l compress -t N.

    On Windows, Linux ELF binaries are launched via `wsl` with /mnt/<drive> paths.
    """
    address_file.write_text(target + "\n", encoding="ascii")
    use_wsl = sys.platform == "win32" and is_linux_elf(binary)
    bin_s = win_to_wsl_path(binary) if use_wsl else str(binary)
    addr_s = win_to_wsl_path(address_file) if use_wsl else str(address_file)
    inner = [
        bin_s,
        "-m",
        "address",
        "-f",
        addr_s,
        "-r",
        f"{to_hex(start)}:{to_hex(end)}",
        "-l",
        "compress" if compressed else "uncompress",
        "-t",
        str(threads),
        "-s",
        "1",  # emit keys/s once per second for R_peak / R_sustained
    ]
    if use_wsl:
        # Line-buffer so stop_on_hit can see Hit! without waiting for process exit.
        return ["wsl", "-e", "stdbuf", "-oL", "-eL", *inner]
    return inner


# KeyHunt keeps scanning after a hit; BitCrack usually exits. For known-hit
# calibration we stop the process once a hit line appears so the run ends cleanly.
_HIT_LINE_RE = re.compile(
    r"(?:Hit!\s*Private\s*Key|Private\s*key|Priv(?:ate)?)\s*[:=]?\s*(?:0x)?[0-9a-fA-F]+",
    re.I,
)


def run_process(
    cmd: list[str],
    *,
    seconds: float | None,
    cwd: Path | None = None,
    stop_on_hit: bool = False,
) -> tuple[int | None, str, str, float, bool]:
    """Run scanner; optional wall-clock timeout. Captures combined output.

    If stop_on_hit is True (known-hit calibration), terminate once a private-key
    hit line is observed. That is a normal success path for scanners that do not
    exit on find (e.g. keyhunt), not a throughput timeout failure.
    """
    t0 = time.perf_counter()
    timed_out = False
    hit_stopped = False
    # WSL-wrapped cmds: do not set a Windows cwd (paths are already absolute /mnt/...)
    effective_cwd = None if (cmd and cmd[0].lower() == "wsl") else (
        str(cwd) if cwd else None
    )
    out_chunks: list[str] = []
    err_chunks: list[str] = []
    rc: int | None = None

    proc = subprocess.Popen(
        cmd,
        cwd=effective_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None and proc.stderr is not None

    def _kill_tree() -> None:
        if proc.poll() is not None:
            return
        try:
            if sys.platform == "win32" and cmd and cmd[0].lower() == "wsl":
                # Also kill Linux-side binary; Windows wsl.exe may linger otherwise.
                subprocess.run(
                    ["wsl", "-e", "pkill", "-9", "-f", "keyhunt"],
                    capture_output=True,
                    timeout=5,
                )
                subprocess.run(
                    ["wsl", "-e", "pkill", "-9", "-f", "BitCrack"],
                    capture_output=True,
                    timeout=5,
                )
            proc.kill()
        except OSError:
            pass

    try:
        while True:
            if seconds is not None and (time.perf_counter() - t0) >= seconds:
                timed_out = True
                _kill_tree()
                break
            line = proc.stdout.readline()
            if line:
                out_chunks.append(line)
                if stop_on_hit and _HIT_LINE_RE.search(line):
                    hit_stopped = True
                    _kill_tree()
                    break
            elif proc.poll() is not None:
                break
            else:
                time.sleep(0.01)
        # Drain remaining pipes (best-effort)
        try:
            rest_out, rest_err = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            _kill_tree()
            rest_out, rest_err = proc.communicate(timeout=2)
        if rest_out:
            out_chunks.append(rest_out)
        if rest_err:
            err_chunks.append(rest_err)
        rc = proc.returncode
    except Exception:
        _kill_tree()
        raise

    wall = time.perf_counter() - t0
    out = "".join(out_chunks)
    err = "".join(err_chunks)
    if hit_stopped:
        # Normal termination for known-hit calibration against non-exiting scanners.
        timed_out = False
        if rc is None or rc != 0:
            rc = 0
    return rc, out, err, wall, timed_out


def summarize_rates(samples: list[float]) -> tuple[float | None, float | None]:
    if not samples:
        return None, None
    peak = max(samples)
    # sustained = median of latter half (after warmup)
    half = samples[len(samples) // 2 :] or samples
    sust = statistics.median(half)
    return peak, sust


def run_native(
    *,
    backend: str,
    binary: Path,
    target: str,
    start: int,
    end: int,
    seconds: float | None,
    threads: int,
    checkpoint: Path | None,
    found_file: Path | None,
    expect_private: int | None,
    work_dir: Path,
    bitcrack_device: int | None = None,
) -> NativeRunResult:
    if start > end:
        raise ValueError("start > end")
    target_h160 = decode_address_h160(target)
    notes: list[str] = []
    device_notes = ""

    if backend == "bitcrack":
        name = binary.name.lower()
        if "clbitcrack" in name or name.startswith("cl"):
            device_notes = "OpenCL BitCrack — EXPERIMENTAL per upstream docs"
            notes.append("clBitCrack_experimental")
        elif "cubitcrack" in name or name.startswith("cu"):
            device_notes = "CUDA BitCrack"
        found_file = found_file or (work_dir / "bitcrack_found.txt")
        cmd = build_bitcrack_cmd(
            binary,
            target,
            start,
            end,
            found_file=found_file,
            checkpoint=checkpoint,
            device=bitcrack_device,
        )
    elif backend == "keyhunt":
        device_notes = "KeyHunt CPU compressed address mode"
        addr_file = work_dir / "keyhunt_targets.txt"
        cmd = build_keyhunt_cmd(
            binary, target, start, end, threads=threads, address_file=addr_file
        )
    else:
        raise ValueError(f"unknown backend: {backend}")

    started = datetime.now(timezone.utc).isoformat()
    # Known-hit calibration: stop when a hit line appears (keyhunt does not exit).
    # Throughput-only runs pass seconds=... and expect_private=None.
    stop_on_hit = expect_private is not None and seconds is None
    if backend == "keyhunt" and stop_on_hit:
        notes.append("stop_on_hit=keyhunt_known_hit_calibration")
        device_notes = "KeyHunt CPU compressed address mode (WSL-capable)"
    # Safety ceiling for known-hit runs so a miss cannot hang forever.
    effective_seconds = seconds if seconds is not None else (120.0 if stop_on_hit else None)
    rc, stdout, stderr, wall, timed_out = run_process(
        cmd,
        seconds=effective_seconds,
        cwd=binary.parent,
        stop_on_hit=stop_on_hit,
    )
    finished = datetime.now(timezone.utc).isoformat()
    if stop_on_hit and timed_out:
        notes.append("known_hit_safety_timeout")

    combined = stdout + "\n" + stderr
    if found_file and found_file.is_file():
        combined += "\n" + found_file.read_text(encoding="utf-8", errors="replace")

    rate_samples = parse_rates(combined)
    R_peak, R_sust = summarize_rates(rate_samples)
    totals = parse_totals(combined)
    keys_reported = totals[-1] if totals else None

    privs = extract_priv_candidates(combined)
    verified: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for d in privs:
        rec = verify_hit(d, target_h160=target_h160, start=start, end=end)
        (verified if rec["accepted"] else rejected).append(rec)

    expect_match: bool | None = None
    if expect_private is not None:
        expect_match = any(v["d"] == expect_private and v["accepted"] for v in verified)
        if not expect_match:
            # still verify expected key ourselves for diagnostics
            self_check = verify_hit(
                expect_private, target_h160=target_h160, start=start, end=end
            )
            notes.append(f"expect_self_check={self_check['reason']}")

    return NativeRunResult(
        backend=backend,
        binary=str(binary),
        command=cmd,
        target_address=target,
        target_h160=target_h160.hex(),
        start=start,
        end=end,
        R_peak=R_peak,
        R_sustained=R_sust,
        rate_samples=rate_samples,
        keys_tested_reported=keys_reported,
        wall_s=wall,
        found_private_keys=[to_hex(d) for d in privs],
        verified_hits=verified,
        rejected_hits=rejected,
        expect_private=to_hex(expect_private) if expect_private is not None else None,
        expect_match=expect_match,
        returncode=rc,
        timed_out=timed_out,
        stdout_tail=stdout[-4000:],
        stderr_tail=stderr[-4000:],
        notes=notes,
        device_notes=device_notes,
        started_at_utc=started,
        finished_at_utc=finished,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="P71 native BitCrack/KeyHunt bridge")
    ap.add_argument("--backend", choices=["bitcrack", "keyhunt"], required=True)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--target", default=P71_ADDR)
    ap.add_argument("--start", type=str, required=True, help="inclusive start (hex or int)")
    ap.add_argument("--end", type=str, required=True, help="inclusive end (hex or int)")
    ap.add_argument("--seconds", type=float, default=None, help="wall-clock limit (benchmark)")
    ap.add_argument("--threads", type=int, default=4, help="KeyHunt -t")
    ap.add_argument("--device", type=int, default=None, help="BitCrack -d")
    ap.add_argument("--checkpoint", type=Path, default=None)
    ap.add_argument("--found-file", type=Path, default=None)
    ap.add_argument("--expect-private", type=str, default=None)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument(
        "--allow-outside-p71-band",
        action="store_true",
        help="permit calibration ranges outside [2^70, 2^71-1]",
    )
    args = ap.parse_args()

    if not args.binary.is_file():
        print(f"ERROR: binary not found: {args.binary}", file=sys.stderr)
        return 2

    start = parse_int(args.start)
    end = parse_int(args.end)
    if not args.allow_outside_p71_band:
        if start < P71_D_MIN or end > P71_D_MAX:
            print(
                "ERROR: range outside Puzzle 71 inclusive band "
                f"[{to_hex(P71_D_MIN)}, {to_hex(P71_D_MAX)}]. "
                "Pass --allow-outside-p71-band for S03 calibration windows.",
                file=sys.stderr,
            )
            return 2

    expect = parse_int(args.expect_private) if args.expect_private else None
    work_dir = args.output.parent
    work_dir.mkdir(parents=True, exist_ok=True)

    result = run_native(
        backend=args.backend,
        binary=args.binary,
        target=args.target,
        start=start,
        end=end,
        seconds=args.seconds,
        threads=args.threads,
        checkpoint=args.checkpoint,
        found_file=args.found_file,
        expect_private=expect,
        work_dir=work_dir,
        bitcrack_device=args.device,
    )

    payload = asdict(result)
    payload["path_locked"] = "HASH160(compressed SEC([d]G)); Base58 only after verified hit"
    payload["p71_band_inclusive"] = {"min_hex": to_hex(P71_D_MIN), "max_hex": to_hex(P71_D_MAX)}
    payload["s03_gate"] = {
        "expect_private_required_for_calibration": True,
        "expect_match": result.expect_match,
        "verified_hit_count": len(result.verified_hits),
        "pass": bool(result.expect_match) if expect is not None else None,
    }
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"backend={result.backend} device={result.device_notes}")
    print(f"cmd={' '.join(result.command)}")
    print(f"wall_s={result.wall_s:.2f} timed_out={result.timed_out} rc={result.returncode}")
    print(f"R_peak={result.R_peak} R_sustained={result.R_sustained}")
    print(f"verified_hits={len(result.verified_hits)} rejected={len(result.rejected_hits)}")
    if expect is not None:
        print(f"expect_match={result.expect_match}")
    print(f"wrote {args.output}")

    if expect is not None:
        return 0 if result.expect_match else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
