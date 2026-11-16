# 本次验证结果

验证日期：2026-11-16（Asia/Shanghai）

环境：Windows 11、Python 3.13.1、NumPy 2.5.5、SciPy 1.18.1、Matplotlib 3.11.2、psutil 7.2.2、freud 3.6.1。

## 自动化测试

```text
............................                                             [100%]
28 passed in 2.17s
```

- Dense 与周期 cKDTree：17 项；
- 周期 Cell-linked List：8 项；
- freud Figure 3 复现：3 项。

## 核心 Benchmark

命令：`python -m scripts.benchmark --repeats 3`

- N=2,000 Dense：0.211017 s，峰值工作集 333.8 MiB；
- N=2,000 周期 cKDTree：0.003494 s，峰值工作集 59.2 MiB；
- 同机时间中位数比：60.4×；
- N=30,000 周期 cKDTree：0.052758 s，峰值工作集 64.0 MiB；
- N=30,000 Dense：未运行；单个 `(N,N,3)` float64 位移张量解析值约 20.1 GiB。

## Cell List

命令：`python -m scripts.benchmark_cell_list`

三个规模的逐粒子计数均与周期 cKDTree 完全一致。纯 Python Cell List 在 N=10,000 时中位数为 1.421771 s，编译后的 SciPy cKDTree 为 0.016941 s。

## freud（2020）Figure 3 工作负载

命令：`python paper_reproduction/reproduce_figure3.py --number 100 --repeats 5`

- 10 个官方规模：50、80、100、200、400、600、1,000、2,000、3,000、5,000；
- SciPy 与 freud 使用相同点集、周期盒、cutoff 和自配对口径；
- 10 个规模的有向含自身邻居数全部一致；
- N=5,000：SciPy 0.017003 s/次，freud 0.006563 s/次，当前机器约 2.59×；
- `freud_threads=0` 表示库默认/自动线程策略；正式图未强制单线程。

本机 freud 3.6.1 在显式 `--threads 1` 时曾在 Windows 进程退出阶段触发原生库异常，因此最终完整基准采用稳定的默认线程配置。该现象不影响默认线程结果，但单线程变体应在目标环境单独验证。

## 生成物

- 核心结果：6 组 PNG + PDF；
- Figure 3：1 组 PNG + PDF；
- 总计：7 张 PNG + 7 张 PDF；
- 原始证据：CSV、JSON、JSONL、profile `.prof/.txt`、测试日志和环境元数据。

