"""Offline orchestration and real namespace boundaries; no provider calls."""
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from execution import run_command
from independent import evaluate_patch

ROOT = Path(__file__).resolve().parent


class SelfTestSessionTests(unittest.TestCase):
    def test_node_orchestration_suite(self):
        subprocess.run([str(Path(shutil.which('node')).resolve()), '--test',
                        str(ROOT/'self-test-session.test.mjs')], check=True,
                       capture_output=True, timeout=20)

    def test_local_success_cannot_replace_independent_grading(self):
        # Local smoke checks intentionally miss a defect. The grader must still
        # reject this submitted candidate, ignoring agent-authored test files.
        task = 'parse-duration'
        candidate = 'def parse_duration(text):\n    return 0\n'
        initial = (ROOT/'fixtures'/task/'initial/solution.py').read_text()
        with tempfile.TemporaryDirectory(prefix='synthetic-self-test-boundary-') as tmp:
            root = Path(tmp)
            workspace = root/'workspace'
            workspace.mkdir()
            (workspace/'solution.py').write_text(candidate)
            (workspace/'local_self_test.py').write_text('''import unittest
from pathlib import Path
from solution import parse_duration
class LocalSmoke(unittest.TestCase):
    def test_public_zero(self): self.assertEqual(parse_duration('0s'), 0)
    def test_private_paths_unavailable(self):
        for path in ['/checks', '/run/objective.txt', '/run/local-token',
                     ''' + repr(str(ROOT/'fixtures'/task/'acceptance')) + ''']:
            self.assertFalse(Path(path).exists(), path)
''')
            (workspace/'test_acceptance.py').write_text('raise RuntimeError("agent test must never enter grader")\n')
            (workspace/'driver.mjs').write_text('''
import {runSelfTestSession} from '/eval/self-test-session.mjs';
let prompts = 0;
const session = {
 setAutoRetryEnabled() {}, setAutoCompactionEnabled() {},
 subscribe() { return () => {}; }, abort() {},
 async prompt(text) { prompts++; if (text !== 'Public duration objective') throw Error('unexpected feedback'); },
};
const result = await runSelfTestSession({session, objective:'Public duration objective'});
console.log(JSON.stringify({result, prompts}));
''')
            report = run_command(None, workspace,
                                 [str(Path(shutil.which('node')).resolve()), '/work/driver.mjs'],
                                 mounts=[(ROOT/'self-test-session.mjs', '/eval/self-test-session.mjs')], timeout=10)
            self.assertEqual(report['exit_code'], 0, report['stderr'].decode(errors='replace')[:1000])
            local = json.loads(report['stdout'])
            self.assertEqual(local, {'result': {'localSelfTest': 'passed', 'repairs': 0}, 'prompts': 1})
            diff = ''.join(difflib.unified_diff(initial.splitlines(True), candidate.splitlines(True),
                                               fromfile='a/solution.py', tofile='b/solution.py'))
            grade = evaluate_patch(task, diff, root/'independent')
            self.assertNotIn('infrastructure_failure', grade)
            self.assertFalse(grade['success'])
            self.assertGreater(grade['failed'] + grade['errors'], 0)
            self.assertEqual((workspace/'solution.py').read_text(), candidate)
            self.assertEqual(local['prompts'], 1)  # No grading-to-session feedback.


if __name__ == '__main__':
    unittest.main()
