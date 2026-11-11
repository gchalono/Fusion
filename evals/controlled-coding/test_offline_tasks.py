"""Scripted test-double controls; these do not measure model coding performance."""
import difflib
import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import independent
import offline_eval
import pilot


class OfflineTaskTests(unittest.TestCase):
    def test_default_and_explicit_bindings(self):
        self.assertEqual(pilot.fixture_binding()['task_id'], 'merge-intervals')
        for task in offline_eval.IMPLEMENTATIONS:
            with self.subTest(task=task), tempfile.TemporaryDirectory(prefix='synthetic-binding-') as tmp:
                root = Path(tmp)/'synthetic-only'
                binding = pilot.initialize(root, task=task)
                self.assertEqual(binding['task_id'], task)
                self.assertTrue(binding['stored_file_sha256'])
                self.assertTrue(all(p.startswith('fixtures/'+task+'/') for p in binding['stored_file_sha256']))
                self.assertEqual(json.loads((root/'fixture-binding.json').read_text()), binding)
        with self.assertRaisesRegex(ValueError, 'unknown_frozen_task'):
            pilot.fixture_binding('unknown')

    def test_all_scripted_controls_in_independent_sandbox(self):
        for task, variants in offline_eval.IMPLEMENTATIONS.items():
            initial = (independent.ROOT/'fixtures'/task/'initial/solution.py').read_text()
            for variant, code in variants.items():
                with self.subTest(task=task, variant=variant), tempfile.TemporaryDirectory(prefix='synthetic-grading-') as tmp:
                    diff = ''.join(difflib.unified_diff(initial.splitlines(True), code.splitlines(True), fromfile='a/solution.py', tofile='b/solution.py'))
                    grade = independent.evaluate_patch(task, diff, Path(tmp)/'synthetic-only')
                    self.assertNotIn('infrastructure_failure', grade, grade)
                    self.assertEqual(grade['success'], variant == 'correct', grade)

    def test_cli_routes_selected_task_and_reports_classification(self):
        for task in offline_eval.IMPLEMENTATIONS:
            with self.subTest(task=task), tempfile.TemporaryDirectory(prefix='synthetic-cli-') as tmp:
                root = Path(tmp)/'synthetic-only'
                def execute(output, runtime, run):
                    self.assertEqual(run, task+':A')
                    self.assertEqual(json.loads((output/'fixture-binding.json').read_text())['task_id'], task)
                    (output/'candidate.patch').write_text('scripted patch')
                    return {'exit_code': 0, 'timed_out': False}, b'scripted', output/'workspace'
                with patch('sys.argv', ['offline_eval.py', '--task', task, '--runtime', tmp, '--output', str(root)]), patch.object(offline_eval, 'start_stub') as stub, patch.object(offline_eval, 'execute_agent', side_effect=execute), patch.object(independent, 'evaluate_patch', return_value={'success': True}) as grader:
                    stub.return_value = (unittest.mock.Mock(), [])
                    with contextlib.redirect_stdout(io.StringIO()):
                        offline_eval.main()
                    stub.assert_called_once_with(root, 'correct', task=task)
                    grader.assert_called_once_with(task, 'scripted patch', root/'independent-check')
                record = json.loads((root/'test-double-coding-observation.json').read_text())
                self.assertEqual(record['task'], task)
                self.assertEqual(record['classification'], 'SYNTHETIC_TEST_DOUBLE_PLUMBING_NOT_CODING_PERFORMANCE')


if __name__ == '__main__':
    unittest.main()
