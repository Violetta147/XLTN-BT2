"""Custom one-step residual AR(1) weighted NLS; not joint-ML/author solver."""
import numpy as np
from scipy.optimize import minimize_scalar
from harmonic_nls import basis, OFFSETS


def noise_parameter(segment, fs, anchor, order=3):
    weights = np.sqrt(np.hanning(len(segment)))
    design = basis(len(segment), fs, anchor, order)
    coefficients, _, rank, _ = np.linalg.lstsq(design*weights[:, None], segment*weights, rcond=None)
    assert rank == design.shape[1]
    error = segment-design@coefficients
    denominator = float(error[:-1]@error[:-1])
    raw = float(error[1:]@error[:-1])/denominator if denominator else 0.
    return float(np.clip(raw, -.95, .95)), raw


def whiten(values, rho):
    out = values.copy()
    out[0] *= np.sqrt(1-rho*rho)
    out[1:] = values[1:]-rho*values[:-1]
    return out


def residual(segment, fs, frequency, order, rho):
    weights = np.sqrt(np.hanning(len(segment)))
    design = whiten(basis(len(segment), fs, frequency, order), rho)*weights[:, None]
    target = whiten(segment, rho)*weights
    coefficients, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    assert rank == design.shape[1]
    error = target-design@coefficients
    return float(error@error), coefficients


def refine(segment, fs, anchor, order=3):
    assert order == 3
    lower, upper = max(70., anchor*2**(-100/1200)), min(400., anchor*2**(100/1200))
    grid = np.unique(np.clip(anchor*2**(OFFSETS/1200), lower, upper))
    if not np.any(segment-segment[0]):
        return dict(f0=float(anchor), cost=0., score=0., rho=0., rho_raw=0.,
                    grid=grid, grid_cost=np.zeros(len(grid)), bracket=np.array([anchor, anchor]),
                    at_boundary=False, silent_fallback=True)
    rho, raw = noise_parameter(segment, fs, anchor, order)
    costs = np.array([residual(segment, fs, f, order, rho)[0] for f in grid])
    best = int(np.argmin(costs))
    left, right = grid[max(0, best-1)], grid[min(len(grid)-1, best+1)]
    candidates = [(costs[best], grid[best])]
    if right > left:
        optimized = minimize_scalar(lambda logf: residual(segment, fs, np.exp(logf), order, rho)[0],
            bounds=(np.log(left), np.log(right)), method='bounded', options=dict(xatol=1e-8, maxiter=100))
        if optimized.success and np.isfinite(optimized.fun):
            candidates.append((float(optimized.fun), float(np.exp(optimized.x))))
    cost, frequency = min(candidates, key=lambda pair: (pair[0], pair[1]))
    return dict(f0=float(frequency), cost=float(cost), score=float(-cost), rho=rho, rho_raw=raw,
                grid=grid, grid_cost=costs, bracket=np.array([left, right]),
                at_boundary=bool(np.isclose(frequency, lower, atol=1e-4) or np.isclose(frequency, upper, atol=1e-4)),
                silent_fallback=False)
