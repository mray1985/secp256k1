# Putting the Puzzle Together

Cross-thread index: **ChatGPT patent dialogue** (`00_Projects/patent/`) ↔ **Cursor briefcase lab** (`ARCHIVE/briefcase/`).

This project is not one hypothesis — it is three stacked rooms:

| Room | Objects | Where it lives |
|------|---------|----------------|
| **Field** | `x, y, p−y, β, 7⁻¹ mod p` | `The Real Decimal/`, `headed.txt`, `THEWAY.txt` |
| **Scalar** | `d, k, r, s, z, λ, 7⁻¹ mod N` | `53125.txt`, RSZ courtroom, TDAD scalar |
| **Chain** | genesis vout order, spend scripts, batch sweep | `puzzlepubkeys/`, mempool spend `5d45587c…` |

Hard gate (both threads agree):

```text
[d]G = P  AND  HASH160(compress(P)) = target
```

Everything else is witness / echo / courtroom packet — not proof.
