"""FNXC:TaskManagerOfflineValidation 2026-11-09-20:38:
Offline regression for native TEST DOUBLE payloads and measured wire bounds."""
import hashlib,json,sys,unittest,tempfile
from pathlib import Path
from contract import canonical
from task_manager_adapter import experiment_contract
from task_manager_native import script,persist_checked_outputs
from task_manager_tokens import measure

EVIDENCE=Path('/workspace/tm-resume-evidence')

class ValidationTests(unittest.TestCase):
 def test_sensitive_output_is_rejected_before_any_artifact_is_written(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);secret=b'TEST_DOUBLE_ONLY_PRIVATE_VALUE'
   (root/'local-token').write_bytes(secret);(root/'upstream-key').write_bytes(b'TEST_DOUBLE_ONLY_OTHER_VALUE')
   with self.assertRaisesRegex(ValueError,'token_in_collected_output'):
    persist_checked_outputs(root,{'stdout':secret,'stderr':b''},b'')
   self.assertFalse((root/'agent-stdout.txt').exists());self.assertFalse((root/'agent-stderr.txt').exists())
   persist_checked_outputs(root,{'stdout':b'TEST DOUBLE safe','stderr':b''},b'')
   self.assertEqual((root/'agent-stdout.txt').read_bytes(),b'TEST DOUBLE safe')

 def test_every_fixture_reply_fits_existing_512_byte_conservative_output_bound(self):
  for variant in ('coding','security','unauthorized'):
   delta,finish=script({'messages':[]},variant)
   self.assertEqual(finish,'tool_calls');self.assertLessEqual(len(canonical(delta)),512)
   self.assertIn('TEST_DOUBLE',delta['tool_calls'][0]['id'])
   final,reason=script({'messages':[{'role':'tool'}]},variant)
   self.assertEqual(reason,'stop');self.assertLessEqual(len(canonical(final)),512)

 def test_active_contract_unchanged_and_separate_from_proposal(self):
  self.assertEqual(experiment_contract()['frozen_coding_token_limit'],16000)
  self.assertEqual(experiment_contract()['per_run_coding_cap_usd'],'0.12')
  proposal=json.loads(Path(__file__).with_name('TOKEN_BOUND_PROPOSED_NOT_ACTIVE.json').read_text())
  self.assertEqual(proposal['status'],'PROPOSED_NOT_ACTIVE');self.assertEqual(proposal['operator_approval_artifact'],'none')
  self.assertEqual(proposal['unchanged_request_cap'],4)

 @unittest.skipUnless((EVIDENCE/'native-A/result.json').is_file(),'private native evidence unavailable')
 def test_measured_native_A_and_projected_B_C_fit_money_not_active_token_bound(self):
  m,p=measure(EVIDENCE/'native-A')
  self.assertEqual(m['arms']['A']['fixture_two_request_cumulative_upper'],12621)
  self.assertTrue(m['arms']['A']['fits_active_16000'])
  for arm in 'BC':
   self.assertFalse(m['arms'][arm]['fits_active_16000'])
   self.assertTrue(m['arms'][arm]['fits_120000_micro_run_cap'])
  self.assertEqual(p['proposed_cumulative_bound'],144384)
  self.assertEqual(p['four_request_worst_case_reserved_micro_usd'],77416)

 @unittest.skipUnless((EVIDENCE/'native-A-repeat/result.json').is_file(),'private native evidence unavailable')
 def test_native_repeat_has_equal_patch_and_actual_wires(self):
  for name in ('candidate.patch','native-wire-01.json','native-wire-02.json'):
   self.assertEqual((EVIDENCE/'native-A'/name).read_bytes(),(EVIDENCE/'native-A-repeat'/name).read_bytes())

 @unittest.skipUnless((EVIDENCE/'native-security/agent-stdout.txt').is_file(),'private native evidence unavailable')
 def test_actual_native_security_and_unknown_tool_outcomes(self):
  safe=(EVIDENCE/'native-security/agent-stdout.txt').read_text();deny=(EVIDENCE/'native-unauthorized/agent-stdout.txt').read_text()
  self.assertIn('TEST_DOUBLE_SECURITY_PASS',safe);self.assertIn('Network is unreachable',safe)
  self.assertIn('Tool unauthorized_test_tool not found',deny)
  self.assertIn('"isError":true',deny)

 @unittest.skipUnless((EVIDENCE/'native-crash/recovery-control.json').is_file(),'private native evidence unavailable')
 def test_native_crash_keeps_exposure_without_Pi_replay(self):
  v=json.loads((EVIDENCE/'native-crash/recovery-control.json').read_text());self.assertTrue(v['native_aborted'])
  self.assertTrue(v['broker_explicit_resume_verified']);self.assertFalse(v['Pi_conversation_replay']);self.assertGreater(v['uncertain_exposure_retained'],0)
