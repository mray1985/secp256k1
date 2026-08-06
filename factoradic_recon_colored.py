#!/usr/bin/env python3
"""
Reconstruct all puzzle keys in factoradic form and color by order (max_k).

Lead arithmetic: term = a * k!, then add into running total (or subtract from d).
Same max_k (factoradic order) -> same color. Adjacent orders get related hues.
"""
from __future__ import annotations

import colorsys
import csv
import math
from pathlib import Path

CSV_IN = Path(r"C:\Users\mitch\Downloads\factoradic_private_keys.csv")
OUT_HTML = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_RECON_COLORED.html")
OUT_TXT = Path(r"C:\Users\mitch\Desktop\secp256k1\logs\FACTORADIC_RECON_COLORED.txt")


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
    """Return (total, [(k, a, a*k!), ...]) high-to-low, only nonzero."""
    terms: list[tuple[int, int, int]] = []
    total = 0
    for k, a in enumerate(digs):
        if not a:
            continue
        term = a * math.factorial(k)  # multiply then add
        total += term
        terms.append((k, a, term))
    terms.reverse()
    return total, terms


def order_color(max_k: int, k_min: int, k_max: int) -> tuple[str, str, str]:
    """
    Map factoradic order max_k -> distinct RGB family.
    Cycles through orange / blue / green / magenta / cyan / yellow-green.
    Returns (bg, fg, accent).
    """
    palette = [
        ((255, 140, 40), (40, 20, 0), (255, 180, 90)),    # orange
        ((50, 110, 220), (230, 240, 255), (120, 170, 255)),  # blue
        ((40, 170, 90), (10, 40, 20), (100, 220, 140)),   # green
        ((200, 60, 140), (255, 230, 245), (240, 120, 180)),  # magenta
        ((30, 170, 180), (10, 40, 45), (90, 220, 230)),   # cyan
        ((210, 180, 40), (40, 35, 0), (240, 220, 100)),   # gold
        ((160, 80, 220), (245, 235, 255), (200, 150, 255)),  # purple
        ((220, 80, 60), (255, 235, 230), (255, 140, 120)),   # red-orange
    ]
    # stable index by max_k so same order always same color
    idx = (max_k - k_min) % len(palette)
    bg, fg, acc = palette[idx]
    # slight lightness shift within long plateaus is handled by lead frac elsewhere
    def css(rgb: tuple[int, int, int]) -> str:
        return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    return css(bg), css(fg), css(acc)


def lead_frac(digs: list[int]) -> float:
    if not digs:
        return 0.0
    k = len(digs) - 1
    a = digs[k]
    return a / k if k else 1.0


def fmt_terms(terms: list[tuple[int, int, int]], limit: int | None = None) -> str:
    use = terms if limit is None else terms[:limit]
    return " + ".join(f"{a}×{k}!" for k, a, _ in use)


def fmt_terms_full(digs: list[int]) -> str:
    """Every slot max_k..0, including zeros."""
    if not digs:
        return "0"
    mk = len(digs) - 1
    return " + ".join(f"{digs[k]}×{k}!" for k in range(mk, -1, -1))


def main() -> None:
    rows_in = []
    with CSV_IN.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["puzzle"])
            d = int(row["private_key"])
            digs = to_factoradic(d)
            total, terms = reconstruct(digs)
            mk = len(digs) - 1 if digs else 0
            a = digs[mk] if digs else 0
            rows_in.append(
                {
                    "n": n,
                    "d": d,
                    "digs": digs,
                    "terms": terms,
                    "total": total,
                    "ok": total == d,
                    "max_k": mk,
                    "lead_a": a,
                    "digit_frac": lead_frac(digs),
                    "cell_frac": ((d - a * math.factorial(mk)) / math.factorial(mk))
                    if mk and digs
                    else 0.0,
                    "plateau_frac": ((d - math.factorial(mk)) / (mk * math.factorial(mk)))
                    if mk and d >= math.factorial(mk)
                    else 0.0,
                    "mass_frac": (a * math.factorial(mk) / d) if d and digs else 0.0,
                }
            )

    ks = [r["max_k"] for r in rows_in]
    k_min, k_max = min(ks), max(ks)

    # group by order
    by_k: dict[int, list[int]] = {}
    for r in rows_in:
        by_k.setdefault(r["max_k"], []).append(r["n"])

    # ---- text ----
    txt: list[str] = []
    txt.append("FACTORADIC RECONSTRUCTION — colored by order (max_k)")
    txt.append("term = a * k!  then ADD into total (rebuild) / SUBTRACT from d (peel)")
    txt.append("=" * 96)
    txt.append("")
    txt.append("ORDER COLOR GROUPS (same max_k = same color family)")
    for k in sorted(by_k):
        puzzles = ",".join(str(n) for n in by_k[k])
        txt.append(f"  max_k={k:2d}  count={len(by_k[k]):2d}  puzzles=[{puzzles}]")
    txt.append("")
    txt.append(
        f"{'n':>3} {'max_k':>5} {'a':>3} {'ok':>3}  full reconstruction (all nonzero a×k!)"
    )
    txt.append("-" * 96)
    prev = None
    for r in rows_in:
        jump = "  << order jump" if prev is not None and r["max_k"] != prev else ""
        txt.append(
            f"{r['n']:3d} {r['max_k']:5d} {r['lead_a']:3d} {'OK' if r['ok'] else 'BAD':>3}  "
            f"{fmt_terms_full(r['digs'])}{jump}"
        )
        # also dump peel sequence: subtract each term from d
        running = r["d"]
        peel_parts = []
        for k, a, term in r["terms"]:
            running -= term
            peel_parts.append(f"-{a}×{k}! → {running}")
        txt.append(f"     peel: {' | '.join(peel_parts)}")
        txt.append(f"     digits[{r['max_k']}..0]: {r['digs'][::-1]}")
        prev = r["max_k"]
    txt.append("")
    txt.append(f"Exact rebuild: {sum(1 for r in rows_in if r['ok'])}/{len(rows_in)}")
    OUT_TXT.write_text("\n".join(txt) + "\n", encoding="utf-8")

    # ---- HTML ----
    legend_items = []
    for k in sorted(by_k):
        bg, fg, acc = order_color(k, k_min, k_max)
        legend_items.append(
            f'<span class="leg" style="background:{bg};color:{fg};border-color:{acc}">'
            f"max_k={k} · {len(by_k[k])} puzzles</span>"
        )

    body_rows = []
    prev = None
    for r in rows_in:
        bg, fg, acc = order_color(r["max_k"], k_min, k_max)
        # shade by digit_frac within the order color (darker bar = higher lead)
        frac = r["digit_frac"]
        bar_w = int(round(frac * 100))
        jump = r["max_k"] != prev if prev is not None else False
        jump_cls = " jump" if jump else ""
        # FULL sequence: every k from max_k down to 0 (zeros included)
        term_spans = []
        mk = r["max_k"]
        digs = r["digs"]
        for k in range(mk, -1, -1):
            a = digs[k] if k < len(digs) else 0
            term = a * math.factorial(k)
            if k == mk:
                weight = "lead"
            elif a == 0:
                weight = "zero"
            else:
                weight = "term"
            term_spans.append(
                f'<span class="{weight}" title="{a}×{k}! = {term}">'
                f"{a}×{k}!</span>"
            )
        recon = " + ".join(term_spans)
        dig_hi = ",".join(str(a) for a in digs[::-1])
        # peel only nonzero terms (subtract from d)
        running = r["d"]
        peel_bits = []
        for k, a, term in r["terms"]:
            running -= term
            peel_bits.append(f"−{a}×{k}!→{running}")
        peel = " · ".join(peel_bits)
        body_rows.append(
            f"""
<tr class="row{jump_cls}" style="--bg:{bg};--fg:{fg};--acc:{acc}">
  <td class="n">{r['n']}</td>
  <td class="k"><b>{r['max_k']}</b></td>
  <td class="a">{r['lead_a']}</td>
  <td class="frac">
    <div class="bar"><div class="fill" style="width:{bar_w}%"></div></div>
    <span class="fnum">{frac:.2f}</span>
  </td>
  <td class="phases" title="digit / cell / plateau / mass">
    {r['digit_frac']:.2f} · {r['cell_frac']:.2f} · {r['plateau_frac']:.2f} · {r['mass_frac']:.2f}
  </td>
  <td class="ok">{'✓' if r['ok'] else '✗'}</td>
  <td class="recon">
    <div>{recon}</div>
    <div class="digits">digits[max_k..0] = [{dig_hi}]</div>
    <div class="peel">peel: {peel}</div>
  </td>
  <td class="d"><code>{r['d']}</code></td>
</tr>"""
        )
        prev = r["max_k"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Factoradic reconstruction — colored by order</title>
<style>
  :root {{
    --ink: #1a1a1a;
    --muted: #666;
    --paper: #f7f4ef;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    background:
      radial-gradient(1200px 600px at 10% -10%, #ffe0c2 0%, transparent 55%),
      radial-gradient(900px 500px at 90% 0%, #cfe0ff 0%, transparent 50%),
      radial-gradient(800px 500px at 50% 100%, #d8f5e2 0%, transparent 45%),
      var(--paper);
    color: var(--ink);
    padding: 28px 22px 60px;
  }}
  h1 {{
    font-family: "IBM Plex Serif", Georgia, serif;
    font-weight: 650;
    font-size: 1.85rem;
    margin: 0 0 6px;
    letter-spacing: -0.02em;
  }}
  .sub {{
    color: var(--muted);
    max-width: 72ch;
    line-height: 1.45;
    margin-bottom: 18px;
  }}
  code, .d code {{
    font-family: "IBM Plex Mono", Consolas, monospace;
    font-size: 0.82rem;
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 14px 0 22px;
  }}
  .leg {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    border: 2px solid;
    font-size: 0.78rem;
    font-weight: 600;
  }}
  .wrap {{
    overflow-x: auto;
    border-radius: 14px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(6px);
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    min-width: 1100px;
  }}
  th {{
    text-align: left;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #444;
    padding: 12px 10px;
    border-bottom: 1px solid #ddd;
    background: rgba(255,255,255,0.9);
    position: sticky;
    top: 0;
    z-index: 2;
  }}
  td {{
    padding: 9px 10px;
    vertical-align: middle;
    border-bottom: 1px solid rgba(0,0,0,0.06);
  }}
  tr.row {{
    background: color-mix(in srgb, var(--bg) 22%, white);
    color: var(--ink);
  }}
  tr.row:hover {{
    background: color-mix(in srgb, var(--bg) 38%, white);
  }}
  tr.jump td {{
    border-top: 3px solid var(--acc);
  }}
  td.n, td.k, td.a, td.ok {{
    font-variant-numeric: tabular-nums;
    font-weight: 650;
  }}
  td.k b {{
    display: inline-block;
    min-width: 1.6em;
    padding: 2px 8px;
    border-radius: 8px;
    background: var(--bg);
    color: var(--fg);
  }}
  td.ok {{ color: #1a7a3a; }}
  .bar {{
    width: 72px;
    height: 8px;
    background: rgba(0,0,0,0.08);
    border-radius: 99px;
    overflow: hidden;
    display: inline-block;
    vertical-align: middle;
    margin-right: 6px;
  }}
  .fill {{
    height: 100%;
    background: var(--bg);
  }}
  .fnum {{ font-size: 0.78rem; color: #444; }}
  .phases {{ font-size: 0.75rem; color: #555; white-space: nowrap; }}
  .recon {{
    font-family: "IBM Plex Mono", Consolas, monospace;
    font-size: 0.72rem;
    line-height: 1.7;
    white-space: normal;
    word-break: break-word;
    max-width: 70vw;
  }}
  .digits {{
    font-family: "IBM Plex Mono", Consolas, monospace;
    font-size: 0.68rem;
    color: #555;
    margin-top: 4px;
  }}
  .peel {{
    font-family: "IBM Plex Mono", Consolas, monospace;
    font-size: 0.65rem;
    color: #666;
    margin-top: 3px;
    line-height: 1.45;
  }}
  .lead {{
    background: var(--bg);
    color: var(--fg);
    padding: 1px 6px;
    border-radius: 6px;
    font-weight: 700;
    white-space: nowrap;
  }}
  .term {{
    color: #333;
    padding: 0 2px;
    white-space: nowrap;
  }}
  .zero {{
    color: #aaa;
    padding: 0 2px;
    white-space: nowrap;
  }}
  .foot {{
    margin-top: 16px;
    color: var(--muted);
    font-size: 0.85rem;
  }}
</style>
</head>
<body>
  <h1>Factoradic reconstruction — colored by order</h1>
  <p class="sub">
    Every puzzle key rebuilt as <code>d = Σ (a<sub>k</sub> · k!)</code> with
    <b>multiply then add</b> (<code>term = a·k!</code>).
    Rows sharing the same factoradic order <code>max_k</code> share a color
    (orange / blue / green / magenta / cyan / gold / purple / red-orange).
    <b>Full sequences</b>: every nonzero <code>a×k!</code> term, the complete digit
    vector <code>[max_k..0]</code> (zeros included), and the peel chain
    <code>d − a·k! → rem</code> down to 0. Lead term is the solid chip;
    bar = <code>digit_frac = a/k</code>. Phases = digit · cell · plateau · mass.
  </p>
  <div class="legend">
    {''.join(legend_items)}
  </div>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th>n</th>
          <th>order max_k</th>
          <th>a</th>
          <th>digit_frac</th>
          <th>phases</th>
          <th>ok</th>
          <th>full reconstruction (every nonzero a×k!) + digits + peel</th>
          <th>d</th>
        </tr>
      </thead>
      <tbody>
        {''.join(body_rows)}
      </tbody>
    </table>
  </div>
  <p class="foot">
    Exact rebuild {sum(1 for r in rows_in if r['ok'])}/{len(rows_in)} ·
    orders {k_min}–{k_max} · source {CSV_IN.name} ·
    also wrote {OUT_TXT.name}
  </p>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_TXT}")
    print(f"Exact rebuild: {sum(1 for r in rows_in if r['ok'])}/{len(rows_in)}")
    print("Order groups:")
    for k in sorted(by_k):
        print(f"  max_k={k:2d}  n={by_k[k]}")


if __name__ == "__main__":
    main()
