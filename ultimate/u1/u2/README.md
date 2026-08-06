# Puzzle Dynamics Engine Ultimate

Functional modules: State, Transition, Geometry, Grammar, Prediction, Cryptographic, Echo, Correlation, Invariant Finder, and Hypothesis Lab.

## Run
```bash
pip install -r requirements.txt
python run_engine.py --data data --out reports
```

Custom formulas:
```bash
python run_engine.py --formula "(x+y) % N" --formula "lambda_glv * delta % N"
```

The invariant finder ranks exploratory candidates by stability, predictive correlation, and uniqueness. A high score is a lead to audit, not proof of a scalar bridge.
