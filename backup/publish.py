"""Agent-driven sanitized checkpoint publication. Fixed fork/ref; no daemon.
Original source commits are provenance only. They NEVER become backup parents.
"""
import argparse,hashlib,json,os,shutil,subprocess,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
import checkpoint
from verify import verify
HERE=Path(__file__).resolve().parent
FORK=checkpoint.REPO;BRANCH=checkpoint.BRANCH
GENERATED={'checkpoint.py','publish.py','verify.py','offline_tests.py','README.md','REVIEWED_TEST_LITERALS.json','REVIEWED_JSONL_FIXTURES.json','FROZEN_DEPENDENCIES.json','SOURCE_MAP.json','INVENTORY.json','PUBLICATION_SCAN.json','CHECKPOINT_INDEX.json','TEST_RESULTS.json','test_public.py'}
def call(argv,cwd=None):return subprocess.check_output(argv,cwd=cwd,stderr=subprocess.PIPE,text=True).strip()
def git(root,*a):return call(['git',*a],root)
def metadata():
 data=json.loads(call(['gh','api','repos/gchalono/Fusion']))
 actor=json.loads(call(['gh','api','user']))['login']
 if data['full_name']!='gchalono/Fusion' or data['owner']['login']!='gchalono' or actor!='gchalono' or data.get('permissions',{}).get('push') is not True:raise ValueError('REPOSITORY_OR_AUTHORIZATION_UNVERIFIED')
 return {'account':actor,'public_repository_authorized':True,'push_permission':True}
def remote():
 output=call(['git','ls-remote','--heads',FORK,'refs/heads/'+BRANCH])
 if not output:return None
 rows=output.splitlines()
 if len(rows)!=1:raise ValueError('AMBIGUOUS_REMOTE_REF')
 return rows[0].split()[0]
def receipt_path(root):return Path(git(root,'rev-parse','--absolute-git-dir'))/'sanitized-backup-receipt.json'
def inventory(root):
 root=Path(root);source=json.loads((root/'backup/SOURCE_MAP.json').read_text());allowed={x['path'] for x in source['files']}
 allowed|={'backup/'+n for n in GENERATED};allowed|={'backup/public-inputs/'+n for n in ('A.txt','objective.txt','common-instructions.md')}
 files={}
 for p in sorted(root.rglob('*')):
  if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
  name=str(p.relative_to(root))
  if name not in allowed:raise ValueError('UNREVIEWED_GENERATED_FILE:'+name)
  if name=='backup/INVENTORY.json':continue
  files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 (root/'backup/INVENTORY.json').write_text(json.dumps({'files':files,'scope':'public source snapshot; private experiment dependencies excluded'},indent=2)+'\n')
 return files
def commit(root,message):
 files=inventory(root);verify(root)
 for name in [*files,'backup/INVENTORY.json']:
  subprocess.run(['git','add','-f','--',name],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['git','-c','user.name=Fusion sanitized checkpoint','-c','user.email=checkpoint@example.invalid','commit','-m',message],cwd=root,check=True,stdout=subprocess.DEVNULL)
 return git(root,'rev-parse','HEAD')
def push_verify(root,expected_old):
 metadata();verify(root)
 for mode in ([],['--push']):
  urls=git(root,'remote','get-url','--all',*mode,'origin').splitlines()
  if urls!=[FORK]:raise ValueError('WRONG_PUSH_DESTINATION')
 current=remote();head=git(root,'rev-parse','HEAD')
 if current!=expected_old:raise ValueError('REMOTE_CHANGED_REVIEW_REQUIRED')
 if current and subprocess.run(['git','merge-base','--is-ancestor',current,head],cwd=root,capture_output=True).returncode:raise ValueError('BACKUP_HISTORY_DIVERGENCE')
 subprocess.run(['git','push',FORK,head+':refs/heads/'+BRANCH],cwd=root,check=True)
 fetched='refs/remotes/verified-backup/'+str(time.time_ns())
 subprocess.run(['git','fetch','--no-tags',FORK,'refs/heads/'+BRANCH+':'+fetched],cwd=root,check=True,stdout=subprocess.DEVNULL)
 if git(root,'rev-parse',fetched)!=head or remote()!=head:raise ValueError('REMOTE_VERIFICATION_FAILED')
 receipt={'status':'REMOTE_SANITIZED_CODE_SHA_VERIFIED','source_commit':json.loads((Path(root)/'backup/SOURCE_MAP.json').read_text())['source_commit'],'backup_commit':head,'branch':BRANCH,'verified_utc':datetime.now(timezone.utc).isoformat(),'epoch':time.time(),'fresh_clone':'PENDING','private_experiment_recovery':'EXTERNAL_DEPENDENCIES_REQUIRED'}
 receipt_path(root).write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def checkpoint_from(source,destination,event,milestone):
 """Future checkpoints: a new sanitized export with ONLY previous backup parent."""
 source=Path(source).resolve();destination=Path(destination).resolve()
 if git(source,'status','--porcelain','--untracked-files=all'):raise ValueError('SOURCE_DIRTY_REVIEW_AND_COMMIT_FIRST')
 state=receipt_path(HERE.parent)
 if event=='interval' and state.exists() and 0<=time.time()-json.loads(state.read_text()).get('epoch',0)<1200:return {'status':'NOT_DUE'}
 metadata();old=remote()
 if not old:raise ValueError('INITIAL_BACKUP_REQUIRED')
 source_sha=git(source,'rev-parse','HEAD');checkpoint.build(source,source_sha,destination)
 # Transport the trusted public workflow, never source Git metadata or private data.
 for name in GENERATED-{'SOURCE_MAP.json','INVENTORY.json','PUBLICATION_SCAN.json','TEST_RESULTS.json','test_public.py'}:
  if (HERE/name).is_file():shutil.copyfile(HERE/name,destination/'backup'/name)
 shutil.copytree(HERE/'public-inputs',destination/'backup/public-inputs')
 (destination/'backup/INITIAL_SCAN.json').unlink(missing_ok=True)
 subprocess.run(['git','init','--quiet','--initial-branch='+BRANCH,str(destination)],check=True)
 subprocess.run(['git','remote','add','origin',FORK],cwd=destination,check=True)
 subprocess.run(['git','fetch','--no-tags',FORK,'refs/heads/'+BRANCH+':refs/remotes/previous-backup'],cwd=destination,check=True)
 if git(destination,'rev-parse','refs/remotes/previous-backup')!=old:raise ValueError('REMOTE_CHANGED')
 # Adopt only the existing sanitized parent; never source's commit ancestry.
 git(destination,'update-ref','HEAD',old)
 # Explicitly stage all files, including removals from previous snapshot.
 subprocess.run(['git','read-tree','--empty'],cwd=destination,check=True)
 index=json.loads((destination/'backup/CHECKPOINT_INDEX.json').read_text()) if (destination/'backup/CHECKPOINT_INDEX.json').exists() else {'entries':[]}
 index['entries'].append({'source_commit':source_sha,'snapshot_commit':'SELF (resolve commit Source-Commit trailer)','previous_backup':old,'event':event,'milestone':milestone,'remote_status':'PENDING_INDEPENDENT_VERIFICATION'})
 (destination/'backup/CHECKPOINT_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
 # A future checkpoint needs source-independent tests before any publication.
 subprocess.run([os.sys.executable,str(destination/'backup/test_public.py')],cwd=destination,check=True)
 head=commit(destination,'Sanitized checkpoint: '+milestone+'\n\nSource-Commit: '+source_sha)
 return push_verify(destination,old)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--event',choices=['start','milestone','interval','risk','blocker-resolved','stop'],required=True);p.add_argument('--milestone',required=True);a=p.parse_args();print(json.dumps(checkpoint_from(a.source,a.destination,a.event,a.milestone),indent=2))
