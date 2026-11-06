"""Reference implementation: weighted Arrhenius + protected batch reporting."""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path
import numpy as np

KB_EV_PER_K = 8.617333262145e-5


def arrhenius_fit(temperature_K, diffusion_m2s, sem_m2s=None):
    t = np.asarray(temperature_K, dtype=float)
    d = np.asarray(diffusion_m2s, dtype=float)
    if t.ndim != 1 or d.ndim != 1 or len(t) != len(d) or len(t) < 3:
        raise ValueError("T and D must be 1D arrays of equal length >= 3")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(d)):
        raise ValueError("T and D must be finite")
    if np.any(t <= 0) or np.any(d <= 0) or np.unique(t).size < 3:
        raise ValueError("positive D/T and at least three distinct temperatures required")
    x = 1000.0 / t
    y = np.log(d)
    if sem_m2s is not None:
        sem = np.asarray(sem_m2s, dtype=float)
        if sem.shape != d.shape or not np.all(np.isfinite(sem)) or np.any(sem <= 0):
            raise ValueError("SEM must match D and be positive finite")
        weight = d / sem
    else:
        weight = None
    slope, intercept = np.polyfit(x, y, 1, w=weight)
    fitted = slope * x + intercept
    sst = float(np.sum((y - y.mean())**2))
    if sst <= 1e-24:
        raise ValueError("ln(D) variation too small for R2")
    return {
        "Ea_eV": float(-1000.0 * KB_EV_PER_K * slope),
        "D0_m2_s": float(np.exp(intercept)),
        "slope": float(slope),
        "intercept": float(intercept),
        "R2_unweighted": float(1.0 - np.sum((y - fitted)**2) / sst),
    }


def summarize_replicates(raw_dir, output_dir):
    """Read independent synthetic replicates; export table, JSON, PNG and PDF.

    Never writes into raw_dir. Each T directory must contain `replicates.csv`.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    raw = Path(raw_dir).resolve()
    out = Path(output_dir).resolve()
    if not raw.is_dir():
        raise FileNotFoundError(raw)
    if out == raw or raw in out.parents:
        raise ValueError('output_dir must be outside raw_dir')
    folder_re = re.compile(r'^T(\d+)K$')
    rows = []
    for folder in sorted(raw.iterdir()):
        if not folder.is_dir():
            continue
        match = folder_re.fullmatch(folder.name)
        if match is None:
            raise ValueError(f'Unexpected temperature directory {folder.name}')
        temp = int(match.group(1))
        with (folder / 'replicates.csv').open(newline='', encoding='utf-8') as handle:
            data_rows = list(csv.DictReader(handle))
        if len(data_rows) < 3:
            raise ValueError(f'At least 3 replicates required for {temp} K')
        d = np.asarray([float(r['D_m2_s']) for r in data_rows], dtype=float)
        if not np.all(np.isfinite(d)) or np.any(d <= 0):
            raise ValueError(f'Invalid D at T={temp}')
        sem = float(d.std(ddof=1) / np.sqrt(len(d)))
        if not np.isfinite(sem) or sem <= 0:
            raise ValueError(f'Invalid uncertainty at T={temp}')
        rows.append({
            'T_K': temp,
            'n': len(d),
            'mean_D_m2_s': float(d.mean()),
            'SEM_m2_s': sem
        })
    rows.sort(key=lambda row: row['T_K'])
    if len(rows) < 3:
        raise ValueError('Need at least 3 temperatures')
    t = np.asarray([r['T_K'] for r in rows], dtype=float)
    d = np.asarray([r['mean_D_m2_s'] for r in rows], dtype=float)
    sem = np.asarray([r['SEM_m2_s'] for r in rows], dtype=float)
    fit = arrhenius_fit(t, d, sem)
    out.mkdir(parents=True, exist_ok=True)
    with (out/'temperature_summary.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['T_K','n','mean_D_m2_s','SEM_m2_s'])
        writer.writeheader()
        writer.writerows(rows)
    payload = {'input_type':'synthetic_diffusion_replicates', **fit,
               'temperatures_K':[int(v) for v in t], 'n_replicates':[int(v) for v in [r['n'] for r in rows]]}
    (out/'analysis_summary.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    x = 1000.0 / t
    xx = np.linspace(x.min(), x.max(), 250)
    fig, ax = plt.subplots(figsize=(6.3,4.4))
    ax.errorbar(x, np.log(d), yerr=sem/d, fmt='o', capsize=3, label='Temperature means +/- SEM')
    ax.plot(xx, fit['slope']*xx + fit['intercept'], label=f"Weighted fit: Ea={fit['Ea_eV']:.4f} eV")
    ax.set(xlabel=r'1000/T (K$^{-1}$)', ylabel=r'ln[D/(m$^2$ s$^{-1}$)]', title='Weighted Arrhenius fit (mean +/- SEM)')
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out/'arrhenius.png', dpi=240)
    fig.savefig(out/'arrhenius.pdf')
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.3,4.0))
    ax.errorbar(t, d, yerr=sem, fmt='o-', capsize=3)
    ax.set(xlabel='Temperature (K)', ylabel=r'D (m$^2$/s)', title='Mean diffusion coefficient ± SEM')
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
    fig.tight_layout()
    fig.savefig(out/'diffusion_vs_temperature.png', dpi=240)
    plt.close(fig)
    return {'rows': rows, **fit}
