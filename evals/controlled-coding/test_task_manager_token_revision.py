"""Offline scoped revision does not authorize provider spending or alter defaults."""
import tempfile,unittest
from pathlib import Path
from task_manager_token_revision import offline_contract,PROPOSAL_SHA
from task_manager_adapter import experiment_contract
class TokenRevisionTests(unittest.TestCase):
 def test_scoped_revision_preserves_original_contract(self):
  original=experiment_contract();revised=offline_contract()
  self.assertEqual(original['frozen_coding_token_limit'],16000)
  self.assertEqual(revised['frozen_coding_token_limit'],144384)
  changed={k for k in set(original)|set(revised) if original.get(k)!=revised.get(k)}
  self.assertEqual(changed,{'frozen_coding_token_limit','offline_token_revision_proposal_sha256','offline_only'})
  self.assertEqual(revised['provider_spend_authorized_usd'],'0.00')
  self.assertEqual(revised['coding_attempts_per_run'],4)
  self.assertEqual(revised['per_run_coding_cap_usd'],'0.12')
 def test_tampered_proposal_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'proposal.json';p.write_text('{}')
   with self.assertRaisesRegex(ValueError,'hash_mismatch'):offline_contract(p)
 def test_shared_three_arm_maximum_and_restart_preserve_caps(self):
  from budget import AggregateBudget
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'ledger.db';ledger=AggregateBudget(path,experiment_contract=offline_contract())
   for arm in 'ABC':
    run='phase2m-personal-task-manager:'+arm;ledger.control_run('coding',run,'start')
    for _ in range(4):ledger.reserve('coding',run,19354,token_bounds=(32000,4096))
    with self.assertRaisesRegex(ValueError,'experiment_request_cap'):ledger.reserve('coding',run,19354,token_bounds=(32000,4096))
   snap=AggregateBudget(path).snapshot()
   self.assertEqual(snap['reserved_exposure_micro_usd'],232248)
   self.assertEqual(len(snap['reservations']),12)
