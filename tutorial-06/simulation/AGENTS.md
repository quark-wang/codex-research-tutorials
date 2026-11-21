# Simulation-specific guidance

- [SIM-HAMILTONIAN-01] Use `H = -J sum_<ij> s_i s_j`, spins in `{-1,+1}`, periodic boundaries, zero field, and count every bond once.
- [SIM-RNG-02] Derive a distinct recorded seed for every `(L, T, chain)` job; never use global NumPy RNG state.
- [SIM-SAMPLING-03] Separate equilibration and measurement; record sample interval, stored samples, and acceptance fraction.
- [SIM-OUTPUT-04] Write regenerated data under `results/reproduction/` unless a human explicitly updates the release snapshot.
- [SIM-VERIFY-05] Run `python -m pytest -q tests/test_simulation.py`, then the full suite.
