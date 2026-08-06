# Puzzle 160 ECDLP - Continuation Summary
**Last Updated:** 2026-06-13  
**Status:** Multiple candidates tested, none found yet. Primary candidate d2=Lambda_N-2*b_x is in band but fails verification.

## Problem Statement
Find d such that P = d*G on secp256k1 curve, where:
- P = (Px2, Py2) = (101616124637840542991531253248586524020213215258338643076214814468447630501491, 88132823371574229813684435207239348220522140366126834573803505878170136640646)
- G = standard secp256k1 generator
- Expected band: [2^248, 2^250) (corrected from [2^159, 2^160))

## Key Findings (Verified)

### Notable Equations
1. **x-bridge (p-side):** CP1 * Gx_std ≡ Px2 (mod p) ✓
   - CP1 = 92482587651419717586971451131129365162696030810991889729009819064431288116847
   - CP1 = Px2 * Gx_std^-1 (mod p) ✓

2. **x-bridge (N-side):** Lambda_N * rx2 ≡ Px2 (mod N) ✓
   - Lambda_N = 1590449533822558131532290348591220229373973987443621656280254761535309924945
   - rx2 = 73166243711482150095739218900420001340047970263222419524399021938933427175712

3. **y-bridge (N-side):** Lambda_yN * ry2 ≡ Py2 (mod N) ✓
   - Lambda_yN = 49519410995698094917684506851297655330362283402412586862702349008828717083285
   - ry2 = 93506999776394773977012568374000894735649274226096876119078636851803903807856

4. **Phase 11 Integer Equation (VERIFIED):**
   - Lambda_N * qx2 - Qx2 = b_x * N (exact)
   - Where: qx2 = rx2 * delta (mod N), Qx2 = Px2 * delta (mod N), delta = p - N
   - b_x = 429680843809640556896504318302883863992518438102845346670377326599404852023

## Candidates Tested (All FAILED EC verification)

### Primary Candidates (In Band)
1. **d2 = Lambda_N - 2*b_x** = 0x019dc7f35bb98ef4dbea286a6452f08a972265705bb26524469100f8dd5aa3e3
   - 249 bits, IN BAND [2^248, 2^250)
   - d2 * G = (108190595579172525121296369524068964648187656461616193943970324686991723388931, 63292644548948999053766151830812026014177764038895154525395081569960879551016)
   - Status: **FAIL** (x and y do not match P)

2. **Lambda_N - b_x** = 1160768690012917574635786030288336365381455549340776309609877434935905072922
   - 250 bits, IN BAND
   - Status: **FAIL**

3. **Lambda_N** (itself) = 1590449533822558131532290348591220229373973987443621656280254761535309924945
   - 250 bits, IN BAND
   - Status: **FAIL**

4. **defect_value % 2^248 + 2^248** = 1461501637330902918203684832716283019651637574703
   - In band, from discretelog160.txt
   - Status: **FAIL**

5. **Lambda_N - (defect_value // delta)** = 1590449533822558131532290348591220229106197321877614463764548774595518094899
   - 250 bits, IN BAND
   - Status: **FAIL**

### Candidates from Combinations (All Out of Band or Failed)
- CP1 mod N = CP1 (256 bits) - **FAIL**
- CP1 + N - 2^248 (257 bits) - **FAIL**
- CP1 * Gy_std^-1 mod N - 256 bits - **FAIL**
- CP1 * Lambda_yN / Lambda_N mod N - 256 bits - **FAIL**
- d2 + Lambda_yN (255 bits) - **FAIL**
- d2 - Lambda_yN (256 bits) - **FAIL**
- Lambda_N * Lambda_yN mod N (256 bits) - **FAIL**

### Candidates from CP1 Combinations with k_y (All tested, none in band or failed)
- floor(N*k_y/p) * CP1 mod N
- k_y * CP1 mod N
- CP1 * (CP1 - CR1) mod N
- CP1 + CR1 (256 bits)
- CP1 - CR1 (256 bits)

## Open Questions

1. **What is R?** R = (rx2, ry2) is a point on the curve, verified by: ry2^2 ≡ rx2^3 + 7 (mod p). But R ≠ G and CR1 * G ≠ R. What is the scalar r such that R = r*G?

2. **Bridge Constant Relationship:** Lambda = CP1 / CR1 = Px2 / rx2 (mod p) = 54881026424193271572144112405688854256494227595683820452982358052070012199570. This is the p-side bridge constant. Lambda_N = Px2 / rx2 (mod N) verified. lambda_y = Py2 / ry2 (mod p) also exists.

3. **Transformation Space:** In Complexity Simplified transformed space, CP1 = d and CR1 = r. But the transformation uses a different generator G_A, not the standard G. The relationship between G_A and G is unknown.

4. **Y-Bridge Mismatch:** d_from_x = CP1 = 92482... (256 bits), d_from_y = Py2 * Gy_std^-1 mod p = 54216... (255 bits). These differ by 38265... mod p. Why don't they match?

## Next Steps (Suggested)

Based on the user's request to continue from the summary and the findings above:

1. ✓ **DONE** - Test CP1 mod N as candidate (256-bit value, needs band adjustment)
   - Result: CP1 < N but 256 bits, cannot be brought into [2^248, 2^250) without changing mod N value

2. ✓ **DONE** - Verify y-bridge: CP1 = Px2 * Gx_std^-1 mod p, need d = Py2 * Gy_std^-1 mod p equivalent
   - Result: d_from_y = 54216824345750077586866642470380860453225921090215134620344685777122626057588 (255 bits)
   - This is OUT of band [2^248, 2^250)
                     
3. **NEW** - Since d_from_y ≠ CP1, and both are based on coordinate ratios, maybe d is a combination:
   - d = CP1 * d_from_y * Gx_std * Gy_std^-1 mod N?
   - Or use Chinese Remainder Theorem with p and N? (But gcd(p, N) = 1)

4. **NEW** - Investigate the epsilon ladder approach with corrected band
   - Existing epsilon ladder uses old band [2^159, 2^160)
   - Needs to be updated to [2^248, 2^250)

5. **NEW** - The defect might need a different correction. From discretelog160.txt:
   - defect_value = 115792089237316195423570985007957157034604533206538721623099442498080868400175
   - N - defect_value = 730750818233031072536182759505720643437293094162 ≈ 2^159 (but not exact)
   - Maybe defect correction needs to use floor(N*k_y/p) or CP1-CR1 values

6. **RECOMMENDED** - The most promising path is to recognize that:
   - Lambda_N * rx2 ≡ Px2 (mod N) ✓
   - Lambda_yN * ry2 ≡ Py2 (mod N) ✓
   - If we could show that rx2 = G.x and ry2 = G.y, then d = Lambda_N = Lambda_yN
   - But rx2 ≠ G.x and ry2 ≠ G.y
   - However, if there exists a scalar r such that (rx2, ry2) = r*G, then:
     Px2 ≡ Lambda_N * rx2 (mod N)
     Px2 ≡ Lambda_N * (r*G).x (mod N)
   - This doesn't directly give us d without knowing how (r*G).x relates to r and G.x

## Key Files
- `C:\Users\mitch\Desktop\secp256k1\chatt.txt` - Source values
- `C:\Users\mitch\Desktop\secp256k1\discretelog160_updated.txt` - Full pipeline with latest findings
- `C:\Users\mitch\Desktop\secp256k1\test_*.py` - Multiple test files
