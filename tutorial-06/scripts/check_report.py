"""Minimal release guard for generated narrative reports."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("synthetic", "Monte Carlo", "reduced units", "independent chains")


def main() -> int:
    reports = list((ROOT / "reports/generated").glob("*.md"))
    if not reports:
        print("no generated Markdown report found")
        return 1
    failed = False
    for path in reports:
        text = path.read_text(encoding="utf-8")
        missing = [term for term in REQUIRED if term.lower() not in text.lower()]
        print(f"{path.name}: {'PASS' if not missing else 'FAIL missing=' + ','.join(missing)}")
        failed |= bool(missing)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
