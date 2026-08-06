#!/usr/bin/env python3
"""
Filter briefcase puzzle data through md5hashing.net reverse hash database.

Uses Playwright (headless Chromium) because the site is a Meteor SPA; static
HTTP fetch does not return decode results. Queries hash.get indirectly via
/hash/{type}/{digest} pages and scrapes the reversed plaintext when present.

Outputs:
  ARCHIVE/briefcase/md5hashing_filter_report.md
  ARCHIVE/briefcase/md5hashing_filter_report.json
  ARCHIVE/briefcase/md5hashing_cache.json  (incremental cache)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
BRIEFCASE = ROOT / "ARCHIVE" / "briefcase"
CACHE_PATH = BRIEFCASE / "md5hashing_cache.json"
REPORT_MD = BRIEFCASE / "md5hashing_filter_report.md"
REPORT_JSON = BRIEFCASE / "md5hashing_filter_report.json"

SITE_TYPES = {
    "md5": "md5",
    "sha1": "sha1",
    "sha256": "sha256",
    "sha512": "sha512",
    "ripemd160": "ripemd160",
}

REVERSE_RE = re.compile(
    r"Reversed hash value\s*\n\s*([^\n]+)",
    re.IGNORECASE,
)


@dataclass
class Query:
    puzzle: int
    field: str
    algo: str
    digest: str
    expected: str | None = None


@dataclass
class LookupResult:
    puzzle: int
    field: str
    algo: str
    digest: str
    decoded: str | None
    hit: bool
    verified: bool
    expected: str | None = None
    note: str = ""


def parse_identity(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines:
        if " = " in line:
            k, v = line.split(" = ", 1)
            out[k.strip()] = v.strip()
    return out


def parse_rsz(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines:
        m = re.match(r"^(r|s|z|txid|k)\s*=\s*(.+)$", line.strip(), re.I)
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
    return out


def hex_or_int(s: str) -> int | None:
    s = s.strip()
    if not s or s in ("0", "0 (unsolved)", "—", "-"):
        return None
    if s.startswith("0x"):
        return int(s, 16)
    if re.fullmatch(r"[0-9a-fA-F]+", s) and len(s) >= 2:
        try:
            return int(s, 16)
        except ValueError:
            pass
    if s.isdigit():
        return int(s)
    return None


def digest(algo: str, text: str) -> str:
    return hashlib.new(algo, text.encode("utf-8")).hexdigest()


def load_briefcase_queries(
    puzzles: list[int] | None = None,
    include_unsolved: bool = True,
    tier: str = "fast",
) -> list[Query]:
    queries: list[Query] = []
    files = sorted(BRIEFCASE.glob("puzzle_*_ledger.json"))
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "puzzle" not in data:
            continue
        n = int(data["puzzle"])
        if puzzles and n not in puzzles:
            continue

        identity: dict[str, str] = {}
        pubkey = ""
        rsz: dict[str, str] = {}
        verdict = data.get("verdict", {})

        for op in data.get("operations", []):
            if op.get("phase") == "00_identity":
                identity = parse_identity(op.get("lines", []))
            elif op.get("phase") == "01_pubkey":
                for line in op.get("lines", []):
                    if line.startswith("pub_compressed = "):
                        pubkey = line.split(" = ", 1)[1].strip()
            elif op.get("phase", "").startswith("06_rsz"):
                rsz.update(parse_rsz(op.get("lines", [])))

        h160 = identity.get("hash160", "").lower()
        if h160:
            queries.append(Query(n, "hash160", "ripemd160", h160, None))

        addr = identity.get("address", "")
        if addr and tier in ("standard", "full"):
            for algo in ("md5", "sha1", "sha256"):
                queries.append(Query(n, "address", algo, digest(algo, addr), addr))
        elif addr:
            queries.append(Query(n, "address", "sha256", digest("sha256", addr), addr))

        d_raw = identity.get("private key d", "")
        # Never treat placeholder "0 (unsolved)" / "unknown" as a real key.
        if (
            not d_raw
            or "unsolved" in d_raw.lower()
            or "unknown" in d_raw.lower()
        ):
            d = None
        else:
            d = hex_or_int(d_raw.split()[0])
        if d and d > 0:
            # Always include full 64-char hex (Bitcoin key material, never truncated).
            # Label by format slot — for small d, decimal and unpadded hex can be
            # the same string (e.g. d=1 → "1"), so do not infer label from value.
            d_dec = str(d)
            d_hex = f"{d:x}"
            d_hex64 = f"{d:064x}"
            d_hex0x = f"0x{d_hex}"
            if tier == "full":
                plain_variants = [
                    ("private_key_dec", d_dec),
                    ("private_key_hex", d_hex),
                    ("private_key_hex64", d_hex64),
                    ("private_key_0x", d_hex0x),
                ]
                algos = ("md5", "sha1", "sha256")
            elif tier == "standard":
                plain_variants = [
                    ("private_key_dec", d_dec),
                    ("private_key_hex64", d_hex64),
                ]
                algos = ("md5", "sha1", "sha256")
            else:
                plain_variants = [
                    ("private_key_dec", d_dec),
                    ("private_key_hex64", d_hex64),
                ]
                algos = ("md5", "sha256")
            for label, pt in plain_variants:
                for algo in algos:
                    queries.append(Query(n, label, algo, digest(algo, pt), pt))
        elif not include_unsolved:
            continue

        if pubkey and tier in ("standard", "full"):
            algos = ("md5", "sha1", "sha256", "ripemd160") if tier == "full" else ("sha256", "ripemd160")
            for algo in algos:
                queries.append(
                    Query(n, "pub_compressed", algo, digest(algo, pubkey), pubkey)
                )
            if tier == "full":
                try:
                    pk_bytes = bytes.fromhex(pubkey)
                    h = hashlib.new(
                        "ripemd160", hashlib.sha256(pk_bytes).digest()
                    ).hexdigest()
                    if h != h160:
                        queries.append(Query(n, "recomputed_hash160", "ripemd160", h, pubkey))
                except ValueError:
                    pass

        if tier == "full":
            for key in ("r", "s", "z"):
                if key in rsz:
                    val = rsz[key].lower().replace("0x", "")
                    if val:
                        for algo in ("md5", "sha256"):
                            queries.append(
                                Query(n, f"rsz_{key}", algo, digest(algo, val), val)
                            )

            for greek in ("\u039b", "\u039b1"):
                if greek in verdict:
                    val = str(verdict[greek])
                    for algo in ("md5", "sha1", "sha256"):
                        queries.append(Query(n, greek, algo, digest(algo, val), val))

    # dedupe
    seen: set[tuple[str, str]] = set()
    uniq: list[Query] = []
    for q in queries:
        k = (q.algo, q.digest.lower())
        if k in seen:
            continue
        seen.add(k)
        uniq.append(q)
    return uniq


def load_cache() -> dict[str, dict]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def cache_key(algo: str, digest_hex: str) -> str:
    return f"{algo}:{digest_hex.lower()}"


def scrape_decoded(page, algo: str, digest_hex: str, delay: float) -> str | None:
    site_type = SITE_TYPES.get(algo, algo)
    url = f"https://md5hashing.net/hash/{site_type}/{digest_hex.lower()}"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    # Prefer the value panel text; fall back to body regex.
    try:
        page.get_by_text("Reversed hash value", exact=False).first.wait_for(timeout=12000)
        page.wait_for_timeout(max(400, int(delay * 400)))
    except Exception:
        page.wait_for_timeout(int(max(delay, 1.0) * 1000))

    val: str | None = None
    # Site often puts the full plaintext in a selectable value node.
    for sel in (
        "text=Reversed hash value >> xpath=../following-sibling::*[1]",
        "[itemprop='text']",
        ".hash-decoded",
    ):
        try:
            loc = page.locator(sel)
            if loc.count():
                candidate = loc.first.inner_text(timeout=2000).strip()
                if candidate and "reversed" not in candidate.lower():
                    val = candidate
                    break
        except Exception:
            pass

    if val is None:
        body = page.inner_text("body")
        m = REVERSE_RE.search(body)
        if m:
            val = m.group(1).strip()

    if not val or val.lower() in ("n/a", "not found", "—", "-"):
        return None
    # ignore ad copy mistaken as value (private keys / Λ can be long)
    if "try now" in val.lower() or "increase traffic" in val.lower():
        return None
    if len(val) > 4096:
        return None
    return val


def verify_hit(q: Query, decoded: str) -> tuple[bool, str]:
    if q.expected is None:
        return False, "no expected plaintext"
    exp = q.expected
    if decoded == exp:
        return True, "exact match"
    if decoded.lower() == exp.lower():
        return True, "case-insensitive match"
    if exp.isdigit() and decoded.isdigit() and int(decoded) == int(exp):
        return True, "numeric match"
    # full hex compare only (no prefix/substring — that hid truncated keys)
    if (
        all(c in "0123456789abcdefABCDEF" for c in decoded)
        and all(c in "0123456789abcdefABCDEF" for c in exp)
        and decoded.lower() == exp.lower()
    ):
        return True, "hex match"
    return False, "decoded but unrelated"


def run_filter(
    puzzles: list[int] | None = None,
    limit: int | None = None,
    delay: float = 0.8,
    refresh: bool = False,
    tier: str = "fast",
) -> tuple[list[LookupResult], dict]:
    queries = load_briefcase_queries(puzzles=puzzles, tier=tier)
    if limit:
        queries = queries[:limit]

    cache = load_cache()
    results: list[LookupResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # bootstrap session + cookie banner once
        page.goto("https://md5hashing.net/hash/md5/5d41402abc4b2a76b9719d911017c592", timeout=60000)
        try:
            page.locator('text="I Agree"').first.click(timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        pending = [
            q
            for q in queries
            if refresh or cache_key(q.algo, q.digest) not in cache
        ]
        print(
            f"Queries: {len(queries)} total, {len(pending)} need network lookup",
            flush=True,
        )

        for i, q in enumerate(queries, 1):
            ck = cache_key(q.algo, q.digest)
            decoded: str | None
            if not refresh and ck in cache:
                decoded = cache[ck].get("decoded")
            else:
                try:
                    decoded = scrape_decoded(page, q.algo, q.digest, delay)
                except Exception as exc:
                    decoded = None
                    cache[ck] = {
                        "decoded": None,
                        "error": str(exc),
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    cache[ck] = {
                        "decoded": decoded,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                save_cache(cache)
                done_net = sum(
                    1
                    for qq in queries[:i]
                    if cache_key(qq.algo, qq.digest) in cache
                )
                print(
                    f"  [{i}/{len(queries)}] P{q.puzzle} {q.field} {q.algo} "
                    f"hit={decoded is not None} len_expected={len(q.expected or '')}",
                    flush=True,
                )

            hit = decoded is not None
            verified, note = (False, "")
            if hit and decoded is not None:
                verified, note = verify_hit(q, decoded)

            results.append(
                LookupResult(
                    puzzle=q.puzzle,
                    field=q.field,
                    algo=q.algo,
                    digest=q.digest,
                    decoded=decoded,
                    hit=hit,
                    verified=verified,
                    expected=q.expected,
                    note=note,
                )
            )

        browser.close()

    save_cache(cache)
    return results, {
        "generated": datetime.now(timezone.utc).isoformat(),
        "tier": tier,
        "queries": len(queries),
        "hits": sum(1 for r in results if r.hit),
        "verified": sum(1 for r in results if r.verified),
    }


def write_report(results: list[LookupResult], meta: dict) -> None:
    hits = [r for r in results if r.hit]
    verified = [r for r in results if r.verified]

    lines = [
        "# Briefcase × md5hashing.net filter report",
        "",
        f"Generated: {meta['generated']}",
        f"Tier: {meta.get('tier', 'fast')}",
        (
            f"Queries: {meta['queries']} | Hits: {meta['hits']} | "
            f"Verified matches: {meta['verified']}"
            + (
                f" | Pending network: {meta['pending_network']}"
                if meta.get("pending_network")
                else ""
            )
        ),
        "",
        "Source: [md5hashing.net/hash](https://md5hashing.net/hash) reverse rainbow DB via Playwright.",
        "",
        "## Summary",
        "",
    ]
    def emit_hit(r: LookupResult) -> None:
        """Full values only — never truncate private keys or digests."""
        lines.append(f"#### P{r.puzzle} — {r.field} ({r.algo})")
        lines.append("")
        lines.append(f"- **digest:** `{r.digest}`")
        lines.append(f"- **decoded:** `{r.decoded}`")
        if r.expected is not None:
            lines.append(f"- **expected (full):** `{r.expected}`")
            lines.append(f"- **expected length:** {len(r.expected)}")
        if r.decoded is not None:
            lines.append(f"- **decoded length:** {len(r.decoded)}")
        lines.append(f"- **verified:** {r.verified} ({r.note or '—'})")
        lines.append("")

    if not hits:
        lines.append("No reverse-lookup hits in md5hashing.net database for briefcase digests.")
    else:
        lines.append(
            f"{len(hits)} digest(s) found in site DB; "
            f"{len(verified)} verified against briefcase plaintext."
        )
        lines.append("")
        lines.append("Private-key fields always use the **full** value:")
        lines.append("`private_key_dec` = decimal string, `private_key_hex64` = zero-padded 64-char hex.")
        lines.append("")
        lines.append("### Verified hits")
        lines.append("")
        if verified:
            for r in verified:
                emit_hit(r)
        else:
            lines.append("_Hits found but none matched expected briefcase plaintext._")
            lines.append("")
        lines.append("### All hits (including unverified)")
        lines.append("")
        for r in hits:
            emit_hit(r)

    lines.append("")
    lines.append("## Miss sample (first 20)")
    lines.append("")
    misses = [r for r in results if not r.hit][:20]
    for r in misses:
        lines.append(f"- P{r.puzzle} {r.field} {r.algo}")
        lines.append(f"  - digest: `{r.digest}`")
        if r.expected is not None:
            lines.append(f"  - expected (full): `{r.expected}`")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    REPORT_JSON.write_text(
        json.dumps({"meta": meta, "results": [asdict(r) for r in results]}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Filter briefcase through md5hashing.net")
    ap.add_argument("--puzzle", type=int, action="append", help="limit to puzzle number(s)")
    ap.add_argument("--limit", type=int, help="max queries")
    ap.add_argument("--tier", choices=("fast", "standard", "full"), default="fast")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between lookups")
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    args = ap.parse_args()

    results, meta = run_filter(
        puzzles=args.puzzle,
        limit=args.limit,
        delay=args.delay,
        refresh=args.refresh,
        tier=args.tier,
    )
    write_report(results, meta)
    print(f"Done: {meta['hits']} hits / {meta['queries']} queries -> {REPORT_MD}")


if __name__ == "__main__":
    main()
