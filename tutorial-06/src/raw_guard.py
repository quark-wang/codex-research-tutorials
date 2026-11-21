"""SHA-256 snapshot verification for released Monte Carlo input tables."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


def hash_tree(root: str | Path) -> dict[str, str]:
    directory = Path(root)
    if not directory.is_dir():
        raise ValueError(f"not a directory: {directory}")
    return {
        path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(p for p in directory.rglob("*") if p.is_file())
    }


def write_manifest(raw_root: str | Path, target: str | Path) -> dict[str, object]:
    payload = {"algorithm": "sha256", "root": "data/raw", "files": hash_tree(raw_root)}
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_manifest(raw_root: str | Path, manifest: str | Path) -> dict[str, object]:
    payload = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if payload.get("algorithm") != "sha256" or not isinstance(payload.get("files"), dict):
        raise ValueError("invalid manifest")
    expected, observed = payload["files"], hash_tree(raw_root)
    missing = sorted(set(expected).difference(observed))
    unexpected = sorted(set(observed).difference(expected))
    changed = sorted(k for k in set(expected).intersection(observed) if expected[k] != observed[k])
    return {
        "passed": not (missing or unexpected or changed),
        "expected": expected,
        "observed": observed,
        "missing": missing,
        "unexpected": unexpected,
        "changed": changed,
    }
