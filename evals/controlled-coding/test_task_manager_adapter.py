"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
TEST DOUBLE compatibility checks. No Pi prompt or provider transport is invoked.
Use original private records only to verify historical identity; never synthesize
approvals. Exercise the reused durable ledger with a separate Experiment 2 identity.
"""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from task_manager_adapter import (TASK, SOURCE, sha, verify_sources, load_arm,
    experiment_contract, arming_arithmetic, loop_feasibility, write_manifest)
from budget import AggregateBudget
from contract import canonical, Contract

EVIDENCE=Path('/workspace/phase2m-genuine-success')
PREPARED=Path('/workspace/phase2n-evaluation/frozen')

class TaskManagerTests(unittest.TestCase):
    def test_separate_contract_and_arming(self):
        old=Contract().data;d=experiment_contract()
        self.assertEqual(old['coding_runs'],9);self.assertEqual(d['coding_runs'],3)
        self.assertEqual(d['coding_run_ids'],[TASK+':'+a for a in 'ABC'])
        self.assertEqual(d['provider_spend_authorized_usd'],'0.00')
        self.assertEqual(arming_arithmetic(d)['allocated_usd'],'0.86')
        self.assertTrue(arming_arithmetic(d)['passes'])

    def test_wrong_task_and_arm_rejected_before_evidence(self):
        for task,arm in [('parse-duration','A'),(TASK,'D')]:
            with self.assertRaisesRegex(ValueError,'experiment_task_or_arm_mismatch'):
                load_arm(EVIDENCE,PREPARED,arm,task_id=task)

    @unittest.skipUnless(EVIDENCE.is_dir() and PREPARED.is_dir(),'original private evidence unavailable')
    def test_historical_inputs_and_approvals(self):
        m,approvals=verify_sources(EVIDENCE,PREPARED)
        self.assertEqual(len(approvals),8)
        self.assertEqual(m['native_plan_sha256'],sha((EVIDENCE/'MissionPlanSummary.native.json').read_bytes()))
        self.assertEqual([sha(load_arm(EVIDENCE,PREPARED,a)) for a in 'ABC'],[m['arms'][a]['prompt_sha256'] for a in 'ABC'])

    @unittest.skipUnless(PREPARED.is_dir(),'original private evidence unavailable')
    def test_actual_B_C_two_request_loop_exceeds_token_reservation_cap(self):
        d=experiment_contract()
        for arm in 'BC':
            prompt=(PREPARED/f'prompts/{arm}.txt').read_bytes();proof=loop_feasibility(prompt,d)
            self.assertEqual(proof['status'],'BLOCKED')
            with tempfile.TemporaryDirectory() as tmp:
                b=AggregateBudget(Path(tmp)/'experiment2.db',experiment_contract=d);run=TASK+':'+arm
                b.control_run('coding',run,'start')
                # Even omitting all tool/schema/output overhead, the second
                # durable reservation cannot fit. No network or Pi is needed.
                b.reserve('coding',run,20000,token_bounds=(len(prompt),0))
                with self.assertRaisesRegex(ValueError,'frozen_coding_token_limit'):
                    b.reserve('coding',run,20000,token_bounds=(len(prompt),0))
                self.assertEqual(len(b.snapshot()['reservations']),1)

    def test_reopen_preserves_uncertain_exposure_and_requires_explicit_resume(self):
        d=experiment_contract();run=TASK+':A'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'experiment2.db';b=AggregateBudget(path,experiment_contract=d);b.control_run('coding',run,'start')
            i=b.reserve('coding',run,10000,token_bounds=(1000,512));b.transition(i,'FORWARDED','TEST DOUBLE interruption')
            self.assertEqual(AggregateBudget(path).recover_uncertain(),1);b.control_run('coding',run,'INCOMPLETE')
            with self.assertRaisesRegex(ValueError,'inactive'):b.reserve('coding',run,10000,token_bounds=(1000,512))
            b.control_run('coding',run,'resume');b.reserve('coding',run,10000,token_bounds=(1000,512))
            self.assertEqual(AggregateBudget(path).snapshot()['reserved_exposure_micro_usd'],20000)
            self.assertEqual(b.snapshot()['transitions'][2]['state'],'UNCERTAIN')

    def test_concurrent_budget_exhaustion(self):
        d=experiment_contract();run=TASK+':A'
        with tempfile.TemporaryDirectory() as tmp:
            b=AggregateBudget(Path(tmp)/'experiment2.db',experiment_contract=d);b.control_run('coding',run,'start')
            def attempt(_):
                try:b.reserve('coding',run,40000,token_bounds=(1000,512));return True
                except ValueError:return False
            with ThreadPoolExecutor(max_workers=8) as pool:admitted=list(pool.map(attempt,range(8)))
            self.assertEqual(sum(admitted),3);self.assertEqual(b.snapshot()['reserved_exposure_micro_usd'],120000)

    def test_cross_experiment_and_contract_migration_rejected(self):
        d=experiment_contract()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'experiment2.db';b=AggregateBudget(path,experiment_contract=d)
            with self.assertRaisesRegex(ValueError,'unregistered'):b.reserve('coding','merge-intervals:A',1000,token_bounds=(10,10))
            changed=copy.deepcopy(d);changed['coding_runs']=9
            with self.assertRaisesRegex(ValueError,'experiment_contract_mismatch'):AggregateBudget(path,experiment_contract=changed)

    @unittest.skipUnless(EVIDENCE.is_dir() and PREPARED.is_dir(),'original private evidence unavailable')
    def test_manifest_generation_no_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'manifest.json';m=write_manifest(EVIDENCE,PREPARED,out)
            self.assertEqual(m['source_commits'],SOURCE);self.assertEqual(m['provider_spending_usd'],'0.00')
            self.assertEqual(m['coding_agents_started'],0);self.assertEqual(m['arms']['C']['native_tool_loop_feasibility']['status'],'BLOCKED')
            with self.assertRaises(FileExistsError):write_manifest(EVIDENCE,PREPARED,out)
