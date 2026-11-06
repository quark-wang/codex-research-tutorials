# Codex 科研实战（04）文件包

- `ARTICLE_04.md`：完整公众号文章，含图位、Git 命令、测试和回滚记录。
- `project/`：Git 基线示例（不包含 Git 历史，可自己 `git init`），只含教学用的合成数据及源码。
- `reference/`：独立参考修改与 `reference_feature.patch`；不要把参考修改冒充 Codex 自主开发。
- `assets/`：真实 Python 运行生成的科研图、验证日志、Git 差异和回滚记录。
- `article_figures/`：正文按顺序引用的 6 张修正版配图。
- `render_article_figures.py`：从实际测试、Git 差异和科学结果重新生成正文配图。
- `VERIFICATION_RESULTS.md`：修正版在全新虚拟环境中的完整复验记录。

## 操作顺序

```bash
cd project
python -m pip install -r requirements.txt
python -m scripts.generate_demo
python -m scripts.hash_raw snapshot
python -m pytest -q tests
python -m scripts.plot_baseline
git init -b main
git add .gitignore AGENTS.md README.md requirements.txt src tests acceptance scripts
git commit -m "baseline: verified diffusion fitting"
git worktree add -b codex/batch-report ../codex-lab-04
cd ../codex-lab-04
python -m scripts.generate_demo
python -m scripts.hash_raw snapshot
python -m pytest -q tests acceptance
```

这时新验收测试预期失败（`summarize_replicates` 尚未实现），然后由 Codex 在 `codex-lab-04/` 完成，或按文章操作应用独立参考补丁。

若使用参考补丁，请在工作树根目录（即包含 `src/`、`scripts/` 的目录）运行：

```bash
git apply ../reference/reference_feature.patch
python -m pytest -q tests acceptance
python -m scripts.run_batch
```

`reference/run_batch_after.py` 只是 `scripts/run_batch.py` 的参考源码，不应直接在 `reference/` 目录执行。参考实现会拒绝将 `output_dir` 设为 `raw_data/` 本身或其任何子目录，并生成 CSV、JSON、Arrhenius PNG/PDF 以及 `diffusion_vs_temperature.png`。

## 本地核验得到（不是 Codex 自动修复纪录）

- 初始回归：6 passed
- 初始新功能验收：2 failed
- 审核后的参考实现：8 passed
- 修复后 Ea：0.419902 eV（真值 0.420 eV）
- raw_data SHA-256：7/7 完全一致
- 注入错误公式：2 failed, 6 passed
- 单文件 git restore 后：8 passed

注意 `.gitignore` 不保护已被 Git 跟踪的文件，也不是磁盘备份。`git worktree` 是开发便利功能，不是针对不可信程序的安全边界。
