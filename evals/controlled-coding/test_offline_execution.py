"""Synthetic execution wiring; no provider, historical state, or fixture commits."""
import difflib
import hashlib
import hmac
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from contract import canonical
from execution import coding_command
import independent


class OfflineExecutionTests(unittest.TestCase):
    def test_resolved_node_matches_namespace_runtime_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            actual = root/'node-version/bin/node'
            actual.parent.mkdir(parents=True)
            actual.touch()
            alias = root/'current'
            alias.symlink_to(actual.parent.parent, target_is_directory=True)
            with patch('shutil.which', return_value=str(alias/'bin/node')):
                argv = coding_command(root, 'synthetic')
            self.assertEqual(argv[0], str(actual))
            self.assertEqual(argv[1:3], ['--import', str(root/'node_modules/tsx/dist/loader.mjs')])
            self.assertEqual(argv[-2:], ['synthetic', '/run/objective.txt'])

    def test_grader_applies_patch_without_commits_and_authenticates_result(self):
        task = 'merge-intervals'
        initial = (independent.ROOT/'fixtures'/task/'initial/solution.py').read_text()
        candidate = 'def merge_intervals(intervals):\n    return []\n'
        diff = ''.join(difflib.unified_diff(initial.splitlines(True), candidate.splitlines(True), fromfile='a/solution.py', tofile='b/solution.py'))
        for tamper in (False, True):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as tmp:
                def sandbox(socket, workspace, command, **kw):
                    self.assertIsNone(socket)
                    self.assertEqual((workspace/'solution.py').read_text(), candidate)
                    self.assertNotEqual(subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=workspace, capture_output=True).returncode, 0)
                    self.assertIn('/checks', [target for _, target in kw['mounts']])
                    record = {'success': False}
                    key = bytes.fromhex(json.loads(kw['stdin'])['grading_key'])
                    tag = hmac.new(key, canonical(record), hashlib.sha256).hexdigest()
                    if tamper:
                        record['success'] = True
                    return {'exit_code': 0, 'timed_out': False, 'stdout': canonical({'record': record, 'authentication': tag}), 'stderr': b''}
                with patch.object(independent, 'run_command', side_effect=sandbox):
                    if tamper:
                        with self.assertRaisesRegex(ValueError, 'untrusted_grade_envelope'):
                            independent.evaluate_patch(task, diff, Path(tmp)/'grade')
                    else:
                        self.assertFalse(independent.evaluate_patch(task, diff, Path(tmp)/'grade')['success'])
