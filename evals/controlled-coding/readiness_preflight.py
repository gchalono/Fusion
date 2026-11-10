"""FNXC:RealModelReadiness 2026-11-10-05:09:
Read-only local integrity preflight. This cannot authorize or dispatch inference.
A paid run remains blocked until its separate live controls are verified.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PIN='9afbac61342d18a59b0d1cdd1111d6ef736f82c5'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check():
 def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
 if git('status','--porcelain','--untracked-files=all'):raise ValueError('worktree_dirty')
 subprocess.run(['git','merge-base','--is-ancestor',PIN,'HEAD'],cwd=ROOT,check=True,capture_output=True)
 m=json.loads((ROOT/'evals/controlled-coding/TASK_MANAGER_EXPERIMENT_MANIFEST.json').read_text())
 if len(m['inputs'])!=35:raise ValueError('frozen_inventory_count')
 for p,h in m['inputs'].items():
  if digest(p)!=h:raise ValueError('frozen_input_mismatch:'+p)
 from task_manager_adapter import verify_sources,load_arm
 from original_evaluator_adapter import verify_original
 from verified_browser_runtime import verify
 from task_manager_token_revision import offline_contract
 frozen,bindings=verify_sources('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen')
 evaluator=verify_original();verify()
 seed=subprocess.check_output(['git','-C','/workspace/phase2n-evaluation/frozen/empty-seed','rev-parse','HEAD'],text=True).strip()
 if seed!='f2a49cb3fc7e02cd225053d4e2d07c589b4c808b':raise ValueError('seed_mismatch')
 d=offline_contract()
 if (d['coding_attempts_per_run'],d['max_input_tokens'],d['max_output_tokens'],d['coding_seconds'],d['request_seconds'],d['per_run_coding_cap_usd'],d['aggregate_cap_usd'])!=(4,32000,4096,300,60,'0.12','2.00'):raise ValueError('budget_limits_mismatch')
 freeze=ROOT/'evals/controlled-coding/PHASE3_FROZEN.md'
 if freeze.is_file():
  spec=json.loads(re.search(r'```json\n(.*?)\n```',freeze.read_text(),re.S)[1])
  for p,h in spec['source_sha256'].items():
   if digest(ROOT/p)!=h:raise ValueError('readiness_source_changed:'+p)
 return {'offline_integrity':'VERIFIED','source_commit':git('rev-parse','HEAD'),'original_pin':PIN,'frozen_inputs':35,'approval_bindings':len(bindings),'arm_A_sha256':hashlib.sha256(load_arm('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen','A')).hexdigest(),'seed':seed,'evaluator_sha256':evaluator,'provider_calls':0,'paid_readiness':'BLOCKED','blockers':['current_model_access_and_pricing_unverified','live_supervisor_and_authoritative_historical_ledger_binding_unverified','gateway_only_live_credential_handoff_unverified','private_external_recovery_unavailable']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=check()
 with a.out.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 print(json.dumps({'offline_integrity':r['offline_integrity'],'paid_readiness':r['paid_readiness'],'provider_calls':0}))
