"""FNXC:OfflineFinal 2026-11-09-05:40: Test proposed pricing and refusal gates;
no operator budget is changed and no provider request is made.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from contract import Contract,canonical
from budget import AggregateBudget

class ContractTests(unittest.TestCase):
    def test_operator_allocations_refuse_arming(self):
        c=Contract();self.assertIn('ARMING_ALLOCATION_EXCEEDS_80_PERCENT',c.arming_errors())
        self.assertIn('NO_PAID_AUTHORIZATION',c.arming_errors())
        d=c.data
        from decimal import Decimal
        self.assertEqual(Decimal(d['per_run_coding_cap_usd'])*9+Decimal(d['planning_reserve_usd']),Decimal('1.85'))

    def test_byte_bound_uncached_and_output_clamp(self):
        c=Contract();body={'model':c.data['model'],'messages':[{'role':'user','content':'fixture'}],'max_tokens':9000}
        raw=canonical(body);normalized,bounds=c.prepare(raw)
        self.assertEqual(json.loads(normalized)['max_tokens'],4096)
        self.assertEqual(bounds['input_token_upper_bound'],max(len(raw),len(normalized)))
        self.assertEqual(bounds['reserved_micro_usd'],int(__import__('math').ceil(max(len(raw),len(normalized))*.4+4096*1.6)))
        self.assertEqual(c.estimate({'prompt_tokens':100,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':50}}),41)

    def test_unknown_and_unpriced_requests_fail_closed(self):
        c=Contract();base={'model':c.data['model'],'messages':[{'role':'user','content':'x'}]}
        for change in ({'model':'substitute'},{'n':2},{'web_search_options':{}},{'store':True},{'messages':[{'role':'user','content':[{'type':'image_url','image_url':{}}]}]}):
            with self.subTest(change=change),self.assertRaises(ValueError):c.prepare(canonical(dict(base,**change)))
        with self.assertRaises(ValueError):c.prepare(canonical(dict(base,messages=[{'role':'user','content':'x'*32001}])))

    def test_persisted_contract_stage_limits_and_resume(self):
        c=Contract();d=copy.deepcopy(c.data);d.update(planning_run_ids=['task'],coding_run_ids=['task:A'],frozen_coding_token_limit=16000)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'experiment.db';b=AggregateBudget(path,experiment_contract=d)
            b.control_run('planning','task','start')
            for _ in range(5):b.reserve('planning','task',100000,token_bounds=(100,10))
            with self.assertRaisesRegex(ValueError,'stage_allocation_cap'):AggregateBudget(path).reserve('planning','task',1,token_bounds=(100,10))
            b.control_run('coding','task:A','start');i=b.reserve('coding','task:A',100,token_bounds=(100,10));b.transition(i,'FORWARDED','test');b.recover_uncertain();b.control_run('coding','task:A','INCOMPLETE')
            with self.assertRaisesRegex(ValueError,'inactive'):b.reserve('coding','task:A',2,token_bounds=(1,1))
            b.control_run('coding','task:A','resume');b.reserve('coding','task:A',2,token_bounds=(1,1))
            self.assertEqual(b.snapshot()['reserved_exposure_micro_usd'],500102)
            altered=dict(d,planning_reserve_usd='0.60')
            with self.assertRaisesRegex(ValueError,'contract_mismatch'):AggregateBudget(path,experiment_contract=altered)
