# Tutorial 04 corrected package verification

The corrected package was reproduced from a clean copy in a fresh Python 3.13
virtual environment using the versions allowed by `requirements.txt`:

- NumPy 2.5.4
- Matplotlib 3.11.2
- pytest 9.2.0

Verified workflow:

1. Baseline regression suite: `6 passed`.
2. Before feature implementation: `2 failed, 6 passed` because
   `summarize_replicates` does not yet exist.
3. `git apply --check reference/reference_feature.patch`: passed.
4. Corrected reference feature: `8 passed`.
5. Batch result: `Ea_eV=0.419902`, six temperatures.
6. Raw-data manifest: `7 files identical`.
7. Scope audit: only `src/analysis.py` and `scripts/run_batch.py` changed.
8. After the audited feature checkpoint, the intentional `-1000 -> -1`
   defect produced `2 failed, 6 passed`.
9. Restoring `src/analysis.py` from the checkpoint returned the suite to
   `8 passed` and preserved the 7-file manifest.
10. Merging the feature branch into `main` and rerunning the corrected order
    `generate -> snapshot -> pytest -> verify` again produced `8 passed` and
    `7 files identical`.

The batch implementation generated these five contracted outputs:

- `temperature_summary.csv`
- `analysis_summary.json`
- `arrhenius.png`
- `arrhenius.pdf`
- `diffusion_vs_temperature.png`

The six article figures were regenerated after the source corrections. The
Git review figure now reports the corrected feature diff as 90 insertions and
5 deletions.
