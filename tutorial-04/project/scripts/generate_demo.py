"""Generate synthetic diffusion replicates only (never real MD results)."""
import csv
import json
from pathlib import Path
import numpy as np
from src.analysis import KB_EV_PER_K

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
TEMPERATURES = [700, 800, 900, 1000, 1100, 1200]
EA_TRUE = 0.420
D0_TRUE = 2.0e-6
N_REPS = 10


def main():
    RAW.mkdir(exist_ok=True)
    rng = np.random.default_rng(20261102)
    for temperature in TEMPERATURES:
        sub = RAW / f"T{temperature}K"
        sub.mkdir(parents=True, exist_ok=True)
        true_d = D0_TRUE * np.exp(-EA_TRUE / (KB_EV_PER_K * temperature))
        # Lognormal independent noise, synthetic and reproducible
        replicates = true_d * np.exp(rng.normal(0, 0.025, N_REPS))
        path = sub / "replicates.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["replicate", "D_m2_s"])
            for idx, val in enumerate(replicates, 1):
                writer.writerow([idx, f"{val:.14e}"])
    (RAW / "metadata.json").write_text(json.dumps({
        "source": "Synthetic Arrhenius diffusion teaching data; not VASP or MD",
        "seed": 20261102,
        "temperature_K": TEMPERATURES,
        "replicates_per_temperature": N_REPS,
        "Ea_true_eV": EA_TRUE,
        "D0_true_m2_s": D0_TRUE
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(TEMPERATURES)*N_REPS} replicates in {RAW}")

if __name__ == "__main__":
    main()
