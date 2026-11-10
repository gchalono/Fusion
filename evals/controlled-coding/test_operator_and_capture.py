"""FNXC:LiveCoding 2026-11-10-06:16: Focused TEST-only approval/capture cases."""
import copy,json,os,sqlite3,tempfile,time,unittest
from pathlib import Path
from operator_auth import make_test_trust,sign_payload,ApprovalVerifier,TEST_DOMAIN,LIVE_TRUST
from source_capture import capture
class ApprovalTests(unittest.TestCase):
 def test_valid_modified_unknown_and_live_domain(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);trust=make_test_trust(r/'TEST');payload={'spec':{'domain':TEST_DOMAIN,'nonce':'LOCAL'},'transport':{}}
   envelope=sign_payload(payload,trust.parent/'TEST-operator.key',trust.parent/'operator.pub');v=ApprovalVerifier(trust,envelope,test_only=True);self.assertTrue(v(payload['spec'],envelope['signature']))
   for case in ('modified','unknown','signature','live'):
    with self.subTest(case=case):
     bad=copy.deepcopy(envelope)
     if case=='modified':bad['payload']['spec']['nonce']='ALTERED'
     if case=='unknown':bad['key_id']='f'*64
     if case=='signature':bad['signature']='AAAA'
     if case=='live':bad['payload']['spec']['domain']='FUSION_PHASE3C_LIVE'
     with self.assertRaises(ValueError):ApprovalVerifier(trust,bad,test_only=True)
   with self.assertRaises((ValueError,FileNotFoundError)):ApprovalVerifier(trust,envelope)
 def test_substituted_public_key(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);one=make_test_trust(r/'one');two=make_test_trust(r/'two');p={'spec':{'domain':TEST_DOMAIN},'transport':{}};e=sign_payload(p,one.parent/'TEST-operator.key',one.parent/'operator.pub');(one.parent/'operator.pub').write_bytes((two.parent/'operator.pub').read_bytes())
   with self.assertRaisesRegex(ValueError,'signing_key'):ApprovalVerifier(one,e,test_only=True)
class CaptureTests(unittest.TestCase):
 def test_source_formats_and_runtime_sqlite(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   for ext in ('.py','.js','.mjs','.json','.sql','.html','.css'):(r/('source'+ext)).write_text('{}' if ext=='.json' else 'LOCAL text\n')
   with sqlite3.connect(r/'tasks.sqlite3') as db:db.execute('CREATE TABLE tasks(title)')
   result=capture(r);self.assertEqual(len(result['candidate_files']),7);self.assertEqual(len(result['runtime_data']),1);self.assertNotIn('tasks.sqlite3',result['patch'])
 def test_reject_unsafe_size_link_secret_and_binary(self):
  for case in ('symlink','hardlink','secret','oversized','prohibited','binary','unknown'):
   with self.subTest(case=case),tempfile.TemporaryDirectory() as t:
    r=Path(t)
    if case=='symlink':(r/'x.py').symlink_to('/etc/passwd')
    elif case=='hardlink':(r/'x.py').write_text('LOCAL');os.link(r/'x.py',r/'y.py')
    elif case=='secret':(r/'x.json').write_text('SYNTHETIC_SECRET_VALUE')
    elif case=='oversized':(r/'x.py').write_bytes(b'x'*1000001)
    elif case=='prohibited':(r/'.aws').mkdir();(r/'.aws/config.json').write_text('{}')
    elif case=='binary':(r/'x.js').write_bytes(b'\x00ELF')
    else:(r/'x.db').write_text('not a SQLite database')
    with self.assertRaises(ValueError):capture(r,secrets=('SYNTHETIC_SECRET_VALUE',))
class CredentialDescriptorTests(unittest.TestCase):
 def test_sealed_private_descriptor(self):
  import fcntl
  from real_transport import sealed_credential,validate_credential_fd
  fd=sealed_credential('SYNTHETIC_GATEWAY_CREDENTIAL')
  try:
   self.assertEqual(validate_credential_fd({'credential_fd':fd}),fd);self.assertEqual(os.pread(fd,100,0),b'SYNTHETIC_GATEWAY_CREDENTIAL')
   with self.assertRaises(OSError):os.write(fd,b'changed')
  finally:os.close(fd)
class BrokerProtocolTests(unittest.TestCase):
 def test_native_completion_limit_and_bound_run(self):
  import http.client,socket,threading,secrets
  from pilot import make_inference_server
  from contract import Contract,canonical
  from gateway import Artifacts
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);token=secrets.token_hex(32);calls=[]
   class Ledger:
    def remaining_seconds(self,stage,run):
     if (stage,run)!=('coding','BOUND_RUN'):raise ValueError('run_not_bound')
     return 30
   class Transport:timeout=60
   class Gateway:
    def handle(self,raw):calls.append(json.loads(raw));return 200,'application/json',b'{"local":true}'
   server=make_inference_server(r/'gateway.sock',c=Contract(),transport=Transport(),ledger=Ledger(),run='BOUND_RUN',gateway=Gateway(),token=token,artifacts=Artifacts(r),output_limit=4096,strict=True)
   threading.Thread(target=server.serve_forever,daemon=True).start()
   try:
    c=http.client.HTTPConnection('127.0.0.1:39777',timeout=5)
    def connect():c.sock=socket.socket(socket.AF_UNIX);c.sock.connect(str(r/'gateway.sock'))
    c.connect=connect;c.request('POST','/v1/chat/completions',canonical({'model':Contract().data['model'],'messages':[{'role':'user','content':'LOCAL'}],'max_completion_tokens':4096}),{'Authorization':'Bearer '+token});response=c.getresponse();self.assertEqual(response.status,200);response.read();c.close();self.assertEqual(calls[0]['max_tokens'],4096)
   finally:server.shutdown();server.server_close()
class MissingApprovalTests(unittest.TestCase):
 def test_missing_approval_never_arms_live(self):
  import subprocess,sys
  root=Path(__file__).resolve().parent
  r=subprocess.run([sys.executable,'-B',str(root/'live_supervisor.py'),'run','--approval','/nonexistent/operator-approval.json','--out','/nonexistent/job'],capture_output=True,text=True,env={'PATH':os.defpath})
  self.assertNotEqual(r.returncode,0);self.assertIn('REFUSED_OR_FAILED',r.stdout)
 def test_provider_descriptor_abort_is_terminal(self):
  from real_transport import RealTransport
  # Actual local transport tests cover dispatch; this checks the terminal latch.
  from unittest.mock import patch
  import threading
  t=object.__new__(RealTransport);t.active=set();t._workers=threading.Lock();t._aborted=False;t.abort();self.assertTrue(t._aborted)
class DefaultTierTests(unittest.TestCase):
 def test_only_default_priced_tier_is_accepted(self):
  from contract import Contract,canonical
  c=Contract();body={'model':c.data['model'],'messages':[{'role':'user','content':'LOCAL'}],'max_tokens':4096,'service_tier':'default'}
  self.assertEqual(json.loads(c.prepare(canonical(body))[0])['service_tier'],'default')
  for tier in ('auto','priority','flex',None):
   body['service_tier']=tier
   with self.assertRaisesRegex(ValueError,'unpriced_service_tier'):c.prepare(canonical(body))
class TerminalProviderErrorTests(unittest.TestCase):
 def test_auth_billing_stop_but_native_rate_retry_preserved(self):
  from live_supervisor import terminal_provider_error
  for status,body in ((401,b'{}'),(403,b'{}'),(429,b'{"error":{"code":"insufficient_quota"}}')):self.assertTrue(terminal_provider_error(status,body))
  self.assertFalse(terminal_provider_error(429,b'{"error":{"code":"rate_limit_exceeded"}}'));self.assertFalse(terminal_provider_error(500,b'{}'))
