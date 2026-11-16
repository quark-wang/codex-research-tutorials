# Project instructions

- Preserve scientific equivalence before optimizing performance.
- Never run the dense displacement tensor above the explicit safety limit.
- Treat `results/*.csv`, `results/*.json`, and paper reproduction outputs as generated evidence; regenerate them through the scripts instead of hand-editing values.
- Use deterministic seeds and record the runtime environment.
- Keep SciPy and freud Figure 3 inputs, cutoff, periodic box, warm-up, repeat count, and timing policy identical.
- Do not claim the synthetic uniform-particle examples are experimental material data.
- Run `python -m pytest -q` after source changes and regenerate every affected figure.

