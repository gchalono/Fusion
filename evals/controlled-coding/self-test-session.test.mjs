import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtemp, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {modelFailureCode, runLocalTests, runSelfTestSession} from './self-test-session.mjs';

class ScriptedSession {
  constructor(step) { this.step = step; this.prompts = []; this.listeners = new Set(); this.aborts = 0; }
  setAutoRetryEnabled(value) { assert.equal(value, false); this.retryDisabled = true; }
  setAutoCompactionEnabled(value) { assert.equal(value, false); this.compactionDisabled = true; }
  subscribe(listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }
  emit(event) { for (const listener of this.listeners) listener(event); }
  async abort() { this.aborts++; }
  async prompt(text) {
    assert.ok(this.retryDisabled && this.compactionDisabled);
    this.prompts.push(text);
    await this.step(this.prompts.length, text, this);
  }
}
test('gateway failures keep an allowlisted cause without copying provider text', async () => {
  for (const code of ['provider_output_truncated', 'provider_http_error', 'usage_exceeds_reserved_bound',
                      'call_cap', 'provider_transport_failed', 'transport_authorization_failed']) {
    const session = new ScriptedSession(async (_, __, self) => self.emit({type:'message_end',
      message:{role:'assistant',stopReason:'error',errorMessage:'403 fusion_gateway_failure:'+code+' SYNTHETIC_SECRET'}}));
    await assert.rejects(runSelfTestSession({session, objective:'task',
      runTests:async () => { throw new Error('must not grade after gateway failure'); }}),
      error => error.message === 'gateway_failed:'+code);
    assert.equal(session.aborts, 1);
    assert.equal(session.prompts.length, 1);
  }
  assert.equal(modelFailureCode({stopReason:'error',errorMessage:'SYNTHETIC_SECRET'}), 'model_failed');
  assert.equal(modelFailureCode({stopReason:'error',errorMessage:'fusion_gateway_failure:SYNTHETIC_SECRET'}), 'model_failed');
  assert.equal(modelFailureCode({stopReason:'aborted'}), 'model_aborted');
});
async function workspace(fn) {
  const cwd = await mkdtemp(path.join(tmpdir(), 'synthetic-self-test-'));
  try { return await fn(cwd); } finally { await rm(cwd, {recursive:true, force:true}); }
}
const cases = [
  {
    objective: 'Merge overlapping closed intervals; preserve disjoint intervals.',
    wrong: 'def merge_intervals(xs):\n return [[xs[0][0], xs[-1][1]]] if xs else []\n',
    fixed: 'def merge_intervals(xs):\n out=[]\n for a,b in sorted(xs):\n  if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)\n  else: out.append([a,b])\n return out\n',
    checks: 'from solution import merge_intervals\nclass Checks(unittest.TestCase):\n def test_disjoint(self): self.assertEqual(merge_intervals([[2,3],[6,8]]), [[2,3],[6,8]])\n def test_empty(self): self.assertEqual(merge_intervals([]), [])\n def test_overlap(self): self.assertEqual(merge_intervals([[2,5],[4,8]]), [[2,8]])\n',
  },
  {
    objective: 'Count whitespace-separated words; empty or whitespace-only input has zero words.',
    wrong: "def count_words(s):\n return len(s.split(' '))\n",
    fixed: 'def count_words(s):\n return len(s.split())\n',
    checks: "from solution import count_words\nclass Checks(unittest.TestCase):\n def test_empty(self): self.assertEqual(count_words(''), 0)\n def test_whitespace(self): self.assertEqual(count_words(' \\t '), 0)\n def test_mixed(self): self.assertEqual(count_words('one\\ttwo  three'), 3)\n",
  },
];
for (const fixture of cases) {
  test(`actual local execution and bounded repair: ${fixture.objective}`, () => workspace(async cwd => {
    const session = new ScriptedSession(async (round, feedback, self) => {
      self.emit({type:'tool_execution_start', toolName:'write'});
      if (round === 1) {
        await writeFile(path.join(cwd, 'local_self_test.py'), 'import unittest\n' + fixture.checks);
      } else {
        assert.match(feedback, /AssertionError/);
        assert.doesNotMatch(feedback, /acceptance.*test_log/);
      }
      await writeFile(path.join(cwd, 'solution.py'), round === 1 ? fixture.wrong : fixture.fixed);
    });
    assert.deepEqual(await runSelfTestSession({session, objective:fixture.objective, cwd}), {localSelfTest:'passed', repairs:1});
    assert.equal(session.prompts.length, 2);
    assert.equal(session.listeners.size, 0);
  }));
}
test('passing first submission needs no continuation', () => workspace(async cwd => {
  const session = new ScriptedSession(async () => {
    await writeFile(path.join(cwd, 'solution.py'), cases[1].fixed);
    await writeFile(path.join(cwd, 'local_self_test.py'), 'import unittest\n' + cases[1].checks);
  });
  assert.equal((await runSelfTestSession({session, objective:cases[1].objective, cwd})).repairs, 0);
  assert.equal(session.prompts.length, 1);
}));
test('empty, skipped, failing, syntax-error, and missing tests cannot submit', async () => {
  for (const source of ['', 'import unittest\nclass C(unittest.TestCase):\n @unittest.skip("no")\n def test_x(self): pass\n', 'import unittest\nclass C(unittest.TestCase):\n def test_x(self): self.fail("failure")\n', 'syntax error!']) {
    await workspace(async cwd => {
      if (source) await writeFile(path.join(cwd, 'local_self_test.py'), source);
      const session = new ScriptedSession(async () => {});
      await assert.rejects(runSelfTestSession({session, objective:'task', cwd}), /local_self_test_failed/);
      assert.equal(session.prompts.length, 2);
    });
  }
});
test('local command timeout terminates without repair', () => workspace(async cwd => {
  await writeFile(path.join(cwd, 'local_self_test.py'), 'while True: pass\n');
  const result = await runLocalTests({cwd, timeoutMs:50});
  assert.equal(result.passed, false);
  assert.equal(result.infrastructureFailure, true);
  const session = new ScriptedSession(async () => {});
  await assert.rejects(runSelfTestSession({session, objective:'task', runTests:async () => result}), /local_test_tool_failed/);
  assert.equal(session.prompts.length, 1);
}));
test('tool launch failure stops; no feedback is sent for infrastructure errors', async () => {
  const session = new ScriptedSession(async () => {});
  await assert.rejects(runSelfTestSession({session, objective:'task', cwd:'/nonexistent-synthetic-workspace'}), /local_test_tool_failed/);
  assert.equal(session.prompts.length, 1);
});
test('model failure, gateway exhaustion and implicit retry never trigger repair', async () => {
  for (const event of [
    {type:'message_end',message:{role:'assistant',stopReason:'error',errorMessage:'request budget exhausted'}},
    {type:'message_end',message:{role:'assistant',stopReason:'aborted'}},
    {type:'auto_retry_start'},
  ]) {
    let checks = 0;
    const session = new ScriptedSession(async (_, __, self) => self.emit(event));
    await assert.rejects(runSelfTestSession({session, objective:'task', runTests:async () => {checks++;}}));
    assert.equal(checks, 0);
    assert.equal(session.prompts.length, 1);
    assert.equal(session.aborts, 1);
  }
});
test('tool-call and wall-clock caps abort without further prompts', async () => {
  const session = new ScriptedSession(async (_, __, self) => {
    for (let i=0; i<3; i++) self.emit({type:'tool_execution_start'});
  });
  await assert.rejects(runSelfTestSession({session, objective:'task', maxToolCalls:2}), /local_tool_budget_exhausted/);
  assert.equal(session.prompts.length, 1);
  const hanging = new ScriptedSession(() => new Promise(() => {}));
  await assert.rejects(runSelfTestSession({session:hanging, objective:'task', timeoutMs:20}), /local_deadline_exhausted/);
  assert.equal(hanging.aborts, 1);
});
test('repair prompt contains only local feedback, with secret redaction', async () => {
  const session = new ScriptedSession(async () => {});
  let checks = 0;
  await runSelfTestSession({session, objective:'public objective',
    redact: value => value.replaceAll('SYNTHETIC_SECRET', '[redacted]'),
    runTests:async () => ++checks === 1 ? {passed:false, feedback:'local assertion SYNTHETIC_SECRET'} : {passed:true}});
  assert.match(session.prompts[1], /local assertion \[redacted\]/);
  assert.doesNotMatch(session.prompts[1], /SYNTHETIC_SECRET/);
});
test('budget refusal during repair is terminal and expired work never starts', async () => {
  let checks = 0;
  const session = new ScriptedSession(async round => {
    if (round === 2) throw new Error('gateway_request_cap');
  });
  await assert.rejects(runSelfTestSession({session, objective:'task',
    runTests:async () => { checks++; return {passed:false, feedback:'local failure'}; }}), /gateway_request_cap/);
  assert.equal(checks, 1);
  assert.equal(session.prompts.length, 2);
  const expired = new ScriptedSession(async () => { throw new Error('must not start'); });
  await assert.rejects(runSelfTestSession({session:expired, objective:'task', timeoutMs:0}), /local_deadline_exhausted/);
  assert.equal(expired.prompts.length, 0);
});
test('excessive local output is a tool failure, never a repair prompt', () => workspace(async cwd => {
  await writeFile(path.join(cwd, 'local_self_test.py'), "print('x' * 20000)\n");
  const result = await runLocalTests({cwd});
  assert.equal(result.passed, false);
  assert.equal(result.infrastructureFailure, true);
  assert.ok(result.feedback.length <= 8192);
}));
