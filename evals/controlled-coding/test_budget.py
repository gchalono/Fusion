"""FNXC:ControlledCoding 2026-11-09-03:50: Check shared cap, restart and concurrency without inference."""
import concurrent.futures
import tempfile
import unittest
from pathlib import Path
from budget import AggregateBudget

class BudgetTests(unittest.TestCase):
    def test_aggregate_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'budget.db'
            AggregateBudget(path).reserve('planning','p',1_900_000)
            with self.assertRaisesRegex(ValueError,'aggregate_spend_cap'):
                AggregateBudget(path).reserve('planning','q',100_001)
            AggregateBudget(path).reserve('planning','q',100_000)

    def test_concurrent_and_per_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=AggregateBudget(Path(tmp)/'budget.db')
            def reserve(_):
                try: ledger.reserve('coding','same',40_000); return True
                except ValueError: return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(reserve,range(10))),3)
            for _ in range(4): ledger.reserve('coding','calls',1)
            with self.assertRaisesRegex(ValueError,'coding_run_cap'):
                ledger.reserve('coding','calls',1)

    def test_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=AggregateBudget(Path(tmp)/'budget.db')
            for value in [0,-1,True,1.0]:
                with self.assertRaises(ValueError): ledger.reserve('planning','p',value)

    def test_gateway_denies_before_transport(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
        from gateway import Policy, Artifacts, Gateway, canonical
        from budget import guard_gateway
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'.offline-test').touch()
            ledger=AggregateBudget(root/'budget.db')
            ledger.reserve('planning','prior',2_000_000)
            policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',
                          ('offline.invalid',),4,150_000,1_000_000,1_000_000,100,100,None)
            calls=[]
            gateway=guard_gateway(Gateway(policy,Artifacts(root,offline=True),lambda *args: calls.append(args)),ledger,'coding','A')
            with self.assertRaisesRegex(ValueError,'aggregate_spend_cap'):
                gateway.handle(canonical({'model':'offline-model','messages':[{'role':'user','content':'test'}]}))
            self.assertEqual(calls,[])

    def test_multiprocess_shared_cap(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'ledger.db'
            AggregateBudget(path)
            code = '''from budget import AggregateBudget
import sys
try: AggregateBudget(sys.argv[1]).reserve('planning',sys.argv[2],150000)
except ValueError: sys.exit(3)
'''
            workers = [subprocess.Popen([sys.executable,'-c',code,str(path),str(i)],
                        cwd=Path(__file__).resolve().parent) for i in range(20)]
            codes = [p.wait(timeout=20) for p in workers]
            self.assertEqual(codes.count(0),13)
            self.assertEqual(codes.count(3),7)
            self.assertEqual(AggregateBudget(path).snapshot()['reserved_exposure_micro_usd'],1_950_000)

    def test_interruption_and_no_refund_from_usage(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.db'
            code = '''from budget import AggregateBudget
import os,sys
AggregateBudget(sys.argv[1]).reserve('planning','interrupted',1900000)
os._exit(17)
'''
            proc=subprocess.run([sys.executable,'-c',code,str(path)],cwd=Path(__file__).resolve().parent)
            self.assertEqual(proc.returncode,17)
            ledger=AggregateBudget(path)
            ledger.observe(1,evidence_ref='offline-response-sha256',provider_usage={'prompt_tokens':10,'completion_tokens':2},estimated_charge_micro=2)
            snap=ledger.snapshot()
            self.assertEqual(snap['reserved_exposure_micro_usd'],1_900_000)
            self.assertEqual(snap['observations'][0]['estimated_provider_charge_micro_usd'],2)
            self.assertIsNone(snap['observations'][0]['measured_provider_charge_micro_usd'])
            with self.assertRaisesRegex(ValueError,'aggregate_spend_cap'):
                ledger.reserve('planning','after-crash',100_001)
            with ledger.connect() as db:
                with self.assertRaisesRegex(Exception,'immutable_reservation'):
                    db.execute('DELETE FROM reservations')

    def test_retry_and_uncertain_transport_keep_reservations(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
        from gateway import Policy, Artifacts, Gateway, canonical
        from budget import guard_gateway
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'.offline-test').touch()
            ledger=AggregateBudget(root/'budget.db')
            policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',
                          ('offline.invalid',),4,150_000,1_000_000,1_000_000,100,100,None)
            calls=[]
            def transport(*args):
                self.assertEqual(len(ledger.snapshot()['reservations']),len(calls)+1)
                calls.append(args)
                raise OSError('uncertain response')
            gw=guard_gateway(Gateway(policy,Artifacts(root,offline=True),transport),ledger,'planning','p')
            raw=canonical({'model':'offline-model','messages':[{'role':'user','content':'test'}]})
            for _ in range(3): self.assertEqual(gw.handle(raw)[0],502)
            self.assertEqual(ledger.snapshot()['reserved_exposure_micro_usd'],600)
            self.assertEqual(len(list(root.glob('aggregate-reservation-*.json'))),3)

    def test_database_failure_is_terminal_before_transport(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
        from gateway import Policy, Artifacts, Gateway, canonical, Blocked
        from budget import guard_gateway
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'.offline-test').touch()
            ledger=AggregateBudget(root/'budget.db')
            policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',
                          ('offline.invalid',),4,150_000,1_000_000,1_000_000,100,100,None)
            calls=[]
            gw=guard_gateway(Gateway(policy,Artifacts(root,offline=True),lambda *a: calls.append(a)),ledger,'coding','A')
            raw=canonical({'model':'offline-model','messages':[{'role':'user','content':'test'}]})
            with patch.object(ledger,'reserve',side_effect=OSError('disk failure')):
                with self.assertRaises(OSError): gw.handle(raw)
            with self.assertRaisesRegex(Blocked,'run_terminal'): gw.handle(raw)
            self.assertEqual(calls,[])

    def test_audit_failure_retains_reservation_and_blocks_transport(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
        from gateway import Policy, Artifacts, Gateway, canonical, Blocked
        from budget import guard_gateway
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'.offline-test').touch()
            ledger=AggregateBudget(root/'budget.db')
            policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',
                          ('offline.invalid',),4,150_000,1_000_000,1_000_000,100,100,None)
            calls=[]
            artifacts=Artifacts(root,offline=True)
            gw=guard_gateway(Gateway(policy,artifacts,lambda *a: calls.append(a)),ledger,'coding','A')
            raw=canonical({'model':'offline-model','messages':[{'role':'user','content':'test'}]})
            original=artifacts.write
            def write(name, data):
                if name.startswith('aggregate-'): raise OSError('disk full')
                return original(name,data)
            with patch.object(artifacts,'write',side_effect=write):
                with self.assertRaises(OSError): gw.handle(raw)
            self.assertEqual(ledger.snapshot()['reserved_exposure_micro_usd'],200)
            with self.assertRaisesRegex(Blocked,'run_terminal'): gw.handle(raw)
            self.assertEqual(calls,[])

    def test_observations_do_not_authorize_spend(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            ledger=AggregateBudget(Path(tmp)/'ledger.db')
            ident=ledger.reserve('planning','p',2_000_000)
            ledger.observe(ident,evidence_ref='offline-estimate',provider_usage={'prompt_tokens':0},estimated_charge_micro=0)
            ledger.observe(ident,evidence_ref='offline-invoice',measured_charge_micro=0)
            snap=ledger.snapshot()
            self.assertEqual(snap['remaining_reservable_micro_usd'],0)
            self.assertIsNone(snap['observations'][0]['measured_provider_charge_micro_usd'])
            self.assertEqual(snap['observations'][1]['measured_provider_charge_micro_usd'],0)
            with self.assertRaisesRegex(ValueError,'aggregate_spend_cap'): ledger.reserve('planning','q',1)
            with self.assertRaises(sqlite3.IntegrityError): ledger.observe(999,evidence_ref='missing')
