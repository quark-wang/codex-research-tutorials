"""Reference source for ``project/scripts/run_batch.py``.

Do not run this file in the ``reference/`` directory: that directory is not a
Python project and has no ``src`` package or ``raw_data``. Apply
``reference_feature.patch`` from the project root, then run
``python -m scripts.run_batch`` there.
"""
from pathlib import Path


def main():
    if Path(__file__).resolve().parent.name == 'reference':
        raise SystemExit(
            'This is reference source only. Apply reference_feature.patch from '
            'project/, then run: python -m scripts.run_batch'
        )
    from src.analysis import summarize_replicates

    root = Path(__file__).resolve().parents[1]
    report = summarize_replicates(root/'raw_data', root/'results')
    print(f"BATCH VERIFIED Ea_eV={report['Ea_eV']:.6f} n_T={len(report['rows'])}")


if __name__ == '__main__':
    main()
