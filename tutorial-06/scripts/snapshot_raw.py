from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.raw_guard import verify_manifest, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "verify"))
    args = parser.parse_args()
    raw, manifest = ROOT / "data/raw", ROOT / "data/raw_manifest.json"
    if args.action == "snapshot":
        payload = write_manifest(raw, manifest)
        print(f"snapshotted {len(payload['files'])} raw files")
        return 0
    result = verify_manifest(raw, manifest)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
