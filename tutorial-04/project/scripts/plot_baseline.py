import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.analysis import arrhenius_fit

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'raw_data'
OUT = ROOT/'results'


def main():
    temperatures = []
    diffusion = []
    for folder in sorted(RAW.glob('T*K')):
        temp = int(folder.name[1:-1])
        with (folder/'replicates.csv').open(encoding='utf-8') as f:
            ds = [float(r['D_m2_s']) for r in csv.DictReader(f)]
        temperatures.append(temp)
        diffusion.append(np.mean(ds))
    fit = arrhenius_fit(temperatures, diffusion)
    x = 1000/np.array(temperatures, dtype=float)
    y = np.log(diffusion)
    xs = np.linspace(x.min(), x.max(), 200)
    fig, ax = plt.subplots(figsize=(6.2,4.3))
    ax.scatter(x, y, s=38, label='Synthetic mean D', zorder=3)
    ax.plot(xs, fit['slope']*xs + fit['intercept'], label=f"Unweighted Ea={fit['Ea_eV']:.4f} eV")
    ax.set(xlabel=r'1000/T (K$^{-1}$)', ylabel=r'ln[D/(m$^2$ s$^{-1}$)]', title='Baseline: before feature implementation')
    ax.legend(frameon=False)
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT/'fig01_baseline_arrhenius.png', dpi=240)
    fig.savefig(OUT/'fig01_baseline_arrhenius.pdf')
    plt.close(fig)
    print(f"Baseline Ea={fit['Ea_eV']:.6f} eV")

if __name__=='__main__':
    main()
