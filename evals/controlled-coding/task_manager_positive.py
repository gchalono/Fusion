"""Bounded TEST DOUBLE drives unchanged Fusion/Pi tools; not model effectiveness.
No source fixture is mounted or copied into the coding workspace. Its bytes are
sent as native tool arguments via three local model responses plus one final reply.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from task_manager_native import run
from contract import canonical
ROOT=Path(__file__).resolve().parent

def validate_planned_paths(plan,allow_partial=False):
 names=set(plan.get('planned_paths',[]))
 missing={'run-app','run-tests'}-names
 if not any('test' in Path(n).name and Path(n).suffix in ('.py','.js','.mjs') for n in names):missing.add('assertion-bearing-test-source')
 if missing and not allow_partial:raise ValueError('frozen_contract_missing:'+','.join(sorted(missing)))
 return not missing

def execute(root,runtime,tokenizer,*,arm='A',timeout=90,allow_partial=False):
 root=Path(root)
 planned=subprocess.check_output([__import__('shutil').which('node'),str(ROOT/'task_manager_positive_plan.mjs'),str(Path(tokenizer).resolve())])
 p=json.loads(planned)
 validate_planned_paths(p,allow_partial)
 if p['output_ceiling']!=512 or p['serialization_headroom']!=16 or any(n+16>512 for n in p['counts']):raise ValueError('fixture_output_bound')
 if p['source_sha256']!=hashlib.sha256((ROOT/'task_manager_positive_source.py').read_bytes()).hexdigest():raise ValueError('fixture_source_changed')
 if p['rank_sha256']!='a9e8a0c1f332c58f1a9cef2f8d7be59b31bb4b42531a3a0a64d9ad3b3d19033b':raise ValueError('encoding_ranks_changed')
 steps=[]
 def reply(body):
  index=sum(bool(m.get('tool_calls')) for m in body['messages'] if m['role']=='assistant')
  if index!=len(steps) or index>3:raise ValueError('unexpected_native_sequence')
  steps.append(index)
  if index<3:return p['deltas'][index],'tool_calls'
  return {'role':'assistant','content':'TEST DOUBLE: files written, storage self-test and local HTTP smoke run. Independent acceptance remains required.'},'stop'
 result=run(root,runtime,timeout=timeout,arm=arm,expanded_offline=True,script_override=reply,expected_requests=4,capture_all=True)
 (root/'fixture-plan.json').write_bytes(canonical(p))
 if not result['native_loop_completed'] or steps!=[0,1,2,3]:raise ValueError('native_positive_incomplete')
 if result['candidate_files'].get('application.py')!=p['source_sha256']:raise ValueError('native_source_mismatch')
 # Materialize ONLY the captured patch in a fresh independent Git checkout.
 fresh=root/'patch-checkout';fresh.mkdir()
 env={'PATH':os.environ['PATH'],'HOME':str(root),'GIT_CONFIG_NOSYSTEM':'1'}
 for args in (['init','-q'],['apply','--check',str(root/'candidate.patch')],['apply',str(root/'candidate.patch')]):
  subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=fresh,env=env,check=True,capture_output=True)
 for name,expected in result['candidate_files'].items():
  if hashlib.sha256((fresh/name).read_bytes()).hexdigest()!=expected:raise ValueError('patch_recovery_mismatch')
 from task_manager_grader import grade
 acceptance=grade(fresh/'application.py',root/'independent-acceptance')
 observation={'classification':'TEST DOUBLE native implementation; no treatment effectiveness claim','arm':arm,'native':result,'fixture_counts_o200k':p['counts'],'native_output_ceiling_unchanged':512,'patch_apply_verified':True,'acceptance':acceptance,'real_provider_requests':0,'actual_provider_cost_usd':'0.00'}
 (root/'positive-result.json').write_bytes(canonical(observation));return observation
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--tokenizer',type=Path,required=True);p.add_argument('--partial-diagnostic',action='store_true');p.add_argument('--arm',choices=list('ABC'),default='A');a=p.parse_args();r=execute(a.root,a.runtime,a.tokenizer,arm=a.arm,allow_partial=a.partial_diagnostic);print(json.dumps({'arm':a.arm,'native_completed':r['native']['native_loop_completed'],'requests':r['native']['local_model_wire_requests'],'acceptance':r['acceptance'],'cost':r['actual_provider_cost_usd']},indent=2))
