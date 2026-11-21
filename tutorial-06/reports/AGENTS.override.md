# Report-only override

- [REPORT-SOURCE-01] Build numerical claims only from committed files under `results/`.
- [REPORT-LABEL-02] State that inputs are deterministic synthetic Monte Carlo teaching data.
- [REPORT-WRITE-03] Write only below `reports/generated/`; scientific code, data, and results are read-only here.
- [REPORT-NUMBER-04] Copy values from `results/critical_summary.json` with estimator labels.
- [REPORT-VERIFY-05] Run `python scripts/check_report.py` before declaring completion.
