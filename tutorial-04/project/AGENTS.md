# Codex Research Episode 04 — project contract

This is a disposable scientific analysis demo. NEVER work in a production MD/VASP directory.

- The only editable paths for the batch feature are `src/analysis.py` and `scripts/run_batch.py`.
- `raw_data/`, `results/`, `.audit/`, `tests/`, `acceptance/`, and `.gitignore` are NOT editable by Codex.
- Never run `git clean`, `git reset --hard`, `rm -rf`, `git add -A`, or submit computational jobs.
- Keep the numerical convention: x=1000/T, Ea=-1000*kB*slope; D in m2/s.
- For weighted fitting, propagate relative SEM as sigma_lnD ~= SEM_D / mean_D and give np.polyfit residual weight 1/sigma_lnD.
- Before claiming success, run `python -m pytest -q tests acceptance` and `python -m scripts.check_scope`.
- The user must personally inspect `git diff` before committing.
- This file is guidance, not a filesystem security mechanism.
