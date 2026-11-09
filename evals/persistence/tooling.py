"""FNXC:Persistence 2026-11-09-04:02:
Preserve single-user eval checkpoints without touching production behavior.
Require an externally supplied full baseline, exact fork URL, eval/wip branch,
secret review, passing offline tests and an explicit push. Never merge, reset,
rebase, force, prune or tag. Missing Phase 2M is a development warning only.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from scan import scan

FORK = 'https://github.com/gchalono/Fusion.git'
URLS = {FORK, FORK.removesuffix('.git'), 'git@github.com:gchalono/Fusion.git'}


def git(*args, check=True):
    result = subprocess.run(['git', *args], capture_output=True, text=True, timeout=120)
    if check and result.returncode: raise RuntimeError('GIT_OPERATION_FAILED:'+args[0])
    return result.stdout.strip() if check else result


def root():
    return Path(git('rev-parse', '--show-toplevel'))


def verify_fork():
    for mode in ([], ['--push']):
        urls=git('remote','get-url','--all',*mode,'origin').splitlines()
        if not urls or any(url not in URLS for url in urls): raise RuntimeError('FORK_URL_UNVERIFIED')
    if git('config','--get-regexp',r'^url\..*\.(insteadof|pushinsteadof)$',check=False).returncode==0:
        raise RuntimeError('URL_REWRITE_UNVERIFIED')


def baseline_ok(baseline):
    if not re.fullmatch('[0-9a-f]{40}',baseline): raise ValueError('FULL_EXTERNAL_BASELINE_REQUIRED')
    if git('rev-parse','--verify',baseline+'^{commit}') != baseline:
        raise ValueError('BASELINE_MISMATCH')
    if git('merge-base','--is-ancestor',baseline,'HEAD',check=False).returncode:
        raise ValueError('STALE_CHECKOUT_BASELINE_NOT_CONTAINED')


def remote_tip(branch, fetch=True):
    verify_fork()
    if fetch:
        git('fetch','--no-tags','--no-auto-maintenance',FORK,
            f'refs/heads/{branch}:refs/remotes/persistence/{branch}')
    output=git('ls-remote','--heads',FORK,f'refs/heads/{branch}')
    lines=output.splitlines()
    if len(lines)!=1 or lines[0].split()[1]!=f'refs/heads/{branch}':
        raise RuntimeError('REMOTE_BASELINE_UNVERIFIABLE')
    return lines[0].split()[0]


def artifact_check():
    base=root(); missing=[]
    data=json.loads((base/'evals/artifact-manifest.json').read_text())
    for item in data['artifacts']:
        if not item.get('required_for_phase2n_persistence',False): continue
        original=base/item['path']
        path=original.resolve()
        if not path.is_relative_to(base) or original.is_symlink() or not path.is_file():
            missing.append(item['path']); continue
        raw=path.read_bytes()
        if len(raw)!=item['size_bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            missing.append(item['path'])
    return missing


def preflight(baseline, branch):
    repo=root(); head=git('rev-parse','HEAD')
    result={'repository':str(repo),'branch':git('branch','--show-current'), 'head':head,
            'worktrees':git('worktree','list','--porcelain'), 'failures':[],
            'warnings':['PHASE_2M_ARTIFACTS_MISSING: development dependency, not a persistence failure']}
    if result['branch'] != branch: result['failures'].append('CHECKOUT_BRANCH_MISMATCH')
    try:
        tip=remote_tip(branch)
        result['remote_tip']=tip
        if head != tip:
            relation = 'STALE_CHECKOUT' if git('merge-base','--is-ancestor','HEAD',tip,check=False).returncode==0 else 'LOCAL_AHEAD_OR_DIVERGED'
            result['failures'].append(relation)
    except (RuntimeError, subprocess.SubprocessError):
        result['failures'].append('REMOTE_BASELINE_UNVERIFIABLE')
    try: baseline_ok(baseline)
    except (ValueError,RuntimeError): result['failures'].append('BASELINE_NOT_VERIFIED')
    result['working_changes']=git('status','--porcelain=v1','--untracked-files=all')
    if result['working_changes']: result['failures'].append('WORKTREE_NOT_CLEAN')
    try: result['artifact_failures']=artifact_check()
    except (OSError, ValueError, KeyError): result['artifact_failures']=['MANIFEST_UNREADABLE']
    if result['artifact_failures']: result['failures'].append('ARTIFACT_VERIFICATION_FAILED')
    result['project_documents']={}
    for name in ('AGENTS.md','PROJECT_STATE.md','CHECKPOINTS.md'):
        path=repo/'evals'/name
        if not path.is_file(): result['failures'].append('PROJECT_DOCUMENT_MISSING:'+name)
        else: result['project_documents'][name]=path.read_text()
    result['status']='PREFLIGHT_VERIFIED' if not result['failures'] else 'PREFLIGHT_FAILED'
    return result


def validate():
    for suite in ('controlled-coding','planning-collector','persistence'):
        subprocess.run([sys.executable,'-m','unittest','discover','-s',f'evals/{suite}','-v'],check=True)
    subprocess.run([sys.executable,'evals/controlled-coding/harness.py','verify'],check=True)
    if artifact_check(): raise RuntimeError('ARTIFACT_VERIFICATION_FAILED')


def checkpoint(args):
    baseline_ok(args.baseline); verify_fork()
    branch=git('branch','--show-current')
    if branch != args.branch or not re.fullmatch(r'(eval|wip)/[A-Za-z0-9._/-]+',branch):
        raise ValueError('BRANCH_NOT_AUTHORIZED')
    # Scan from fork main rather than assuming all local ancestry is backed up.
    git('fetch','--no-tags','--no-auto-maintenance',FORK,'refs/heads/main:refs/remotes/persistence/main')
    result=scan('refs/remotes/persistence/main')
    print(json.dumps(result,indent=2))
    if result['findings']: raise RuntimeError('SECRET_REVIEW_REQUIRED')
    print('PROPOSED: offline tests; eval-only implementation commit if needed; checkpoint record; optional non-force push and independent verification')
    if not (args.commit or args.push or args.validate):
        print('DRY_RUN: no content, commit or push changes'); return
    validate()
    if args.commit:
        paths=git('diff','--name-only','HEAD').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()
        if any(not p.startswith('evals/') for p in paths): raise ValueError('OUT_OF_SCOPE_CHANGES')
        # Protect unrelated staged content as well.
        if any(not p.startswith('evals/') for p in git('diff','--cached','--name-only').splitlines()):
            raise ValueError('OUT_OF_SCOPE_INDEX')
        if paths:
            git('add','--','evals')
            git('diff','--cached','--check')
            git('commit','-m','evals: validated persistence implementation')
        implementation=git('rev-parse','HEAD')
        now=datetime.now(timezone.utc).isoformat()
        entry=f'\n## Validated checkpoint {now}\n\nImplementation: `{implementation}`; branch `{branch}`.\nTests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.\nEnvironment: Python {sys.version.split()[0]}; Git {git("--version")}.\nManifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.\n'
        with (root()/'evals/CHECKPOINTS.md').open('a') as f: f.write(entry)
        state=root()/'evals/PROJECT_STATE.md'
        text=state.read_text()
        text=re.sub(r'Latest validated implementation: `[^`]+`', f'Latest validated implementation: `{implementation}`',text)
        state.write_text(text)
        git('add','--','evals/CHECKPOINTS.md','evals/PROJECT_STATE.md')
        git('commit','-m','evals: record validated implementation checkpoint')
    if args.push:
        if git('status','--porcelain=v1','--untracked-files=all'):
            raise RuntimeError('REMOTE_BACKUP_INCOMPLETE_LOCAL_CHANGES')
        # Re-scan every newly created commit before any network write.
        if scan('refs/remotes/persistence/main')['findings']: raise RuntimeError('SECRET_REVIEW_REQUIRED')
        try:
            git('push',FORK,f'HEAD:refs/heads/{branch}')
            if remote_tip(branch)!=git('rev-parse','HEAD'): raise RuntimeError('REMOTE_TIP_MISMATCH')
        except (RuntimeError,subprocess.SubprocessError) as error:
            raise RuntimeError('REMOTE_BACKUP_INCOMPLETE') from error
        print('REMOTE_CODE_BACKUP_VERIFIED',git('rev-parse','HEAD'))


def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    for name in ('preflight','checkpoint'):
        q=sub.add_parser(name); q.add_argument('--baseline',required=True); q.add_argument('--branch',required=True)
        if name=='checkpoint':
            q.add_argument('--commit',action='store_true'); q.add_argument('--push',action='store_true'); q.add_argument('--validate',action='store_true')
    args=p.parse_args()
    try:
        if args.command=='preflight':
            result=preflight(args.baseline,args.branch); print(json.dumps(result,indent=2)); return bool(result['failures'])
        checkpoint(args); return 0
    except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as error:
        print(str(error) if isinstance(error,(RuntimeError,ValueError)) else 'OPERATION_FAILED',file=sys.stderr)
        return 1


if __name__=='__main__': sys.exit(main())
