#!/usr/bin/env python3
"""
ALL puzzles 1..160 factoradic view.

Solved (known d): full reconstruction colored by order.
Unsolved: band construction window — possible lead a*k! and five-back span.
"""
from __future__ import annotations

import colorsys
import csv
import math
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT_HTML = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_ALL_PUZZLES_1_160.html")
OUT_TXT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_ALL_PUZZLES_1_160.txt")

PUZZLE_LO = 1
PUZZLE_HI = 160


def to_factoradic(n: int) -> list[int]:
    digits: list[int] = []
    i = 1
    x = abs(int(n))
    while x:
        digits.append(x % i)
        x //= i
        i += 1
    return digits


def reconstruct(digs: list[int]) -> tuple[int, list[tuple[int, int, int]]]:
    terms: list[tuple[int, int, int]] = []
    total = 0
    for k, a in enumerate(digs):
        if not a:
            continue
        term = a * math.factorial(k)
        total += term
        terms.append((k, a, term))
    terms.reverse()
    return total, terms


def band(n: int) -> tuple[int, int]:
    return 1 << (n - 1), (1 << n) - 1


def band_lead_options(n: int) -> list[tuple[int, int, int]]:
    """Return list of (k, a_lo, a_hi) possible leading terms in puzzle-n band."""
    lo, hi = band(n)
    out: list[tuple[int, int, int]] = []
    k = 1
    while math.factorial(k) <= hi:
        fk = math.factorial(k)
        fkp = math.factorial(k + 1)
        L = max(lo, fk)
        H = min(hi, fkp - 1)
        if L <= H:
            alo = max(L // fk, 1)
            ahi = min(H // fk, k)
            if alo <= ahi:
                out.append((k, alo, ahi))
        k += 1
    return out


def downward_run(digs: list[int]) -> tuple[int, int, list[tuple[int, int]]]:
    if not digs:
        return 0, 0, []
    mk = len(digs) - 1
    terms: list[tuple[int, int]] = []
    for k in range(mk, -1, -1):
        a = digs[k]
        if a == 0:
            break
        terms.append((k, a))
    stop = terms[-1][0] - 1 if terms else -1
    return mk, stop, terms


def order_color(max_k: int, k_min: int, k_max: int) -> tuple[str, str, str]:
    palette = [
        ((255, 140, 40), (40, 20, 0), (255, 180, 90)),
        ((50, 110, 220), (230, 240, 255), (120, 170, 255)),
        ((40, 170, 90), (10, 40, 20), (100, 220, 140)),
        ((200, 60, 140), (255, 230, 245), (240, 120, 180)),
        ((30, 170, 180), (10, 40, 45), (90, 220, 230)),
        ((210, 180, 40), (40, 35, 0), (240, 220, 100)),
        ((160, 80, 220), (245, 235, 255), (200, 150, 255)),
        ((220, 80, 60), (255, 235, 230), (255, 140, 120)),
    ]
    idx = (max_k - k_min) % len(palette) if k_max >= k_min else 0
    bg, fg, acc = palette[idx]

    def css(rgb: tuple[int, int, int]) -> str:
        return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    return css(bg), css(fg), css(acc)


def unsolved_color() -> tuple[str, str, str]:
    return "rgb(90,90,95)", "rgb(240,240,240)", "rgb(160,160,170)"


def main() -> None:
    solved: dict[int, int] = {}
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            solved[int(row["puzzle"])] = int(row["private_key"])

    # Also merge any extras if present — currently same 82
    records = []
    for n in range(PUZZLE_LO, PUZZLE_HI + 1):
        lo, hi = band(n)
        leads = band_lead_options(n)
        if n in solved:
            d = solved[n]
            digs = to_factoradic(d)
            total, terms = reconstruct(digs)
            mk, stop, run_terms = downward_run(digs)
            records.append(
                {
                    "n": n,
                    "solved": True,
                    "d": d,
                    "digs": digs,
                    "terms": terms,
                    "ok": total == d,
                    "max_k": mk,
                    "stop": stop,
                    "run_terms": run_terms,
                    "run": len(run_terms),
                    "leads": leads,
                    "lo": lo,
                    "hi": hi,
                }
            )
        else:
            # representative order = highest possible lead k in band
            mk = leads[-1][0] if leads else 0
            records.append(
                {
                    "n": n,
                    "solved": False,
                    "d": None,
                    "digs": None,
                    "terms": None,
                    "ok": None,
                    "max_k": mk,
                    "stop": None,
                    "run_terms": None,
                    "run": None,
                    "leads": leads,
                    "lo": lo,
                    "hi": hi,
                }
            )

    ks_solved = [r["max_k"] for r in records if r["solved"]]
    k_min, k_max = min(ks_solved), max(ks_solved)

    # ---- text ----
    txt: list[str] = []
    txt.append(f"ALL PUZZLES {PUZZLE_LO}..{PUZZLE_HI} — factoradic")
    txt.append(f"solved with d: {sum(1 for r in records if r['solved'])}")
    txt.append(f"unsolved (band window only): {sum(1 for r in records if not r['solved'])}")
    txt.append("=" * 96)
    for r in records:
        if r["solved"]:
            mk = r["max_k"]
            digs = r["digs"]
            full = " + ".join(f"{digs[k]}×{k}!" for k in range(mk, -1, -1))
            run = " ".join(f"{k}!" for k, _ in r["run_terms"])
            txt.append(f"P{r['n']:03d} SOLVED  max_k={mk} run={r['run']}  {run} | break@{r['stop']}!")
            txt.append(f"         FULL: {full}")
            txt.append(f"         d={r['d']}  ok={r['ok']}")
        else:
            lead_s = ", ".join(
                f"{alo}..{ahi}×{k}!" if alo != ahi else f"{alo}×{k}!"
                for k, alo, ahi in r["leads"]
            )
            windows = []
            for k, alo, ahi in r["leads"]:
                five = " ".join(f"{j}!" for j in range(k, max(k - 5, 0), -1))
                windows.append(f"[{alo}..{ahi}]×{k}! → five-back {five}")
            txt.append(f"P{r['n']:03d} UNSOLVED max_k~{r['max_k']}  leads: {lead_s}")
            for wline in windows:
                txt.append(f"         {wline}")
    OUT_TXT.write_text("\n".join(txt) + "\n", encoding="utf-8")

    # ---- HTML ----
    legend = []
    seen_k = sorted({r["max_k"] for r in records if r["solved"]})
    for k in seen_k:
        bg, fg, acc = order_color(k, k_min, k_max)
        cnt = sum(1 for r in records if r["solved"] and r["max_k"] == k)
        legend.append(
            f'<span class="leg" style="background:{bg};color:{fg};border-color:{acc}">'
            f"max_k={k} · {cnt}</span>"
        )
    ubg, ufg, uacc = unsolved_color()
    legend.append(
        f'<span class="leg" style="background:{ubg};color:{ufg};border-color:{uacc}">'
        f"unsolved band · {sum(1 for r in records if not r['solved'])}</span>"
    )

    body = []
    prev_k = None
    for r in records:
        if r["solved"]:
            bg, fg, acc = order_color(r["max_k"], k_min, k_max)
            digs = r["digs"]
            mk = r["max_k"]
            term_spans = []
            for k in range(mk, -1, -1):
                a = digs[k]
                term = a * math.factorial(k)
                if k == mk:
                    cls = "lead"
                elif a == 0:
                    cls = "zero"
                else:
                    cls = "term"
                term_spans.append(
                    f'<span class="{cls}" title="{a}×{k}!={term}">{a}×{k}!</span>'
                )
            recon = " + ".join(term_spans)
            run = " ".join(f"{k}!" for k, _ in r["run_terms"])
            dig_hi = ",".join(str(a) for a in digs[::-1])
            jump = prev_k is not None and r["max_k"] != prev_k
            body.append(
                f"""
<tr class="row{' jump' if jump else ''}" style="--bg:{bg};--fg:{fg};--acc:{acc}">
  <td class="n">{r['n']}</td>
  <td class="st">SOLVED</td>
  <td class="k"><b>{r['max_k']}</b></td>
  <td class="run">{r['run']}</td>
  <td class="ok">{'✓' if r['ok'] else '✗'}</td>
  <td class="recon">
    <div>{recon}</div>
    <div class="digits">digits[{mk}..0]=[{dig_hi}]</div>
    <div class="peel">down-span: {run} → break @{r['stop']}!</div>
  </td>
  <td class="d"><code>{r['d']}</code></td>
</tr>"""
            )
            prev_k = r["max_k"]
        else:
            bg, fg, acc = unsolved_color()
            lead_bits = []
            for k, alo, ahi in r["leads"]:
                five = " ".join(f"{j}!" for j in range(k, max(k - 5, 0), -1))
                if alo == ahi:
                    lead_bits.append(f"<b>{alo}×{k}!</b> → {five}")
                else:
                    lead_bits.append(f"<b>{alo}..{ahi}×{k}!</b> → {five}")
            lead_html = "<br/>".join(lead_bits) if lead_bits else "—"
            body.append(
                f"""
<tr class="row unsolved" style="--bg:{bg};--fg:{fg};--acc:{acc}">
  <td class="n">{r['n']}</td>
  <td class="st">UNSOLVED</td>
  <td class="k"><b>~{r['max_k']}</b></td>
  <td class="run">—</td>
  <td class="ok">—</td>
  <td class="recon">
    <div class="band">band [2^{r['n']-1}, 2^{r['n']}) — plant lead then ADD lower a·k!</div>
    <div class="peel">{lead_html}</div>
  </td>
  <td class="d"><code>unknown</code></td>
</tr>"""
            )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Factoradic — all puzzles {PUZZLE_LO}..{PUZZLE_HI}</title>
<style>
  body {{
    margin: 0; padding: 28px 22px 60px;
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    background:
      radial-gradient(1000px 500px at 8% -10%, #ffe0c2 0%, transparent 55%),
      radial-gradient(900px 500px at 92% 0%, #cfe0ff 0%, transparent 50%),
      #f7f4ef;
    color: #1a1a1a;
  }}
  h1 {{ font-family: Georgia, serif; margin: 0 0 8px; font-size: 1.85rem; }}
  .sub {{ color: #555; max-width: 80ch; line-height: 1.45; margin-bottom: 14px; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0 20px; }}
  .leg {{ padding:6px 10px; border-radius:999px; border:2px solid; font-size:0.75rem; font-weight:650; }}
  .wrap {{ overflow-x:auto; border-radius:14px; background:rgba(255,255,255,0.75);
           box-shadow:0 12px 40px rgba(0,0,0,0.08); }}
  table {{ border-collapse:collapse; width:100%; min-width:1200px; }}
  th {{ text-align:left; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em;
       padding:12px 10px; border-bottom:1px solid #ddd; position:sticky; top:0;
       background:rgba(255,255,255,0.95); }}
  td {{ padding:9px 10px; border-bottom:1px solid rgba(0,0,0,0.06); vertical-align:top; }}
  tr.row {{ background: color-mix(in srgb, var(--bg) 22%, white); }}
  tr.unsolved {{ background: color-mix(in srgb, var(--bg) 35%, white); opacity:0.95; }}
  tr.jump td {{ border-top: 3px solid var(--acc); }}
  td.k b {{ display:inline-block; padding:2px 8px; border-radius:8px; background:var(--bg); color:var(--fg); }}
  td.st {{ font-size:0.72rem; font-weight:700; letter-spacing:0.04em; }}
  .recon {{ font-family: Consolas, monospace; font-size:0.7rem; line-height:1.7; word-break:break-word; }}
  .lead {{ background:var(--bg); color:var(--fg); padding:1px 6px; border-radius:6px; font-weight:700; white-space:nowrap; }}
  .term {{ white-space:nowrap; }}
  .zero {{ color:#aaa; white-space:nowrap; }}
  .digits,.peel,.band {{ color:#555; font-size:0.65rem; margin-top:3px; }}
  .band {{ color:#333; font-weight:600; }}
  .d code {{ font-size:0.75rem; }}
  .foot {{ margin-top:14px; color:#666; font-size:0.85rem; }}
</style>
</head>
<body>
  <h1>Factoradic — all puzzles {PUZZLE_LO}–{PUZZLE_HI}</h1>
  <p class="sub">
    <b>Solved</b>: full sequence <code>max_k! … 0!</code> (zeros included), multiply-then-add.
    Color = factoradic order. <b>Unsolved</b>: grey — possible lead <code>a×k!</code> in the
    band, plus five-back construction window (<code>k! (k-1)! …</code>). Seed may sit
    below floor; add lower terms to enter range.
  </p>
  <div class="legend">{''.join(legend)}</div>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th>n</th><th>status</th><th>order</th><th>down-run</th><th>ok</th>
          <th>full sequence / band window</th><th>d</th>
        </tr>
      </thead>
      <tbody>
        {''.join(body)}
      </tbody>
    </table>
  </div>
  <p class="foot">
    Solved {sum(1 for r in records if r['solved'])} ·
    Unsolved {sum(1 for r in records if not r['solved'])} ·
    heights {PUZZLE_LO}–{PUZZLE_HI} ·
    {OUT_TXT.name}
  </p>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_TXT}")
    print(
        f"solved={sum(1 for r in records if r['solved'])} "
        f"unsolved={sum(1 for r in records if not r['solved'])} "
        f"total={len(records)}"
    )


if __name__ == "__main__":
    main()
