# LEDGER S-02 — Native Kangaroo equivalence and throughput

**Status:** **PASS** (CPU / WSL patched JeanLucPons) — **not P135-ready**.

**Prerequisite:** S-01 PASS (correctness only; no P135 feasibility promotion).

> **S-01: PASS** — reference interval-DLP implementation is correct and checkpoint-reproducible. No P135 feasibility promotion.

> **S-02: PASS** — native engine reproduces the same scalars and provides a trustworthy throughput distribution (CPU). P135 remains infeasible at measured rate.

## Locked question — answered

\[
\boxed{\text{Yes (CPU): same scalars; }C\text{ distribution measured; }T_{135}\text{ stated as range.}}
\]

## Formulation (identical to S-01)

\[
L=2^{n-1},\quad Q=P_n-[L]G,\quad Q=[u]G,\quad 0\le u<L
\]

Native infile: `0` … `L-1` (hex), compressed \(Q\).

## Results (10 seeds each; JeanLuc `Final Count`)

| n | PASS | median \(C\) | p90 \(C\) | range \(C\) | notes |
|--:|-----:|-------------:|----------:|------------:|-------|
| 35 | 10/10 | 1.65 | 4.27 | 1.17–5.43 | exact \(u\) |
| 40 | 10/10 | 1.56 | 3.42 | 0.24–3.71 | exact \(u\) |
| 45 | 10/10 | 2.78 | 4.77 | 0.91–5.74 | exact \(u\) |
| 50 | 10/10 | 1.66 | 2.61 | 0.55–2.95 | exact \(u\) |

\[
C_i=\frac{\text{native\_count}_i}{\sqrt{2^{n-1}}}
\]

**\(C\) band (across ladder):** median-of-medians (35–50) ≈ **1.66**; median-of-p90s ≈ **3.84**; max p90 ≈ **4.77**.

**Wording cleanup:** \(C=1.66\) is the **median of per-size medians** over \{35,40,45,50\}, **not** the pooled \(n\ge 45\) median. Pooled \(n\ge 45\) (20 runs): median ≈ **2.08**, empirical p90 ≈ **4.53**. Median of \{45,50\} size-medians alone would be **2.22**. See S-03.

Single-run S-01 \(n=45\) at \(4.21\sqrt{L}\) sits inside this native p90 band — variance, not a bug.

## Checkpoint (interrupt → resume)

n=50: workfile written mid-run, process killed with no key yet; resume recovered exact \(u=d_{50}-L\). **PASS.**

## Throughput (n≥45; process overhead negligible)

| field | value |
|-------|-------|
| Device | WSL Ubuntu CPU, 4 threads |
| Binary | `Kangaroo/kangaroo` (patched `Final Count`) |
| Median effective ops/s | ≈ **1.70×10⁷** |
| Op metric | JeanLuc Count — **not** equated to Python step counter |

## P135 projection (range, not best-run)

\[
T_{135}\approx\frac{C\cdot 2^{67}}{1.70\times 10^{7}\,\mathrm{ops/s}}
\]

| \(C\) | years (approx.) |
|-------|----------------:|
| median 1.66 | **4.6×10⁵** |
| p90 3.84 | **1.1×10⁶** |
| max p90 4.77 | **1.3×10⁶** |

Constant not guaranteed; GPU would change the denominator, not the \(2^{67}\) numerator.

## Promotion gate

| Gate | Status |
|------|--------|
| All recovered keys exact | **PASS** (40/40) |
| No false collision survives verify | **PASS** |
| Checkpoint restoration | **PASS** (n=50 interrupt) |
| Scaling \(\propto\sqrt{L}\) | **PASS** (\(C=O(1)\)) |
| Throughput reproducible | **PASS** |
| \(T_{135}\) as range from distribution | **PASS** |
| GLV / negation on/off measured | **not done** (`USE_SYMMETRY` off; no claim) |
| P135-ready | **NO** |

## Artifacts

| item | path |
|------|------|
| Prereg | `logs/prereg/S-20260710-02_native_kangaroo_equivalence.md` |
| Harness | `s02_native_kangaroo_equivalence.py` |
| Results | `logs/s02_native/S02_results.json` |
| Checkpoint | `logs/s02_native/S02_checkpoint_n50.json` |
| Patch | `Kangaroo/Thread.cpp` Final Count line |

## Next (optional)

- GPU throughput distribution (same ladder / same \(C\) protocol)
- **2026-07-10 probe:** Intel HD 530 Vulkan kangaroo (oritwoen/wgpu) ≈ \(2.8\times10^{5}\) ops/s — **slower** than JeanLuc CPU; see `LEDGER_P135_IGPU_KANGAROO_PROBE.md`
- Controlled `USE_SYMMETRY` on/off builds if claiming negation speedup
- Do **not** promote P135 without a measured ops/s that changes the year-scale conclusion
