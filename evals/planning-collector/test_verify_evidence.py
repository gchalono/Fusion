"""FNXC:NativeIsolation 2026-11-09-05:12: Replayed capture verification must
retain DB-diff evidence while checking the shared SQLite budget read-only.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'controlled-coding'))
from budget import AggregateBudget,guard_gateway
from gateway import Policy,Gateway,Artifacts,canonical
from verify_evidence import verify


class EvidenceTests(unittest.TestCase):
    def fixture(self, root):
        (root/'.offline-test').touch();r=root/'results';r.mkdir()
        g=root/'scratch/gateway-artifacts';g.mkdir(parents=True);(g/'.offline-test').touch()
        p=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',('offline.invalid',),4,150000,1000000,1000000,100,100,100)
        ledger=AggregateBudget(r/'shared-budget.db')
        gateway=guard_gateway(Gateway(p,Artifacts(g,offline=True),lambda *_:(200,'application/json',canonical({'model':'offline-model','choices':[]}))),ledger,'planning','fixture')
        gateway.handle(canonical({'model':'offline-model','messages':[{'role':'user','content':'OFFLINE TEST DOUBLE'}],'max_tokens':100}))
        records={
          'verification.json':{'request_count_match':True,'direct_mock_bypass_blocked':True,'external_route_blocked':True,'reserved_micro_usd_estimated':200,'gateway_forwarded_attempts':1,'scenario':'normal','native_failure':False},
          'database-before.json':{'counts':{'project.ai_sessions':0},'row_hashes':{'project.ai_sessions':'before'}},
          'database-after.json':{'counts':{'project.ai_sessions':1},'row_hashes':{'project.ai_sessions':'after'}},
          'filesystem-before.json':{},'filesystem-after.json':{},
          'processes-before.json':['PID PPID COMMAND'],'processes-after.json':['PID PPID COMMAND'],
          'mcp.json':{'servers':[],'errors':[]},'gateway-policy.json':asdict(p),
          'native-test-double.json':{'classification':'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS','summary':{'title':'OFFLINE TEST DOUBLE'}}}
        for name,value in records.items():(r/name).write_bytes(canonical(value))

    def test_budget_check_preserves_database_diff(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.fixture(root)
            result=verify(root)
            self.assertEqual(result['database_changed_tables'],['project.ai_sessions'])
            self.assertEqual(result['model_http_attempts'],1)
            self.assertEqual(result['reserved_micro_usd_estimated'],200)
            # Preserve verification of historical artifact names as well.
            (root/'results/native-test-double.json').rename(root/'results/native-result.json')
            self.assertTrue(verify(root)['verified'])

    def test_rejects_tampered_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.fixture(root)
            (root/'results/gateway-policy.json').write_text('{}')
            with self.assertRaises(AssertionError):verify(root)
