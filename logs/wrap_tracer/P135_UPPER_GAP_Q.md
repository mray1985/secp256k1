# P135 upper-gap point \(Q = P-[U]G\)

**Status:** **LOCKED FACT — 0 verified bits**

\[
U=2^{135}-1,\qquad Q=P_{135}-[U]G=[d-U]G=-[g]G,\quad g=U-d.
\]

Band: \(2^{134}\le d\le U\). Then \(g\in[0,2^{134})\).

## Verified coordinates (even \(y\), compressed `02…`)

| | value |
|--|------:|
| \(Q_x\) | 52886041483769761904968341876867358442579522291679760649513667751265486773330 |
| \(Q_y\) | 63913543214727770248777694773511805483462696697028811296623304851008216065287 |

\[
\boxed{(Q_x<G_x,\; Q_y>G_y)}
\]

Exact for this point. **Not** a proof that \(g\) lies above/below a scalar threshold — \(-[g]G\) coordinates do not move monotonically in \(g\).

## Pitfall

Some ledgers store \(p-y\) under the name `Py`. The compressed prefix `02` requires the **even** branch. The odd branch yields a different \(Q\).

## Better object

\[
\boxed{\text{How far is }Q\text{ from }\mathcal{O},-G,-[2]G,\ldots\text{ in scalar space?}}
\]

| Landmark | Scalar meaning |
|----------|----------------|
| \(Q=\mathcal{O}\) | \(d=U\) |
| \(Q=-G\) | \(d=U-1\) |
| \(Q=-[2]G\) | \(d=U-2\) |
| \(Q=-[g]G\) | upper-gap DLP |

This is the **upper-bound** form of the interval discrete-log problem (dual to S-01 band-floor \(Q_{\mathrm{floor}}=P-[2^{134}]G\)).

Relation: \(u+g=2^{134}-1\) with \(u=d-2^{134}\).

## Run

```powershell
python p135_upper_gap_Q.py
```

Artifact: `logs/wrap_tracer/p135_upper_gap_Q.json`
