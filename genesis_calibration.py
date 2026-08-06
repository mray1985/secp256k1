#!/usr/bin/env python3
"""Genesis coinbase #0 calibration — test byte indices vs shelf2/offset terms."""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
ECDLP = ROOT / "ECDLP"
sys.path.insert(0, str(ECDLP))
sys.path.insert(0, str(ROOT))

from hashkeys_rsz import (  # noqa: E402
    EARLY_SOLVED,
    P7_D,
    P7_PX,
    P7_PY,
    PUZZLE_RSZ,
    rsz_bridge_features,
)

from ecdlp_full_pipeline import (  # noqa: E402
    N,
    P115_D,
    P115_K,
    P115_OFFSET_SHELF2,
    PuzzleConfig,
    apply_puzzle_defaults,
    build_bridge_offset_terms,
    compute_alignment_frame,
    compute_order_in_the_court,
    compute_shelf_iteration_matrix,
    delta,
    puzzle_band,
    verify_n_y_compression,
    y_even,
)

try:
    from ecdsa import SECP256k1, SigningKey

    _HAS_ECDSA = True
except ImportError:
    _HAS_ECDSA = False

GENESIS_DUMP = ROOT / "02_Research" / "notes" / "genesis block.txt"
G_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
G_Y = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
GENESIS_X = 0x678AFDB0FE5548271967F1A67130B7105CD6A828E03909A67962E0EA1F61DEB6


def parse_genesis_hex_dump(path: Path) -> bytes:
    """Parse xxd-style dump into contiguous bytes."""
    out = bytearray()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("0000125"):
            continue
        if "|" not in line:
            continue
        hex_part = line.split("|")[0].strip()
        parts = hex_part.split(None, 1)
        if len(parts) < 2:
            continue
        for tok in parts[1].split():
            out.append(int(tok, 16))
    return bytes(out)


def coinbase_script(raw: bytes) -> bytes:
    """Return coinbase script bytes (skip 4-byte tx version + varint if present)."""
    # genesis block.txt dump starts at offset 0x28 in blk00000.dat slice — script at 3b a3...
    idx = raw.find(bytes.fromhex("3ba3edfd"))
    return raw[idx:] if idx >= 0 else raw


def scalar_from_pubkey(d: int) -> tuple[int, int]:
    sk = SigningKey.from_secret_exponent(d, curve=SECP256k1)
    pub = sk.get_verifying_key().to_string()
    return int.from_bytes(pub[1:33], "big"), int.from_bytes(pub[33:65], "big")


def bridge_state(cfg: PuzzleConfig) -> dict:
    apply_puzzle_defaults(cfg)
    lo, hi, _ = puzzle_band(cfg.puzzle_num)
    px, rx = cfg.Px, cfg.rx
    py, ry = cfg.Py, cfg.ry
    assert py is not None and ry is not None
    row = cfg.row

    qx = [(rx[i] * delta) % N for i in range(3)]
    qx_scaled = [(px[i] * delta) % N for i in range(3)]
    lambda_ns = [(qx_scaled[i] * pow(qx[i], -1, N)) % N for i in range(3)]
    n_yc = verify_n_y_compression(px_triple=px, rx_triple=rx, py=py, ry=ry)
    lam_y_n = n_yc.lambda_y_n
    lambda_p = (px[row] * pow(rx[row], -1, N)) % N
    gap = (lambda_p - (px[0] * pow(rx[0], -1, N)) % N) % N  # same row if row=0

    py1 = y_even(px[0])
    ry1 = y_even(rx[0])
    oitc = compute_order_in_the_court(
        lo=lo,
        qx=qx,
        qy=(ry1 * delta) % N,
        qx_scaled=qx_scaled,
        qy_scaled=(py1 * delta) % N,
        lambda_ns=lambda_ns,
        lam_y_n=lam_y_n,
    )
    sim = compute_shelf_iteration_matrix(lo, [oitc.shelf2, oitc.shelf3, oitc.shelf_y])
    af = compute_alignment_frame(
        oitc=oitc, sim=sim, lo=lo, hi=hi, known_d=cfg.known_d
    )
    terms = build_bridge_offset_terms(
        oitc=oitc,
        sim=sim,
        lambda_ns=lambda_ns,
        lo=lo,
        hi=hi,
        gap=gap,
        lambda_p=lambda_p,
        lambda_n_target=lambda_p,
        calibrated_offset=af.offset_shelf2,
    )
    true_off = None
    if cfg.known_d is not None:
        true_off = (cfg.known_d - oitc.shelf2) % lo
    return {
        "cfg": cfg,
        "lo": lo,
        "hi": hi,
        "oitc": oitc,
        "sim": sim,
        "af": af,
        "terms": terms,
        "true_offset": true_off,
        "gap": gap,
        "lambda_ns": lambda_ns,
    }


def genesis_coinbase_features(script: bytes) -> list[tuple[str, int]]:
    """Index-derived scalars from coinbase script (calibration #0 feed)."""
    feats: list[tuple[str, int]] = []

    def add(name: str, val: int) -> None:
        feats.append((name, val % N))

    # ASCII anchor positions
    anchors = {
        "gv.a": b"gv",
        "Q2:": b"Q2:",
        "K.^J": b"K.",
        "Times": b"The Times",
        "bailout": b"bailout",
        "CA.g": b"\x04g",  # pubkey push
    }
    for label, needle in anchors.items():
        i = script.find(needle)
        if i >= 0:
            add(f"idx({label})", i)
            add(f"byte@{label}", script[i])
            if i + 3 <= len(script):
                add(f"le32@{label}", int.from_bytes(script[i : i + 4], "little"))
            if i + 8 <= len(script):
                add(f"be64@{label}", int.from_bytes(script[i : i + 8], "big"))

    # 第 ordinal counts from poetic gloss -> cumulative indices
    dai_runs = [1, 2, 9, 3]
    pos = 0
    for run_i, count in enumerate(dai_runs):
        chunk = []
        for j in range(count):
            if pos < len(script):
                chunk.append(script[pos])
            pos += 1
        if chunk:
            add(f"dai_run{run_i}_sum", sum(chunk))
            add(f"dai_run{run_i}_int", int.from_bytes(bytes(chunk), "big"))
            add(f"dai_run{run_i}_start_idx", pos - len(chunk))

    # D/8 tail: index 8 and byte/8
    if len(script) > 8:
        add("byte@8", script[8])
        add("sum_first_8", sum(script[:8]))
        add("int_first_8", int.from_bytes(script[:8], "big"))

    # 中時三正十手司物 -> 3, 10, 8 markers
    for n, tag in [(3, "san"), (10, "ju"), (8, "hachi")]:
        if n < len(script):
            add(f"byte@pos{n}({tag})", script[n])
    add("3*10+8", 3 * 10 + 8)
    add("3*10*8", 3 * 10 * 8)

    # Full-script aggregates
    add("sum_all", sum(script))
    add("len_script", len(script))
    add("xor_all", eval("^".join(str(b) for b in script) or "0"))  # noqa: S307

    # Genesis pubkey x embedded in script
    gx_off = script.find(bytes.fromhex("678afdb0fe554827")[:8])
    if gx_off >= 0:
        add("genesis_pubkey_push_idx", gx_off)

    # Times message slice
    t0 = script.find(b"The Times")
    if t0 >= 0:
        msg = script[t0 : t0 + 75]
        add("times_len", len(msg))
        add("times_sum", sum(msg))
        add("times_int_mod", int.from_bytes(msg[:16].ljust(16, b"\x00"), "big"))

    return feats


def match_report(
    puzzle: str,
    lo: int,
    true_off: int | None,
    terms: list[tuple[str, int]],
    feats: list[tuple[str, int]],
) -> list[str]:
    lines: list[str] = []
    term_by_val: dict[int, list[str]] = {}
    for name, v in terms:
        k = v % lo
        term_by_val.setdefault(k, []).append(name)

    hits: list[tuple[str, str, int]] = []
    for fname, fval in feats:
        residue = fval % lo
        if true_off is not None and residue == true_off % lo:
            hits.append(("TRUE_OFFSET", fname, residue))
        if residue in term_by_val:
            for tname in term_by_val[residue]:
                hits.append((tname, fname, residue))

    lines.append(f"--- {puzzle} (LO bits={lo.bit_length()}) ---")
    if true_off is not None:
        lines.append(f"  true offset (d-shelf2) mod LO = {true_off} ({true_off.bit_length()} bits)")
    if not hits:
        lines.append("  no coinbase feature residue matches true offset or bridge terms")
    else:
        seen: set[tuple[str, str]] = set()
        for tname, fname, res in hits:
            key = (tname, fname)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"  MATCH  {fname} -> {tname}  residue={res} ({res.bit_length()} bits)")
    return lines


def main() -> None:
    if not GENESIS_DUMP.is_file():
        raise SystemExit(f"missing {GENESIS_DUMP}")

    raw = parse_genesis_hex_dump(GENESIS_DUMP)
    script = coinbase_script(raw)
    feats = genesis_coinbase_features(script)

    print("=" * 72)
    print("GENESIS #0 CALIBRATION — coinbase bytes vs shelf2/offset terms")
    print("=" * 72)
    print(f"script length = {len(script)} bytes")
    print(f"genesis pubkey X matches = {GENESIS_X:x}")
    print()
    print("Coinbase ASCII anchors:")
    for label in ("gv.a", "Q2:", "Times", "CA.g"):
        i = script.find({"gv.a": b"gv", "Q2:": b"Q2:", "Times": b"The Times", "CA.g": b"\x04g"}[label])
        print(f"  {label:8s} @ index {i if i >= 0 else 'MISSING'}")
    print()

    calibrations: list[tuple[str, PuzzleConfig]] = []

    # P7 — early solved puzzle (d=76 decimal); band [64, 128)
    cfg7 = PuzzleConfig(
        puzzle_num=7,
        Px=[P7_PX, P7_PX, P7_PX],
        rx=list(PuzzleConfig().rx),
        Py=P7_PY,
        ry=PuzzleConfig().ry,
        row=0,
        known_d=P7_D,
    )
    calibrations.append((f"P7 (d={P7_D})", cfg7))

    # P115 — primary solved bridge calibration
    calibrations.append(("P115", PuzzleConfig(puzzle_num=115, known_d=P115_D)))

    # P1 — scalar anchor d=1 (simplest band); use G as puzzle point
    if _HAS_ECDSA:
        px1, py1 = scalar_from_pubkey(1)
        cfg1 = PuzzleConfig(
            puzzle_num=1,
            Px=[px1, px1, px1],
            rx=list(PuzzleConfig().rx),
            Py=py1,
            ry=PuzzleConfig().ry,
            row=0,
            known_d=1,
        )
        calibrations.append(("P1 (d=1)", cfg1))

    # P135 — unsolved target
    calibrations.append(("P135", PuzzleConfig(puzzle_num=135)))

    # RSZ features from hashkeys.space (115 has known k; 135/160 have R,S,Z,pub only)
    rsz_feats: list[tuple[str, int]] = []
    for pn in (115, 135, 160):
        rsz_feats.extend(rsz_bridge_features(pn))
    combined_feats = feats + rsz_feats

    all_lines: list[str] = []
    p115_true = None
    for label, cfg in calibrations:
        st = bridge_state(cfg)
        lines = match_report(label, st["lo"], st["true_offset"], st["terms"], combined_feats)
        all_lines.extend(lines)
        all_lines.append("")
        if label == "P115":
            p115_true = st["true_offset"]
            shelf2 = st["oitc"].shelf2
            all_lines.append(f"  P115 shelf2 = {shelf2}")
            all_lines.append(f"  P115 known offset = {P115_OFFSET_SHELF2}")
            all_lines.append(f"  recomputed offset = {st['true_offset']}")
            all_lines.append(f"  offset match frozen const = {st['true_offset'] == P115_OFFSET_SHELF2}")
            all_lines.append("")

    print("\n".join(all_lines))

    print("=" * 72)
    print("HASHKEYS RSZ — bridge nonce hook (https://hashkeys.space/rsz/)")
    print("=" * 72)
    p115_rsz = PUZZLE_RSZ[115]
    print(f"  P115 k from site  = {p115_rsz.k}")
    print(f"  P115 k pipeline   = {P115_K}")
    print(f"  P115 k match      = {p115_rsz.k == P115_K}")
    print(f"  P115 ECDSA s*k=z+rd = {p115_rsz.verify_ecdsa(P115_D)}")
    print(f"  P7 d=76 decimal   = {EARLY_SOLVED[7]}  (band [64,128); no RSZ row)")
    print(f"  P7 structural     = d6+d5+d3-1 = 49+21+7-1 = 76")
    print(f"  P135 RSZ pub      = {PUZZLE_RSZ[135].pub_compressed}")
    print(f"  P160 RSZ pub      = {PUZZLE_RSZ[160].pub_compressed}")
    print()

    # Cross-puzzle: same coinbase residue -> candidate offset for P135
    print("=" * 72)
    print("CROSS-PUZZLE PROJECTION (P135 candidates from P115-matched features)")
    print("=" * 72)
    st135 = bridge_state(PuzzleConfig(puzzle_num=135))
    lo135 = st135["lo"]
    shelf2_135 = st135["oitc"].shelf2
    if p115_true is not None:
        for fname, fval in feats:
            off = fval % lo135
            # only show if this feature matched P115 true offset mod P115 LO
            if off % puzzle_band(115)[0] == p115_true % puzzle_band(115)[0]:
                d_cand = (shelf2_135 + off) % N
                in_band = lo135 <= d_cand < st135["hi"]
                print(
                    f"  {fname}: offset_mod_LO135={off} ({off.bit_length()}b) "
                    f"-> d={d_cand} in_band={in_band}"
                )

    out = ROOT / "genesis_calibration_report.txt"
    out.write_text("\n".join(all_lines), encoding="utf-8")
    print()
    print(f"Report written: {out}")


if __name__ == "__main__":
    main()
