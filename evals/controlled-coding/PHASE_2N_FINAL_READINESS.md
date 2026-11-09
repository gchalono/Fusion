# Phase 2N offline blocker resolution

**PARTIALLY_READY** — **VERIFIED:** the requested offline blocker checks pass.
**BLOCKED:** live execution remains disabled and unauthorized ($0.00). This report
requests no paid execution. All offline answers, approvers, inference fixtures and
wire doubles used here are **SYNTHETIC**, never historical Phase 2M evidence or
human approvals. Earlier results are historical unless explicitly rerun below.

## Recovery and tests

| Claim | Tag | Evidence |
|---|---|---|
| Initial HEAD exactly 73dd29ab2237fb9e7c47458b9deb0b11d681f033; clean persistence preflight passed | VERIFIED | blocker-resolution-observations.json: initial_checkpoint/initial_preflight and original preflight SHA-256 |
| Before changes: 74 passed, 0 failed, 0 skipped (28 coding, 37 collector, 9 persistence) | VERIFIED | Three baseline suite logs, SHA-256 pointers in observations |
| After changes: 75 passed, 0 failed, 0 skipped (29 coding, 37 collector, 9 persistence) | VERIFIED | Three final suite logs; checkpoint tooling reruns all three |
| Frozen fixtures and acceptance criteria unchanged | VERIFIED | harness.py verify passed; no fixture/frozen.json diff |
| Production packages unchanged, including prepared native runtime | VERIFIED | Both Git packages trees equal ef70b0eb0b194ba1481c73d5c27ac1bfa352d515; diff confined to evals |
| Normal review mechanism permitted this phase's namespace/native/coding checks | VERIFIED | Successful reviewed command execution; no bypass of the earlier unavailable review service |
| Current code checkpoint and fresh-clone recovery | UNVERIFIED at document creation | Final operator report supplies the independently verified publication SHA and fresh recovery result; CHECKPOINTS.md records the implementation |

## Budget correction

**VERIFIED:** `experiment-parameters.json` now configures planning **$0.50**,
coding **9 × $0.12 = $1.08**, total **$1.58**, and unallocated headroom **$0.42**.
The exact unchanged arming formula is:

`9 × per_run_coding_cap + planning_reserve ≤ 0.80 × aggregate_cap`

`9 × $0.12 + $0.50 = $1.58 ≤ 0.80 × $2.00 = $1.60` — **PASS**.

**VERIFIED:** stage limits do not allocate the $0.42 headroom automatically.
`budget.py` enforces the tighter $0.12 run cap even after reopening SQLite; a new
regression test reserves that cap and verifies that a further reservation fails.
The gateway policy uses the same tighter cap. Frozen metadata's older $0.15 ceiling
is preserved; the effective runtime limit is the stricter $0.12 contract, not a
fixture rewrite. Existing experiment contracts remain immutable and are not
silently migrated or refunded.

**VERIFIED:** the aggregate $2 ceiling, 80% threshold, uncached input reservation,
request-byte upper bound, 32,000/4,096 request limits, 12 planning/4 coding attempt
limits, 600/300-second original stage deadlines, at-most-60-second request timeout,
and frozen 16,000 coding token upper bound remain unchanged. Retried, reformatted
and compaction HTTP attempts require separate committed reservations. Reserved
exposure, reported usage, estimated charges and measured charges remain separate.
Evidence: contract/budget tests, native attempt links and independently replayed
ledger verification. Proposed allocations confer no spending authorization.

## Native compaction diagnosis

**VERIFIED — classification exactly 1: Fixture never triggers compaction.**
The explicit manual API was called, but SDK preparation rejected the default
fixture before any summarization HTTP request: `SESSION_TOO_SMALL`, corresponding
to `Nothing to compact (session too small)`. Fourteen branch entries represented
about 3,334 context tokens, below the default 20,000-token retained tail.
Evidence: SYNTHETIC `compaction.json`, exception SHA-256, recorded SDK settings,
and installed Pi SDK `AgentSession.compact` / `prepareCompaction` source.

| Candidate category | Tag | Confirming/ruling-out evidence |
|---|---|---|
| 1. Fixture never triggers compaction | VERIFIED — confirmed | Default preparation has no messages to summarize; retain tail 20,000 versus context about 3,334; no compaction HTTP attempt |
| 2. Compaction attempted but incomplete | VERIFIED — ruled out as original cause | Manual entry point was invoked, but failed during eligibility preparation. A separate eligible control completed actual native summarization |
| 3. Insufficient token budget | VERIFIED — ruled out as original cause | Exception is eligibility-related, not a token cap. Trigger used reserveTokens 4,096 and output requests 3,276/2,048, all below the unchanged gateway 4,096 ceiling |
| 4. Deadline or request-limit exhaustion | VERIFIED — ruled out | Five interview attempts plus two compaction attempts = 7/12; planning reserved $0.063686 < $0.50; original 600-second deadline retained; no timeout/exhaustion exception |
| 5. Genuine native integration failure | VERIFIED — ruled out for this fixture | Actual SDK trigger completed, independent evidence verifier passed, only project.ai_sessions changed; empty MCP and no execution records |

**VERIFIED:** the separate **SYNTHETIC trigger control** applies the SDK's public
in-memory settings override only to its disposable test session: retained tail
512, summary reserve 4,096. It does not modify production source, frozen tasks,
request/time/spend/security limits or the default fixture's observed failure.
`SYNTHETIC-triggered-compaction.json` records completion. The default
`compaction.json` deliberately still records `not_completed / SESSION_TOO_SMALL`.
No success was manufactured or substituted for that default observation.

**VERIFIED:** genuine PostgreSQL/ICU 60 loaded using the existing rootless dependency
directory; the same `fusion-phase2a-pilot` start ledger and three-starts/hour cap
were preserved. Two native starts were used in this phase. The independent verifier
now checks the dynamically priced durable reservation links and bounds separately
from the older fixed native audit upper bound; it does not relabel one as another.
Historical evidence verification remains supported.

**UNVERIFIED:** suitability for arbitrarily long native planning sessions. The
native catalog still reports a 128,000-token window despite the test provider's
smaller metadata; the gateway independently enforces its 32,000-byte bound and
fails closed. The small fixture and explicit trigger control do not prove that
native automatic compaction will occur before that stricter gateway bound in a
long session. No cap was loosened to accommodate the catalog mismatch.

## Native approval integration

**VERIFIED:** the existing planning approval bridge was exercised against actual
`getMissionInterviewSession` / `submitMissionInterviewResponse` interfaces in the
prepared Fusion runtime. The bridge resolves the same module/session store as
the native runner, rechecks the current question immediately before submission,
and never starts a mission, autopilot or provider-backed interview.

| Required check | Result/tag | Evidence |
|---|---|---|
| Correct question hashing | PASS — VERIFIED | Native question JSON hash equals persisted approval binding |
| Verbatim answer preservation | PASS — VERIFIED | SYNTHETIC JSON answer including surrounding whitespace/newline preserved and rehashed immediately before native map parsing/submission |
| Explicit approval verification | PASS — VERIFIED | Wrong APPROVE hash rejected; only the labeled test approver supplies the valid test command |
| Rejection of edited approvals | PASS — VERIFIED | Edited persisted answer rejected before native callback |
| Rejection of missing approvals | PASS — VERIFIED | Missing record rejected before native callback |
| Rejection of synthetic approvals in live mode | PASS — VERIFIED | Submission without explicit test permission rejected; existing live-path rejection unit tests also rerun |
| Correct gateway accounting | PASS — VERIFIED | 7 native HTTP contacts = 7 gateway attempts = 7 durable planning reservations, including retry/format/compaction traffic |
| Crash/restart behavior | PASS — VERIFIED | Separate approver process exits after durable submission intent; restart refuses replay and invokes no native callback; an explicit new SYNTHETIC approval is used for the positive path |
| Shared experiment-ledger integration | PASS — VERIFIED | Actual Arm A continuation uses that same experiment.db: 7 planning + 3 coding reservations |

**VERIFIED:** only **SYNTHETIC** approvals were created. `approval_fixture.py`
requires a marked private test directory and never reads a human TTY. The signed
question/approval records carry the SYNTHETIC label. Native response values are
parsed from the approved verbatim JSON only because the actual native interface
accepts a response map. No historical Phase 2M records were recreated.

## Reproducibility, security and accounting

**VERIFIED:** two identical Arm A profiles completed with the genuine Fusion
shared Pi session, tools/subprocesses, gateway-to-local-TLS inference double,
generated solution patch, and independent acceptance in a second no-network,
no-credential sandbox. Normalized patches, grading, request accounting and coding
ledger reservations/usage estimates/transitions matched exactly. Timestamps,
absolute paths and reservation/run identifiers were excluded. Three coding attempts
per run; normalized SHA-256:
`72ccccad3838afa61ab175f3b8077fd99c3b6d22a0d46085650319aa5aa00c08`.
Evidence: `blocker_checks.py` and SYNTHETIC reproducibility observation.

**VERIFIED:** first canonical frozen fixture remains `merge-intervals`.
Frozen manifest SHA-256:
`9d71a3317b9e0531af7c6dee66c8ba6ad70a36b6bd7be0ccc0ee8fb997b90c30`.
Derived fixture fingerprint (not a stored fixture-file hash):
`1618bc5acc2627e2f2574cc05266a4821db736ec0690594e60fc8def2ae3fe33`.
The recorded component hashes were checked/printed before execution.

**VERIFIED:** existing wrong-patch and test-tampering controls were rerun under
the tighter budget and rejected by independent acceptance, as expected. Gateway
kill and abort regressions were also rerun: each retained full uncertain exposure,
refused implicit restart, required explicit resume/new token and counted four
attempts without resetting the original deadline. Evidence: observations JSON
negative_controls/gateway_recovery and original evidence SHA-256 pointers.

**VERIFIED:** current 30-case isolation/canary probe reports **ENFORCED**, with
all blocks and positive controls passing, initial gateway canary present and no
canary found in collected sandbox observations. Four supplemental protocol-specific
positive controls passed: DNS/UDP on port 53 at a reserved address, raw ICMP echo,
IPv6 TCP, and TCP at the metadata address. These controls run in a separate trusted
user/network namespace with only loopback/assigned local aliases and no external
route. Namespace-only capabilities permit test sink setup; the coding sandbox
retains dropped capabilities and its existing seccomp filter. No host policy,
interface, firewall or installed library was changed.

**INFERRED:** these controls support the measured unprivileged command boundary,
not protection against host administrators, kernel/VM exploits or malicious trusted
harness changes. Coding remains the shared Pi session, not TaskExecutor or a
recovered Phase 2M supervisor. Fresh HOME/in-memory sessions, allowlisted public
runtime, isolated filesystems and the run-bound inference socket remain in use.

**VERIFIED:** shared experiment exposure is **69,651 micro-USD**: planning
63,686 plus coding 5,965. Seven planning records remain `UNCERTAIN` because the
SYNTHETIC upstream deliberately omits usage; three coding records are `SETTLED`
on SYNTHETIC reported usage with estimated charge, not measured billing. No refunds
or measured charge records were introduced. This reserved exposure is **not**
provider spend. Independent native verification also checks the separate legacy
fixed audit upper bound of 135,478 micro-USD without substituting it for the
shared durable exposure.

## Final validation and remaining limits

**VERIFIED:** offline regressions, native evidence replay, frozen verification,
protocol controls, reproducibility and current isolation checks pass. The read-only
live preflight ran without a live flag/auth file and returned **LIVE_REFUSED**,
exit 1. Arming-allocation failure is gone; missing paid authorization, missing
human approvals, model availability and live pipeline gates still refuse execution.
The pre-publication recovery subcheck also correctly reports a dirty tree while
these edits are pending; a clean fresh-clone preflight follows publication.

**VERIFIED:** no paid inference or real-provider-host requests were made. Evidence
is local-only namespace routing, scrubbed process environments, explicit local
SYNTHETIC transports, contact/reservation counters and the unchanged $0.00 contract.
No invoice-based measured charge is claimed. No provider pricing/availability host
was queried. No host-wide changes, production edits or review bypass occurred.

**UNVERIFIED:** real provider schema fidelity, deprecated model availability,
long-session native catalog/compaction compatibility, actual human-channel approval
operation and integrated live execution. The live pipeline remains disabled and
is not authorized by offline test records. These limits do not prevent the
requested SYNTHETIC offline validation; they prevent a claim of live readiness.

**UNVERIFIED:** off-VM preservation of private raw artifacts. Only reviewed code,
frozen fixtures and sanitized observations are pushed. Private TLS keys, approval
keys/records, native raw logs and complete private evidence remain outside Git.

**INFERRED:** historical Phase 2M evidence remains an independent development
limitation recorded in PROJECT_STATE.md. No repeated search was undertaken because
no new recovery location was supplied, and none was reconstructed.

**VERIFIED:** `blocker-resolution-observations.json` contains the per-check results,
source SHA-256 values and SHA-256 pointers to original VM-local evidence. Early
DNS positive-control setup lacked namespace-only port-53 bind permission; adding
that permission solely to the trusted control fixed it without altering the coding
sandbox. The source-allowlist regression was updated to inspect both the runner
and approval bridge for the same forbidden entry points, then all 37 collector
tests passed. Neither development failure remains unresolved.

**BLOCKED:** paid/live execution remains unavailable under the $0.00 authorization.
The next permitted work is offline investigation of the long-session catalog
mismatch if needed; this report does not request provider inference or paid approval.
