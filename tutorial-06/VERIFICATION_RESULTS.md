# Verification results

Release verification date: 2026-11-21 (Asia/Shanghai).

## Observed environment

- Windows 11 (`10.0.26200`)
- Python 3.13.1
- NumPy 2.2.2
- pandas 2.2.3
- Matplotlib 3.10.3
- Numba 0.65.1
- pytest 9.2.0

## Automated evidence

```text
................................................                         [100%]
48 passed in 3.83s
wrote 7 PNG/PDF figure pairs
RELEASE_REPORT.md: PASS
raw hash: PASS; schema: PASS
paper reproduction: PASS
```

The final verification wrapper completed in 11.75 s, excluding Monte Carlo generation. Runtime is machine-dependent.

A final complete 176-chain run from the reviewed source wrote `results/reproduction/ising_chain_summary.csv` in **105.57 s** on this machine. Its SHA-256 exactly matched the released table:

```text
5a962c4a33163a3e88dd87e61935a6b5144ad193110a51d769c97dce91a0e89f
```

Runtime is machine-dependent; the byte-identical table is the determinism check.

## Saratz Figure 9(a-b) independent reproduction

Target: N. Saratz et al., *Nature Communications* **7**, 13611 (2016), Figure 9(a-b), DOI `10.1038/ncomms13611`.

This project independently generated the numerical relationships; it did not use the paper's original point data or recover unpublished random seeds.

| Item | Observed value |
| --- | ---: |
| lattice sizes | 10, 20, 40 |
| temperature points per size | 61 (`1.50` to `3.00`) |
| independent chains per state point | 4 |
| chain rows | 732 |
| summary rows | 183 |
| equilibration sweeps per chain | 3,000 |
| measurement sweeps per chain | 9,000 |
| stored samples per chain | 1,000 |
| final-source wall time | 136.23 s |

Observed quantitative checks:

```text
mean |mL - m_infinity| for T <= 2 = 0.000360751
mL(T=3, L=10) = 0.277135
mL(T=3, L=20) = 0.1357175
mL(T=3, L=40) = 0.066789375
```

The release verifier additionally passed all of the following: 732/183-row schemas, 61-temperature grid, four unique chains per point, `T>=Tc` ratio filtering, finite-size ordering at `T=3`, and recorded SHA-256 values for the final source script, chain CSV, summary CSV, PNG, and PDF.

Reproduction PNG SHA-256:

```text
707544e824f07d359c827b7cb162d7fc5ce424db68a680bb6b62382f59386cb7
```

## Released workload

| Item | Observed value |
| --- | ---: |
| lattice sizes | 8, 12, 16, 24 |
| temperatures | 11 (`1.80` to `2.80`) |
| independent chains per state point | 4 |
| chain rows | 176 |
| equilibration sweeps per chain | 600 |
| measurement sweeps per chain | 1,200 |
| sample interval | 4 sweeps |
| stored samples per chain | 300 |
| master seed | 20261121 |

Released input SHA-256:

```text
5a962c4a33163a3e88dd87e61935a6b5144ad193110a51d769c97dce91a0e89f
```

## Critical-region estimates

The exact reference for the infinite 2D square lattice is:

```text
Tc = 2.269185314213022 J/kB
```

Observed finite-size estimators:

| Estimator | Result |
| --- | ---: |
| largest-size (`L=24`) local quadratic susceptibility peak | 2.312318 |
| Binder crossing `L=8/12` | 2.236106 |
| Binder crossing `L=12/16` | 2.305727 |
| Binder crossing `L=16/24` | 2.233151 |
| median Binder crossing | 2.236106 |

These are deliberately reported as finite-size, finite-grid Monte Carlo estimates. Their deviations from the exact infinite-lattice value are not software failures.

## Instruction and policy evidence

- 6 working-directory scopes resolved: root, simulation, analysis, figures, paper_reproduction, reports.
- 6 actual `codex-cli 0.171.0-alpha.13` probes were executed with a read-only sandbox; every marker list matched the deterministic resolver exactly.
- `reports/AGENTS.override.md` shadowed `reports/AGENTS.md` as expected.
- 4 proposed-change scenarios checked mechanically.
- The safe analysis and safe figure scenarios passed.
- Raw-input tampering and a report-scope escape were rejected.

## Figure inventory

1. `fig01_instruction_hierarchy` — deterministic instruction chain plus actual CLI-probe match status.
2. `fig02_magnetization` — finite-size absolute magnetization.
3. `fig03_energy` — energy per spin.
4. `fig04_heat_capacity` — heat-capacity anomaly.
5. `fig05_susceptibility` — susceptibility peak and finite-size shift.
6. `fig06_binder_crossings` — Binder cumulants and interpolated crossings.
7. `fig07_verification_dashboard` — release evidence summary.

The additional paper target is:

8. `paper_reproduction/results/figures/fig08_saratz_figure9ab_reproduction` — independent reproduction of Saratz Figure 9(a-b), plus its chain CSV, summary CSV, and provenance metadata.

Every item exists as both 300 dpi PNG and vector PDF. The seven base figures are listed in `results/figure_manifest.csv`; the paper figure hashes are recorded in `paper_reproduction/results/reproduction/figure9_metadata.json`.
