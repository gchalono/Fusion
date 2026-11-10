"""FNXC:HistoricalLedger 2026-11-10-05:38: Table-driven offline continuation
checks. Forked/process competitors and actual SIGKILL; no provider access.
"""
import json,os,shutil,sqlite3,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from history_budget import HistoryBudget,original_anchor
from history_budget_test_support import fixture,open_,start,reserve,spec,sign,Reader,KEY
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'planning-collector'))
class HistoryTests(unittest.TestCase):
 def test_import_settlement_replaces_reservation_and_restart(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);before=r();b,run=start(p,w,r);self.assertEqual(b.snapshot()['exposure_micro_usd'],11522)
   n=reserve(b,run);self.assertEqual(b.snapshot()['exposure_micro_usd'],30876)
   b.transition(n,'FORWARDED','LOCAL');b.observe(n,evidence_ref='LOCAL complete response',provider_usage={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15},estimated_charge_micro=12);b.transition(n,'SETTLED','complete response')
   self.assertEqual(b.snapshot()['exposure_micro_usd'],11534);self.assertEqual(len(b.snapshot()['settlements']),1)
   b.control_run('coding',run,'COMPLETE');b.close();b=open_(p,w,r)
   self.assertEqual(b.snapshot()['exposure_micro_usd'],11534);self.assertEqual(r(),before)
   with self.assertRaises(ValueError):b.control_run('coding',run,'resume')
   b.close()
 def test_uncertain_cases_full_charge(self):
  for case in ('missing_usage','interrupted_stream','failed_request','timeout','ambiguous_usage'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t);b,run=start(p,w,r);n=reserve(b,run);b.transition(n,'FORWARDED','LOCAL')
    if case=='ambiguous_usage':
     b.observe(n,evidence_ref='LOCAL invalid',provider_usage={'prompt_tokens':True,'completion_tokens':0});b.transition(n,'SETTLED','invalid usage')
    else:b.transition(n,'UNCERTAIN',case)
    self.assertEqual(b.snapshot()['exposure_micro_usd'],30876);b.close()
 def test_caps_clock_and_signed_scope(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);b=open_(p,w,r)
   for key,value in [('source_commit','f'*40),('config_sha256','f'*64),('anchor_sha256','f'*64),('expires_at',0),('domain','FUSION_PHASE3C_LIVE')]:
    s=spec(b);s[key]=value
    with self.assertRaises(ValueError):b.authorize_run(s,sign(s))
   s=spec(b);b.authorize_run(s,sign(s));run=s['run_id']
   for _ in range(4):reserve(b,run)
   with self.assertRaisesRegex(ValueError,'request_cap'):reserve(b,run)
   self.assertEqual(b.snapshot()['exposure_micro_usd'],11522+77416)
   with self.assertRaises(ValueError):b.authorize_run(s,sign(s))
   b.close();b=open_(p,w,r);self.assertEqual(b.snapshot()['requests'],4)
   self.assertEqual(b.snapshot()['runs'][0][4],'INCOMPLETE');b.close()
 def test_aggregate_unresolved_exhaustion(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t,unresolved=1980000);b,run=start(p,w,r)
   with self.assertRaisesRegex(ValueError,'aggregate_spend_cap'):reserve(b,run)
   self.assertEqual(b.snapshot()['requests'],0);b.close()
 def test_anchor_is_immutable_and_admission_rederives_journal(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);b,run=start(p,w,r)
   with b.connect() as db:
    for sql in ('UPDATE history_anchor SET body=body','DELETE FROM history_anchor'):
     with self.assertRaisesRegex(sqlite3.DatabaseError,'immutable_history_anchor'):db.execute(sql)
   (r.path/'00.json').write_text('changed')
   with self.assertRaisesRegex(ValueError,'anchor_mismatch'):reserve(b,run)
   b._unlock()
 def test_empty_deleted_corrupt_rollback_and_witness(self):
  for case in ('empty','deleted','corrupt','witness_mismatch','witness_ahead','witness_missing','chain_tamper','anchor_tamper'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t)
    if case=='empty':p.write_bytes(b'')
    elif case=='deleted':p.unlink()
    elif case=='corrupt':p.write_bytes(b'CORRUPT')
    elif case=='witness_missing':w.unlink()
    elif case.startswith('witness'):
     d=json.loads(w.read_text());d['head']='f'*64
     if case=='witness_ahead':d['seq']+=1
     w.write_text(json.dumps(d))
    else:
     with sqlite3.connect(p) as db:
      table='continuation_events' if case=='chain_tamper' else 'history_anchor';db.execute('DROP TRIGGER '+table+'_no_update');db.execute('UPDATE '+table+' SET body=\'{}\'')
    with self.assertRaises((ValueError,sqlite3.DatabaseError,KeyError,TypeError)):open_(p,w,r,recover=True)
    with self.assertRaises(ValueError):HistoryBudget.initialize(p,w,reader=r,test_key=KEY)
 def test_separate_process_owners(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t)
   code='''import sys,time
from pathlib import Path
from history_budget_test_support import *
p,w,j=map(Path,sys.argv[1:]);r=Reader(j)
try:
 b,run=start(p,w,r);reserve(b,run);print('OWNED',flush=True);time.sleep(1);b.close()
except (BlockingIOError,ValueError):sys.exit(3)
'''
   args=[sys.executable,'-B','-c',code,str(p),str(w),str(r.path)]
   one=subprocess.Popen(args,cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);self.assertEqual(one.stdout.readline().strip(),'OWNED')
   others=[subprocess.Popen(args,cwd=HERE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for _ in range(5)]
   self.assertEqual([x.wait(timeout=5) for x in others],[3]*5);self.assertEqual(one.wait(timeout=5),0);one.stdout.close();one.stderr.close()
   b=open_(p,w,r);self.assertEqual(b.snapshot()['requests'],1);self.assertLess(b.snapshot()['exposure_micro_usd'],2000000);b.close()
 def test_actual_sigkill_recovery_points(self):
  for point in ('after_reserve_commit','before_dispatch','after_forward_commit','after_settle_commit'):
   with self.subTest(point=point),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t)
    code='''import sys
from pathlib import Path
from history_budget_test_support import *
p,w,j=map(Path,sys.argv[1:4]);point=sys.argv[4]
b,run=start(p,w,Reader(j),crash_at=point);n=reserve(b,run);b.transition(n,'FORWARDED','LOCAL dispatch');b.transition(n,'UNCERTAIN','LOCAL interrupted')
'''
    worker=subprocess.run([sys.executable,'-B','-c',code,str(p),str(w),str(r.path),point],cwd=HERE,capture_output=True,text=True,timeout=10)
    self.assertEqual(worker.returncode,-9,worker.stderr);self.assertIn('INJECTION:'+point,worker.stdout)
    b=open_(p,w,r,recover=True);snap=b.snapshot();self.assertEqual(snap['requests'],1);self.assertEqual(snap['exposure_micro_usd'],30876);self.assertEqual(snap['runs'][0][4],'INCOMPLETE')
    with self.assertRaises(ValueError):reserve(b,snap['runs'][0][1])
    b.close()
 @unittest.skipUnless(Path('/tmp/fusion-genuine-pilot-ch9ihrxf/gateway').is_dir(),'Private original journal intentionally absent in public recovery')
 def test_real_47_replay(self):
  a=original_anchor();self.assertEqual(a['record_count'],47);self.assertEqual(a['historical_retained_micro_usd'],11522);self.assertEqual(a['historical_unresolved_micro_usd'],0)
 def test_clock_and_request_count_survive_restart(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);b=open_(p,w,r);s=spec(b);s['expires_at']=time.time()+.15;b.authorize_run(s,sign(s));n=reserve(b,s['run_id']);before=b.snapshot()['runs'][0][2:4];time.sleep(.18)
   with self.assertRaisesRegex(ValueError,'stale'):reserve(b,s['run_id'])
   b._unlock();b=open_(p,w,r,recover=True);self.assertEqual(b.snapshot()['runs'][0][2:4],before);self.assertEqual(b.snapshot()['requests'],1);b.close()
 def test_settlement_crash_keeps_durable_verified_charge(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t)
   code='''import sys
from pathlib import Path
from history_budget_test_support import *
p,w,j=map(Path,sys.argv[1:]);b,run=start(p,w,Reader(j),crash_at='after_settle_commit');n=reserve(b,run);b.transition(n,'FORWARDED','LOCAL');b.observe(n,evidence_ref='LOCAL complete',provider_usage={'prompt_tokens':10,'completion_tokens':5});b.transition(n,'SETTLED','LOCAL complete')
'''
   q=subprocess.run([sys.executable,'-B','-c',code,str(p),str(w),str(r.path)],cwd=HERE,capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,-9,q.stderr)
   b=open_(p,w,r,recover=True);self.assertEqual(b.snapshot()['exposure_micro_usd'],11534);self.assertEqual(b.snapshot()['requests'],1);b.close()
 def test_rollback_behind_witness_refused(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);old=Path(t)/'old.db'
   src=sqlite3.connect(p);dst=sqlite3.connect(old);src.backup(dst);src.close();dst.close()
   b,run=start(p,w,r);reserve(b,run);b.close()
   src=sqlite3.connect(old);dst=sqlite3.connect(p);src.backup(dst);src.close();dst.close()
   with self.assertRaisesRegex(ValueError,'witness_ahead'):open_(p,w,r,recover=True)
 def test_existing_gateway_interface_and_missing_usage(self):
  from history_budget import bind_anchored_gateway
  from gateway import Gateway,Policy,Artifacts,canonical
  for complete in (True,False):
   with self.subTest(complete=complete),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t);b,run=start(p,w,r);root=Path(t)/'evidence';root.mkdir();(root/'.offline-test').touch()
    policy=Policy('OpenAI',b.contract['model'],'https://offline.invalid/v1/chat/completions',('offline.invalid',),4,120000,400000,1600000,32000,4096,4096)
    calls=[]
    def response(*args):
     calls.append(args);body={'model':policy.model,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'LOCAL'}}]}
     if complete:body['usage']={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}
     return 200,'application/json',canonical(body)
    g=Gateway(policy,Artifacts(root,offline=True),response)
    with self.assertRaisesRegex(ValueError,'test_domain'):bind_anchored_gateway(g,b,run)
    g=bind_anchored_gateway(g,b,run,synthetic=True);g.handle(canonical({'model':policy.model,'messages':[{'role':'user','content':'LOCAL'}],'max_completion_tokens':4096}))
    self.assertEqual(len(calls),1);self.assertEqual(b.snapshot()['exposure_micro_usd'],11534 if complete else 30876);b.close()
 def test_admission_bounds_and_test_domain_reject_live(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t)
   with self.assertRaises(ValueError):HistoryBudget(p,w,reader=r)
   b,run=start(p,w,r)
   for amount,bounds in [(19353,(32000,4096)),(19354,(32000,768)),(19354,(32001,4096))]:
    with self.assertRaisesRegex(ValueError,'fixed_uncached'):b.reserve('coding',run,amount,token_bounds=bounds)
   self.assertEqual(b.snapshot()['requests'],0);b.close()
 def test_live_domain_never_accepts_dev_test_key(self):
  # Explicit TEST anchor can never be opened in LIVE mode, irrespective of key.
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t)
   with self.assertRaisesRegex(ValueError,'domain'):HistoryBudget(p,w)
 def test_snapshot_schema_or_owner_tamper_fails_closed(self):
  for case in ('owner','schema'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t);b,run=start(p,w,r)
    if case=='owner':
     owner=Path(str(p)+'.owner');owner.rename(Path(str(p)+'.old-owner'));owner.touch()
    else:
     with sqlite3.connect(p) as db:db.execute('DROP TRIGGER history_anchor_no_delete')
    with self.assertRaisesRegex(ValueError,'owner_lock|state_changed'):reserve(b,run)
    b._unlock()
 def test_kill9_after_actual_synthetic_gateway_dispatch(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);contact=Path(t)/'synthetic-upstream-contact'
   code='''import os,signal,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd().parent/'planning-collector'))
from history_budget_test_support import *
from history_budget import bind_anchored_gateway
from gateway import Policy,Artifacts,Gateway,canonical
p,w,j,contact=map(Path,sys.argv[1:]);b,run=start(p,w,Reader(j));e=p.parent/'wire';e.mkdir();(e/'.offline-test').touch()
policy=Policy('OpenAI',b.contract['model'],'https://offline.invalid/v1/chat/completions',('offline.invalid',),4,120000,400000,1600000,32000,4096,4096)
def upstream(url,raw):
 contact.write_text('SYNTHETIC upstream dispatched; no provider');os.kill(os.getpid(),signal.SIGKILL)
g=bind_anchored_gateway(Gateway(policy,Artifacts(e,offline=True),upstream),b,run,synthetic=True)
g.handle(canonical({'model':policy.model,'messages':[{'role':'user','content':'LOCAL'}],'max_completion_tokens':4096}))
'''
   worker=subprocess.run([sys.executable,'-B','-c',code,str(p),str(w),str(r.path),str(contact)],cwd=HERE,capture_output=True,text=True,timeout=10)
   self.assertEqual(worker.returncode,-9,worker.stderr);self.assertTrue(contact.is_file());b=open_(p,w,r,recover=True)
   self.assertEqual(b.snapshot()['exposure_micro_usd'],30876);self.assertEqual(b.snapshot()['requests'],1)
   with self.assertRaises(ValueError):reserve(b,b.snapshot()['runs'][0][1])
   b.close()
 def test_anchor_replace_and_count_order_ambiguity(self):
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);b,run=start(p,w,r)
   with b.connect() as db:
    with self.assertRaisesRegex(sqlite3.DatabaseError,'immutable_history_anchor'):db.execute('INSERT OR REPLACE INTO history_anchor SELECT * FROM history_anchor')
   (r.path/'46.json').unlink()
   with self.assertRaisesRegex(ValueError,'count'):reserve(b,run)
   b._unlock()
 def test_concurrent_requests_are_bounded_by_one_authoritative_transaction(self):
  import concurrent.futures
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t);b,run=start(p,w,r)
   def attempt(_):
    try:return reserve(b,run)
    except ValueError:return None
   with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(attempt,range(12)))
   self.assertEqual(sum(x is not None for x in results),4);self.assertEqual(b.snapshot()['exposure_micro_usd'],88938);b.close()
 def test_legacy_constructor_cannot_erase_anchored_history(self):
  from budget import AggregateBudget
  with tempfile.TemporaryDirectory() as t:
   p,w,r=fixture(t)
   with self.assertRaisesRegex(ValueError,'requires_history_adapter'):AggregateBudget(p)
   b=open_(p,w,r);self.assertEqual(b.snapshot()['exposure_micro_usd'],11522);b.close()
 def test_actual_gateway_failure_and_timeout_are_full_reservations(self):
  from history_budget import bind_anchored_gateway
  from gateway import Gateway,Policy,Artifacts,canonical
  for case in ('http500','timeout'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    p,w,r=fixture(t);b,run=start(p,w,r);e=Path(t)/'wire';e.mkdir();(e/'.offline-test').touch()
    policy=Policy('OpenAI',b.contract['model'],'https://offline.invalid/v1/chat/completions',('offline.invalid',),4,120000,400000,1600000,32000,4096,4096)
    def upstream(*args):
     if case=='timeout':raise TimeoutError('LOCAL synthetic timeout')
     return 500,'application/json',b'{"error":"LOCAL failure"}'
    g=bind_anchored_gateway(Gateway(policy,Artifacts(e,offline=True),upstream),b,run,synthetic=True)
    status,_,_=g.handle(canonical({'model':policy.model,'messages':[{'role':'user','content':'LOCAL'}],'max_tokens':4096}))
    self.assertEqual(status,502 if case=='timeout' else 500);self.assertEqual(b.snapshot()['exposure_micro_usd'],30876);self.assertEqual(b.snapshot()['requests'],1);b.close()
