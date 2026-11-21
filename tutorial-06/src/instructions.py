"""Machine-testable model of documented project AGENTS.md discovery."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


RULE_RE = re.compile(r"^- \[([A-Z0-9_-]+)\]\s+(.+)$")


@dataclass(frozen=True)
class InstructionSource:
    relative_path: str
    rule_ids: tuple[str, ...]


def parse_rules(path: str | Path) -> list[tuple[str, str]]:
    rules = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = RULE_RE.match(line.strip())
        if match:
            rules.append((match.group(1), match.group(2)))
    return rules


def discover_project_instructions(
    project_root: str | Path,
    working_directory: str | Path,
    fallback_filenames: Iterable[str] = (),
) -> list[InstructionSource]:
    """Resolve one file per directory from project root down to the cwd.

    This deliberately excludes global CODEX_HOME guidance so results are portable.
    """
    root, cwd = Path(project_root).resolve(), Path(working_directory).resolve()
    try:
        relative = cwd.relative_to(root)
    except ValueError as exc:
        raise ValueError("working_directory must be inside project_root") from exc
    candidates = ("AGENTS.override.md", "AGENTS.md", *tuple(fallback_filenames))
    directories, cursor = [root], root
    for part in relative.parts:
        cursor = cursor / part
        directories.append(cursor)
    sources = []
    for directory in directories:
        for name in candidates:
            path = directory / name
            if path.is_file() and path.read_text(encoding="utf-8").strip():
                sources.append(
                    InstructionSource(
                        path.relative_to(root).as_posix(),
                        tuple(rule_id for rule_id, _ in parse_rules(path)),
                    )
                )
                break
    return sources


def active_rule_ids(sources: Iterable[InstructionSource]) -> list[str]:
    return [rule for source in sources for rule in source.rule_ids]
