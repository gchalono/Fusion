"""FNXC:RealModelReadiness 2026-11-10-04:59:
Deterministic native Pi LOCAL-only Arm A rehearsal and adversarial wire matrix.
Never imports a real credential or exposes a live transport flag. Raw artifacts
are private; prepared responses do not demonstrate real-model coding ability.
"""
import argparse,hashlib,json,time
from pathlib import Path
from contract import canonical
from task_manager_native import run
from task_manager_full_native import plan
from original_evaluator_adapter import evaluate
ROOT=Path(__file__).resolve().parent

def tool(name,args,i=0):
 return {'index':i,'id':'LOCAL_'+str(i),'type':'function','function':{'name':name,'arguments':args if isinstance(args,str) else json.dumps(args)}}

def execute(out,runtime,tokenizer,case):
 out=Path(out);steps=[]
 files,p=plan(tokenizer)
 def reply(body):
  i=sum(bool(m.get('tool_calls')) for m in body['messages'] if m['role']=='assistant');steps.append(i)
  if case in ('full','budget-mid-run'):
   if i<3:return p['deltas'][i],'tool_calls'
   if case=='full':return {'role':'assistant','content':'LOCAL scripted completion; not real-model ability'},'stop'
   calls=[tool('read',{'path':'README.md'})]
  elif case=='nonterminating':calls=[tool('read',{'path':'README.md'})]
  elif i:return {'role':'assistant','content':'LOCAL double stopped'},'stop'
  elif case=='parallel':calls=[tool('write',{'path':'one.py','content':'# local\n'},0),tool('write',{'path':'two.py','content':'# local\n'},1)]
  elif case=='malformed':calls=[tool('write','{not-json')]
  elif case=='partial':calls=[tool('write','{"path":"one.py","content":')]
  elif case=='length':return {'role':'assistant','content':'LOCAL truncated'},'length'
  elif case=='oversized-tool':calls=[tool('bash',{'command':"python3 -c 'print(\"x\"*100000)'"})]
  else:raise ValueError('unknown_case')
  return {'role':'assistant','tool_calls':calls},'tool_calls'
 response=None
 if case in ('429','500'):
  response=lambda body,n:(int(case),'application/json',b'{"error":{"message":"LOCAL wire failure","type":"rate_limit_error"}}')
 r=run(out,runtime,expanded_offline=True,readiness=True,script_override=reply,response_override=response,expected_requests=4 if case in ('full','budget-mid-run','nonterminating') else 2,capture_all=True,timeout=45)
 assert r['local_model_wire_requests']<=4
 assert len(r['ledger']['reservations'])==r['local_model_wire_requests']
 assert r['ledger']['reserved_exposure_micro_usd']<=120000
 assert r['active_offline_output_bound']==4096
 wires=[json.loads(Path(p).read_text()) for p in r['wire_files']]
 assert all(w['max_tokens']==4096 for w in wires)
 summary={k:r[k] for k in ('exit_code','local_model_wire_requests','timed_out','patch_sha256','native_loop_completed')}
 summary.update(case=case,real_provider_requests=0,exposure_micro_usd=r['ledger']['reserved_exposure_micro_usd'])
 if case in ('full','budget-mid-run'):
  for name,body in files.items():assert r['candidate_files'][name]==hashlib.sha256((body+'\n').encode()).hexdigest()
  assert r['patch_sha256']=='df383ba28a82be9f2a07b36d188a4f4bec11f551f1013634186c3752c2b0ba6c'
  # Same candidate/evaluator/browser/isolation: do NOT rerun the browser. Run
  # other original assertions and retain their raw browser-unavailable outcome.
  (out/'full-native-result.json').write_bytes(canonical(r))
  grading=evaluate(out,out/'independent-evaluator')
  assert grading['non_browser_passed']
  summary.update(non_browser_passed=True,browser='NOT_RERUN: unchanged verified patch/evaluator/runtime/isolation; BROWSER_ACCEPTANCE_FINAL.md',termination='terminated-by-budget' if case=='budget-mid-run' else 'completed')
 if case in ('budget-mid-run','nonterminating'):
  audit=(out/'agent-stdout.txt').read_text();assert '403' in audit or 'error' in audit
  assert r['local_model_wire_requests']==4
 if case=='parallel':assert set(r['candidate_files'])=={'one.py','two.py'}
 (out/'readiness-receipt.json').write_bytes(canonical(summary))
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--tokenizer',type=Path,required=True);p.add_argument('--case',choices=['full','budget-mid-run','parallel','malformed','partial','length','oversized-tool','nonterminating','429','500','all'],default='all');a=p.parse_args()
 cases=['full','budget-mid-run','parallel','malformed','partial','length','oversized-tool','nonterminating','429','500'] if a.case=='all' else [a.case]
 a.out.mkdir(parents=True,exist_ok=False);a.out.chmod(0o700)
 receipts=[]
 for case in cases:
  receipts.append(execute(a.out/case,a.runtime,a.tokenizer,case));print(json.dumps(receipts[-1]),flush=True)
 (a.out/'matrix.json').write_bytes(canonical(receipts))
