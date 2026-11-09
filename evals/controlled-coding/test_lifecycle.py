"""FNXC:NativeIsolation 2026-11-09-04:44: Keep interrupted exposure durable;
never label fixture usage measured or refund a settled reservation.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from budget import AggregateBudget, guard_gateway
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
from gateway import Policy, Gateway, Artifacts, canonical


class LifecycleTests(unittest.TestCase):
    def test_restart_recovers_forwarded_without_refund(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.db'
            code="from budget import AggregateBudget; import os,sys; b=AggregateBudget(sys.argv[1]); i=b.reserve('coding','A',150000); b.transition(i,'FORWARDED','before_transport'); os._exit(19)"
            result=subprocess.run([sys.executable,'-c',code,str(path)],cwd=Path(__file__).resolve().parent)
            self.assertEqual(result.returncode,19)
            ledger=AggregateBudget(path)
            self.assertEqual(ledger.recover_uncertain(),1)
            snapshot=ledger.snapshot()
            self.assertEqual(snapshot['transitions'][-1]['state'],'UNCERTAIN')
            self.assertEqual(snapshot['reserved_exposure_micro_usd'],150000)
            self.assertEqual(ledger.recover_uncertain(),0)
            with self.assertRaisesRegex(ValueError,'coding_run_cap'):ledger.reserve('coding','A',1)
            with self.assertRaisesRegex(ValueError,'invalid_ledger_transition'):ledger.transition(1,'SETTLED','automatic')

    def test_usage_classification_and_reservations(self):
        for variant in ('usage','missing','truncated','error'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'.offline-test').touch()
                ledger=AggregateBudget(root/'ledger.db')
                policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',('offline.invalid',),4,150000,1000000,1000000,100,100,100)
                def transport(*_):
                    if variant=='error':raise OSError('local interruption')
                    body={'model':'offline-model','choices':[{'finish_reason':'length' if variant=='truncated' else 'stop'}]}
                    if variant!='missing':body['usage']={'prompt_tokens':5,'completion_tokens':7}
                    return 200,'application/json',canonical(body)
                gateway=guard_gateway(Gateway(policy,Artifacts(root,offline=True),transport),ledger,'coding','A')
                request=canonical({'model':'offline-model','messages':[{'role':'user','content':'fixture'}],'max_tokens':100})
                for _ in range(2):gateway.handle(request)
                snapshot=ledger.snapshot()
                self.assertEqual(snapshot['reserved_exposure_micro_usd'],400)
                self.assertEqual(len(snapshot['reservations']),2)
                terminal=[x for x in snapshot['transitions'] if x['state'] in ('SETTLED','UNCERTAIN')]
                self.assertEqual([x['state'] for x in terminal],['SETTLED' if variant=='usage' else 'UNCERTAIN']*2)
                if variant=='usage':
                    self.assertEqual(snapshot['observations'][0]['estimated_provider_charge_micro_usd'],12)
                    self.assertIsNone(snapshot['observations'][0]['measured_provider_charge_micro_usd'])

    def test_events_are_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=AggregateBudget(Path(tmp)/'ledger.db');ledger.reserve('planning','P',1)
            with ledger.connect() as db:
                with self.assertRaisesRegex(Exception,'immutable_transition'):db.execute('DELETE FROM transitions')

    def test_concurrent_processes_share_per_run_money_and_calls(self):
        for amount,admitted in ((40000,3),(1,4)):
            with self.subTest(amount=amount),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'ledger.db';AggregateBudget(path)
                code="from budget import AggregateBudget; import sys; b=AggregateBudget(sys.argv[1]);\ntry: b.reserve('coding','same-run',int(sys.argv[2]))\nexcept ValueError: sys.exit(3)"
                processes=[subprocess.Popen([sys.executable,'-c',code,str(path),str(amount)],cwd=Path(__file__).resolve().parent) for _ in range(16)]
                codes=[p.wait(timeout=10) for p in processes]
                self.assertEqual(codes.count(0),admitted)
                self.assertEqual(codes.count(3),16-admitted)
                self.assertEqual(AggregateBudget(path).snapshot()['reserved_exposure_micro_usd'],amount*admitted)

    def test_policy_cannot_change_across_restarts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.db';AggregateBudget(path).bind_policy('coding','A','a'*64)
            AggregateBudget(path).bind_policy('coding','A','a'*64)
            with self.assertRaisesRegex(ValueError,'run_policy_mismatch'):
                AggregateBudget(path).bind_policy('coding','A','b'*64)
