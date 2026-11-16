# freud（2020）Figure 3 工作负载复现

本目录重新执行 Ramasubramani 等人在 *Computer Physics Communications*
254, 107275 (2020) Figure 3 所使用的邻居搜索工作负载：周期立方盒、半径
`r=1`、均匀随机粒子、平均约12个非自身邻居，并比较 SciPy `cKDTree`
与 freud `AABBQuery`。默认点数严格采用教程中的 10 组：`50, 80, 100,
200, 400, 600, 1000, 2000, 3000, 5000`。

两条曲线使用同一组确定性坐标和同一邻居定义：周期边界、有向邻居关系、
包含自身。SciPy 通过 `query_ball_tree` 物化结果；freud 通过 `AABBQuery`
并显式设置 `exclude_ii=False`。图例同时标注实际运行的库版本。

这些输出是当前机器上的**新测量**，不是从论文图片数字化得到的原始数据；不同
硬件、线程数和软件版本的绝对时间不应直接相等。

## 安装

```bash
python -m pip install numpy scipy matplotlib pytest freud-analysis
```

## 完整复现

默认保留 freud 的线程配置，并记录到 `outputs/run_metadata.json`：

```bash
python paper_reproduction/reproduce_figure3.py --number 100 --repeats 5
```

单线程对照应作为不同的计时口径单独运行：

```bash
python paper_reproduction/reproduce_figure3.py \
  --number 100 --repeats 5 --threads 1 \
  --output-dir paper_reproduction/outputs_single_thread
```

如果 freud 确实无法安装，可以显式允许 SciPy-only 输出：

```bash
python paper_reproduction/reproduce_figure3.py \
  --number 3 --repeats 2 --allow-partial
```

部分运行的图片会明确命名为 `figure3_partial_scipy_only.*`，不会伪造 freud
曲线。完整运行生成：

```text
outputs/
├── new_benchmark.csv
├── run_metadata.json
├── figure3_new_benchmark.png
└── figure3_new_benchmark.pdf
```

## 测试

```bash
python -m pytest -q paper_reproduction/test_figure3.py
```

测试覆盖盒长公式与确定性点集、SciPy 周期/自配对/有向关系定义，以及在 freud
不可用时的透明失败与部分输出路径。

