# Analysis-specific guidance

- [ANALYSIS-UNITS-01] In reduced units report `E/N`, `|M|/N`, `Cv/N`, `chi_abs/N`, and dimensionless `U4`.
- [ANALYSIS-FORMULA-02] Use `Cv/N=beta^2(<E^2>-<E>^2)/N`, `chi_abs/N=beta(<M^2>-<|M|>^2)/N`, and `U4=1-<M^4>/(3<M^2>^2)`.
- [ANALYSIS-CHAINS-03] Compute nonlinear observables per independent chain, then report chain mean and SEM.
- [ANALYSIS-TC-04] Estimate Tc from the largest-size susceptibility peak and Binder crossings; exact Tc is reference only.
- [ANALYSIS-VERIFY-05] Run `python -m pytest -q tests/test_analysis.py`, then the full suite.
