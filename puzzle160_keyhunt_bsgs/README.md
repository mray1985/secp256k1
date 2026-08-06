# Puzzle 160 — KeyHunt BSGS + 7M KB bloom + m96 complement

## KeyHunt paths (your install)

| Item | Path |
|------|------|
| **keyhunt.exe** (use this) | `Z:\root\keyhunt-main\keyhunt-win-main\MinGW\keyhunt.exe` |
| CYGWIN build (smaller) | `Z:\root\keyhunt-main\keyhunt-win-main\CYGWIN\keyhunt.exe` |
| **Useful tools** | `Z:\root\keyhunt-main\keyhunt-win-main\Useful\` |
| Bloom/table CWD | `Z:\root\keyhunt-main\keyhunt-win-main\MinGW\` |

**Useful/** contains helper binaries (not needed for BSGS puzzle 160, but handy):

- `keysubtracter.exe` — xpoint mode pubkey subtraction
- `b58dec.exe` — base58 address → hash160
- `RMD160-Sort.exe` — sort hash160 lists
- `to_h160.py` — batch address → hash160 (needs `bitcoinlib`)

Use **MinGW** build for large `-k` (ServerEdition, >64 GB RAM fix on Windows).

## Stack (how it wraps)

```
N + 1 = m × d
        |m ~ 2^96| × |d ~ 2^160| ≈ 2^256

KeyHunt BSGS  → d-leg  [2^159, 2^160-1]  d·G = P_160
m96 shells    → m-leg  [2^95, 2^96)     m·P_160  +  (N+1) walk
7M KB bloom   → baby-step x table for BSGS (your prior run)
G-prefix prune → skip emissions / seeds where trace leaks Gx prefix (550...)
```

## Your bloom / RAM setting

KeyHunt **`-k` is a K factor (decimal), not kilobytes.**

Your setup: **`-k 512 -t 4`** ≈ **~8 GB** BSGS bloom + bP table (AlbertoBSD docs for puzzle 125).

Files land in `WORKDIR` as `keyhunt_bsgs_*.blm` and `keyhunt_bsgs_*.tbl`.  
**Deleted them?** Run `rebuild_bloom.bat` — `-S` recreates on first launch with the same `-k`.

## Launch (double-click or cmd)

```bat
run_p160_bsgs_7m.bat
```

Or manually from `MinGW` folder (so `.blm` / `.tbl` reuse):

```bat
cd /d Z:\root\keyhunt-main\keyhunt-win-main\MinGW
keyhunt.exe -m bsgs ^
  -f C:\Users\mitch\Desktop\secp256k1\puzzle160_keyhunt_bsgs\P160_compressed.pub ^
  -b 160 ^
  -k 512 ^
  -t 4 ^
  -s 10 ^
  -S -q
```

`-b 160` = official band `2^159` .. `2^160-1`. Equivalent explicit range:

`800000000000000000000000000000000:ffffffffffffffffffffffffffffffff`

**First run (or after delete):** `-S` writes four files into CWD (`keyhunt_bsgs_4_*.blm`, `_6_*.blm`, `_7_*.blm`, `_2_*.tbl`). Build takes time.  
**Later runs:** same `-k 512` reads them from disk (fast startup).

Adjust `-t` (threads), `-s` (stats interval). Add `-R` for random sweep within the band.

## After a hit — verify the 2^96 complement wrap

```python
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
d = <found key>
m = (N + 1) // d
assert 2**96 <= m < 2**97   # m-band partner
# optional: m shell trace should be low G-prefix leak (see puzzle160_m96_g_prefix_prune.py)
```

## Narrow BSGS (leader ± window, same bloom)

When barcode leaders give a center `d0`, sub-range still uses same bloom philosophy:

```bat
keyhunt.exe -m bsgs -f P160.pub -r START:END -k 512 -t 4
```

Example centers (d-band):
- py_w15: 803505878170136640646881328233715742298136844352
- px_w0:  1016161246378405429915312532485865240202132152583
- y2_w21: 1279319893184270309653638302331043709986753761686
- rmd_wrap2: 999836400474710041910519435328613735285013260936

## G-prefix speed filter (concept)

On m96 shells `S = m·P_160`, run `(N+1)·S` DA trace:

- **G fingerprints** (first 3 digits): Gx→`550`, Gy→`326`, etc.
- **Clean shell** = few trace coords containing G prefixes → better `d ≈ (N+1)/m` seed
- **G-tainted shell** = prune; don't spawn KeyHunt sub-ranges from those steps

This does not replace BSGS; it **zeros in** which d-windows are worth a bloom-backed run.

## Files

| File | Purpose |
|------|---------|
| `paths.bat` | KEYHUNT / USEFUL / WORKDIR / bloom size |
| `P160.pub` | uncompressed puzzle 160 pubkey |
| `P160_compressed.pub` | compressed (02…) — KeyHunt test format |
| `rebuild_bloom.bat` | one-shot recreate deleted `.blm` / `.tbl` |
| `run_p160_bsgs_7m.bat` | full-band launcher (`-k 512 -t 4`) |
| `run_p160_leader_*.bat` | narrow ±1T ranges per barcode leader |
| `gen_leader_bats.py` | regenerate leader `.bat` files |
| `verify_p160_hit.py` | post-hit: d·G + m-band check |
