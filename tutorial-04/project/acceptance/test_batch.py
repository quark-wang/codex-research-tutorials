"""Independent acceptance test. Do not let Codex change this test."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest


def test_batch_report_outputs(tmp_path):
    from src.analysis import arrhenius_fit, summarize_replicates
    root = Path(__file__).resolve().parents[1]
    raw = root / 'raw_data'
    assert raw.is_dir(), 'first run python -m scripts.generate_demo'
    summary = summarize_replicates(raw, tmp_path)
    assert len(summary['rows']) == 6
    assert 0.39 < summary['Ea_eV'] < 0.45
    assert (tmp_path/'temperature_summary.csv').is_file()
    assert (tmp_path/'arrhenius.png').is_file()
    assert (tmp_path/'arrhenius.pdf').is_file()
    assert (tmp_path/'diffusion_vs_temperature.png').is_file()
    assert (tmp_path/'analysis_summary.json').is_file()
    with (tmp_path/'temperature_summary.csv').open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    assert all(int(r['n']) == 10 for r in rows)
    assert all(float(r['SEM_m2_s']) > 0 for r in rows)
    payload = json.loads((tmp_path/'analysis_summary.json').read_text(encoding='utf-8'))
    assert payload['input_type'] == 'synthetic_diffusion_replicates'

    # The batch result must use the propagated SEM weights, not merely expose
    # a weighted arrhenius_fit() that summarize_replicates() never calls.
    t = np.asarray([row['T_K'] for row in summary['rows']], dtype=float)
    d = np.asarray([row['mean_D_m2_s'] for row in summary['rows']], dtype=float)
    sem = np.asarray([row['SEM_m2_s'] for row in summary['rows']], dtype=float)
    expected = arrhenius_fit(t, d, sem)
    unweighted = arrhenius_fit(t, d)
    for key in ('slope', 'intercept', 'Ea_eV', 'D0_m2_s', 'R2_unweighted'):
        assert summary[key] == pytest.approx(expected[key], rel=1e-12, abs=1e-15)
        assert payload[key] == pytest.approx(expected[key], rel=1e-12, abs=1e-15)
    assert summary['slope'] != pytest.approx(unweighted['slope'], rel=1e-8, abs=1e-12)


def test_batch_read_only(tmp_path):
    from src.analysis import summarize_replicates
    root = Path(__file__).resolve().parents[1]
    raw = root/'raw_data'
    assert raw.is_dir()
    def state():
        return {
            str(p.relative_to(raw)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in raw.rglob('*') if p.is_file()
        }
    before = state()
    summarize_replicates(raw, tmp_path)
    assert before == state()

    # Keep the acceptance suite at two tests while covering both unsafe output
    # layouts. Neither rejected call may change the raw-data inventory.
    for relative_output in (Path('.'), Path('generated_outputs')):
        output = raw / relative_output
        with pytest.raises(ValueError, match='outside raw_dir'):
            summarize_replicates(raw, output)
        assert before == state()
        if relative_output != Path('.'):
            assert not output.exists()
