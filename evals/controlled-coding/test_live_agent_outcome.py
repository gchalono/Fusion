"""Exercise live outcome state without creating a session or any approvals."""
from pathlib import Path
import shutil
import subprocess
import unittest


class LiveAgentOutcomeTests(unittest.TestCase):
    def test_retry_success_clears_stale_error_but_terminal_failure_survives(self):
        module = Path(__file__).with_name('live-agent-outcome.mjs').resolve().as_uri()
        code = '''
import assert from 'node:assert/strict';
const {nextModelError} = await import(process.argv[1]);
const token = 'SYNTHETIC_TOKEN';
const assistant = (stopReason, errorMessage) => ({type:'message_end',message:{role:'assistant',stopReason,errorMessage}});
let error = nextModelError(undefined, assistant('error', 'Connection error '+token), token);
assert.equal(error, 'Connection error [redacted]');
error = nextModelError(error, {type:'auto_retry_start'}, token);
assert.equal(error, 'Connection error [redacted]');
for (const stopReason of ['stop', 'toolUse']) {
  assert.equal(nextModelError(error, assistant(stopReason), token), undefined);
}
assert.equal(nextModelError(error, {type:'message_end',message:{role:'toolResult'}}, token), error);
assert.equal(nextModelError(error, assistant(undefined), token), error);
assert.equal(nextModelError(undefined, assistant('error', 'final failure'), token), 'final failure');
assert.equal(nextModelError(undefined, assistant('aborted'), token), 'model run failed');
'''
        subprocess.run([str(Path(shutil.which('node')).resolve()), '--input-type=module',
                        '-e', code, module], check=True, capture_output=True, timeout=10)
