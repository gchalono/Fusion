"""Sanitized source snapshots: copy allowlisted blobs, never original Git history.
User-authorized destination is exactly gchalono/Fusion backup/fusion-checkpoints.
No daemon, hooks, force pushes, merges, original parents or provider requests.
"""
import argparse,hashlib,json,os,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
REPO='https://github.com/gchalono/Fusion.git'
BRANCH='backup/fusion-checkpoints'
ROOT_FILES={'.gitignore','.gitattributes','.dockerignore','AGENTS.md','CLAUDE.md','LICENSE','README.md','CONCEPTS.md','package.json','pnpm-lock.yaml','pnpm-workspace.yaml','tsconfig.json','tsconfig.base.json','tsconfig.placeholder.d.ts','eslint.config.mjs','i18next.config.ts'}
ROOTS={'packages','plugins','scripts'}
EVAL_JSON={'evals/artifact-manifest.json','evals/controlled-coding/experiment-parameters.json','evals/controlled-coding/frozen.json','evals/controlled-coding/TASK_MANAGER_EXPERIMENT_MANIFEST.json','evals/controlled-coding/TOKEN_BOUND_PROPOSED_NOT_ACTIVE.json','evals/controlled-coding/token_measurements.json','evals/controlled-coding/offline-readiness-observations.json','evals/controlled-coding/readiness-evidence.json','evals/controlled-coding/blocker-resolution-observations.json','evals/persistence/reviewed-artifacts.json','evals/planning-collector/briefs.json','evals/planning-collector/config.example.json'}
SYNTHETIC_STREAMS={'plugins/fusion-plugin-cursor-runtime/src/__tests__/fixtures/cursor-mcp-server-failure.stream.jsonl','plugins/fusion-plugin-cursor-runtime/src/__tests__/fixtures/cursor-mcp-tool-call.stream.jsonl','scripts/__tests__/fixtures/pg-loaded-failure-census/high.jsonl'}
BANNED_COMPONENTS={'.git','.fusion','.kb','.claude','.agents','node_modules','dist','coverage','test-results','playwright-report','__pycache__'}
BANNED_SUFFIXES={'.db','.sqlite','.sqlite3','.pem','.key','.log','.jsonl','.pyc'}
KEYS=[rb'(?<![A-Za-z0-9])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'github_pat_[A-Za-z0-9_]{20,}',rb'AKIA[A-Z0-9]{16}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?i)Bearer\s+[A-Za-z0-9._~+/-]{24,}',rb'(?i)(?:api[_-]?key|password|client_secret)\s*[:=]\s*[\"\x27][A-Za-z0-9+/=_-]{24,}[\"\x27]']
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE).decode().strip()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def selected(path,mode):
 p=Path(path)
 if mode not in ('100644','100755'):return False,'nonregular/symlink/submodule'
 if any(c in BANNED_COMPONENTS or c.startswith('.fusion-backup') for c in p.parts):return False,'runtime/private directory'
 if p.name=='.env' or p.name.startswith('.env.') or p.name in ('auth.json','credentials','id_rsa','id_ed25519'):return False,'credential filename'
 if p.suffix in BANNED_SUFFIXES and path not in SYNTHETIC_STREAMS:return False,'database/secret/runtime log'
 if path in ROOT_FILES or path=='.changeset/config.json':return True,'explicit root configuration/source'
 if p.parts[0] in ROOTS:return True,'published-baseline production source/test/asset'
 if p.parts[0]=='evals':
  if path.startswith('evals/controlled-coding/fixtures/') and p.name=='objective.txt':return True,'explicit frozen synthetic benchmark objective'
  if 'evidence' in p.parts or 'dry-run' in p.parts:return False,'runtime evidence/output'
  if p.suffix in ('.py','.mjs','.mts','.md','.sh') or path in EVAL_JSON or p.name=='.gitignore':return True,'evaluation source/test or reviewed metadata'
 return False,'not allowlisted'
def scan_bytes(path,raw):
 findings=[]
 if raw.startswith(b'SQLite format 3\x00'):findings.append('database_content')
 for pattern in KEYS:
  for match in re.finditer(pattern,raw):findings.append('credential_pattern:line='+str(raw[:match.start()].count(b'\n')+1))
 return findings

def build(source,commit,destination):
 source=Path(source).resolve();destination=Path(destination).resolve()
 if destination.exists():raise ValueError('destination_exists_do_not_overwrite')
 if git(source,'cat-file','-t',commit)!='commit':raise ValueError('source_commit_missing')
 destination.mkdir(parents=True);included=[];excluded=[];findings=[]
 entries=subprocess.check_output(['git','ls-tree','-rz','--full-tree',commit],cwd=source).split(b'\0')
 process=subprocess.Popen(['git','cat-file','--batch'],cwd=source,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
 for entry in entries:
  if not entry:continue
  header,name=entry.split(b'\t',1);mode,kind,oid=header.decode().split();path=name.decode()
  allowed,reason=selected(path,mode)
  if not allowed:excluded.append({'path':path,'reason':reason,'source_blob':oid});continue
  if Path(path).is_absolute() or '..' in Path(path).parts or any(ord(c)<32 for c in path):raise ValueError('unsafe_path')
  process.stdin.write((oid+'\n').encode());process.stdin.flush();parts=process.stdout.readline().split();raw=process.stdout.read(int(parts[2]));assert process.stdout.read(1)==b'\n'
  flags=scan_bytes(path,raw)
  findings.extend({'path':path,'code':f,'blob':oid} for f in flags)
  target=destination/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);target.chmod(0o755 if mode=='100755' else 0o644)
  included.append({'path':path,'sha256':digest(raw),'source_blob':oid,'mode':mode,'category':reason})
 process.stdin.close();process.wait();assert process.returncode==0
 backup=destination/'backup';backup.mkdir()
 (backup/'SOURCE_MAP.json').write_text(json.dumps({'source_commit':commit,'source_repository':'gchalono/Fusion','history_included':False,'files':included,'excluded':excluded,'privacy_policy':'No original Git directory/history, operational databases, raw approval records or provider logs.'},indent=2)+'\n')
 (backup/'INITIAL_SCAN.json').write_text(json.dumps({'status':'BLOCKED' if findings else 'PATTERN_SCAN_PASSED','findings':findings,'review_note':'Source roots are byte-identical to verified published baseline eb7eef49d5a0fe3e84e99be30e8ed9622a694e35; evaluation code and metadata receive separate review. Not a guarantee of private-data absence.'},indent=2)+'\n')
 return {'included':len(included),'excluded':len(excluded),'findings':findings}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--commit',required=True);p.add_argument('--destination',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.commit,a.destination)))
