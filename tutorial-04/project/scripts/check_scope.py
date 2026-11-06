"""Check changed Git paths (staged, unstaged, added, removed, renamed).
Must be run in a Git repository after an initial baseline commit.
Post-hoc detector; not an access-control system.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'src/analysis.py', 'scripts/run_batch.py'}


def git(*args):
    cp = subprocess.run(['git', *args], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)
    return [line for line in cp.stdout.splitlines() if line]


def main():
    tracked = set(git('diff', '--no-renames', '--name-only', 'HEAD', '--'))
    untracked = set(git('ls-files', '--others', '--exclude-standard'))
    modified = tracked | untracked
    excluded = sorted(modified - ALLOWED)
    tracked_raw = git('ls-files', '--', 'raw_data', 'results', '.audit')
    if tracked_raw:
        raise SystemExit(f'FAIL: generated/raw paths were tracked: {tracked_raw}')
    if excluded:
        raise SystemExit(f'FAIL: changes outside approved scope: {excluded}')
    print('SCOPE PASS:', ', '.join(sorted(modified)) or '(clean tree)')
    print('RAW UNTRACKED: no raw_data, results or audit files in git index')

if __name__ == '__main__':
    main()
