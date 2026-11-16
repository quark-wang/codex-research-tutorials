# 从这里开始

如果只想确认附件可复现，请在项目根目录依次运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.benchmark --repeats 3
.\.venv\Scripts\python.exe -m scripts.make_figures
.\.venv\Scripts\python.exe -m scripts.benchmark_cell_list
.\.venv\Scripts\python.exe .\paper_reproduction\reproduce_figure3.py --number 100 --repeats 5
```

随后检查：

- `results/benchmark.csv`：Dense 与周期 cKDTree 的中位数及最小/最大值汇总；
- `results/benchmark_trials.jsonl`：每次独立子进程的原始测量；
- `results/benchmark_cell_list.csv`：Cell List 与 cKDTree 对照；
- `results/environment.json`：运行环境；
- `results/*.png` 与 `results/*.pdf`：教程主线图；
- `paper_reproduction/outputs/new_benchmark.csv`：Figure 3 原始计时；
- `paper_reproduction/outputs/run_metadata.json`：复现参数与版本；
- `paper_reproduction/outputs/figure3_new_benchmark.*`：SciPy 与 freud 完整复现图。

如需从干净环境安装依赖：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

