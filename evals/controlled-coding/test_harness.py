"""FNXC:ControlledCoding 2026-11-09-03:50: Validate freeze, arm separation and negative controls offline."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import harness
from acceptance import evaluate

REFERENCES = {
'merge-intervals': '''def merge_intervals(intervals):
    out = []
    for a,b in sorted(intervals):
        if a > b: raise ValueError()
        if out and a <= out[-1][1]: out[-1][1] = max(b,out[-1][1])
        else: out.append([a,b])
    return out
''',
'parse-duration': '''import re
def parse_duration(text):
    text = text.strip()
    if not text: raise ValueError()
    total = 0
    while text:
        m = re.match(r"(\\d+)([hms])",text)
        if not m: raise ValueError()
        total += int(m[1])*dict(h=3600,m=60,s=1)[m[2]]
        text = text[m.end():].lstrip()
    return total
''',
'stable-toposort': '''def stable_toposort(nodes, edges):
    edges=set(map(tuple,edges))
    if any(a not in nodes or b not in nodes for a,b in edges): raise ValueError()
    out=[]
    while len(out)<len(nodes):
        ready=[n for n in nodes if n not in out and not any(b==n and a not in out for a,b in edges)]
        if not ready: raise ValueError()
        out.append(ready[0])
    return out
'''}

class HarnessTests(unittest.TestCase):
    def test_freeze_and_tamper(self):
        harness.verify()
        with patch.object(harness, 'inventory', return_value={}):
            with self.assertRaisesRegex(ValueError, 'frozen_inputs_changed'):
                harness.verify()

    def test_arm_information(self):
        t = 'merge-intervals'
        plan = {'native_plan': 'native', 'approved_clarification_answers': ['approved']}
        self.assertEqual(set(harness.inputs(t,'A',plan)), {'objective'})
        self.assertEqual(set(harness.inputs(t,'B',plan)), {'objective','native_plan'})
        self.assertIn('approved_clarification_answers',harness.inputs(t,'C',plan))
        self.assertIsNone(harness.inputs(t,'B'))

    def test_dry_run_no_fabricated_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            result = harness.dry_run(Path(temp)/'runs')
            self.assertEqual(len(result['runs']),9)
            self.assertEqual(result['new_provider_requests_dispatched'],0)
            for row in result['runs']:
                self.assertIsNone(row['coding_cost_usd'])
                self.assertIsNone(row['acceptance_passed'])
            with self.assertRaises(FileExistsError):
                harness.dry_run(Path(temp)/'runs')

    def test_independent_tests_positive_and_negative_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref=Path(tmp)/'reference.py'
            for task,code in REFERENCES.items():
                with self.subTest(task=task):
                    self.assertEqual(evaluate(task,harness.ROOT/'fixtures'/task/'initial/solution.py')['status'],'failed')
                    ref.write_text(code)
                    self.assertEqual(evaluate(task,ref)['status'],'passed')

if __name__ == '__main__': unittest.main()
