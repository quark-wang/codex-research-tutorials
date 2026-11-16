# Codex 科研实战（05）配套项目

本项目对应教程《3 万原子配位分析性能优化——从 cKDTree 到 freud（2020）Figure 3 方法学复现》。它包含可执行源码、自动化测试、独立进程基准、原始 CSV/JSON、PNG/PDF，以及 freud 与 SciPy 使用相同输入的 Figure 3 复现实验。

## 快速开始（Windows PowerShell）

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.profile_methods
.\.venv\Scripts\python.exe -m scripts.benchmark --repeats 3
.\.venv\Scripts\python.exe -m scripts.make_figures
.\.venv\Scripts\python.exe -m scripts.benchmark_cell_list
.\.venv\Scripts\python.exe .\paper_reproduction\reproduce_figure3.py --number 100 --repeats 5
```

## 目录

```text
Codex_Research_Tutorial_05/
├── ARTICLE_05.md                 # 与真实运行结果同步的公众号正文
├── src/                          # Dense、周期 cKDTree、Cell List
├── tests/                        # 28 项物理与接口测试
├── scripts/                      # profiling、benchmark、绘图脚本
├── results/                      # 原始 CSV/JSON、日志、PNG/PDF
├── paper_reproduction/           # freud (2020) Figure 3 复现
├── article_figures/              # 正文用图副本
├── START_HERE.md                 # 最短运行说明
└── VERIFICATION_RESULTS.md       # 本次实际验证记录
```

## 结果解释边界

- Dense 的 30,000 粒子内存值是按数组形状推导的理论值，不会在普通工作站上强行运行。
- 基准使用确定随机种子生成均匀粒子体系；它用于比较算法，不代表特定材料轨迹。
- 绝对耗时依赖 CPU、操作系统、Python、NumPy、SciPy 和 freud 版本；应比较同机同输入下的趋势。
- Figure 3 是依据论文作者公开工作负载重新计算的新数据，不是从论文图片中抄录或数字化得到的数据。

