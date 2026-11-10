"""FNXC:Activation 2026-11-10-21:44: TEST-only non-consuming preflight cases."""
import copy,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from operator_auth import make_test_trust,sign_payload,ApprovalVerifier,TEST_DOMAIN
from history_budget import HistoryBudget,sha,canonical
from activation_preflight import readonly_ledger,validate_scope
import live_supervisor as s
class ActivationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.state=self.root/'state';self.state.mkdir();(self.state/'.synthetic-rehearsal').touch()
  self.db=self.state/'continuation.sqlite3';self.w=self.state/'witness.json'
  HistoryBudget.initialize(self.db,self.w,test_key=s.TEST_SELECTOR)
  self.trust=make_test_trust(self.root/'TEST');self.spec=s.prepare_spec(test_state=self.state)
 def tearDown(self):self.tmp.cleanup()
 def sign(self,spec):return sign_payload({'spec':spec,'transport':{}},self.trust.parent/'TEST-operator.key',self.trust.parent/'operator.pub')
 def verify(self,spec):return ApprovalVerifier(self.trust,self.sign(spec),test_only=True)
 def test_valid_repeat_inspection_no_consumption_or_writes(self):
  before=[p.read_bytes() for p in (self.db,self.w)]
  for _ in range(2):
   self.verify(self.spec)
   with readonly_ledger(self.db,self.w) as (b,db):
    self.assertEqual(validate_scope(self.spec,b,db)['worst_case_micro_usd'],77416)
    self.assertEqual(db.execute('SELECT COUNT(*) FROM run_authorizations').fetchone()[0],0)
    with self.assertRaises(Exception):db.execute("DELETE FROM run_authorizations")
  self.assertEqual(before,[p.read_bytes() for p in (self.db,self.w)])
 def test_expiry_and_wrong_digest(self):
  for field,value in [('expires_at',time.time()-1),('config_sha256','0'*64),('ledger_id','0'*64),('model','unsupported')]:
   with self.subTest(field=field):
    spec={**self.spec,field:value};self.verify(spec)
    with readonly_ledger(self.db,self.w) as (b,db):
     with self.assertRaises(ValueError):validate_scope(spec,b,db)
 def test_consumed_approval_rejected(self):
  envelope=self.sign(self.spec);v=ApprovalVerifier(self.trust,envelope,test_only=True)
  with s.open_ledger(self.state,v) as b:b.authorize_run(self.spec,envelope['signature'])
  with readonly_ledger(self.db,self.w) as (b,db):
   with self.assertRaisesRegex(ValueError,'consumed'):validate_scope(self.spec,b,db)
 def test_unenrolled_tampered_and_TEST_live_rejected(self):
  e=self.sign(self.spec);bad=copy.deepcopy(e);bad['payload']['spec']['nonce']='a'*64
  with self.assertRaises(ValueError):ApprovalVerifier(self.trust,bad,test_only=True)
  other=make_test_trust(self.root/'other')
  with self.assertRaises(ValueError):ApprovalVerifier(other,e,test_only=True)
  with self.assertRaises(ValueError):ApprovalVerifier(self.trust,e)
 def test_missing_private_state_never_initialized(self):
  missing=self.root/'missing'
  with self.assertRaises(ValueError):
   with readonly_ledger(missing,self.w):pass
  self.assertFalse(missing.exists())
if __name__=='__main__':unittest.main()
