"""FNXC:RealModelReadiness 2026-11-10-04:59: Local-only bounds, settlement,
crash recovery and adversarial real-shaped transport; no provider/key access.
"""
import concurrent.futures,json,tempfile,time,unittest
from pathlib import Path
from budget import AggregateBudget
from contract import Contract,canonical
from readiness_profile import NAME,ceiling
from task_manager_token_revision import offline_contract
from real_transport import RealTransport
from offline_eval import start_stub

class ReadinessTests(unittest.TestCase):
 def test_partial_and_empty_candidate_patch_roundtrip(self):
  import subprocess
  from task_manager_native import new_file_patch
  for body in (b'partial shell content',b'',b'complete\n'):
   with self.subTest(body=body),tempfile.TemporaryDirectory() as t:
    root=Path(t);subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-c','core.hooksPath=/dev/null','apply','-'],cwd=root,input=new_file_patch('partial.sh',body,'100755').encode(),check=True,capture_output=True)
    self.assertEqual((root/'partial.sh').read_bytes(),body);self.assertTrue((root/'partial.sh').stat().st_mode&0o111)
 def test_zero_exit_after_native_error_is_incomplete(self):
  from task_manager_native import native_outcome
  for reason,expected in (('error',False),('length',False),('stop',True)):
   raw=b'OFFLINE_AUDIT_ONLY '+canonical({'events':[{'type':'model_end','stopReason':reason,'errorMessage':'403 LOCAL budget' if reason=='error' else None}]})
   endings,complete,termination=native_outcome(raw,0,4,4)
   self.assertEqual(complete,expected)
   if reason=='error':self.assertEqual(termination,'terminated-by-budget')
 def test_profile_defaults_and_no_paid_promotion(self):
  self.assertEqual(ceiling({}),512)
  d=offline_contract();d['readiness_profile']=NAME
  self.assertEqual(ceiling(d,offline=True),4096)
  for flags in ({},{'offline':True,'paid':True},{'offline':True,'production':True}):
   with self.assertRaises(ValueError):ceiling(d,**flags)
  d['offline_output_profile']='experiment2-offline-test-double-768'
  with self.assertRaises(ValueError):ceiling(d,offline=True)
 def test_worst_case_caps_fifth_and_restart(self):
  with tempfile.TemporaryDirectory() as t:
   d=offline_contract();p=Path(t)/'ledger.db';b=AggregateBudget(p,experiment_contract=d);run=d['coding_run_ids'][0];b.control_run('coding',run,'start')
   for i in range(4):
    n=b.reserve('coding',run,19354,token_bounds=(32000,4096));b.transition(n,'FORWARDED','LOCAL dispatch')
    if i==0:
     b.observe(n,evidence_ref='LOCAL verified complete usage',provider_usage={'prompt_tokens':12,'completion_tokens':2},estimated_charge_micro=8);b.transition(n,'SETTLED','recorded; no refund')
   recovered=AggregateBudget(p,experiment_contract=d);self.assertEqual(recovered.recover_uncertain(),3)
   self.assertEqual(recovered.snapshot()['reserved_exposure_micro_usd'],77416)
   with self.assertRaisesRegex(ValueError,'request_cap'):recovered.reserve('coding',run,19354,token_bounds=(32000,4096))
 def test_shared_aggregate_and_concurrent_reservations(self):
  with tempfile.TemporaryDirectory() as t:
   b=AggregateBudget(Path(t)/'ledger.db');b.reserve('planning','historical',1900000)
   def attempt(i):
    try:return b.reserve('planning',str(i),19354)
    except ValueError:return None
   with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:rows=list(pool.map(attempt,range(12)))
   self.assertEqual(sum(x is not None for x in rows),5)
   self.assertEqual(AggregateBudget(b.path).snapshot()['reserved_exposure_micro_usd'],1996770)
 def test_missing_failure_timeout_crash_retain_reservation(self):
  for reason in ('missing_usage','http_429','http_500','client_timeout','crash_after_dispatch','partial_stream'):
   with self.subTest(reason=reason),tempfile.TemporaryDirectory() as t:
    b=AggregateBudget(Path(t)/'ledger.db');n=b.reserve('coding','A',19354);b.transition(n,'FORWARDED','LOCAL')
    b=AggregateBudget(b.path);self.assertEqual(b.recover_uncertain(),1)
    self.assertEqual(b.snapshot()['remaining_reservable_micro_usd'],1980646)
 def test_unapproved_model_and_endpoint(self):
  c=Contract()
  with self.assertRaises(ValueError):c.prepare(canonical({'model':'unapproved','messages':[{'role':'user','content':'x'}]}))
  with self.assertRaises(ValueError):RealTransport(test_mode=True,test_root='/tmp',test_url='https://api.openai.com/v1/chat/completions')
 def test_real_worker_http_errors_and_timeout(self):
  for case in ('429','500','timeout'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    root=Path(t);(root/'.offline-test').touch()
    def response(body,n):
     if case=='timeout':time.sleep(.4)
     return int(case) if case!='timeout' else 200,'application/json',b'{"error":{"message":"LOCAL double"}}'
    server,contacts=start_stub(root,response=response)
    try:
     tr=RealTransport(test_mode=True,test_root=root,test_url=f'https://localhost:{server.server_port}/v1/chat/completions',test_ca=root/'tls.crt',test_key_file=root/'upstream-key',timeout=.1 if case=='timeout' else 5)
     raw,_=Contract().prepare(canonical({'model':Contract().data['model'],'messages':[{'role':'user','content':'LOCAL'}],'max_tokens':4096}))
     if case=='timeout':
      with self.assertRaisesRegex(OSError,'deadline'):tr('https://api.openai.com/v1/chat/completions',raw)
     else:
      status,_,_=tr('https://api.openai.com/v1/chat/completions',raw);self.assertEqual(status,int(case))
     self.assertEqual(len(contacts),1);self.assertTrue(contacts[0]['gateway_auth_valid'])
     self.assertFalse(tr.active)
    finally:server.shutdown();server.server_close()
 @unittest.skipUnless(Path('/workspace/Fusion/packages').is_dir(),'Outer executor required: sanitized recovery intentionally forbids nested namespace creation; native receipt tested separately')
 def test_namespace_process_tree_cleanup(self):
  import time
  from execution import run_command
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   result=run_command(None,root,['/bin/bash','-c','(sleep 1.5; touch /work/late-child) & echo LOCAL_CHILD_STARTED; sleep 30'],timeout=.6)
   self.assertTrue(result['timed_out']);self.assertIn(b'LOCAL_CHILD_STARTED',result['stdout'])
   time.sleep(1.6);self.assertFalse((root/'late-child').exists())
 @unittest.skipUnless(Path('/workspace/Fusion/packages').is_dir(),'Outer executor required: sanitized recovery intentionally forbids nested namespace creation; native receipt tested separately')
 def test_actual_sandbox_credential_and_proc_boundary(self):
  import os
  from execution import run_command
  with tempfile.TemporaryDirectory() as t:
   code='''import os,json,pathlib,socket
p=pathlib.Path
checks={'provider_env_absent':all(k not in os.environ for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN')),'host_workspace_absent':not p('/workspace').exists(),'hidden_absent':not p('/checks').exists(),'host_home_absent':not p('/root/.config').exists(),'proc_provider_names_absent':True}
for f in p('/proc').glob('[0-9]*/environ'):
 try:
  if b'OPENAI_API_KEY=' in f.read_bytes():checks['proc_provider_names_absent']=False
 except OSError:pass
s=socket.socket();s.settimeout(.1)
try:s.connect(('192.0.2.1',443));checks['direct_egress_denied']=False
except OSError:checks['direct_egress_denied']=True
finally:s.close()
print(json.dumps(checks));assert all(checks.values())
'''
   result=run_command(None,Path(t),['python3','-c',code],timeout=5)
   self.assertEqual(result['exit_code'],0,result['stderr']);self.assertTrue(all(json.loads(result['stdout']).values()))
 def test_synthetic_credential_reflection_is_blocked(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'.offline-test').touch()
   def response(body,n):return 200,'application/json',(root/'upstream-key').read_bytes()
   server,contacts=start_stub(root,response=response)
   try:
    tr=RealTransport(test_mode=True,test_root=root,test_url=f'https://localhost:{server.server_port}/v1/chat/completions',test_ca=root/'tls.crt',test_key_file=root/'upstream-key')
    raw,_=Contract().prepare(canonical({'model':Contract().data['model'],'messages':[{'role':'user','content':'LOCAL'}],'max_tokens':4096}))
    with self.assertRaises(OSError):tr('https://api.openai.com/v1/chat/completions',raw)
   finally:server.shutdown();server.server_close()
 def test_stream_usage_and_interrupted_stream_settlement(self):
  from budget import guard_gateway
  from gateway import Gateway,Policy,Artifacts
  for done in (False,True):
   with self.subTest(done=done),tempfile.TemporaryDirectory() as t:
    root=Path(t);(root/'.offline-test').touch();ledger=AggregateBudget(root/'ledger.db')
    model='offline-model';policy=Policy('offline',model,'https://offline.invalid/v1/chat/completions',('offline.invalid',),4,120000,400000,1600000,100,100,100)
    def transport(*_):
     frames=[{'model':model,'choices':[{'finish_reason':'stop','delta':{'content':'LOCAL'}}]},{'model':model,'choices':[],'usage':{'prompt_tokens':5,'completion_tokens':3}}]
     payload=b''.join(b'data: '+canonical(x)+b'\n\n' for x in frames)+(b'data: [DONE]\n\n' if done else b'')
     return 200,'text/event-stream',payload
    g=guard_gateway(Gateway(policy,Artifacts(root,offline=True),transport),ledger,'coding','A')
    g.handle(canonical({'model':model,'messages':[{'role':'user','content':'LOCAL'}],'max_tokens':100}))
    snap=ledger.snapshot();self.assertEqual(snap['transitions'][-1]['state'],'SETTLED' if done else 'UNCERTAIN')
    self.assertGreater(snap['reserved_exposure_micro_usd'],0)
