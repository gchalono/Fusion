"""Source-independent evaluation tests. Missing private tests are SKIPPED, never passed.
Run in a clean namespace without the original /workspace evidence mounts.
"""
import json,os,subprocess,sys,unittest
# No host /etc is mounted. Local synthetic TLS certificate needs no system config.
os.environ["OPENSSL_CONF"]="/dev/null"
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
missing_original=subprocess.run(['git','cat-file','-e','b3bc7b0dc6c2751bb3b499d9ce6023b3e2c7284c'],cwd=ROOT,capture_output=True).returncode!=0
all_results=[]
for folder in ('controlled-coding','planning-collector','persistence'):
 suite=unittest.defaultTestLoader.discover(str(ROOT/'evals'/folder),pattern='test*.py')
 def mark(node):
  if isinstance(node,unittest.TestSuite):
   for item in node:mark(item)
  elif missing_original and node.id().endswith('LocalGateTests.test_modified_or_advanced_worktree_cannot_repass_original_gate'):
   method=node._testMethodName;setattr(node,method,unittest.skip('Requires original private-history checkpoint, intentionally absent from sanitized orphan. Not a passed security test.')(getattr(node,method)))
 mark(suite)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 all_results.append({'suite':folder,'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'failed':len(result.failures)+len(result.errors),'skipped':len(result.skipped),'skip_reasons':[{'test':str(t),'reason':reason} for t,reason in result.skipped]})
print(json.dumps({'classification':'PUBLIC_SNAPSHOT_OFFLINE_TESTS_PRIVATE_DEPENDENCIES_EXPLICIT','results':all_results},indent=2));raise SystemExit(any(r['failed'] for r in all_results))
