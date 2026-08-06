# Summary

## Objective
Determine P135's private key by reverse-engineering hex extraction pattern from 53125.txt and contact_sheet_key.png, then extracting d from x_hex.

## Key Findings

### P125 Y extraction solved
- Cross-reference at x_hex[26]='4' inserted between Y grid positions 13 and 39 left-to-right → d[17:]="9960225e44877ac" matches (32 hex chars)
- Y positions: [4,15,60,61,18,21,50,64,13,39,51,2,16,25] + cross-ref at col 26
- X positions: [7,23,36,44,0,6,48,53,32,33,46,47,55,61,12,30,48]
- 4 Y-grid overrides (cols 60→6, 50→5, 39→8, 51→7, 64→E) have grid values equal to correct d chars

### Contact sheet image structure
- 800×2040 RGB, 12 thick bands (140 rows) + 12 thin bands (10 rows) alternating
- P125 band: rows 1195-1334 (thick), 1340-1349 (thin)
- P135 band: rows 855-994 (thick), 1000-1009 (thin)
- Puzzles: 160→105 descending (thick bands at rows 5, 175, 345, 515, 685, 855, 1025, 1195, 1365, 1535, 1705, 1875)
- Pixel data columns: 96 to 800 (704 data columns), non-white pixels form column clusters
- R/G/B values are multiples of 28: 0, 28, 56, 84, 112, 140, 168, 196, 224, 252

### Computation result ≠ private key
- For P125 and P130: `result^N/256` integer has exactly N bits but differs from d
- P125 result: 0x1cd006b64844c1ff2ba67565b52de987, d: 0x1c533b6bb7f0804e09960225e44877ac
- P130 result: 0x347730af51c9d7986226f341ae78111ab, d: 0x33e7665705359f04f28b88cf897c603c9
- Verified via ecdsa library SECP256k1 curve

### P130 annotations decoded
- Cross-ref markers x0→6 and x9→8: X-grid columns 0 and 9 contain values differing from x_hex[0] and x_hex[9]
- 8 annotation groups: 33E7, 665, 70, 53, 59F04F28B, 88C, F_97C_03, C9
- Group structure encodes the non-zero portion of d: 33e7665705359f04f28b88cf897c603c9

### Computation sequences (P135)
- 135x: [20589, 10254, 5107, 2543, 1266, 630, 314, 156, 77, 38, 19, 9, 4, 2, 1]
- 135y: [32155784, 23035, 11472, 5713, 2845, 1417, 705, 351, 175, 87, 43, 21, 10, 5, 2, 1]
- 135(y^2=x^3+7) mod p RESULT: (23643, 11775, 5864, 2920, 1454, 724, 360, 179, 89, 44, 22, 11, 5, 2, 1, 0, 0)

### Sequence pattern
- Each sequence value = result of iterative (y^2 = x^3 + 7)^(k/255.47...) mod p - 2^k
- All unsolved puzzles (135, 140, 145, 150, 155, 160) share this iterative pattern
- Solved puzzles (130, 125, 120, 115, 110) have grid but no iterative sequences

### rmd160 triplets
- R = RMD160(SHA256(uncompressed_pubkey))
- G = RMD160(SHA256(02-compressed_pubkey))
- B = RMD160(SHA256(03-compressed_pubkey))
- rmd160→position mapping: Byte%64, XOR, hash combinations all fail to directly match extraction positions

### P135 x_hex and y_hex
- x_hex: 145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16
- y_hex: 667A05E9A1BDD6F70142B66558BD12CE2C0F9CBC7001B20C8A6A109C80DC5330
- (y^2 = x^3 + 7) mod p: B146AAFD382C29F4B4EFDEF289C8BE53C6091A94D81EC27F61177D316DA8E3E1
- log2 value: 255.4698538032563791...

### Contact sheet: pixel R values in multiples of 28
- Row 1195 (P125): columns 0-20 all R=252=9×28, then pairs at columns 21+ have different R values
- Each PAIR of pixel columns has identical RGB values, suggesting 64 pixel cols = 32 data units
- Thin bands (10 rows) have very sparse data (1-2 non-white pixels per row)
- All 64 x_hex columns appear as non-white in thick bands → raw mod64 doesn't distinguish extraction subset

### Mystery numbers (P135 lines 78-79)
- Line 78: 145261182339667120712099431353032309608116 (not x_dec, not d)
- Line 79: DCAEFCEFFBBFEEAAFBBDDE = 266790037955370537520446942 (neither is valid d)

## P135 vs P125 encoding difference
- P125 uses mult28 (R = digit×28, max 252 → only digits 0-9)
- P125 key letters (a-f) come from VISIBLE rendered text in image, not pixel data
- P135 uses ASCII-hex (R ∈ {48-57, 97-102}) — all 16 hex chars storable in pixel data
- P135 has NO visible text grid (unlike P125's lines 408-415)

## Image layout (verified)
- 10 puzzle bands, each 140 thick rows + ~6-10 thin rows
- Band 4 (rows 855-994) = P135, thick band 140 rows, thin band 6 rows (1002-1007)
- Band 6 (rows 1195-1334) = P125, thick band 140 rows, thin band 8 rows (1340-1347)

## P125 text grid analysis
- Text grid (lines 408-415) shows 28 key chars at specific x_hex column positions
- Grid chars in reading order DON'T directly concatenate to the private key
- Thin band gray values < 140 map to thick-band rows, but DON'T match text grid positions
- Thin band appears NOT to encode key extraction positions for either P125 or P135

## P135 pixel band analysis
- R channel: 44,188 hex chars (ASCII) + 54,372 non-hex/background values
- Only 553 lowercase letters (a-f) in entire band — very sparse (1.25%)
- Lowercase letters cluster at same (cycle, mod64) across consecutive rows — likely rendering artifacts
- G and B channels encode readable ASCII text fragments ("Tso", "h d", "ibe", "sa", "ic", "r") — these are labels/annotations from rendered text
- ALL non-background pixels have R∈{48-57,97-102} (hex ASCII) making the entire band hex-readable

## Mismatch analysis (R ≠ x_hex)
- Every mod64 column has 500-700 mismatch rows across cycles 2-7
- 35,612 total mismatch positions across 35 valid columns
- First-mismatch-per-column gives ALL digits (0-9), no lowercase letters
- Lowercase letters only appear at SPECIFIC (row,cycle) combos, not in first mismatch

## Sequence-based extraction attempts
- Combined mod64 from x+y+y2 sequences = 35 unique values → need exactly 34
- Every 35→34 removal tried — no candidate starts with 4-7 or contains lowercase letters
- Direct (row=y2%140, col=x%704) pairs: only 7/15 valid, no letters
- Thin→thick mapping via (y2%6, x%704): most positions white/invalid
- Annotation "DCAEFCEFFBBFEEAAFBBDDE" (22 hex, 88 bits) not found as substring in R data
- Sequence products/combinations don't directly equal d or x

## Current assessment
- EXTRACTION METHOD FOR P135 REMAINS UNKNOWN
- P125's text grid was manually derived from visible text — no automation pattern to transfer
- The computation sequences likely encode (row, cycle) selection per column, but mapping formula is unclear
- Thin band MAY encode positions for different puzzles (P130, P140) — not verified
- A brute-force of all possible 34-char hex strings from band data is infeasible (35k+ positions)

## To verify P135 key
- Compute d*G on secp256k1 and check x-coordinate matches x_hex
- Available: ecdsa Python library with SECP256k1

## Files
- `53125.txt`: Main data file (puzzles 160→105)
- `contact_sheet_key.png`: Pixel grid encoding extraction
- `rmd_trinagulation.txt`: RIPEMD-160 triplets per puzzle
- `barcoding.txt`: Band width references (82/160/256/64)
