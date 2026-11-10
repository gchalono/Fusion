"""Native full-contract TEST DOUBLE. No completed source enters the coding mount.
Prepared FILES are transmitted solely through bounded native tool-call replies.
"""
import ast,hashlib,json,os,subprocess
from pathlib import Path
from contract import canonical
from task_manager_native import run
ROOT=Path(__file__).resolve().parent
RANK='a9e8a0c1f332c58f1a9cef2f8d7be59b31bb4b42531a3a0a64d9ad3b3d19033b'
def prepared_files():
 tree=ast.parse((ROOT/'task_manager_contract_proposal.py').read_text())
 return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)))
def plan(tokenizer):
 tokenizer=Path(tokenizer).resolve();package=tokenizer.parent.parent
 metadata=json.loads((package/'package.json').read_text())
 if metadata['name']!='js-tiktoken' or metadata['version']!='1.0.21' or hashlib.sha256((tokenizer.parent/'ranks/o200k_base.js').read_bytes()).hexdigest()!=RANK:raise ValueError('tokenizer_identity')
 files=prepared_files();p=json.loads(subprocess.check_output(['node',str(ROOT/'task_manager_contract_feasibility.mjs'),str(tokenizer),'--emit-768'],input=canonical(files)))
 if not p['fits'] or len(p['deltas'])!=3 or any(n+16>768 for n in p['counts']):raise ValueError('reply_bound')
 return files,p

def execute(root,runtime,tokenizer,*,arm='A'):
 root=Path(root);files,p=plan(tokenizer);steps=[]
 def reply(body):
  i=sum(bool(m.get('tool_calls')) for m in body['messages'] if m['role']=='assistant')
  if i!=len(steps) or i>3:raise ValueError('unexpected_native_sequence')
  steps.append(i)
  if i<3:return p['deltas'][i],'tool_calls'
  return {'role':'assistant','content':'TEST DOUBLE: implementation files constructed, local tests and HTTP smoke executed; independent acceptance required.'},'stop'
 result=run(root,runtime,arm=arm,expanded_offline=True,offline_768=True,script_override=reply,expected_requests=4,capture_all=True)
 (root/'fixture-plan.json').write_bytes(canonical(p))
 if not result['native_loop_completed'] or steps!=[0,1,2,3]:raise ValueError('native_incomplete')
 if set(result['candidate_files'])!=set(files):raise ValueError('generated_file_inventory')
 for name,body in files.items():
  if result['candidate_files'][name]!=hashlib.sha256((body+'\n').encode()).hexdigest():raise ValueError('generated_source_mismatch:'+name)
 for name in ('run-app','run-tests'):
  if result['candidate_modes'][name]!='100755':raise ValueError('launcher_mode')
 audit=(root/'agent-stdout.txt').read_text();event=json.loads(audit.split('OFFLINE_AUDIT_ONLY ',1)[1].splitlines()[0])
 if any(e.get('isError') for e in event['events']):raise ValueError('native_tool_error')
 if [e for e in event['events'] if e['type']=='model_end'][-1].get('stopReason')=='error':raise ValueError('native_model_error')
 fresh=root/'patch-checkout';fresh.mkdir()
 env={'PATH':os.environ['PATH'],'HOME':str(root),'GIT_CONFIG_NOSYSTEM':'1'}
 for args in (['init','-q'],['apply','--check',str(root/'candidate.patch')],['apply',str(root/'candidate.patch')]):subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=fresh,env=env,check=True,capture_output=True)
 for name,expected in result['candidate_files'].items():
  if hashlib.sha256((fresh/name).read_bytes()).hexdigest()!=expected:raise ValueError('patch_source_mismatch')
  if bool((fresh/name).stat().st_mode&0o111)!=(result['candidate_modes'][name]=='100755'):raise ValueError('patch_mode_mismatch')
 result.update(classification='TEST DOUBLE native full-contract candidate; acceptance not implied',patch_apply_verified=True,output_encoding_counts=p['counts'])
 (root/'full-native-result.json').write_bytes(canonical(result));return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--tokenizer',type=Path,required=True);p.add_argument('--arm',choices=list('ABC'),default='A');a=p.parse_args();r=execute(a.root,a.runtime,a.tokenizer,arm=a.arm);print(json.dumps({k:r[k] for k in ('native_loop_completed','local_model_wire_requests','candidate_files','candidate_modes','output_encoding_counts')}))
