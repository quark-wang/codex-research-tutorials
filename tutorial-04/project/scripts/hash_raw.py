"""Create / verify content hashes of raw_data, including file additions and deletions."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw_data'
AUDIT = ROOT / '.audit' / 'raw_manifest.json'


def inventory():
    if not RAW.exists():
        raise SystemExit('raw_data/ missing: run python -m scripts.generate_demo first')
    return {
        str(p.relative_to(RAW)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in RAW.rglob('*') if p.is_file()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['snapshot', 'verify'])
    mode = parser.parse_args().mode
    if mode == 'snapshot':
        AUDIT.parent.mkdir(exist_ok=True)
        AUDIT.write_text(json.dumps(inventory(), indent=2), encoding='utf-8')
        print(f'RAW SNAPSHOT: {len(inventory())} files')
    else:
        if not AUDIT.exists():
            raise SystemExit('Missing snapshot; run snapshot first')
        before = json.loads(AUDIT.read_text(encoding='utf-8'))
        after = inventory()
        if before != after:
            modified = sorted(set(before) ^ set(after) | {p for p in before.keys() & after.keys() if before[p] != after[p]})
            raise SystemExit('RAW HASH CHANGED: ' + ', '.join(modified))
        print(f'RAW VERIFIED: {len(after)} files identical')

if __name__ == '__main__':
    main()
