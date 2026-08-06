#!/usr/bin/env python3
"""
Pairing-advantage filter for candidate invariants F(d, Px, Py, n).

Laboratory rule:
  "Looks similar" ≠ "depends on the correct pairing."
  Ask:  P_i = [d_i]G  versus  P_π(i) ≠ [d_i]G

Need simultaneously:
  score_real strong,  score_shuffled ordinary,  Δ unusually large (low null p).

False-positive benchmark (sawtooth): Δ ≈ 0.125 with p ≈ 0.15 — not a magical cutoff.

Exclude trivial classes:
  F = 1{P=[d]G}                         (DL recomputation on known solved d)
  formulas implied by y^2 = x^3+7 mod p (curve membership alone)

Pre-register each F before peeking: logs/prereg/F_PREREG_TEMPLATE.md

Promote ONLY if ALL of:
  advantage > 0.12
  p_shuffle < 0.01
  beats random n-bit
  beats random EC pairs
  holds out-of-sample
  direction consistent across puzzle ranges
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Sequence

from ecdsa import SECP256k1, SigningKey

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT_DIR = Path(r"C:\Users\mitch\Desktop\secp256k1\logs")
PREREG_DIR = OUT_DIR / "prereg"
ARCHIVE = Path(
    r"C:\Users\mitch\Desktop\secp256k1\ARCHIVE\briefcase\factoradic_native_lead_falsified"
)
ARCHIVE_PREREG = ARCHIVE / "prereg"

N_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P_FIELD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

# Promotion gate (tightened) — nuisance baseline advantage ≈ 0.12
ADVANTAGE_FLOOR = 0.12
P_SHUFFLE_MAX = 0.01
DEFAULT_SHUFFLE_TRIALS = 1000
DEFAULT_RAND_TRIALS = 200
DEFAULT_EC_TRIALS = 50
HOLDOUT_TRAIN_MAX_N = 50  # train 1..50, test 51..max_n
RANGE_SPLITS = ((1, 35), (36, 70))  # direction consistency


@dataclass
class PuzzleRow:
    n: int
    d: int
    px: int
    py: int


@dataclass
class GateChecks:
    advantage_gt_floor: bool
    p_shuffle_ok: bool
    beats_rand_nbit: bool
    beats_rand_ec: bool
    holds_oos: bool
    direction_consistent: bool

    @property
    def all_pass(self) -> bool:
        return all(
            [
                self.advantage_gt_floor,
                self.p_shuffle_ok,
                self.beats_rand_nbit,
                self.beats_rand_ec,
                self.holds_oos,
                self.direction_consistent,
            ]
        )


@dataclass
class FilterResult:
    name: str
    score_real: float
    score_shuffled_mean: float
    score_shuffled_sd: float
    advantage: float
    p_shuffled: float
    score_rand_nbit_mean: float
    score_rand_ec_mean: float
    score_nearby_mean: float
    control_native_lead_advantage: float
    beats_control: bool
    score_train: float
    score_test: float
    advantage_train: float
    advantage_test: float
    score_range_lo: float
    score_range_hi: float
    gate: GateChecks
    verdict: str  # PROMOTE | FAIL | BORDERLINE
    notes: list[str] = field(default_factory=list)


ScoreFn = Callable[[Sequence[PuzzleRow]], float]


# ---------------------------------------------------------------------------
# Pre-registration + trivial-class guards
# ---------------------------------------------------------------------------

TRIVIAL_EXCLUSIONS = (
    "DL recomputation: F=1{P=[d]G} (or any verify of already-known solved d vs its point)",
    "Curve membership alone: formulas implied by y^2 ≡ x^3+7 (mod p) for every valid point",
)


@dataclass
class PreregRecord:
    """Lock a candidate F before examining results."""

    candidate_id: str
    short_name: str
    formula: str
    domains: str  # e.g. "d in band, Px/Py in F_p, g in p-domain"
    score_definition: str
    expected_direction: str  # "higher" | "lower" | "abs"
    allowed_parameters: dict
    holdout_split: str
    null_families: list[str]
    not_dl_recompute: bool
    not_curve_membership_only: bool
    trivial_exclusion_justification: str
    registered_date: str = field(default_factory=lambda: date.today().isoformat())
    evaluated_date: str | None = None
    locked: bool = True

    def assert_ready(self) -> None:
        if not self.not_dl_recompute or not self.not_curve_membership_only:
            raise ValueError(
                "Candidate fails trivial-class exclusion. "
                + " | ".join(TRIVIAL_EXCLUSIONS)
            )
        if not self.formula.strip() or not self.score_definition.strip():
            raise ValueError("formula and score_definition must be non-empty before eval")
        if not self.locked:
            raise ValueError("Prereg must be locked before evaluation")


def save_prereg(rec: PreregRecord) -> Path:
    PREREG_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PREREG.mkdir(parents=True, exist_ok=True)
    path = PREREG_DIR / f"{rec.candidate_id}.json"
    text = json.dumps(asdict(rec), indent=2)
    path.write_text(text, encoding="utf-8")
    (ARCHIVE_PREREG / path.name).write_text(text, encoding="utf-8")
    return path


def load_prereg(candidate_id: str) -> PreregRecord:
    path = PREREG_DIR / f"{candidate_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return PreregRecord(**data)


def on_curve(px: int, py: int) -> bool:
    return (py * py - (px * px * px + 7)) % P_FIELD == 0


def is_trivial_curve_membership_score(rows: Sequence[PuzzleRow]) -> bool:
    """True if every row already satisfies the curve equation (score would be vacuous)."""
    return all(on_curve(r.px, r.py) for r in rows)


def to_factoradic(n: int) -> list[int]:
    n = abs(int(n))
    digits: list[int] = []
    i = 1
    while n:
        digits.append(n % i)
        n //= i
        i += 1
    return digits


def lead_frac(n: int) -> float:
    digs = to_factoradic(n)
    if not digs:
        return 0.0
    mk = len(digs) - 1
    a = digs[mk]
    return a / mk if mk else 1.0


def lead_native(x: int, m: int) -> int:
    L = max(x.bit_length(), m)
    return x >> (L - m)


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denx = sum((a - mx) ** 2 for a in xs) ** 0.5
    deny = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (denx * deny) if denx and deny else 0.0


def pub_xy(d: int) -> tuple[int, int]:
    sk = SigningKey.from_secret_exponent(d % N_ORDER, curve=SECP256k1, hashfunc=hashlib.sha256)
    raw = sk.get_verifying_key().to_string()
    return int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")


def load_puzzles(max_n: int = 70) -> list[PuzzleRow]:
    rows: list[PuzzleRow] = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            if n > max_n:
                continue
            d = int(row["private_key"])
            px, py = pub_xy(d)
            rows.append(PuzzleRow(n=n, d=d, px=px, py=py))
    rows.sort(key=lambda r: r.n)
    return rows


def score_native_lead_corr(rows: Sequence[PuzzleRow]) -> float:
    """CONTROL: corr(d_frac, native_lead_n(Px)_frac) — known scale-drift artifact."""
    dF = [lead_frac(r.d) for r in rows]
    pF = [lead_frac(lead_native(r.px, r.n)) for r in rows]
    return pearson(dF, pF)


def shuffle_points(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    """Break pairing: keep (n,d), reassign (Px,Py) from the same set."""
    pts = [(r.px, r.py) for r in rows]
    rng.shuffle(pts)
    return [PuzzleRow(n=r.n, d=r.d, px=px, py=py) for r, (px, py) in zip(rows, pts)]


def random_nbit_rows(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    out = []
    for r in rows:
        lo, hi = 1 << (r.n - 1), (1 << r.n) - 1
        d = rng.randrange(lo, hi + 1)
        out.append(PuzzleRow(n=r.n, d=d, px=rng.randrange(P_FIELD), py=rng.randrange(P_FIELD)))
    return out


def random_ec_rows(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    out = []
    for r in rows:
        lo, hi = 1 << (r.n - 1), (1 << r.n) - 1
        d = rng.randrange(lo, hi + 1)
        px, py = pub_xy(d)
        out.append(PuzzleRow(n=r.n, d=d, px=px, py=py))
    return out


def nearby_height_rows(rows: Sequence[PuzzleRow], rng: random.Random) -> list[PuzzleRow]:
    by_n = {r.n: r for r in rows}
    ns = [r.n for r in rows]
    out = []
    for r in rows:
        cands = [n for n in ns if 1 <= abs(n - r.n) <= 3] or [n for n in ns if n != r.n]
        j = by_n[rng.choice(cands)]
        out.append(PuzzleRow(n=r.n, d=r.d, px=j.px, py=j.py))
    return out


def _sign(x: float) -> int:
    if x > 1e-12:
        return 1
    if x < -1e-12:
        return -1
    return 0


def _subset_advantage(
    score_fn: ScoreFn,
    rows: Sequence[PuzzleRow],
    rng: random.Random,
    shuffle_trials: int,
    make_shuffle: Callable[[Sequence[PuzzleRow], random.Random], list[PuzzleRow]] | None = None,
) -> tuple[float, float]:
    """Return (score_real, advantage) on a subset."""
    if len(rows) < 8:
        return 0.0, 0.0
    _sh = make_shuffle or shuffle_points
    real = score_fn(rows)
    shuf = [score_fn(_sh(rows, rng)) for _ in range(shuffle_trials)]
    return real, real - statistics.fmean(shuf)


def evaluate(
    name: str,
    score_fn: ScoreFn,
    rows: Sequence[PuzzleRow],
    *,
    rng: random.Random | None = None,
    shuffle_trials: int = DEFAULT_SHUFFLE_TRIALS,
    rand_trials: int = DEFAULT_RAND_TRIALS,
    ec_trials: int = DEFAULT_EC_TRIALS,
    advantage_floor: float = ADVANTAGE_FLOOR,
    p_shuffle_max: float = P_SHUFFLE_MAX,
    holdout_train_max_n: int = HOLDOUT_TRAIN_MAX_N,
    prereg: PreregRecord | None = None,
    make_rand_nbit: Callable[[Sequence[PuzzleRow], random.Random], list[PuzzleRow]] | None = None,
    make_rand_ec: Callable[[Sequence[PuzzleRow], random.Random], list[PuzzleRow]] | None = None,
    make_nearby: Callable[[Sequence[PuzzleRow], random.Random], list[PuzzleRow]] | None = None,
    make_shuffle: Callable[[Sequence[PuzzleRow], random.Random], list[PuzzleRow]] | None = None,
    control_rows: Sequence[PuzzleRow] | None = None,
) -> FilterResult:
    rng = rng or random.Random(20260709)
    notes: list[str] = []
    _shuffle = make_shuffle or shuffle_points
    _rand_nbit = make_rand_nbit or random_nbit_rows
    _rand_ec = make_rand_ec or random_ec_rows
    _nearby = make_nearby or nearby_height_rows

    if prereg is not None:
        prereg.assert_ready()
        notes.append(f"prereg locked: {prereg.candidate_id} ({prereg.short_name})")
    else:
        notes.append(
            "WARNING: no prereg record — register F before peeking "
            f"(see {PREREG_DIR / 'F_PREREG_TEMPLATE.md'})"
        )

    # Vacuous curve-membership check: all real points are on-curve by construction;
    # flag if the candidate name suggests that class.
    if "curve" in name.lower() and "membership" in name.lower():
        notes.append("REJECT class: curve-membership-only candidates are excluded.")
    if "1{p=[d]g}" in name.lower().replace(" ", "") or "dl_recompute" in name.lower():
        notes.append("REJECT class: DL-recomputation candidates are excluded.")

    score_real = score_fn(rows)
    shuf = [score_fn(_shuffle(rows, rng)) for _ in range(shuffle_trials)]
    shuf_mean = statistics.fmean(shuf)
    shuf_sd = statistics.pstdev(shuf) if len(shuf) > 1 else 0.0
    ge = sum(1 for s in shuf if abs(s) >= abs(score_real))
    p_shuf = (ge + 1) / (len(shuf) + 1)
    advantage = score_real - shuf_mean

    rand_scores = [score_fn(_rand_nbit(rows, rng)) for _ in range(rand_trials)]
    ec_scores = [score_fn(_rand_ec(rows, rng)) for _ in range(ec_trials)]
    near_scores = [score_fn(_nearby(rows, rng)) for _ in range(rand_trials)]
    rand_mean = statistics.fmean(rand_scores)
    ec_mean = statistics.fmean(ec_scores)
    near_mean = statistics.fmean(near_scores)

    # Control baseline (native-n sawtooth) — use original (d,Px) rows if provided
    ctrl_src = control_rows if control_rows is not None else rows
    ctrl_real = score_native_lead_corr(ctrl_src)
    ctrl_shuf = [
        score_native_lead_corr(shuffle_points(ctrl_src, rng)) for _ in range(min(200, shuffle_trials))
    ]
    ctrl_adv = ctrl_real - statistics.fmean(ctrl_shuf)
    beats_control = abs(advantage) > abs(ctrl_adv) + 0.02

    # Out-of-sample chronological holdout
    train = [r for r in rows if r.n <= holdout_train_max_n]
    test = [r for r in rows if r.n > holdout_train_max_n]
    oos_shuf = max(100, shuffle_trials // 5)
    score_train, adv_train = _subset_advantage(score_fn, train, rng, oos_shuf, _shuffle)
    score_test, adv_test = _subset_advantage(score_fn, test, rng, oos_shuf, _shuffle)

    # Direction consistency across ranges
    lo_a, lo_b = RANGE_SPLITS[0]
    hi_a, hi_b = RANGE_SPLITS[1]
    range_lo = [r for r in rows if lo_a <= r.n <= lo_b]
    range_hi = [r for r in rows if hi_a <= r.n <= hi_b]
    score_lo, adv_lo = _subset_advantage(score_fn, range_lo, rng, oos_shuf, _shuffle)
    score_hi, adv_hi = _subset_advantage(score_fn, range_hi, rng, oos_shuf, _shuffle)

    # Gate checks
    # "beats" null means real score is more extreme in the SAME direction as advantage,
    # and |real| exceeds |null mean| (or advantage vs that null is positive in score space).
    # For correlation-style scores: require score_real > null_mean when advantage > 0,
    # and score_real < null_mean when advantage < 0.
    def beats_null(null_mean: float) -> bool:
        if advantage >= 0:
            return score_real > null_mean + 0.02
        return score_real < null_mean - 0.02

    holds_oos = (
        _sign(adv_train) == _sign(adv_test) != 0
        and abs(adv_test) > 0.05
        and abs(adv_train) > 0.05
    )
    # Prefer same direction of raw score (or advantage) across ranges
    direction_consistent = _sign(score_lo) == _sign(score_hi) != 0 or (
        _sign(adv_lo) == _sign(adv_hi) != 0 and abs(adv_lo) > 0.05 and abs(adv_hi) > 0.05
    )

    gate = GateChecks(
        advantage_gt_floor=advantage > advantage_floor,
        p_shuffle_ok=p_shuf < p_shuffle_max,
        beats_rand_nbit=beats_null(rand_mean),
        beats_rand_ec=beats_null(ec_mean),
        holds_oos=holds_oos,
        direction_consistent=direction_consistent,
    )

    if name.upper().startswith("CONTROL"):
        verdict = "FAIL"
        notes.append("CONTROL feature: always FAIL by policy (sawtooth null model).")
    elif gate.all_pass and beats_control:
        verdict = "PROMOTE"
    elif advantage <= 0.05 and p_shuf > 0.10:
        verdict = "FAIL"
        notes.append("Advantage near zero / shuffle does not destroy score.")
    elif not gate.advantage_gt_floor or not gate.p_shuffle_ok:
        verdict = "FAIL"
        notes.append("Failed hard gate: advantage>0.12 and p_shuffle<0.01.")
    else:
        verdict = "BORDERLINE"
        failed = [k for k, v in asdict(gate).items() if not v]
        notes.append(f"Partial gate failures: {', '.join(failed)}")

    return FilterResult(
        name=name,
        score_real=score_real,
        score_shuffled_mean=shuf_mean,
        score_shuffled_sd=shuf_sd,
        advantage=advantage,
        p_shuffled=p_shuf,
        score_rand_nbit_mean=rand_mean,
        score_rand_ec_mean=ec_mean,
        score_nearby_mean=near_mean,
        control_native_lead_advantage=ctrl_adv,
        beats_control=beats_control,
        score_train=score_train,
        score_test=score_test,
        advantage_train=adv_train,
        advantage_test=adv_test,
        score_range_lo=score_lo,
        score_range_hi=score_hi,
        gate=gate,
        verdict=verdict,
        notes=notes,
    )


def format_result(r: FilterResult) -> str:
    g = r.gate
    lines = [
        f"name:              {r.name}",
        f"score_real:        {r.score_real:+.4f}",
        f"score_shuffled:    {r.score_shuffled_mean:+.4f}  (sd={r.score_shuffled_sd:.4f})",
        f"ADVANTAGE:         {r.advantage:+.4f}   [= real - shuffled]",
        f"p_shuffled:        {r.p_shuffled:.4f}",
        f"rand n-bit mean:   {r.score_rand_nbit_mean:+.4f}",
        f"rand EC mean:      {r.score_rand_ec_mean:+.4f}",
        f"nearby height mean:{r.score_nearby_mean:+.4f}",
        f"control native-n advantage: {r.control_native_lead_advantage:+.4f}",
        f"beats_control:     {r.beats_control}",
        f"holdout train/test score:     {r.score_train:+.4f} / {r.score_test:+.4f}",
        f"holdout train/test advantage: {r.advantage_train:+.4f} / {r.advantage_test:+.4f}",
        f"range scores ({RANGE_SPLITS[0]}/{RANGE_SPLITS[1]}): "
        f"{r.score_range_lo:+.4f} / {r.score_range_hi:+.4f}",
        "",
        "PROMOTION GATE:",
        f"  [ {'OK' if g.advantage_gt_floor else 'NO'} ] advantage > {ADVANTAGE_FLOOR}",
        f"  [ {'OK' if g.p_shuffle_ok else 'NO'} ] p_shuffle < {P_SHUFFLE_MAX}",
        f"  [ {'OK' if g.beats_rand_nbit else 'NO'} ] beats random n-bit",
        f"  [ {'OK' if g.beats_rand_ec else 'NO'} ] beats random EC pairs",
        f"  [ {'OK' if g.holds_oos else 'NO'} ] holds out-of-sample",
        f"  [ {'OK' if g.direction_consistent else 'NO'} ] direction consistent across ranges",
        f"VERDICT:           {r.verdict}",
    ]
    for n in r.notes:
        lines.append(f"note: {n}")
    return "\n".join(lines)


def demo_control(rows: list[PuzzleRow]) -> FilterResult:
    return evaluate(
        "CONTROL: native m=n factoradic lead corr",
        score_native_lead_corr,
        rows,
        shuffle_trials=DEFAULT_SHUFFLE_TRIALS,
        rand_trials=DEFAULT_RAND_TRIALS,
        ec_trials=40,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Pairing-advantage promotion gate")
    ap.add_argument("--demo-control", action="store_true", help="Run native-lead control (expect FAIL)")
    ap.add_argument("--max-n", type=int, default=70)
    args = ap.parse_args()

    rows = load_puzzles(args.max_n)
    print(f"Loaded {len(rows)} puzzles (1..{args.max_n})")

    print()
    print("=" * 72)
    print("CONTROL DEMO — native lead (expect FAIL under promotion gate)")
    print("=" * 72)
    res = demo_control(rows)
    print(format_result(res))

    policy = {
        "laboratory_rule": (
            '"Looks similar" ≠ "depends on the correct pairing." '
            "Ask P_i=[d_i]G versus P_π(i)≠[d_i]G. "
            "Need score_real strong, score_shuffled ordinary, Δ unusually large."
        ),
        "promote_only_if": {
            "advantage": f"> {ADVANTAGE_FLOOR}",
            "p_shuffle": f"< {P_SHUFFLE_MAX}",
            "beats_random_nbit": True,
            "beats_random_ec": True,
            "holds_out_of_sample": True,
            "direction_consistent_across_ranges": True,
        },
        "false_positive_benchmark": {
            "control": "native m=n factoradic lead",
            "score_real": 0.610,
            "score_shuffled": 0.485,
            "advantage": 0.125,
            "p_shuffle": 0.15,
            "meaning": (
                "Ordinary null noise / convincing coincidence shape — "
                "NOT a magical cutoff. New F must beat this AND have low null p."
            ),
        },
        "exclude_trivial": list(TRIVIAL_EXCLUSIONS),
        "preregistration": {
            "required_before_peeking": True,
            "template": str(PREREG_DIR / "F_PREREG_TEMPLATE.md"),
            "fields": [
                "exact formula and reductions",
                "domains p or N",
                "score definition",
                "expected direction",
                "allowed parameters",
                "holdout split",
                "null families",
            ],
        },
        "worthwhile_middle_ground": (
            "Compact F(d,Px,Py) not guaranteed by curve membership alone "
            "and destroyed by permutation — fingerprint of correct attachment."
        ),
        "archive": str(ARCHIVE),
    }
    payload = {"policy": policy, "result": asdict(res)}
    text = format_result(res) + "\n\n" + json.dumps(payload, indent=2)
    out = OUT_DIR / "PAIRING_ADVANTAGE_FILTER_CONTROL.txt"
    out.write_text(text, encoding="utf-8")
    (ARCHIVE / "PAIRING_ADVANTAGE_FILTER_CONTROL.txt").write_text(text, encoding="utf-8")

    # Gate doc is maintained as a locked policy file (do not overwrite with a stub).
    gate_md = OUT_DIR / "PAIRING_PROMOTION_GATE.md"
    if gate_md.exists():
        (ARCHIVE / "PAIRING_PROMOTION_GATE.md").write_text(
            gate_md.read_text(encoding="utf-8"), encoding="utf-8"
        )
    PREREG_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PREREG.mkdir(parents=True, exist_ok=True)
    tmpl = PREREG_DIR / "F_PREREG_TEMPLATE.md"
    if tmpl.exists():
        (ARCHIVE_PREREG / tmpl.name).write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")

    print()
    print(f"Wrote {out}")
    print(f"Gate policy: {gate_md}")
    print(f"Prereg template: {tmpl}")
    print()
    print('Rule: "Looks similar" != "depends on the correct pairing."')
    print("Gate: advantage>0.12, p_shuffle<0.01, beats nulls, OOS, direction-consistent.")
    print("Exclude: DL-recompute and curve-membership-only. Preregister before peeking.")


if __name__ == "__main__":
    main()
