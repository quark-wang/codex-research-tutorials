# Codex 科研实战 04 — Git 科研代码保护实验

This project contains ONLY synthetic diffusion data generated locally.

## Quick start

```bash
python -m pip install -r requirements.txt
python -m scripts.generate_demo
python -m scripts.hash_raw snapshot
python -m pytest -q tests
python -m scripts.plot_baseline
```

Then initialize Git and commit the baseline:

```bash
git init -b main
git add .gitignore AGENTS.md requirements.txt README.md src tests acceptance scripts
git commit -m "baseline: reproducible diffusion fitting"
git check-ignore -v raw_data/T700K/replicates.csv
git ls-files raw_data
git worktree add -b codex/batch-report ../codex-lab-04
```

The linked worktree has no raw_data, because raw_data is ignored. From its directory run `python -m scripts.generate_demo` and `python -m scripts.hash_raw snapshot` to create new synthetic data, then run Codex on that worktree. The `acceptance/` tests initially fail because `summarize_replicates` is not yet implemented.

## Reference implementation

Outside the project folder there is a `reference/` directory in the ZIP. It contains the instructor's tested after-version source. Use it to reproduce verified output if Codex is not available; DO NOT confuse these instructor results with a real Codex run.
