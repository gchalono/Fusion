/** Local checks are untrusted agent evidence, never independent acceptance. */
import {execFile} from 'node:child_process';

export const SELF_TEST_PROMPT = `Implement spec. Derive/name boundary, empty/invalid and interaction unittest cases in local_self_test.py importing solution.py. Run via bash; inspect failures, fix code, keep assertions. Submit on pass. One repair; same caps. No model retries/private tests.`;

const GATEWAY_FAILURES = new Set(['provider_http_error', 'provider_output_truncated',
  'provider_usage_missing_or_ambiguous', 'incomplete_live_stream', 'incomplete_live_response',
  'usage_exceeds_reserved_bound', 'invalid_usage', 'response_model_mismatch', 'unsupported_response',
  'response_too_large', 'unprepared_request', 'whole_request_deadline', 'transport_worker_failed',
  'transport_authorization_failed', 'transport_request_rejected', 'provider_transport_failed',
  'call_cap', 'spend_ceiling', 'run_deadline_or_inactive', 'frozen_coding_token_limit',
  'experiment_request_cap', 'stage_allocation_cap', 'aggregate_spend_cap',
  'forward_failed', 'gateway_failure', 'coding_run_cap', 'under_reserved_request', 'request_token_limit',
  'unknown_model_or_unpriced_feature', 'store_not_authorized', 'messages_required',
  'unpriced_modality', 'unpriced_tool', 'ambiguous_output_limit', 'invalid_output_limit',
  'input_byte_bound_exceeded', 'unsupported_request_shape', 'invalid_transport_response',
  'redirect_forbidden', 'destination_mismatch', 'credential_in_request', 'credential_reflected']);

export function modelFailureCode(message) {
  const match = String(message.errorMessage ?? '').match(/fusion_gateway_failure:([a-z_]+)\b/);
  if (match && GATEWAY_FAILURES.has(match[1])) return 'gateway_failed:'+match[1];
  return message.stopReason === 'aborted' ? 'model_aborted' : 'model_failed';
}

const RUNNER = `import sys, unittest
sys.path.insert(0, '.')
suite = unittest.defaultTestLoader.discover('.', pattern='local_self_test.py')
if suite.countTestCases() == 0:
    print('No local unittest cases found', file=sys.stderr)
    sys.exit(2)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
`;

// Runs inside the existing coding namespace. No host fixtures or grader imports.
export function runLocalTests({cwd, timeoutMs = 5000}) {
  return new Promise(resolve => {
    execFile('/usr/bin/python3', ['-I', '-B', '-c', RUNNER],
      {cwd, timeout: timeoutMs, killSignal: 'SIGKILL', maxBuffer: 8192},
      (error, stdout, stderr) => resolve({
        passed: !error,
        infrastructureFailure: !!error && (typeof error.code !== 'number' || !!error.signal),
        feedback: (stdout + stderr).slice(0, 8192),
      }));
  });
}

export async function runSelfTestSession({session, objective, cwd = '/work',
  timeoutMs = 60000, maxToolCalls = 32, redact = value => value,
  runTests = runLocalTests}) {
  // Use the original prompt method, never promptWithFallback. Refuse implicit
  // provider retries/compaction calls; the gateway retains all existing caps.
  session.setAutoRetryEnabled(false);
  session.setAutoCompactionEnabled(false);
  let stopped;
  let tools = 0;
  const deadline = Date.now() + timeoutMs;
  let rejectStop;
  const stopSignal = new Promise((_, reject) => { rejectStop = reject; });
  function stop(reason) {
    if (stopped) return;
    stopped = reason;
    rejectStop(new Error(reason));
    Promise.resolve(session.abort()).catch(() => {});
  }
  const unsubscribe = session.subscribe(event => {
    if (event.type === 'auto_retry_start') stop('automatic_retry_refused');
    if (event.type === 'tool_execution_start' && ++tools > maxToolCalls) stop('local_tool_budget_exhausted');
    if (event.type === 'message_end' && event.message?.role === 'assistant' &&
        ['error', 'aborted'].includes(event.message.stopReason)) stop(modelFailureCode(event.message));
  });
  const timer = setTimeout(() => stop('local_deadline_exhausted'), Math.max(0, timeoutMs));
  const bounded = operation => Promise.race([operation, stopSignal]);
  try {
    if (timeoutMs <= 0) throw new Error('local_deadline_exhausted');
    await bounded(session.prompt(objective));
    for (let round = 0; round < 2; round++) {
      if (stopped || Date.now() >= deadline) throw new Error(stopped || 'local_deadline_exhausted');
      const result = await bounded(runTests({cwd, timeoutMs: Math.max(1, Math.min(5000, deadline - Date.now()))}));
      if (result.passed) return {localSelfTest: 'passed', repairs: round};
      if (result.infrastructureFailure) throw new Error('local_test_tool_failed');
      if (round === 1) throw new Error('local_self_test_failed');
      const output = redact(result.feedback);
      const failures = output.split('\n').filter(line =>
        /^(?:FAIL:|ERROR:|[\w.]+(?:Error|Exception|Exit):)/.test(line)).join('\n');
      const feedback = failures ? failures.slice(0, 256) : output.slice(-256);
      await bounded(session.prompt(`Local self-tests failed. Fix code per spec; keep assertions. Only repair:\n${feedback}`));
    }
  } finally {
    clearTimeout(timer);
    unsubscribe?.();
  }
}
