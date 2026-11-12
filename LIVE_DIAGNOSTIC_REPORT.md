# First genuine live run: read-only diagnosis

Baseline: `25e38461597daa5ea656f58212402ac026df3b54`, with the previously
authorized live-runner changes in this isolated worktree.

The existing `~/fusion-first-live-run-001` and
`~/fusion-first-live-authority/experiment.db` were inspected without changing them.
SQLite was opened with `mode=ro` and `PRAGMA query_only=ON`. Inspected fields were
run controls, reservation/transition state, numeric accounting and authority
counts. Only summarized result metadata, agent-error markers, artifact existence
and the untrusted candidate were examined. No credentials, signing keys, signed
approval files, local gateway token or raw request/response payloads were read.

## Findings

1. Four provider requests succeeded at the transport/accounting boundary. Every
   reservation advanced RESERVED → FORWARDED → SETTLED, with valid reported
   usage and no response truncation. Settlement requires HTTP 200 and validated
   usage in the existing gateway. This does not prove delivery to the agent,
   correct code, independent acceptance or measured provider billing.
2. The relay had a real three-second idle-close bug. Responses are buffered by
   the trusted gateway before delivery. Request 2 took 3,536 ms, so the relay
   could close while a valid provider response was still being generated.
   Request 3 has the exact same recorded request hash as request 2, consistent
   with the native retry after the lost response. This explains the observed
   local BrokenPipe and unnecessary repeat provider call. The other recorded
   latencies were 1,993, 2,608 and 1,258 ms.
3. The pi-claude-cli warning was a separate optional-provider import failure.
   Pi aliases the root pi-ai import to `compat.js`; appending the transcript
   subpath then resolves to the nonexistent `compat.js/utils/transcript`.
   The selected OpenAI provider still completed four requests, so this warning
   was not a failure to reach the selected provider.
   Separately, the live adapter latched any assistant error permanently. Pi can
   emit an assistant error and later recover via its native retry, but the adapter
   would still throw that stale error after a successful later response. This is
   a second genuine execution bug; the original event stream was not retained,
   so its exact contribution to the final connection error cannot be proved.
4. The ledger records `merge-intervals:A` as INCOMPLETE. Both authority kinds
   have one consumed entry. All four requests count toward its unchanged limit;
   all $0.007909 of durable reserved exposure remains charged. Estimated usage
   totals $0.001519, with no measured bill recorded. The legacy gateway's
   separate policy accumulator was $0.054480; it is not the durable ledger sum
   or a measured bill. None of these amounts may be refunded by resetting state.
5. `agent-stderr.txt` contains the connection-error marker, but no supervisor
   exit-code, timeout or abort record was saved. Its mtime is about 21.85 seconds
   after the recorded start, not 300 seconds. No exact exit code or final kill
   signal can honestly be reconstructed. The four-call allowance was exhausted;
   a later attempt must be refused, but the original artifacts do not establish
   whether that refusal was the final trigger. New telemetry records that cause.
6. The original run did not produce `candidate.patch`, `independent-check` or
   `live-observation.json`: grading never ran in that execution. A separate fresh
   offline diagnostic sandbox graded the preserved candidate against unchanged
   acceptance tests: 3/4 passed, `test_case_0` failed, zero errors. This is a new
   diagnostic result, not an original live-run grade. The generated candidate
   and frozen acceptance criteria were not edited or used as scripted model
   output in regression tests.

## Small fixes

- The shared relay waits for data/EOF under the existing transport and owned
  process deadlines; silence is no longer interpreted as a disconnected client.
- Disconnection handling covers both response headers and body. It never
  retries, refunds or reverses a settled provider request.
- The live adapter tracks the latest assistant outcome instead of latching a
  recovered error. Final errors and aborts still fail; unrelated tool events do
  not clear an error. Native retry settings and reservation limits are unchanged.
- Both known vendored consumers, pi-claude-cli and droid-cli, import transcript
  helpers through Pi's explicit compatible entry point, whose exported functions
  are already present in the installed SDK.
- Future executions save `termination.json` with scalar supervisor flags, exit
  code, elapsed time, gateway-attempt count and a fixed safe gateway failure code,
  including before failure prevents grading. The original run gains no new file.

## Surface Enumeration

The shared relay serves both offline and live adapters and both traffic
directions; regressions cover idle gaps, later byte delivery and peer EOF without
real-time sleeps. Gateway response tests cover header/body disconnection without
another dispatch. The actual Pi session regression exercises extension loading
and independent grading and rejects the missing-transcript warning. Outcome-state
tests cover error → native retry → success, final error/abort, token redaction and
unrelated events. Termination
tests cover successful and failed processes, absence of a falsely claimed grade,
and retained INCOMPLETE state. Four-call refusal retains the first cause across
later aborted requests. All signing, budget, isolation and deadline checks remain.

## Symptom Verification

- Original symptom: valid buffered responses outlived the relay's idle window,
  causing local connection errors/retries; optional extension loading resolved
  the transcript import under a file path; failed executions lost their exact
  process-termination evidence.
- Exact reproduction: deterministic relay readiness fakes simulate an idle gap
  followed by bytes, a disconnected HTTP client fails while headers/body are
  written, the real local-TLS Pi session loads extensions, and an injected failed
  coding process exits before grading. These use no paid transport or real keys.
- Assertion it is gone: delayed bytes are delivered in both directions; client
  disconnects do not escape or redispatch; the genuine local Pi session has no
  missing-transcript error; exact safe termination fields survive process failure
  and the ledger remains INCOMPLETE with no successful acceptance artifact.

## Follow-up authority

A separately authorized follow-up run is reasonable after these infrastructure
fixes, but A is consumed and may not be replayed. The operator must explicitly
select a distinct registered identity consistent with the experiment design,
retain the same immutable contract and ledger/aggregate accounting, and authorize
that follow-up. Do not rotate ledgers, reuse A, increase limits, create approvals
automatically or claim that a new paid run has happened. The existing first-run
preflight intentionally rejects an existing ledger; it has not been weakened
into a retry authorization mechanism. No provider cap is claimed.

## Changed files and validation

Execution fixes: `isolation.py`, `live.py`, `live-agent.mts`, the new
`live-agent-outcome.mjs`, `packages/pi-claude-cli/index.ts` and
`packages/droid-cli/index.ts`. Regression coverage: `test_live.py`, new
`test_inference_bridge.py` and `test_live_agent_outcome.py`. The provider import
fix has a patch changeset at `.changeset/controlled-coding-provider-import.md`.
This diagnosis is a new record; earlier records were not rewritten.

Offline suites passed: 55 controlled-coding, 37 planning-collector and 9
persistence tests. Targeted provider suites passed 55 Claude CLI and 8 Droid CLI
tests. Both provider typechecks and scoped lint passed, along with frozen fixture
verification, changeset format, whitespace and credential-pattern scans. These
164 tests use offline fixtures; no paid request or new genuine authority was
created. No real credential/signing-key/approval file was read, and no commit or
push was performed. The original dirty checkout remains unchanged.
