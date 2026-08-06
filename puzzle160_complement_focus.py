#!/usr/bin/env python3
"""Puzzle 160 — unified complement m-leg focus: [2^96, 2^97) partner search.

Combines:
  - epsilon ladder  m = 2^96 + eps·2^57  + NP1 divisibility scan
  - G-prefix shell prune on m·P_160 walks
  - positional k-ladder partners d_k(N), d_k(P)
  - KeyHunt BSGS .bat export for top d windows around (N+1)//m

Gate: d·G == P_160 (only EC match certifies the key).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from multiprocessing import Pool, cpu_count
from pathlib import Path

from ecdsa import SECP256k1

from probe_height96 import (
    NDIG,
    fingerprints_for_point,
    rank_board,
    score_trace,
    scalar_mul,
    trace_mult,
)

# Reuse ladder math from epsilon tool (same repo).
from puzzle160_epsilon_ladder import (
    D_BASE,
    D_HI,
    D_LO,
    OFFSET_96,
    P_SHIFT,
    STEP_56,
    STEP_57,
    check_d_g,
    d_from_k,
    ladder_params,
    scan_divisors,
)

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
NP1 = N + 1
M_LO, M_HI = 2**96, 2**97
G = SECP256k1.generator
GX, GY = G.x(), G.y()

P160 = (
    101616124637840542991531253248586524020213215258338643076214814468447630501491,
    88132823371574229813684435207239348220522140366126834573803505878170136640646,
)
P160_X, P160_Y = P160

ROOT = Path(__file__).resolve().parent
OUT_TXT = ROOT / "puzzle160_complement_focus_report.txt"
OUT_JSON = ROOT / "puzzle160_complement_focus.json"
EXPORT_DIR = ROOT / "puzzle160_keyhunt_bsgs" / "complement_exports"
PATHS_BAT = ROOT / "puzzle160_keyhunt_bsgs" / "paths.bat"
PUB_REL = "P160_compressed.pub"

ANCHOR_A = 0x1564DE685E4BB400000000000
MAX_EPS_SPAN_DEFAULT = 1_000_000
# KeyHunt BSGS: range (hi-lo) must be >= default BSGS_N (0x100000000000); see keyhunt.cpp
MIN_KEYHUNT_SPAN = 0x100000000000
DEFAULT_HALF_WINDOW = max(10**12, MIN_KEYHUNT_SPAN // 2)


@dataclass
class ShellRow:
    m: int
    name: str
    g_contains: int
    g_start: int
    px_contains: int
    clean_score: float
    np1_rem: int
    d_est: int
    d_in_band: bool
    exact_div: bool
    d_g_match: bool


@dataclass
class DWindow:
    label: str
    center: int
    lo: int
    hi: int
    source: str
    span: int
    m_partner: int | None = None
    clean_score: float | None = None


def clip_d_range(center: int, half_window: int, min_span: int = MIN_KEYHUNT_SPAN) -> tuple[int, int, int]:
    """KeyHunt BSGS needs (hi-lo+1) >= min_span. Extend downward first when clipped at band top."""
    d_top = D_HI - 1
    lo = max(center - half_window, D_LO)
    hi = min(center + half_window, d_top)
    span = hi - lo + 1
    if span < min_span:
        need = min_span - span
        extend_lo = min(need, lo - D_LO)
        lo -= extend_lo
        need -= extend_lo
        if need > 0:
            hi = min(d_top, hi + need)
        span = hi - lo + 1
    if span < min_span:
        hi = d_top
        lo = max(D_LO, d_top - min_span + 1)
        span = hi - lo + 1
    return lo, hi, span


@dataclass
class ComplementConfig:
    eps_lo: int = 0
    eps_hi: int | None = None
    m_max_samples: int = 3000
    ladder_k: int = 8
    window: int = DEFAULT_HALF_WINDOW
    workers: int = max(1, cpu_count() - 1)
    export_bats: bool = True
    quick: bool = False


@dataclass
class ComplementResult:
    config: ComplementConfig
    divisor_hits: list[tuple[int, int, int]] = field(default_factory=list)
    shell_rows: list[ShellRow] = field(default_factory=list)
    ladder_rows: list[dict] = field(default_factory=list)
    d_windows: list[DWindow] = field(default_factory=list)
    solution_d: int | None = None
    solution_method: str | None = None
    elapsed_s: float = 0.0
    lines: list[str] = field(default_factory=list)


def verify_d(d: int) -> bool:
    if not (D_LO <= d < D_HI):
        return False
    pt = d * G
    return pt.x() == P160_X and pt.y() == P160_Y


def write_solution(method: str, d: int, extra: str = "") -> None:
    sol = ROOT / "PUZZLE_160_SOLUTION.txt"
    body = f"method={method}\nd={d}\nhex={hex(d)}\n{extra}\n"
    sol.write_text(body, encoding="utf-8")
    print(f"\n*** SOLUTION *** {method}\nd={d}\nWrote {sol}")


def g_fingerprints(ndig: int = NDIG) -> dict[str, str]:
    return fingerprints_for_point(GX, GY)


def score_m_shell(m: int, name: str) -> ShellRow | None:
    shell = scalar_mul(m, P160)
    if shell is None:
        return None
    tr = trace_mult(NP1, shell)
    fps_g = g_fingerprints()
    stats = score_trace(tr, fps_g, ndig=NDIG)
    g_contains = sum(s.contains for s in stats.values())
    g_start = sum(s.start for s in stats.values())
    px_stats = score_trace(tr, fingerprints_for_point(P160_X, P160_Y), ndig=NDIG)
    px_contains = rank_board(px_stats, "contains")[0][1]
    rem = NP1 % m
    d_est = NP1 // m
    exact = rem == 0
    d_band = D_LO <= d_est < D_HI
    d_g = verify_d(d_est) if exact else False
    clean = -g_contains - 0.5 * g_start + 0.1 * px_contains - (rem.bit_length() / 256.0)
    return ShellRow(
        m=m,
        name=name,
        g_contains=g_contains,
        g_start=g_start,
        px_contains=px_contains,
        clean_score=clean,
        np1_rem=rem,
        d_est=d_est,
        d_in_band=d_band,
        exact_div=exact,
        d_g_match=d_g,
    )


def iter_m_samples(max_samples: int) -> list[tuple[str, int]]:
    """Anchors + coarse grid across [2^96, 2^97)."""
    seen: set[int] = set()
    out: list[tuple[str, int]] = []

    def add(name: str, m: int) -> None:
        if M_LO <= m < M_HI and m not in seen:
            seen.add(m)
            out.append((name, m))

    add("m_lo", M_LO)
    add("m_lo+2^57", M_LO + STEP_57)
    add("m_lo+2^56", M_LO + STEP_56)
    add("m_mid", (M_LO + M_HI - 1) // 2)
    add("m_hi-1", M_HI - 1)
    if M_LO <= ANCHOR_A < M_HI:
        add("anchor_a", ANCHOR_A)

    # Positional ladder fixed m = 2^96 for k>=1
    add("ladder_m", 2**96)

    # Epsilon grid: m = 2^96 + eps·2^57
    base, step, _, max_eps = ladder_params(96)
    eps_stride = max(1, max_eps // max(max_samples // 2, 1))
    for eps in range(0, min(max_eps, max_samples * eps_stride), eps_stride):
        add(f"eps_{eps}", base + eps * step)
        if len(out) >= max_samples:
            break

    # Uniform coarse grid fill
    span = M_HI - M_LO
    grid_step = max(1, span // max(max_samples - len(out), 1))
    for i, m in enumerate(range(M_LO, M_HI, grid_step)):
        if len(out) >= max_samples:
            break
        add(f"grid_{i}", m)

    return out


def run_positional_ladder(k_max: int) -> list[dict]:
    rows: list[dict] = []
    for k in range(1, k_max + 1):
        for leg in ("n", "p"):
            d = d_from_k(k, leg)
            m = 2**96
            rem = NP1 % m
            rows.append(
                {
                    "k": k,
                    "leg": leg,
                    "m": m,
                    "d_pred": d,
                    "d_in_band": D_LO <= d < D_HI,
                    "rem": rem,
                    "exact_div": rem == 0,
                    "d_g_match": check_d_g(d) if rem == 0 else verify_d(d) if D_LO <= d < D_HI else False,
                }
            )
    return rows


def build_d_windows(shell_rows: list[ShellRow], cfg: ComplementConfig) -> list[DWindow]:
    windows: dict[int, DWindow] = {}

    def add(label: str, center: int, source: str, m_partner: int | None = None, clean: float | None = None) -> None:
        if not (D_LO <= center < D_HI):
            return
        lo, hi, span = clip_d_range(center, cfg.window)
        key = center
        if key not in windows:
            windows[key] = DWindow(
                label=label,
                center=center,
                lo=lo,
                hi=hi,
                source=source,
                span=span,
                m_partner=m_partner,
                clean_score=clean,
            )

    # Exact NP1 hits first
    for r in shell_rows:
        if r.exact_div and r.d_in_band:
            add(f"exact_m_{r.name}", r.d_est, "np1_exact", r.m, r.clean_score)

    # Cleanest shells by d_est
    ranked = sorted(shell_rows, key=lambda x: (-x.clean_score, x.np1_rem))
    for i, r in enumerate(ranked[:12]):
        if r.d_in_band:
            add(f"clean_{i}_{r.name}", r.d_est, "g_prune_clean", r.m, r.clean_score)

    # D_BASE anchor from ladder
    add("D_BASE", D_BASE, "ladder_D_BASE")

    # Small remainder bias
    small_rem = sorted([r for r in shell_rows if r.d_in_band], key=lambda x: x.np1_rem)[:8]
    for i, r in enumerate(small_rem):
        add(f"small_rem_{i}", r.d_est, f"rem={r.np1_rem}", r.m, r.clean_score)

    return sorted(windows.values(), key=lambda w: (-(w.clean_score or 0), w.center))


def export_keyhunt_bats(windows: list[DWindow], cfg: ComplementConfig) -> list[Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, w in enumerate(windows[:20], start=1):
        bat = EXPORT_DIR / f"run_p160_comp_{i:03d}_{w.label[:24].replace(' ', '_')}.bat"
        bat.write_text(
            f"""@echo off
setlocal
call "%~dp0..\\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: {w.label}
echo Source: {w.source}
echo Center d={w.center}
echo m partner={w.m_partner}
echo Range {w.lo:x}:{w.hi:x}  span={w.span}  (KeyHunt min span {MIN_KEYHUNT_SPAN:x})
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r {w.lo:x}:{w.hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
""",
            encoding="utf-8",
        )
        written.append(bat)

    manifest = EXPORT_DIR / "complement_manifest.txt"
    manifest.write_text(
        "\n".join(
            [
                "Puzzle 160 complement KeyHunt exports",
                f"half_window=+-{cfg.window}  min_span={MIN_KEYHUNT_SPAN:x}",
                f"count={len(written)}",
                "",
                *[f"{p.name}  {w.label}  span={w.span}  {w.lo:x}:{w.hi:x}" for p, w in zip(written, windows[:20])],
            ]
        ),
        encoding="utf-8",
    )
    written.append(manifest)
    return written


def run_complement_focus(cfg: ComplementConfig | None = None) -> ComplementResult:
    if cfg is None:
        cfg = ComplementConfig()
    if cfg.quick:
        cfg.eps_hi = cfg.eps_hi or min(99_999, cfg.eps_lo + 100_000 - 1)
        cfg.m_max_samples = min(cfg.m_max_samples, 500)
        cfg.ladder_k = min(cfg.ladder_k, 5)
        cfg.export_bats = False

    base, step, _, max_eps = ladder_params(96)
    eps_hi = cfg.eps_hi if cfg.eps_hi is not None else min(max_eps - 1, cfg.eps_lo + MAX_EPS_SPAN_DEFAULT - 1)

    t0 = time.time()
    lines: list[str] = [
        "Puzzle 160 complement focus — m-leg [2^96, 2^97)",
        f"d target [2^159, 2^160)  NP1 bits={NP1.bit_length()}",
        f"D_BASE = floor((N+1)/2^96) = {D_BASE}",
        f"eps scan [{cfg.eps_lo}, {eps_hi}]  step=2^57  workers={cfg.workers}",
        f"m-shell samples cap={cfg.m_max_samples}  ladder k=1..{cfg.ladder_k}",
        "",
    ]

    result = ComplementResult(config=cfg, lines=lines)

    # Phase 1: epsilon divisor scan
    lines.append("=== Phase 1: epsilon NP1 divisor scan ===")
    hits = scan_divisors(base, step, cfg.eps_lo, eps_hi, cfg.workers, chunk=250_000, progress=not cfg.quick)
    result.divisor_hits = hits
    lines.append(f"exact m|(N+1) hits in eps window: {len(hits)}")
    for eps, m, d in hits[:20]:
        ok = verify_d(d)
        lines.append(f"  eps={eps}  m={m}  d={d}  d*G={ok}")
        if ok:
            result.solution_d = d
            result.solution_method = f"np1_divisor eps={eps}"
            write_solution(result.solution_method, d, f"m={m}\neps={eps}\n")

    if result.solution_d is not None:
        result.elapsed_s = time.time() - t0
        result.lines = lines
        return result

    # Phase 2: G-prefix m-shell prune
    lines.append("")
    lines.append("=== Phase 2: G-prefix m-shell prune ===")
    shell_rows: list[ShellRow] = []
    for name, m in iter_m_samples(cfg.m_max_samples):
        row = score_m_shell(m, name)
        if row:
            shell_rows.append(row)
            if row.d_g_match:
                result.solution_d = row.d_est
                result.solution_method = f"shell exact {name}"
                write_solution(result.solution_method, row.d_est, f"m={m}\n")
                break
    result.shell_rows = shell_rows
    ranked = sorted(shell_rows, key=lambda x: (-x.clean_score, -x.px_contains))
    lines.append(f"shells scored: {len(shell_rows)}")
    for r in ranked[:10]:
        lines.append(
            f"  {r.name:14} m={r.m}  clean={r.clean_score:.2f}  G={r.g_contains}  "
            f"rem={r.np1_rem}  d_est={r.d_est}  band={r.d_in_band}"
        )

    if result.solution_d is not None:
        result.elapsed_s = time.time() - t0
        result.lines = lines
        return result

    # Phase 3: positional ladder
    lines.append("")
    lines.append("=== Phase 3: positional k-ladder (m=2^96) ===")
    ladder = run_positional_ladder(cfg.ladder_k)
    result.ladder_rows = ladder
    for row in ladder:
        tag = f"k={row['k']} leg={row['leg']}"
        lines.append(
            f"  {tag}  d={row['d_pred']}  band={row['d_in_band']}  "
            f"rem={row['rem']}  dG={row['d_g_match']}"
        )
        if row["d_g_match"]:
            result.solution_d = row["d_pred"]
            result.solution_method = f"positional {tag}"
            write_solution(result.solution_method, row["d_pred"])
            break

    if result.solution_d is not None:
        result.elapsed_s = time.time() - t0
        result.lines = lines
        return result

    # Phase 4: KeyHunt d-window export
    lines.append("")
    lines.append("=== Phase 4: KeyHunt d-window export ===")
    windows = build_d_windows(shell_rows, cfg)
    result.d_windows = windows
    lines.append(f"d windows ranked: {len(windows)}  (half_window=+-{cfg.window}, min_span={MIN_KEYHUNT_SPAN:x})")
    for w in windows[:8]:
        lines.append(f"  {w.label:20} center={w.center}  span={w.span}  {w.lo:x}:{w.hi:x}  src={w.source}")

    if cfg.export_bats and windows:
        bats = export_keyhunt_bats(windows, cfg)
        lines.append(f"exported {len(bats)} files under {EXPORT_DIR.relative_to(ROOT)}")
        lines.append(f"manifest: {EXPORT_DIR.name}/complement_manifest.txt")

    lines.append("")
    lines.append("NO SOLUTION this pass — run KeyHunt on complement_exports/ or widen --eps-hi.")
    result.elapsed_s = time.time() - t0
    result.lines = lines
    return result


def format_report(result: ComplementResult) -> str:
    return "\n".join(result.lines) + f"\n\nelapsed={result.elapsed_s:.1f}s\n"


def write_artifacts(result: ComplementResult) -> None:
    report = format_report(result)
    OUT_TXT.write_text(report, encoding="utf-8")
    payload = {
        "elapsed_s": result.elapsed_s,
        "solution_d": str(result.solution_d) if result.solution_d else None,
        "solution_method": result.solution_method,
        "divisor_hits": [(e, str(m), str(d)) for e, m, d in result.divisor_hits[:50]],
        "top_shells": [asdict(r) for r in sorted(result.shell_rows, key=lambda x: -x.clean_score)[:30]],
        "d_windows": [
            {
                "label": w.label,
                "center": str(w.center),
                "lo": hex(w.lo),
                "hi": hex(w.hi),
                "source": w.source,
            }
            for w in result.d_windows[:30]
        ],
        "ladder": result.ladder_rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Puzzle 160 unified complement m-leg runner")
    ap.add_argument("--eps-lo", type=int, default=0)
    ap.add_argument("--eps-hi", type=int, default=None)
    ap.add_argument("--m-samples", type=int, default=3000)
    ap.add_argument("--ladder-k", type=int, default=8)
    ap.add_argument("--window", type=int, default=DEFAULT_HALF_WINDOW, help="Half-width around d center (total span auto-bumped to KeyHunt min)")
    ap.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    ap.add_argument("--no-export-bats", action="store_true")
    ap.add_argument("--quick", action="store_true", help="fast pass for pipeline hook")
    args = ap.parse_args()

    cfg = ComplementConfig(
        eps_lo=args.eps_lo,
        eps_hi=args.eps_hi,
        m_max_samples=args.m_samples,
        ladder_k=args.ladder_k,
        window=args.window,
        workers=args.workers,
        export_bats=not args.no_export_bats,
        quick=args.quick,
    )
    result = run_complement_focus(cfg)
    write_artifacts(result)
    print(format_report(result))
    print(f"Wrote {OUT_TXT}")
    print(f"Wrote {OUT_JSON}")
    return 0 if result.solution_d is None else 0


if __name__ == "__main__":
    raise SystemExit(main())
