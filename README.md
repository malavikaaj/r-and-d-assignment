## Parametric Curve Fit – R&D/AI Assignment

This repository includes a Python solver for the assignment to estimate the unknowns `θ`, `M`, and `X` of the parametric curve:

`x = t cos(θ) − e^{M|t|} sin(0.3 t) sin(θ) + X`

`y = 42 + t sin(θ) + e^{M|t|} sin(0.3 t) cos(θ)`

### Data
- CSV used: `data/xy_data.csv` (columns: `x,y`)

### Method (Brief)
- Rotate coordinates by `θ` to an orthonormal basis `(e1, e2)`.
- Project each point onto `e1` to estimate `t` via `t = (x−X) cosθ + (y−42) sinθ`.
- The `e2` projection should equal `R(t) = e^{M|t|} sin(0.3 t)`; minimize the L1 residual between observed `e2` and `R(t)` over `θ`, `M`, `X`.
- Optimization: coarse grid followed by local refinement (coordinate descent with shrinking steps).

### Fitted Parameters
- `θ ≈ 30.000°`
- `M ≈ 0.030000`
- `X ≈ 55.000000`
- L1 residual on perpendicular component: `≈ 0.02257`
- L1 position error (|Δx|+|Δy|): `≈ 0.03083`

### Final Equation 
`\left(t*\cos(30.000000\,\deg)-e^{0.030000\left|t\right|}\cdot\sin(0.3t)\sin(30.000000\,\deg)+55.000000,\;42+t*\sin(30.000000\,\deg)+e^{0.030000\left|t\right|}\cdot\sin(0.3t)\cos(30.000000\,\deg)\right)`

### Reproduce Locally
- Ensure Python 3 is available.
- Download CSV to `data/xy_data.csv`.
- Run: `python3 scripts/solve_params.py data/xy_data.csv`
- Outputs: `results.json` and `results.md` with the fitted parameters and equation.
