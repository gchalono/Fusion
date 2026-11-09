"""FNXC:ControlledCoding 2026-11-09-03:50:
Run independent frozen tests only after coding ends. This local verifier is for
trusted offline validation; it is not an isolation boundary for model code.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from harness import ROOT, sha, verify


def evaluate(task, candidate):
    verify()
    fixture = ROOT/'fixtures'/task
    if not fixture.is_dir() or task not in [p.name for p in (ROOT/'fixtures').iterdir()]:
        raise ValueError('unknown_task')
    candidate = Path(candidate)
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError('invalid_candidate')
    with tempfile.TemporaryDirectory(prefix='fusion-2n-acceptance-') as tmp:
        shutil.copyfile(candidate, Path(tmp)/'solution.py')
        shutil.copyfile(fixture/'acceptance/test_acceptance.py', Path(tmp)/'test_acceptance.py')
        env = {'PATH': os.defpath, 'PYTHONHASHSEED': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
        try:
            proc = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_acceptance'],
                                  cwd=tmp, env=env, capture_output=True, text=True, timeout=10)
            return {'status': 'passed' if proc.returncode == 0 else 'failed',
                    'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr,
                    'candidate_sha256': sha(candidate.read_bytes())}
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'exit_code': None}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('task'); p.add_argument('candidate', type=Path)
    a = p.parse_args()
    r = evaluate(a.task, a.candidate)
    print(json.dumps(r, indent=2))
    sys.exit(0 if r['status'] == 'passed' else 1)
