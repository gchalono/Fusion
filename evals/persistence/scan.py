"""FNXC:Persistence 2026-11-09-04:02: Scan every introduced blob version and local
changes before backup. Findings contain paths/lines only. Hash-reviewed offline
fixtures/logs require explicit review; this pattern scan is not proof of secrecy.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args])


PATTERNS = [rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}',
            rb'gh[pousr]_[A-Za-z0-9]{20,}', rb'github_pat_[A-Za-z0-9_]{20,}',
            rb'AKIA[A-Z0-9]{16}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'(?i)Bearer\s+[A-Za-z0-9._~+/-]{24,}',
            rb'(?i)(?:api[_-]?key|password|client_secret)\s*[:=]\s*[\"\x27][A-Za-z0-9+/=_-]{24,}[\"\x27]']


def inspect(path, data, reviewed):
    findings = []
    name = Path(path).name.lower()
    if (name == '.env' or name.startswith('.env.') or name in ('auth.json', 'credentials', 'id_rsa', 'id_ed25519')
            or name.endswith(('.pem', '.key', '.sqlite', '.db'))):
        findings.append({'path': path, 'line': 1, 'code': 'sensitive_filename'})
    for pattern in PATTERNS:
        for match in re.finditer(pattern, data):
            findings.append({'path': path, 'line': data[:match.start()].count(b'\n')+1, 'code': 'credential_pattern'})
    # Raw transcripts/provider records require a separate storage decision.
    if re.search(r'(?i)(?:transcript|request-\d|response-\d|native-result|gateway-artifacts)', path):
        findings.append({'path': path, 'line': 1, 'code': 'sensitive_artifact_path'})
    needs_review = name.endswith('.log') or '/evidence/' in path or name in ('briefs.json', 'config.example.json')
    if needs_review and hashlib.sha256(data).hexdigest() not in reviewed.get(path, []):
        findings.append({'path': path, 'line': 1, 'code': 'artifact_review_required'})
    return findings


def scan(base, tip='HEAD', include_worktree=True):
    root = Path(git('rev-parse', '--show-toplevel').decode().strip())
    policy = root/'evals/persistence/reviewed-artifacts.json'
    reviewed = json.loads(policy.read_text()) if policy.exists() else {}
    findings, seen = [], set()
    for line in git('rev-list', '--objects', f'{base}..{tip}').decode().splitlines():
        parts = line.split(' ', 1)
        if len(parts) < 2: continue
        oid, path = parts
        if git('cat-file', '-t', oid).strip() != b'blob': continue
        findings.extend(inspect(path, git('cat-file', 'blob', oid), reviewed))
        seen.add(oid)
    if include_worktree:
        names = set()
        for args in [('diff', '--name-only', '-z', 'HEAD'), ('ls-files', '--others', '--exclude-standard', '-z')]:
            names.update(x.decode() for x in git(*args).split(b'\0') if x)
        # Scan index versions too; unstaged edits must not hide staged credentials.
        for path in git('diff', '--cached', '--name-only', '-z').split(b'\0'):
            if not path: continue
            name=path.decode()
            staged=subprocess.run(['git','show',':'+name],capture_output=True)
            if staged.returncode==0: findings.extend(inspect(name,staged.stdout,reviewed))
        for name in sorted(names):
            p=root/name
            if p.is_symlink(): findings.append({'path':name,'line':1,'code':'unreviewed_symlink'})
            elif p.is_file(): findings.extend(inspect(name,p.read_bytes(),reviewed))
    return {'status':'SCAN_PASSED' if not findings else 'SCAN_BLOCKED',
            'introduced_blob_versions':len(seen), 'findings':findings,
            'method':'built-in credential patterns plus hash-reviewed artifact allowlist; manual review also required'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--base',required=True)
    parser.add_argument('--tip',default='HEAD'); args=parser.parse_args()
    result=scan(args.base,args.tip); print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['findings']))
