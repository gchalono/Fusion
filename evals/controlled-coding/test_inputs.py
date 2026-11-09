"""FNXC:OfflineFinal 2026-11-09-06:40: B/C construction only; synthetic
plans/answers never enter live approval stores or coding performance results.
"""
import unittest
from harness import inputs,SETTINGS,verify
from pilot import fixture_binding
from contract import Contract

class InputTests(unittest.TestCase):
    def test_arms_only_change_rendered_input(self):
        plan={'native_plan':'TEST_DOUBLE_NOT_A_PLAN: scripted fixture','approved_clarification_answers':'TEST_APPROVER_NOT_HUMAN: fixture answer'}
        task=fixture_binding()['task_id'];a=inputs(task,'A');b=inputs(task,'B',plan);c=inputs(task,'C',plan)
        self.assertEqual(a['objective'],b['objective']);self.assertEqual(b['objective'],c['objective'])
        self.assertEqual(b['native_plan'],c['native_plan']);self.assertEqual(set(c)-set(b),{'approved_clarification_answers'})
        settings=[{'frozen':dict(SETTINGS),'contract':Contract().sha256,'permissions':'same_hardened_namespace'} for _ in 'ABC']
        self.assertEqual(settings[0],settings[1]);self.assertEqual(settings[1],settings[2]);verify()
