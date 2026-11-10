"""FNXC:Activation 2026-11-10-22:00: TEST keys only; no upstream dispatch."""
import copy,json,tempfile,time,unittest
from pathlib import Path
from operator_auth import NO_PROVIDER_CAP_ACK,require_risk_ack,make_test_trust,sign_payload,ApprovalVerifier,TEST_DOMAIN
from contract import canonical,Contract
from history_budget import sha,continuation_contract
from live_supervisor import approved_metadata,MODEL
from real_transport import validate,sealed_credential
import os
class RiskTests(unittest.TestCase):
 def test_exact_acknowledgment_and_rejections(self):
  require_risk_ack({'no_provider_cap_acknowledgment':dict(NO_PROVIDER_CAP_ACK)})
  cases=[{}, {'provider_side_cap_confirmed':True}]
  for key in NO_PROVIDER_CAP_ACK:
   a=dict(NO_PROVIDER_CAP_ACK);a.pop(key);cases.append({'no_provider_cap_acknowledgment':a})
  a=dict(NO_PROVIDER_CAP_ACK);a['authorized_runs']=True;cases.append({'no_provider_cap_acknowledgment':a})
  for c in cases:
   with self.subTest(case=c),self.assertRaisesRegex(ValueError,'acknowledgment'):require_risk_ack(c)
 def test_signed_ack_is_bound_and_unsigned_or_altered_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   trust=make_test_trust(Path(t)/'TEST');payload={'spec':{'domain':TEST_DOMAIN},'transport':{'no_provider_cap_acknowledgment':dict(NO_PROVIDER_CAP_ACK)}}
   e=sign_payload(payload,trust.parent/'TEST-operator.key',trust.parent/'operator.pub');ApprovalVerifier(trust,e,test_only=True)
   for change in ('alter','remove','unsigned'):
    bad=copy.deepcopy(e)
    if change=='alter':bad['payload']['transport']['no_provider_cap_acknowledgment']['authorized_runs']=2
    elif change=='remove':bad['payload']['transport'].pop('no_provider_cap_acknowledgment')
    else:bad['signature']=''
    with self.subTest(change=change),self.assertRaises(ValueError):ApprovalVerifier(trust,bad,test_only=True)
 def test_metadata_pricing_model_and_ack_gates(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'TEST-metadata.json';m={'timestamp':time.time(),'pricing_verified':True,'model_access':'VERIFIED','http_status':200,'model':{'id':MODEL},'classification':'SYNTHETIC'}
   def check(m,ack=True):
    p.write_bytes(canonical(m));transport={'metadata_sha256':sha(p.read_bytes())}
    if ack:transport['no_provider_cap_acknowledgment']=dict(NO_PROVIDER_CAP_ACK)
    return approved_metadata(p,{'transport':transport})
   self.assertTrue(check(m)['pricing_verified'])
   with self.assertRaisesRegex(ValueError,'acknowledgment'):check(m,False)
   for bad in ({**m,'pricing_verified':False},{**m,'model':{'id':'other'}},{**m,'timestamp':0}):
    with self.assertRaisesRegex(ValueError,'pricing_required'):check(bad)
 def test_transport_requires_ack_and_preserves_model_endpoint_spend(self):
  # Ephemeral trusted transport-permit fixture, TEST credential; never called.
  with tempfile.TemporaryDirectory(prefix='TEST-transport-') as t:
   r=Path(t);cfg=continuation_contract();cfg.update(provider_spend_authorized_usd='0.12',model_availability='VERIFIED');cp=r/'contract.json';cp.write_bytes(canonical(cfg));c=Contract(cp)
   fd=sealed_credential('TEST_NOT_A_PROVIDER_CREDENTIAL')
   try:
    permit={'live_authorized':True,'model':MODEL,'contract_sha256':c.sha256,'approved_hosts':['api.openai.com'],'expires_at':time.time()+60,'authorized_spend_usd':.12,'credential_fd':fd,'no_provider_cap_acknowledgment':dict(NO_PROVIDER_CAP_ACK)}
    ap=r/'permit.json';ap.write_bytes(canonical(permit));ap.chmod(0o600)
    config={'live':True,'authorization_file':str(ap),'contract_path':str(cp),'credential_fd':fd}
    self.assertEqual(validate(config)[1],'https://api.openai.com/v1/chat/completions')
    for field,value in [('no_provider_cap_acknowledgment',None),('model','other'),('approved_hosts',['example.invalid']),('authorized_spend_usd',0)]:
     ap.write_bytes(canonical({**permit,field:value}))
     with self.subTest(field=field),self.assertRaises(ValueError):validate(config)
   finally:os.close(fd)
if __name__=='__main__':unittest.main()
