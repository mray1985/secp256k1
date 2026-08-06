# RMD160-spine unreduced curve ledger

## Raw-value ledger

$$x^3+7 = y^2 + C p$$

Columns: `y2_full`, `x3plus7_full`, `p_carry` (not mod p).

Puzzles with curve account: **88**. All satisfy `X-Y-Cp=0`.
P135 `p_carry` matches provided constant: **yes**.

## Rank ledger

Spine: RMD160 rank `H` over 160.
Stretch: `R160 = 1+(r-1)*159/(M-1)`.
`E_f = R160_f - H`.
`pay` omitted (same order as rmd160).

Fit `H_hat = sum w_f R160_f` on ['Px', 'Py', 'neg_y', 'y2_full', 'x3plus7_full', 'p_carry']:
- weights: `{'Px': 0.0, 'Py': 0.236054, 'neg_y': 0.358384, 'y2_full': 0.236054, 'x3plus7_full': 0.0, 'p_carry': 0.169507}`
- MAE=40.3984, RMSE=46.0553, Spearman=0.1422

Files:
- `CHART_BY_RMD160.csv` / `.txt`
- `UNREDUCED_CURVE_LEDGER.txt`
- `ledger.json`
