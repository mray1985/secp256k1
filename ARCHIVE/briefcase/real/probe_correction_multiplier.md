# Probe: correction multiplier composites

Prior pass: B / B4 / Δ / C alone do not land on ledger objects.
This pass: scale known objects by `C` / `C⁻¹`, and packet × correction.

`correction = (p−N)/B^4 = 1.2707681476957356442703017100172422436809463020206897778591194007162688642277912`
`C_p = Δ·B4⁻¹ mod p = 77971234722912277281798096523408933079102615211656040185053424205597174876124`
`C_N = Δ·B4⁻¹ mod N = 80693466525888938314810921860815482573429063665938278805806464124388781033089`

**Hit count:** 1

## Hits

- **special** `floor(packet*DELTA) / floor(packet*B4)` / `near_correction` → `correction_multiplier`

## Special: packet floor ratio vs correction

- floor(packet*DELTA) / floor(packet*B4) = `1.2707681476957356442703017100172422436939426831654605227809015028943624412495354`
- correction = `1.2707681476957356442703017100172422436809463020206897778591194007162688642277912`
- abs_diff = `0.0000000000000000000000000000000000000129963811447707449217821021780935770217442`
- near_correction = `True`

## Ruling

If correction appears as a scale between ledger objects, it is part of the modulus-accounting layer. Still not a key.
