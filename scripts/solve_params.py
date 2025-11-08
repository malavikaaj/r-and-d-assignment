#!/usr/bin/env python3
import csv
import json
import math
import sys
from pathlib import Path


def load_points(csv_path):
    pts = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        cols = [c.strip().lower() for c in header] if header else []
        has_t = 't' in cols
        idx_t = cols.index('t') if has_t else None
        idx_x = cols.index('x') if 'x' in cols else 0
        idx_y = cols.index('y') if 'y' in cols else 1
        for row in reader:
            try:
                x = float(row[idx_x])
                y = float(row[idx_y])
                t = float(row[idx_t]) if has_t else None
                pts.append((x, y, t))
            except Exception:
                continue
    return pts, has_t


def compute_error(pts, theta_deg, M, X, use_given_t=False):
    th = math.radians(theta_deg)
    c = math.cos(th)
    s = math.sin(th)
    e1x, e1y = c, s
    e2x, e2y = -s, c
    total = 0.0
    for x, y, t_given in pts:
        dx = x - X
        dy = y - 42.0
        t = t_given if (use_given_t and t_given is not None) else (dx * e1x + dy * e1y)
        dot_e2 = dx * e2x + dy * e2y
        R = math.exp(M * abs(t)) * math.sin(0.3 * t)
        r = dot_e2 - R
        total += abs(r)
    return total


def coarse_search(pts, use_given_t=False):
    best = None
    # Coarse grids
    theta_grid = [0.5 + i for i in range(0, 50)]  # ~0.5..49.5 deg step 1
    M_grid = [round(-0.05 + i * 0.01, 5) for i in range(11)]  # -0.05..0.05 step 0.01
    X_grid = [i for i in range(0, 101, 5)]  # 0..100 step 5
    for th in theta_grid:
        for M in M_grid:
            for X in X_grid:
                err = compute_error(pts, th, M, X, use_given_t)
                if (best is None) or (err < best['err']):
                    best = {'theta_deg': th, 'M': M, 'X': X, 'err': err}
    return best


def refine_search(pts, start, use_given_t=False, max_iters=30):
    th = start['theta_deg']
    M = start['M']
    X = start['X']
    step_th = 1.0
    step_M = 0.01
    step_X = 2.0
    best_err = compute_error(pts, th, M, X, use_given_t)
    for _ in range(max_iters):
        improved = False
        candidates = []
        for dth in (-step_th, 0.0, step_th):
            th_c = max(0.001, min(49.999, th + dth))
            for dM in (-step_M, 0.0, step_M):
                M_c = max(-0.05, min(0.05, M + dM))
                for dX in (-step_X, 0.0, step_X):
                    X_c = max(0.0, min(100.0, X + dX))
                    candidates.append((th_c, M_c, X_c))
        # Evaluate unique candidates
        seen = set()
        for th_c, M_c, X_c in candidates:
            key = (round(th_c, 6), round(M_c, 6), round(X_c, 6))
            if key in seen:
                continue
            seen.add(key)
            err = compute_error(pts, th_c, M_c, X_c, use_given_t)
            if err < best_err:
                th, M, X = th_c, M_c, X_c
                best_err = err
                improved = True
        if not improved:
            # reduce step sizes
            step_th = max(0.05, step_th * 0.5)
            step_M = max(0.001, step_M * 0.5)
            step_X = max(0.2, step_X * 0.5)
            # stop if steps are very small
            if step_th <= 0.05 and step_M <= 0.001 and step_X <= 0.2:
                break
    return {'theta_deg': th, 'M': M, 'X': X, 'err': best_err}


def final_l1_xy(pts, theta_deg, M, X, use_given_t=False):
    th = math.radians(theta_deg)
    c = math.cos(th)
    s = math.sin(th)
    total = 0.0
    for x, y, t_given in pts:
        dx = x - X
        dy = y - 42.0
        t = t_given if (use_given_t and t_given is not None) else (dx * c + dy * s)
        Rx = c * t - s * (math.exp(M * abs(t)) * math.sin(0.3 * t)) + X
        Ry = 42.0 + s * t + c * (math.exp(M * abs(t)) * math.sin(0.3 * t))
        total += abs(Rx - x) + abs(Ry - y)
    return total


def main():
    if len(sys.argv) < 2:
        print("Usage: solve_params.py data/xy_data.csv")
        sys.exit(1)
    csv_path = Path(sys.argv[1]).resolve()
    pts, has_t = load_points(csv_path)
    if not pts:
        print("No points loaded from", csv_path)
        sys.exit(2)
    use_given_t = has_t
    coarse = coarse_search(pts, use_given_t)
    refined = refine_search(pts, coarse, use_given_t)
    l1_xy = final_l1_xy(pts, refined['theta_deg'], refined['M'], refined['X'], use_given_t)
    result = {
        'theta_deg': refined['theta_deg'],
        'M': refined['M'],
        'X': refined['X'],
        'err_e2_l1': refined['err'],
        'err_xy_l1': l1_xy,
        'has_t_in_csv': has_t
    }
    print(json.dumps(result, indent=2))
    # also write to results.json and results.md
    out_json = Path('results.json')
    out_md = Path('results.md')
    out_json.write_text(json.dumps(result, indent=2))
    equation = (
        f"\\left(t*\\cos({result['theta_deg']:.6f}\\,\\deg)"
        f"-e^{{{result['M']:.6f}\\left|t\\right|}}\\cdot\\sin(0.3t)\\sin({result['theta_deg']:.6f}\\,\\deg)"
        f"+{result['X']:.6f},\\;42+t*\\sin({result['theta_deg']:.6f}\\,\\deg)"
        f"+e^{{{result['M']:.6f}\\left|t\\right|}}\\cdot\\sin(0.3t)\\cos({result['theta_deg']:.6f}\\,\\deg)\\right)"
    )
    out_md.write_text(
        "# Fitted Parameters\n\n"
        + json.dumps(result, indent=2)
        + "\n\n**Equation (LaTeX-ready):**\n\n" + equation + "\n"
    )


if __name__ == '__main__':
    main()