"""Render all six Tutorial 04 article figures from verified local outputs."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PROJECT = Path(os.environ.get("TUTORIAL04_PROJECT", ROOT / "project"))
LAB = Path(os.environ.get("TUTORIAL04_LAB", ROOT / "codex-lab-04"))
ASSETS = Path(os.environ.get("TUTORIAL04_ASSETS", ROOT / "assets"))
OUTPUT = Path(os.environ.get("TUTORIAL04_OUTPUT", ROOT / "article_figures"))
BASE_REF = os.environ.get("TUTORIAL04_BASE_REF", "main")

WIDTH = 1080
OUTER_BG = "#f3f5f7"
TERMINAL_BG = "#0d1117"
TERMINAL_BAR = "#161b22"
TEXT = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#3fb950"
RED = "#ff7b72"
CYAN = "#58a6ff"
ORANGE = "#d29922"

FONT_CN = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 31)
FONT_CN_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 46)
FONT_MONO = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaMono.ttf", 38)
FONT_MONO_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 38)


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env={**__import__("os").environ, "NO_COLOR": "1", "PYTHONIOENCODING": "utf-8"},
    )
    return (completed.stdout + completed.stderr).strip()


def line_color(line: str) -> str:
    lowered = line.lower()
    if line.startswith("PS>"):
        return CYAN
    if line.startswith("+") and not line.startswith("+++"):
        return GREEN
    if line.startswith("-") and not line.startswith("---"):
        return RED
    if line.startswith("@@") or line.startswith("diff --git"):
        return CYAN
    if "passed" in lowered or "verified" in lowered or "scope pass" in lowered:
        return GREEN
    if "failed" in lowered or "error" in lowered or "importerror" in lowered:
        return RED
    if "obtained:" in lowered or "expected:" in lowered:
        return ORANGE
    if line.startswith("...") or line.startswith("["):
        return MUTED
    return TEXT


def wrap_lines(lines: list[str], max_chars: int) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        expanded = line.expandtabs(4)
        if not expanded:
            wrapped.append("")
            continue
        pieces = textwrap.wrap(
            expanded,
            width=max_chars,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=True,
            break_on_hyphens=False,
            subsequent_indent="  ",
        )
        wrapped.extend(pieces or [""])
    return wrapped


def terminal_panel(title: str, lines: list[str], width: int = 1020) -> Image.Image:
    padding = 28
    bar_height = 64
    line_height = 51
    char_width = max(1, int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength("M", font=FONT_MONO)))
    max_chars = max(40, (width - 2 * padding) // char_width)
    lines = wrap_lines(lines, max_chars)
    height = bar_height + 2 * padding + line_height * len(lines)
    panel = Image.new("RGB", (width, height), TERMINAL_BG)
    draw = ImageDraw.Draw(panel)
    draw.rectangle((0, 0, width, bar_height), fill=TERMINAL_BAR)
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        x = 28 + index * 34
        draw.ellipse((x, 21, x + 18, 39), fill=color)
    draw.text((145, 14), title, font=FONT_CN, fill="#c9d1d9")
    y = bar_height + padding
    for line in lines:
        font = FONT_MONO_BOLD if line.startswith("PS>") else FONT_MONO
        draw.text((padding, y), line, font=font, fill=line_color(line))
        y += line_height
    return panel


def stack_figure(title: str, panels: list[Image.Image], destination: Path) -> None:
    top = 105
    gap = 28
    bottom = 40
    height = top + bottom + sum(panel.height for panel in panels) + gap * (len(panels) - 1)
    canvas = Image.new("RGB", (WIDTH, height), OUTER_BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 24), title, font=FONT_CN_BOLD, fill="#18212b")
    y = top
    for panel in panels:
        x = (WIDTH - panel.width) // 2
        canvas.paste(panel, (x, y))
        y += panel.height + gap
    canvas.save(destination, dpi=(220, 220))


def excerpt_diff(diff_text: str) -> list[str]:
    lines = diff_text.splitlines()
    header = lines[:5]
    patterns = [
        '"Ea_eV": float(-1000.0 * KB_EV_PER_K * slope)',
        "+def summarize_replicates",
        "+    fit = arrhenius_fit(t, d, sem)",
    ]
    ranges: list[tuple[int, int]] = []
    for pattern in patterns:
        for index, line in enumerate(lines):
            if pattern in line:
                before, after = (4, 5) if "Ea_eV" in pattern else (3, 8)
                ranges.append((max(0, index - before), min(len(lines), index + after + 1)))
                break
    selected = header[:]
    for start, end in ranges:
        selected.append("... [unchanged diff context omitted] ...")
        selected.extend(lines[start:end])
    return selected


def key_failure_lines(text: str) -> list[str]:
    lines = text.splitlines()
    selected = [lines[0]] if lines else []
    patterns = [
        "test_known_activation_energy",
        "Obtained:",
        "Expected:",
        "test_batch_report_outputs",
        "assert 0.39 <",
        "2 failed, 6 passed",
    ]
    for pattern in patterns:
        match = next((line for line in lines if pattern in line), None)
        if match is not None:
            selected.append(match)
    return selected


def concise_acceptance_lines(text: str) -> list[str]:
    lines = text.splitlines()
    selected = ["FF                              [100%]"]
    for line in lines:
        if "ImportError: cannot import name 'summarize_replicates'" in line:
            selected.extend(
                [
                    "acceptance/test_batch.py",
                    "ImportError: cannot import name",
                    "  'summarize_replicates'",
                ]
            )
            break
    summary = next((line for line in reversed(lines) if " failed in " in line), None)
    if summary is not None:
        selected.append(summary)
    return selected


def render_scientific_figures() -> None:
    with (LAB / "results" / "temperature_summary.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    temperature = np.asarray([float(row["T_K"]) for row in rows])
    mean_d = np.asarray([float(row["mean_D_m2_s"]) for row in rows])
    sem_d = np.asarray([float(row["SEM_m2_s"]) for row in rows])
    x = 1000.0 / temperature
    y = np.log(mean_d)
    xx = np.linspace(float(x.min()), float(x.max()), 250)

    baseline_slope, baseline_intercept = np.polyfit(x, y, 1)
    baseline_ea = -1000.0 * 8.617333262145e-5 * baseline_slope
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    ax.plot(x, y, "o", label="Synthetic mean D")
    ax.plot(
        xx,
        baseline_slope * xx + baseline_intercept,
        label=f"Unweighted Ea={baseline_ea:.4f} eV",
    )
    ax.set(
        xlabel=r"1000/T (K$^{-1}$)",
        ylabel=r"ln[D/(m$^2$ s$^{-1}$)]",
        title="Baseline: before feature implementation",
    )
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig01_baseline_arrhenius.png", dpi=240)
    plt.close(fig)

    summary = json.loads(
        (LAB / "results" / "analysis_summary.json").read_text(encoding="utf-8")
    )
    fig, ax = plt.subplots(figsize=(6.3, 4.4))
    ax.errorbar(
        x,
        y,
        yerr=sem_d / mean_d,
        fmt="o",
        capsize=3,
        label="Temperature means ± SEM",
    )
    ax.plot(
        xx,
        summary["slope"] * xx + summary["intercept"],
        label=f"Weighted fit: Ea={summary['Ea_eV']:.4f} eV",
    )
    ax.set(
        xlabel=r"1000/T (K$^{-1}$)",
        ylabel=r"ln[D/(m$^2$ s$^{-1}$)]",
        title="Weighted Arrhenius fit (mean ± SEM)",
    )
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig04_weighted_arrhenius.png", dpi=240)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    ax.errorbar(
        temperature,
        mean_d,
        yerr=sem_d,
        fmt="o-",
        capsize=3,
        label="Temperature means ± SEM",
    )
    ax.set(
        xlabel="Temperature (K)",
        ylabel=r"D (m$^2$/s)",
        title="Mean diffusion coefficient ± SEM",
    )
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig05_diffusion_vs_temperature.png", dpi=240)
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    render_scientific_figures()

    baseline_output = run([sys.executable, "-m", "pytest", "-q", "tests"], PROJECT)
    acceptance_output = run(
        [sys.executable, "-m", "pytest", "-q", "acceptance", "--tb=line"], PROJECT
    )
    panel_baseline = terminal_panel(
        "A｜已验证的基线",
        ["PS> python -m pytest -q tests", *baseline_output.splitlines()],
    )
    panel_acceptance = terminal_panel(
        "B｜新功能实现前的验收",
        [
            "PS> python -m pytest -q acceptance --tb=line",
            *concise_acceptance_lines(acceptance_output),
        ],
    )
    stack_figure(
        "图 2｜基线通过，新增验收失败",
        [panel_baseline, panel_acceptance],
        OUTPUT / "fig02_pytest_before_feature.png",
    )

    stat = run(
        [
            "git",
            "diff",
            "--stat",
            f"{BASE_REF}..codex/batch-report",
            "--",
            "src/analysis.py",
            "scripts/run_batch.py",
        ],
        LAB,
    )
    panel_scope = terminal_panel(
        "A｜参考实现的修改范围",
        [
            "PS> git diff --stat `",
            f"    {BASE_REF}..codex/batch-report",
            *stat.splitlines(),
        ],
    )
    panel_physics = terminal_panel(
        "B｜保留原有科学约定（上下文）",
        [
            "weight = d / sem",
            '"Ea_eV": float(',
            "    -1000.0 * KB_EV_PER_K * slope",
            ")",
        ],
    )
    panel_batch = terminal_panel(
        "C｜新增批量汇总入口（diff 摘录）",
        [
            "+def summarize_replicates(",
            "+    raw_dir, output_dir",
            "+):",
            "+    ...",
            "+    sem = float(",
            "+      d.std(ddof=1) /",
            "+      np.sqrt(len(d))",
            "+    )",
            "+    fit = arrhenius_fit(t, d, sem)",
        ],
    )
    stack_figure(
        "图 3｜Git 差异与科学公式审查",
        [panel_scope, panel_physics, panel_batch],
        OUTPUT / "fig03_git_diff_review.png",
    )

    rollback_test = (ASSETS / "test_after_rollback.txt").read_text(encoding="utf-8").strip()
    rollback_raw = (ASSETS / "raw_after_rollback.txt").read_text(encoding="utf-8").strip()
    panel_bad_diff = terminal_panel(
        "A｜故意注入 1000 倍单位错误",
        [
            "PS> git diff -- src/analysis.py",
            '- "Ea_eV": float(',
            "-   -1000.0 * KB_EV_PER_K * slope",
            "- )",
            '+ "Ea_eV": float(',
            "+   -1.0 * KB_EV_PER_K * slope",
            "+ )",
        ],
    )
    panel_bad_test = terminal_panel(
        "B｜测试准确拦截错误",
        [
            "PS> python -m pytest -q `",
            "    tests acceptance",
            "F.....F.                     [100%]",
            "test_known_activation_energy",
            "Obtained: 0.00041999999999999866",
            "Expected: 0.42",
            "test_batch_report_outputs",
            "assert 0.39 < Ea_eV < 0.45",
            "2 failed, 6 passed",
        ],
    )
    panel_restore = terminal_panel(
        "C｜只恢复受影响文件并重新验收",
        [
            "PS> git restore --source=HEAD `",
            "    --staged --worktree -- `",
            "    src/analysis.py",
            "PS> python -m pytest -q `",
            "    tests acceptance",
            *rollback_test.splitlines(),
            "PS> python -m scripts.hash_raw `",
            "    verify",
            *rollback_raw.splitlines(),
        ],
    )
    stack_figure(
        "图 6｜错误注入与精确回滚",
        [panel_bad_diff, panel_bad_test, panel_restore],
        OUTPUT / "fig06_rollback_verification.png",
    )

    print(f"Generated 6 article figures in {OUTPUT}")


if __name__ == "__main__":
    main()
