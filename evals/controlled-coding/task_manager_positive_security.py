"""Existing runner/broker integrated negatives, local TEST DOUBLE only.
These are separate diagnostic sessions, not extra steps in a treatment run.
"""
import json,subprocess,threading,time
from pathlib import Path
from task_manager_native import run
from task_manager_adapter import TASK
from pilot import spawn_broker,request_admin
from budget import AggregateBudget
ROOT=Path(__file__).resolve().parent

def exercise(root,runtime,tokenizer,*,offline_768=False):
 root=Path(root);root.mkdir(exist_ok=False)
 p=json.loads(subprocess.check_output(['node',str(ROOT/'task_manager_positive_plan.mjs'),str(tokenizer)]))
 def replies(body):
  n=sum(bool(m.get('tool_calls')) for m in body['messages'] if m['role']=='assistant')
  if n<3:return p['deltas'][n],'tool_calls'
  return {'role':'assistant','tool_calls':[{'index':0,'id':'TEST_DOUBLE_FIFTH_DENIAL','type':'function','function':{'name':'bash','arguments':'{"command":"echo TEST_DOUBLE_EXTRA_TOOL"}'}}]},'tool_calls'
 security=run(root/'security',runtime,arm='A',expanded_offline=True,offline_768=offline_768,variant='security',capture_all=True)
 unauthorized=run(root/'unauthorized',runtime,arm='A',expanded_offline=True,offline_768=offline_768,variant='unauthorized',capture_all=True)
 exhaustion=run(root/'exhaustion',runtime,arm='A',expanded_offline=True,offline_768=offline_768,script_override=replies,expected_requests=4,capture_all=True,timeout=20)
 hit=threading.Event();release=threading.Event();killed=[]
 def hook(process):
  def kill_after_contact():
   if hit.wait(15):process.kill();process.wait(timeout=5);killed.append(True);release.set()
  threading.Thread(target=kill_after_contact,daemon=True).start()
 crash=run(root/'crash',runtime,arm='A',expanded_offline=True,offline_768=offline_768,script_override=replies,expected_requests=4,capture_all=True,pause=(hit,release),broker_hook=hook,timeout=25)
 state=AggregateBudget(root/'crash/experiment.db').snapshot();before=state['reserved_exposure_micro_usd']
 token=(root/'crash/local-token').read_bytes();process,log=spawn_broker(root/'crash',TASK+':A',resume=True)
 try:
  rotated=(root/'crash/local-token').read_bytes()!=token
  after=AggregateBudget(root/'crash/experiment.db').snapshot()['reserved_exposure_micro_usd'];request_admin(root/'crash','abort')
 finally:process.wait(timeout=10);log.close()
 exhausted=(root/'exhaustion/agent-stdout.txt').read_text()
 safe=(root/'security/agent-stdout.txt').read_text();denied=(root/'unauthorized/agent-stdout.txt').read_text()
 record={'classification':'TEST DOUBLE integrated native diagnostics; not treatment effectiveness','credential_hidden_file_cross_arm_and_direct_egress_probe': 'TEST_DOUBLE_SECURITY_PASS' in safe and 'Network is unreachable' in safe,'gateway_positive_requests':security['local_model_wire_requests'],'unauthorized_tool_denied':'Tool unauthorized_test_tool not found' in denied and '"isError":true' in denied,'exhaustion_native_error_after_four': '"stopReason":"error"' in exhausted and '403' in exhausted,'exhaustion_local_upstream_requests':exhaustion['local_model_wire_requests'],'exhaustion_reserved_requests':len(exhaustion['ledger']['reservations']),'exhaustion_native_timed_out':exhaustion['timed_out'],'crash_native_aborted':crash['aborted'],'crash_after_upstream_contact':bool(killed),'crash_uncertain_exposure_micro_usd':before,'broker_resume_rotated_token':rotated,'broker_resume_preserved_exposure':before==after,'Pi_conversation_recovery':False,'real_provider_requests':0,'actual_provider_cost_usd':'0.00'}
 (root/'security-result.json').write_text(json.dumps(record,indent=2)+'\n');return record
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--offline-768',action='store_true');p.add_argument('--root',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--tokenizer',type=Path,required=True);a=p.parse_args();print(json.dumps(exercise(a.root,a.runtime,a.tokenizer,offline_768=a.offline_768),indent=2))
