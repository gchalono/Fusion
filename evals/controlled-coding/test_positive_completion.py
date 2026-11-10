"""Offline regression for exact private recovery and positive native fixture."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from private_recovery import build
from task_manager_native import reject_output_secrets
ROOT=Path(__file__).resolve().parent
TOKENIZER=Path('/workspace/fusion-offline-tokenizer/node_modules/js-tiktoken/dist/index.js')
class CompletionTests(unittest.TestCase):
 def setup_inputs(self,root):
  base=root/'source';base.mkdir();entries=[]
  for i in range(32):
   p=base/(str(i)+'.json');p.write_text(json.dumps({'TEST_DOUBLE':i}));entries.append({'source_path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  mapping=root/'mapping.json';mapping.write_text(json.dumps({'private_dependencies':entries}));return base,mapping
 def test_private_archive_exact_restore_and_refuse_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);base,m=self.setup_inputs(root);out=root/'archive';restore=root/'restore'
   result=build(m,out,restore,base=base);self.assertEqual(result['files'],32);self.assertFalse(result['private_recovery_verified_off_environment'])
   for p in base.iterdir():self.assertEqual(p.read_bytes(),(restore/p.name).read_bytes())
   self.assertEqual(out.stat().st_mode&0o777,0o700)
   self.assertEqual((out/'private-dependencies.tar.gz').stat().st_mode&0o777,0o600)
   with self.assertRaisesRegex(ValueError,'destination_exists'):build(m,out,root/'another',base=base)
 def test_private_archive_missing_or_changed_input_fails_before_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);base,m=self.setup_inputs(root);(base/'0.json').write_text('changed')
   with self.assertRaisesRegex(ValueError,'hash_mismatch'):build(m,root/'out',root/'restore',base=base)
   self.assertFalse((root/'out').exists())
 def test_private_archive_rejects_secret_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);base,m=self.setup_inputs(root);p=base/'0.json';p.write_text('sk-proj-'+'X'*40);d=json.loads(m.read_text());d['private_dependencies'][0]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();m.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'secret_pattern'):build(m,root/'out',root/'restore',base=base)
 def test_capture_guard_checks_every_candidate_file(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'local-token').write_bytes(b'TEST_DOUBLE_LOCAL_ONLY');(r/'upstream-key').write_bytes(b'TEST_DOUBLE_UPSTREAM_ONLY')
   with self.assertRaisesRegex(ValueError,'token_in_collected_output'):reject_output_secrets(r,b'README TEST_DOUBLE_LOCAL_ONLY')
 @unittest.skipUnless(TOKENIZER.is_file(),'public js-tiktoken 1.0.21 utility not installed in recovery namespace')
 def test_three_bounded_replies_reconstruct_source_and_use_all_native_tools(self):
  p=json.loads(subprocess.check_output(['node',str(ROOT/'task_manager_positive_plan.mjs'),str(TOKENIZER)]))
  self.assertTrue(all(x+16<=512 for x in p['counts']));self.assertEqual(p['output_ceiling'],512)
  calls=[c for d in p['deltas'] for c in d['tool_calls']];self.assertEqual({c['function']['name'] for c in calls},{'read','write','bash'})
  # Run ONLY emitted file-write commands and check exact byte reconstruction;
  # do not start any service or execute the candidate in this unit test.
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'application.py').write_text(json.loads(calls[1]['function']['arguments'])['content'])
   for c in calls[2:]:
    command=json.loads(c['function']['arguments'])['command']
    fragment=command.partition('\n')[2].partition('\nTEST_DOUBLE_CODE\n')[0]
    with (root/'application.py').open('ab') as f:f.write(fragment.encode())
   self.assertEqual((root/'application.py').read_bytes(),(ROOT/'task_manager_positive_source.py').read_bytes())
