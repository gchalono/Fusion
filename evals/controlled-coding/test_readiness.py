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
