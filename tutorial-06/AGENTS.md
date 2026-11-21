# Repository guidance for Codex

- [ROOT-DATA-01] Treat `data/raw/` as an immutable released snapshot. Regenerated tables belong in `results/reproduction/`.
- [ROOT-PROVENANCE-02] Preserve `synthetic_monte_carlo` and seed metadata in every machine-readable derivative.
- [ROOT-SCOPE-03] Keep changes inside the smallest relevant subtree and do not access credentials or files outside this repository.
- [ROOT-VERIFY-04] After Python changes run `python -m pytest -q`; before release run `python scripts/run_verification.py`.
- [ROOT-EVIDENCE-05] Separate measured Monte Carlo estimates, exact formulas, and interpretation.

This deterministic teaching workload is the zero-field ferromagnetic square-lattice Ising model with periodic boundaries and `J = k_B = 1`. Passing tests does not prove equilibration for arbitrary production parameters or replace autocorrelation analysis.
