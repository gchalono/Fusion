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
