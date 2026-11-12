# Run 3 diagnosis and prospective diagnostic correction

Historical run: `~/fusion-self-test-live-run-003`, `parse-duration:A`.
Only termination/result/failure metadata, fixed stderr markers and selected
read-only ledger columns were inspected. No private approval, credential, signing
key, gateway token or raw provider request/response was opened. Historical run
files, contract, approvals and ledger were not changed.

## Established facts

- The process exited -9 after 18.125 seconds, with `aborted=true`,
  `gateway_aborted=true`, `timed_out=false`. The owning supervisor killed the
  namespace after the gateway's fail-closed abort, not its 300-second deadline.
- Attempt 1 completed with validated provider usage, no truncation, 3,624 ms
  latency, 422 input and 274 output tokens, and a SETTLED ledger transition.
- Attempt 2 reserved 2405 micro-USD and reached FORWARDED. It ended UNCERTAIN
  with `transport_or_accounting_interrupted`; no provider usage observation was
  recorded. Its only failure artifact says `forward_failed`, while termination
  says `gateway_failure`. No second response or detailed exception was retained.
- The two durable reservations are 1853 + 2405 = 4258 micro-USD. Two calls were
  used, below four. Reserved token bounds total 2583+512+3964+512 = 7571, below
  16000. Reservation checks succeeded. Neither per-run money, aggregate money,
  request count nor the run deadline was exhausted at that boundary.
- The original run never produced a candidate patch or independent live grade.
  A workspace candidate is not a graded successful submission.

## Exact-cause limitation

The precise second-attempt downstream rejection is not recoverable from these
artifacts. The shared gateway overwrote unexpected failures with `forward_failed`;
the live adapter retained only a small subset of codes; the worker discarded
exception classification; the session then labeled any model failure as
`model_failed_or_budget_exhausted`. That generic message is not evidence of a
budget failure. FORWARDED is also not proof that the provider returned HTTP 200.

Because a failed response was discarded before result persistence, provider
rejection, truncation, malformed/incomplete output, authorization/preparation
failure and accounting interruption cannot honestly be distinguished afterward.
The code's ordinary worker OSError path normally creates a 502 result, which is
absent here; a checked-response/non-OSError rejection is a plausible explanation,
not a measured historical result. No provider outage, incorrect budget arithmetic
or specific request incompatibility is claimed without evidence.

The confirmed implementation defect is **loss of the actual failure classification
across the guarded transport → gateway → local HTTP adapter → self-test session**.
The optional CLI warning is unrelated. No guessed output-limit or retry change
was made to manufacture a successful execution.

## Correction

- Shared gateway diagnostics retain an exact allowlisted code and bounded numeric
  metadata. Arbitrary exception strings, headers, provider bodies and credentials
  never enter failure artifacts or public error replies.
- The live response checker distinguishes HTTP rejection, output truncation,
  missing/ambiguous usage, incomplete streams/finishes and exceeded reserved
  bounds. Unsafe/incomplete responses still abort and retain exposure.
- Worker errors preserve safe authorization/request/transport classifications
  across the process boundary. Timeouts retain their existing deadlines.
- The inference-only HTTP socket returns a fixed structured error marker. The
  self-test session uses only recognized codes from that marker, never arbitrary
  provider text. Unknown model failures stay `model_failed`; they are not called
  budget exhaustion. Terminal errors still abort without a repair or retry.
- The changed shared gateway is included in the signed implementation inventory.
  Old implementation-bound approvals cannot authorize changed code silently.

## Surface Enumeration

Covered paths: streaming and non-streaming replies; HTTP rejection; malformed,
  truncated, incomplete, missing-usage and over-bound responses; worker versus
  parent failure propagation; structured socket failures; model error/abort;
  actual budget refusals; positive local-TLS Pi sessions and independent grading.
Unrecognized or secret-bearing exception text is reduced to a fixed safe code.
The same shared gateway is exercised by collector and controlled-coding tests.

## Symptom Verification

Original symptom: successful first result followed by a failed second attempt,
UNCERTAIN charged exposure, no second result and only generic errors.
Deterministic reproduction: return a valid synthetic first response, then inject
each rejected second response without a provider call or real-time delay.
Assertion: the corresponding fixed code survives in the second failure artifact
and gateway state; exposure remains reserved; unsafe replies remain rejected;
the socket/session propagate only allowlisted causes. These fixtures reproduce
the diagnostic-loss defect, not an invented historical provider response.

## Fresh-run assessment

The diagnostic correction is ready for review. A fresh run would be a separately
authorized diagnostic experiment, not proof that a specific historical provider
failure has been fixed. `parse-duration:A` is consumed and cannot be replayed.
A new unused identity, legitimate continuation authority and a new implementation
binding would be required. No such authority or launch was created here. Keep
Runs A, B and 3, every receipt and all cumulative exposure intact.

## Verification and changed files

The full controlled-coding suite passed 96 tests. The final parent-authorization
classification regression was then added and the 40-test targeted diagnostic,
socket, live, real-transport and reliability suite passed, including the local-TLS
live paths. Collector: 37 passed. Persistence: 9 passed. Node orchestration: 12
passed. Fixture verification, credential-pattern scan and diff whitespace checks
passed. Only disposable synthetic keys/authority and local TLS were used.

Implementation files: `live.py`, `real_transport.py`, `isolation.py`,
`self-test-session.mjs`, `reliability_authorization.py` and the shared
`evals/planning-collector/gateway.py`. Regression files: new
`test_gateway_failure_diagnostics.py`, `test_inference_bridge.py`,
`self-test-session.test.mjs` and the worker-result assertion in `test_live.py`.

Final read-only inspection still showed A INCOMPLETE, B COMPLETE and Run 3
INCOMPLETE, with nine cumulative reservations totaling 18373 micro-USD. Run 3's
two reservations still total 4258 micro-USD. No historical second result or live
grade was created. Original repository files outside this worktree, all historical
outputs, signed approvals and financial records remain untouched. No genuine
authority was signed, paid request made, live experiment launched, commit or push
performed.
