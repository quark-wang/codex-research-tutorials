# Start here — Tutorial 06

## 1. Verify the released project first

From the project root:

```powershell
python -m pip install -r requirements.txt
python scripts/run_verification.py
```

The final release run used Python 3.13.1 and produced `48 passed`, a valid raw-data SHA-256 check, a valid 176-row base schema, six matching read-only Codex CLI probes, and seven base PNG/PDF figure pairs. The paper-reproduction subtree adds one separately hashed PNG/PDF pair.

## 2. Inspect which instructions apply

The project helper implements the documented project-level lookup order: `AGENTS.override.md`, then `AGENTS.md`, then configured fallbacks; at most one nonempty file is selected per directory from the project root down to the working directory.

```powershell
python scripts/build_audits.py
```

Inspect:

- `results/instruction_resolution.csv`
- `results/instruction_resolution.json`
- `results/policy_scenarios.csv`
- `results/policy_scenarios.json`
- `results/codex_instruction_probes/*.json`
- `results/codex_probe_summary.json`

Starting at the repository root activates only the root file. Starting in `analysis/` activates root plus `analysis/AGENTS.md`. Starting in `reports/` activates root plus `reports/AGENTS.override.md`; the same-directory `reports/AGENTS.md` is shadowed.

The committed probe files were produced with `codex-cli 0.171.0-alpha.13`, `--sandbox read-only`, `--ephemeral`, and `-C` pointing at each scope. `scripts/summarize_codex_probes.py` compares those actual JSON outputs with the deterministic resolver.

## 3. Run the science analysis

```powershell
python analysis/run_analysis.py
```

This consumes the immutable released chain summary and writes:

- `results/chain_observables.csv`
- `results/thermodynamic_summary.csv`
- `results/critical_summary.json`

The exact square-lattice value `Tc = 2 / ln(1 + sqrt(2))` is retained as an external reference. It is not fed into the susceptibility-peak or Binder-crossing estimators.

## 4. Regenerate instead of modifying released input

```powershell
python run_experiment.py
```

The default output is under `results/reproduction/`; this prevents routine agent work from overwriting `data/raw/`. The release workload has 176 chains and is intentionally much slower than the tests. For a smoke check:

```powershell
python run_experiment.py --quick
```

## 5. Read the uncertainty correctly

The plotted error bars are SEM across four independent chains. Within-chain samples are correlated, and this compact teaching project does not estimate the integrated autocorrelation time. Therefore these bars must not be relabeled as fully autocorrelation-corrected production uncertainties.

## 6. Reproduce the published-figure target

The external target is Saratz et al., *Nature Communications* **7**, 13611 (2016), Figure 9(a-b). Run a fast plumbing check first:

```powershell
python paper_reproduction/run_figure9_reproduction.py --quick
```

Then run the declared formal workload:

```powershell
python paper_reproduction/run_figure9_reproduction.py
```

Inspect:

- `paper_reproduction/results/reproduction/figure9_chain_summary.csv`
- `paper_reproduction/results/reproduction/figure9_summary.csv`
- `paper_reproduction/results/reproduction/figure9_metadata.json`
- `paper_reproduction/results/figures/fig08_saratz_figure9ab_reproduction.png`
- `paper_reproduction/results/figures/fig08_saratz_figure9ab_reproduction.pdf`

This is an independent numerical reproduction of curve ordering, the Onsager limit, and finite-size scaling. It is not a claim that the paper's unpublished random seeds or pointwise source data were recovered.
