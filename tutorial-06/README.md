# Codex Research Tutorial 06

Executable companion project for **“用分层 AGENTS.md 复现一张 Nature Communications 论文图”**. The project independently recalculates the numerical relationships in Saratz et al., *Nature Communications* **7**, 13611 (2016), Figure 9(a-b), while retaining a separate deterministic 2D-Ising verification workload. It demonstrates that literature targets, repository instructions, physical tests, path audits, schema checks, and immutable-input hashes solve different parts of the reliability problem.

## What is actually included

- 176 independent-chain summaries: 4 lattice sizes × 11 temperatures × 4 chains.
- 600 equilibration sweeps and 1,200 measurement sweeps per chain; one stored sample every 4 sweeps (300 samples per chain).
- `E/N`, `|M|/N`, `Cv/N`, `chi_abs/N`, Binder `U4`, susceptibility-peak and Binder-crossing estimates.
- Root guidance plus nested guidance for simulation, analysis, figures, and reports.
- A paper-specific `paper_reproduction/AGENTS.md` that fixes the external target and disclosure boundary.
- A deliberate same-directory `AGENTS.override.md` precedence example.
- An independent Figure 9(a-b) reproduction: `L=10,20,40`, 61 temperatures, 4 chains per point, 732 chain rows, exact Onsager reference, and FSS collapse.
- 48 automated tests, SHA-256 input verification, schema validation, six actual read-only Codex CLI probes, four mechanical scope scenarios, seven base PNG/PDF pairs, and one paper-reproduction PNG/PDF pair.

The bundled table is **synthetic Monte Carlo teaching data**. It is not an experiment, a DFT calculation, or a universal production-quality equilibrium study.

## Quick start

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python analysis/run_analysis.py
python scripts/build_audits.py
python scripts/summarize_codex_probes.py
python scripts/snapshot_raw.py verify
python scripts/run_verification.py
python paper_reproduction/run_figure9_reproduction.py --quick
```

Regenerate the complete Monte Carlo workload without overwriting released input:

```powershell
python run_experiment.py
```

The default regeneration target is `results/reproduction/ising_chain_summary.csv`.

Regenerate the independent paper target (about 2–3 minutes on the recorded machine):

```powershell
python paper_reproduction/run_figure9_reproduction.py
```

This writes chain-level data, summary data, a provenance/hash JSON, and a new PNG/PDF under `paper_reproduction/results/`. The paper's original numerical data are not bundled or inferred from pixels.

## Evidence versus guidance

`AGENTS.md` is automatically loaded project guidance, not an access-control mechanism. This project therefore pairs it with executable checks:

| Concern | Guidance | Executable evidence |
| --- | --- | --- |
| immutable released data | root `AGENTS.md` | `data/raw_manifest.json` + SHA-256 verification |
| scientific definitions | `analysis/AGENTS.md` | formula/unit tests and schema tests |
| directory-specific behavior | nested instruction files | deterministic resolver + six committed read-only Codex CLI probe JSON files |
| forbidden changes | scope rules | `policy_scenarios.json` |
| publication graphics | `figures/AGENTS.md` | 7 PNG/PDF pairs + manifest |
| published-figure target | `paper_reproduction/AGENTS.md` | 732 new chains + exact Onsager line + metadata hashes + PNG/PDF |

See `START_HERE.md` for the recommended tutorial order and `VERIFICATION_RESULTS.md` for the observed release evidence.
