"""Mechanical path audit that complements—but cannot be replaced by—AGENTS.md."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Iterable


PROTECTED = ("data/raw/", ".git/", ".codex/")
ALLOWED = {
    "simulation": ("simulation/", "run_experiment.py", "src/", "tests/", "results/reproduction/"),
    "analysis": ("analysis/", "src/", "tests/", "results/"),
    "figures": ("figures/", "make_figures.py", "results/figures/"),
    "paper_reproduction": ("paper_reproduction/",),
    "reports": ("reports/generated/",),
}


@dataclass(frozen=True)
class Finding:
    path: str
    code: str
    message: str


def audit_paths(scope: str, changed_paths: Iterable[str]) -> dict[str, object]:
    if scope not in {"root", *ALLOWED}:
        raise ValueError("unknown scope")
    normalized = tuple(_normalize(path) for path in changed_paths)
    findings: list[Finding] = []
    for path in normalized:
        if any(path == p.rstrip("/") or path.startswith(p) for p in PROTECTED):
            findings.append(Finding(path, "PROTECTED_INPUT", "released raw data/control metadata are immutable"))
            continue
        if scope != "root" and not any(path == p or path.startswith(p) for p in ALLOWED[scope]):
            findings.append(Finding(path, f"{scope.upper()}_SCOPE", f"{scope} scope may not modify this path"))
    return {
        "scope": scope,
        "changed_paths": list(normalized),
        "passed": not findings,
        "findings": [asdict(item) for item in findings],
    }


def _normalize(path: str) -> str:
    raw = str(path).replace("\\", "/").strip()
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts or raw in {"", "."}:
        raise ValueError(f"unsafe relative path: {path!r}")
    return candidate.as_posix().lstrip("./")
