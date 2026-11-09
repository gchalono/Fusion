"""FNXC:TaskManagerOfflineValidation 2026-11-09-20:38:
Local-only operator-authorized offline Gate 0; never a live preflight."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
EXPECTED='67749361f8aba2aac5559290975f946d3f34a5c9'
BRANCH='eval/phase2n-task-manager-offline'
REQUIRED=[EXPECTED,'73dd29ab2237fb9e7c47458b9deb0b11d681f033','40a06aa5cb932ddc0ed9bf232aca00999b355d96','29d027ae80795e3803ff64ddb592bc8aad0762ee']

def verify(root,bundle):
 root=Path(root).resolve();bundle=Path(bundle).resolve();checks={}
 def git(*args,cwd=root):return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.PIPE,text=True).strip()
 def require(name,ok):
  checks[name]=bool(ok)
  if not ok:raise RuntimeError('LOCAL_GATE0_FAILED:'+name)
 refs=git('for-each-ref','--format=%(refname) %(objectname)','refs/heads')
 require('exact_commit_exists',git('cat-file','-t',EXPECTED)=='commit')
 require('head_matches_operator_checkpoint',git('rev-parse','HEAD')==EXPECTED)
 require('authorized_branch',git('branch','--show-current')==BRANCH)
 require('clean_before_changes',not git('status','--porcelain','--untracked-files=all'))
 require('recovery_bundle_present',bundle.is_file())
 require('bundle_verify',subprocess.run(['git','bundle','verify',str(bundle)],cwd=root,capture_output=True).returncode==0)
 with tempfile.TemporaryDirectory(prefix='fusion-local-recovery-') as temp:
  env={'PATH':os.environ['PATH'],'HOME':temp,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
  clone=Path(temp)/'recovered'
  subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--quiet','--no-checkout','--branch',BRANCH,str(bundle),str(clone)],check=True,env=env,capture_output=True)
  require('isolated_recovery_head',git('rev-parse','HEAD',cwd=clone)==EXPECTED)
  for commit in REQUIRED:require('bundle_recovers_'+commit,git('cat-file','-t',commit,cwd=clone)=='commit')
  require('complete_git_dependencies',subprocess.run(['git','fsck','--connectivity-only'],cwd=clone,capture_output=True,env=env).returncode==0)
  manifest_path='evals/controlled-coding/TASK_MANAGER_EXPERIMENT_MANIFEST.json'
  original=git('show',EXPECTED+':'+manifest_path,cwd=clone)
  require('recovered_manifest_matches',json.loads(original)==json.loads((root/manifest_path).read_text()))
 manifest=json.loads((root/manifest_path).read_text())
 require('exact_35_inputs',len(manifest['inputs'])==35)
 for name,digest in manifest['inputs'].items():require('input_'+str(len([k for k in checks if k.startswith('input_')])),hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest)
 sys.path.insert(0,str(root/'evals/controlled-coding'))
 from task_manager_adapter import verify_sources
 _,approvals=verify_sources('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen')
 require('original_provenance_and_8_approvals',len(approvals)==8)
 sys.path.insert(0,str(root/'evals/persistence'))
 from tooling import artifact_check
 require('all_frozen_artifacts',not artifact_check())
 require('local_branch_and_recovery_refs_intact',git('for-each-ref','--format=%(refname) %(objectname)','refs/heads')==refs)
 require('still_clean',not git('status','--porcelain','--untracked-files=all'))
 return {'status':'LOCAL_ONLY_GATE0_VERIFIED','scope':'operator-authorized offline work originating at '+EXPECTED,'remote_publication':'UNVERIFIED','valid_for_paid_preflight':False,'provider_spending_authorized_usd':'0.00','bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'checks':checks,'refs':refs.splitlines()}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 try:result=verify(a.root,a.bundle)
 except Exception as error:result={'status':'LOCAL_GATE0_FAILED','error':str(error)}
 with a.out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({'status':result['status'],'checks':len(result.get('checks',{}))}));raise SystemExit(result['status']!='LOCAL_ONLY_GATE0_VERIFIED')
