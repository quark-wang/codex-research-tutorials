"""Baseline scientific fitting routines for Tutorial 04.

Codex assignment: implement summarize_replicates() without changing established behavior.
"""
from __future__ import annotations
import numpy as np

KB_EV_PER_K = 8.617333262145e-5


def arrhenius_fit(temperature_K, diffusion_m2s, sem_m2s=None):
    """Fit ln(D) against 1000/T. Returns fit and physical parameters."""
    t = np.asarray(temperature_K, dtype=float)
    d = np.asarray(diffusion_m2s, dtype=float)
    if t.ndim != 1 or d.ndim != 1 or len(t) != len(d) or len(t) < 3:
        raise ValueError("T and D must be 1D arrays of equal length >= 3")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(d)):
        raise ValueError("T and D must be finite")
    if np.any(t <= 0) or np.any(d <= 0) or np.unique(t).size < 3:
        raise ValueError("positive D/T and at least three distinct temperatures required")
    x = 1000.0 / t
    y = np.log(d)
    if sem_m2s is not None:
        sem = np.asarray(sem_m2s, dtype=float)
        if sem.shape != d.shape or not np.all(np.isfinite(sem)) or np.any(sem <= 0):
            raise ValueError("SEM must match D and be positive finite")
        weight = d / sem
    else:
        weight = None
    slope, intercept = np.polyfit(x, y, 1, w=weight)
    fitted = slope * x + intercept
    sst = float(np.sum((y - y.mean())**2))
    if sst <= 1e-24:
        raise ValueError("ln(D) variation too small for R2")
    return {
        "Ea_eV": float(-1000.0 * KB_EV_PER_K * slope),
        "D0_m2_s": float(np.exp(intercept)),
        "slope": float(slope),
        "intercept": float(intercept),
        "R2_unweighted": float(1.0 - np.sum((y - fitted)**2) / sst),
    }
