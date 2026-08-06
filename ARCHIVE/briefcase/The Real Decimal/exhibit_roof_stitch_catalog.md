# EXHIBIT: roof-stitch catalog — p.N and N.p

## Distinction

| Kind | Example | Role |
|------|---------|------|
| coordinate packet | `x.y / p` with `x < p` | public point witness, stays under field roof |
| roof-stitch | `p.N`, `N.p`, `p.(p-N)`, `N.(p-N)` | roof relationship + overflow, not a pubkey |

```text
p.N = p + N / 10^78
N.p = N + p / 10^78
```

## Summary table

| Normalization | Placement | Meaning |
|---------------|-----------|---------|
| `p.N / 2^256` | under_roof | field roof under binary roof, N in tail |
| `N.p / 2^256` | under_roof | scalar roof under binary roof, p in tail |
| `N.p / p` | **under_roof** | scalar roof inside field courtroom |
| `p.N / p` | **overflow** | field-roof overflow witness |
| `p.N / N` | **overflow** | overflow above scalar roof |
| `N.p / N` | **overflow** | scalar-roof overflow by tiny tail |

## Key values

### N.p / p — under field roof (cleanest pair)

```text
N.p / p = 0.999999999999999999999999999999999999996265544654959865847240417452019444905995...
```

Compare `N / p`:

```text
N / p   = 0.999999999999999999999999999999999999996265544654959865847240417452019444905994...
```

The stitched tail adds `p / (10^78 * p) = 1 / 10^78` above `N/p`.

### p.N / p — field-roof overflow

```text
p.N / p = 1.000000000000000000000000000000000000000000000000000000000000000000000000000000...
         = 1 + N / (10^78 * p)
```

Overflow tail above 1:

```text
(p.N / p) - 1 = 0.0000000000000000000000000000000000000000000000000000000000...
```

### Binary-roof witnesses

```text
p.N / 2^256 = 0.999999999999999999999999999999999999999999999999999999999999999999962907930056...
N.p / 2^256 = 0.999999999999999999999999999999999999996265544654959865847240417451982352836051...
```

### Defect-tail stitches

```text
p.(p-N) = field roof with defect tail (39 digits)
N.(p-N) = scalar roof with defect tail

p.(p-N) / p = 1.000000000000000000000000000000000000000000000000000000000000000000000000000003...  (overflow)
N.(p-N) / p = 0.999999999999999999999999999999999999996265544654959865847240417452019444905998...  (under_roof)
```

## Cross-courtroom reference

```text
N / p       = 0.999999999999999999999999999999999999996265544654959865847240417452019444905994...
(p-N) / p   = 0.000000000000000000000000000000000000003734455345040134152759582547980555094005...
(p-N) / N   = 0.000000000000000000000000000000000000003734455345040134152759582547980555094019...
```

## Clean ruling

```text
p.N is allowed, but it is a roof-stitch, not the same kind of packet as x.y.
It tells us about roof relationship and overflow, not a public point witness.
```

Judge Popcorn: **Roof-stitches measure courtroom overflow; coordinate packets witness public points.**
