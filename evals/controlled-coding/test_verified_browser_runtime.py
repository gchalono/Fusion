"""Synthetic integrity-unit fixtures only; real-browser results are separate."""
import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import verified_browser_runtime as runtime
class BrowserRuntimeTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'root/opt/google/chrome';folder.mkdir(parents=True);(root/'google-chrome-stable.deb').write_bytes(b'TEST DOUBLE PACKAGE')
  files={}
  for name,priv in (('chrome',False),('chrome-sandbox',True)):
   p=folder/name;p.write_bytes(('TEST DOUBLE '+name).encode());p.chmod(0o555);files[name]={'kind':'file','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'privileged':False}
  (folder/'chromium').symlink_to('chrome');files['chromium']={'kind':'symlink','target':'chrome'}
  m={'package_sha256':hashlib.sha256((root/'google-chrome-stable.deb').read_bytes()).hexdigest(),'binary_sha256':files['chrome']['sha256'],'version':'157.0.8103.50','launch_args':['--single-process','--no-zygote','--no-proxy-server'],'files':files};(root/'verified-runtime.json').write_text(json.dumps(m));return folder,m
 def pins(self,m):return patch.multiple(runtime,PACKAGE_SHA=m['package_sha256'],BINARY_SHA=m['binary_sha256'],TREE_SHA=hashlib.sha256(json.dumps(m['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
 def test_signed_tree_and_masked_helper(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);folder,m=self.fixture(root)
   with self.pins(m):
    self.assertEqual(runtime.verify(root)[0],folder)
    # Never create setuid files in a restricted test namespace. Independently
    # test the trusted mapping of already-verified privileged metadata.
    privileged=json.loads(json.dumps(m));privileged['files']['chrome-sandbox']['privileged']=True
    with patch.object(runtime,'verify',return_value=(folder,privileged)):
     entries,_=runtime.mounts(root)
    self.assertEqual(entries[0],(folder,Path('/usr/lib/chromium')));self.assertIn((Path('/dev/null'),Path('/usr/lib/chromium/chrome-sandbox')),entries)
 def test_changed_binary_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);folder,m=self.fixture(root);(folder/'chrome').chmod(0o755);(folder/'chrome').write_text('changed');(folder/'chrome').chmod(0o555)
   with self.pins(m),self.assertRaisesRegex(ValueError,'dependency_changed'):runtime.verify(root)
 def test_changed_manifest_or_launch_profile_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);_,m=self.fixture(root)
   with self.pins(m):
    changed=json.loads(json.dumps(m));changed['files']['chrome']['sha256']='0'*64;(root/'verified-runtime.json').write_text(json.dumps(changed))
    with self.assertRaisesRegex(ValueError,'signed_tree_identity'):runtime.verify(root)
    changed=json.loads(json.dumps(m));changed['launch_args'].append('--unauthorized');(root/'verified-runtime.json').write_text(json.dumps(changed))
    with self.assertRaisesRegex(ValueError,'profile_identity'):runtime.verify(root)
 def test_hidden_assertion_hash_fails_before_browser_import(self):
  script=Path(__file__).with_name('original_browser_runtime.mjs');p=subprocess.run(['node',str(script)],input=b'TEST DOUBLE tampered assertions',capture_output=True,env={'PATH':os.environ['PATH']})
  self.assertNotEqual(p.returncode,0);self.assertIn(b'original_browser_assertions_changed',p.stderr)
