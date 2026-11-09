# Phase 2N final offline readiness

**BLOCKED** — VERIFIED: provider spending remains authorized at $0.00. No paid
inference, live coding mission, autopilot, MCP operation or real provider-host
request was performed. All upstream responses in these checks are test doubles.

## Claim table

| Claim | Status | Evidence |
|---|---|---|
| Feature work is confined to evals; fork fetch/push destination is gchalono/Fusion | VERIFIED | Git diff and remote URL inspection; checkpoint tooling rechecks both URLs |
| Baseline 98e8c310f097372c73c8cde3cab4247c509dde4d is present; 993af2bdf7a5fa223ca16bf233be399bc6fd9a86 is its ancestor | VERIFIED | Initial persistence preflight; live_preflight.py ancestry check |
| Phase 2M supervisor and genuine historical artifacts remain missing | VERIFIED | Existing recovery inventory, PROJECT_STATE.md; no new plausible recovery location supplied; no reconstruction performed |
| 28 coding, 37 collector, 9 persistence unit tests pass: 74 total | VERIFIED | offline-readiness-observations.json evidence hashes; commands below |
| 30 reference namespace cases passed with no_new_privs=1 and UID 65534 | VERIFIED | Hardened security probe 3; summarized with original evidence hash in offline-readiness-observations.json |
| ENFORCED applies to the measured namespace boundary | VERIFIED | isolation.py, security_filter.py; genuine agent runs used execution.py and the same namespace builder |
| Every network protocol has a protocol-identical positive control | UNVERIFIED | Raw ICMP/DNS/IPv6/metadata cases share an allowed HTTP gateway control; additional protocol-specific controls remain required |
| Genuine Fusion shared Pi coding session needs no mission/task/DB in this adapter | VERIFIED | coding-agent.mts; successful secured coding runs and subprocess/tool events |
| Arm A correct scripted patch passes four independent frozen checks | VERIFIED | coding-test-double-2 observation; second sandbox, fresh Git checkout plus patch |
| Wrong patch and test-tampering controls fail independent acceptance | VERIFIED | coding-wrong and coding-tamper observations; both agent processes exited 0 but grading rejected them |
| B/C construction preserves common settings and differs only in rendered inputs | VERIFIED | test_inputs.py; synthetic plan/answer labels, no human approval claim |
| Two identical complete Arm A runs are reproducible | UNVERIFIED | Second identical run was not executed: automatic approval review service usage limit |
| Kill/abort preserve uncertain exposure and require explicit resume | VERIFIED | recovery_checks.py: kill and abort each produced UNCERTAIN,SETTLED,SETTLED,SETTLED; four contacts/four reservations; new token after resume |
| Shared SQLite cap survives concurrent processes, crashes and restart | VERIFIED | test_budget.py plus persisted-contract tests and integrated recovery checks |
| All nine coding IDs and three planning IDs share one contract-bound experiment DB | VERIFIED | pilot.initialize, budget.py; stage allocations and registered IDs are checked inside BEGIN IMMEDIATE |
| Reserved exposure, upstream-reported usage, estimated charge and measured charge are separate | VERIFIED | Append-only reservations/observations/transitions; all measured provider charges remain null |
| Real HTTPS transport is disabled by default and exercised against local TLS | VERIFIED | real_transport.py and test_real_transport.py: streaming, nonstreaming, missing usage, credential/destination boundaries |
| Real provider schema fidelity and model availability | UNVERIFIED | No real call; deprecated exact model must be verified without substitution before live authorization |
| Approval hashes/bindings and rejection of edited/test-double live records | VERIFIED | approvals.py, test_approvals.py; no human answers or approvals generated |
| End-to-end live planning/approval/gateway integration | UNVERIFIED | planning-approval-bridge.mts wraps native APIs; the callback bridge has not been exercised with new real interviews and approved answers |
| Native regression uses real PostgreSQL and genuine ICU 60 | VERIFIED | /tmp/fusion-native-offline-pe0t8uig/results; exit 0, 5 contacts/5 reservations, all output ceilings 4096, only project.ai_sessions changed |
| Native compaction under the supplied contract | UNVERIFIED | Native compaction.json says not_completed; no production change or safety relaxation made |
| Current live preflight fails closed | VERIFIED | live_preflight.py returns LIVE_REFUSED; no authorization, missing approvals, arithmetic conflict and integration gate; sandbox also prevents a current namespace probe |
| Provider spend and real-provider-host contacts in offline checks are zero | VERIFIED | Local-only test transports, network namespaces, scrubbed worker destinations and recorded contacts; no billing measurement implied |
| Remote code backup and fresh recovery of this implementation | UNVERIFIED at document creation | See subsequent CHECKPOINTS.md entry and independently verified branch tip; final operator report records exact SHA |
| Private raw evidence has off-VM backup | UNVERIFIED | Only reviewed code, fixtures and sanitized observations are published; private ledgers/keys/raw logs remain local |

## Implemented boundary and limitations

VERIFIED: `createResolvedAgentSession` in
`packages/engine/src/agents/agent-session-helpers.ts` calls the existing Pi runtime
(`createPiAgentSessionRaw` in `packages/engine/src/agents/pi.ts`). The adapter uses
an in-memory session, fresh HOME and writable work directory, read/write/bash
allowlist, no MCP and no fallback. Existing `sessionPurpose: merger` policy excludes
host extensions that could open a TaskStore. This is the shared Fusion Pi agent
session, **not** TaskExecutor, an orchestrated mission or the missing Phase 2M
supervisor. The public runtime emitted an optional pi-claude-cli compatibility
warning; the Pi session itself completed. Production files were not modified.

VERIFIED: Untrusted code and descendants run in user/network/PID/mount/IPC/UTS
namespaces with dropped capabilities, no_new_privs, masked setuid/setgid binaries,
read-only public runtime, private HOME/tmp and seccomp. Namespace/mount/ptrace,
process-memory inspection, capability/identity changes, namespace clone flags,
non-IP/Unix socket families and setuid chmod are denied. The only host network
path is the per-run inference Unix socket via an in-namespace loopback bridge.
The host gateway owns the credential, immutable contract and ledger. Admin socket,
approval records, hidden acceptance tests and other arm state are not mounted in
the coding view. Abort revokes the token, kills owned transport workers and stops
the gateway; the harness detects broker death and kills its owned namespace.

VERIFIED: Independent grading uses a fresh Git checkout and generated one-file
solution patch, then a second no-network/no-credential sandbox. Frozen checks are
read-only. Candidate imports execute in child workers; the nondumpable grader
holds a fresh MAC key and authenticates its result, rather than trusting candidate
stdout or exit status. Only the trusted generated solution patch is collected;
a fake test file in the coding workspace cannot alter grading.

INFERRED: These checks support isolation from unprivileged model-driven commands
under this measured kernel/runtime configuration. They establish no protection
against privileged host attackers, kernel exploits, VM escapes, malicious trusted
harness changes or future untested runtime changes. Protocol-identical positive
controls and a fresh ENFORCED probe remain live prerequisites.

## Parameters and accounting

VERIFIED: Operator-supplied parameters and source/date are preserved verbatim in
experiment-parameters.json. Requests reject unpriced features, unknown models,
ambiguous output bounds and bodies beyond 32,000 bytes. Input reservation uses
max(received bytes, normalized bytes) at uncached $0.40/M, plus clamped output at
$1.60/M. Cached $0.10/M applies only to estimated charges from reported usage.
32,000/4,096 costs $0.0193536, rounded upward to 19,354 micro-USD for reservation.
Every underlying forwarded attempt, including retry/format/compaction attempts,
must commit a durable reservation before transport. Failed reservation/audit
writes fail closed. Reservations are never silently refunded or reused.

VERIFIED: Stage caps are planning $0.50, coding $1.35; contingency $0.15 is not
transferred. Per-run coding $0.15/4 attempts, planning 12 attempts/task, original
persisted deadlines 300/600 seconds, transport timeout at most 60 seconds. The
frozen stricter 16,000 total coding token upper bound is also retained. The local
scripted fixture requests 512 output tokens identically across arms; this is a
stricter test profile and does not establish performance at 4,096 tokens.
The native test-double runner was tightened from its former 128k/32,768 bounds
and artificial prices to the supplied contract; giant synthetic descriptions
were shortened under evals only. No frozen coding criteria changed.

VERIFIED: **Arming is refused:** 9 × $0.15 + $0.50 = **$1.85**, exceeding
0.8 × $2.00 = **$1.60**. The supplied parameters are proposals, not paid authority.
No limit was increased or silently revised. A compatible revision would require
operator approval, e.g. $0.12/run with $0.50 planning ($1.58 total), or planning
at most $0.25 with $0.15/run. Neither revision has been applied.

## Frozen fixture and evidence

VERIFIED: First fixture in recorded canonical sorted inventory is `merge-intervals`.
The shuffled execution schedule is a different ordering. The exact stored hashes
were printed before the coding evaluation:

- frozen.json SHA-256: `9d71a3317b9e0531af7c6dee66c8ba6ad70a36b6bd7be0ccc0ee8fb997b90c30`
- objective: `398849811813d1415586b86e9c27107cc8e4addd70da06af2fff135ee866e2aa`
- initial solution: `bebc624a42d606c9614702861d999c46f1359b7d4fedda0f0773bb5a6c061d93`
- acceptance: `a3f8ad73b23cadea8e5a196e720f7d0f621ea3240591636680b6b3610dcbb73c`
- derived fixture fingerprint (not a pre-existing stored fixture hash): `1618bc5acc2627e2f2574cc05266a4821db736ec0690594e60fc8def2ae3fe33`

VERIFIED: `offline-readiness-observations.json` contains sanitized coding, native,
security and recovery observations, complete synthetic ledger snapshots and
SHA-256 pointers to VM-local original evidence. No private keys, credentials,
auth files, raw provider records or synthetic human approvals are included.
Stub framing was inspected against installed OpenAI 7.19.0 SDK declarations:
`resources/chat/completions/completions.d.ts` (ChatCompletionChunk) and
`resources/completions.d.ts` (CompletionUsage). This is not real-provider fidelity.

## Reproduction commands and results

VERIFIED environment: Linux 6.18.57; Python 3.12.14; Node v24.22.1;
Git 2.52.0; bubblewrap 0.12.0; prepared native PostgreSQL 15.18.0 runtime.
The ICU package SHA-256 is
`f01f61f57e63dc905e02e6441d10370fe0c79e43e70e6f5fe24b342fd2633209`.
Libraries are supplied through a rootless verified dependency directory, not
fake libraries or production source changes. Runtime starts use the existing
`fusion-phase2a-pilot` ledger and unchanged three-starts/hour limit.

```sh
python -m unittest discover -s evals/controlled-coding -v  # 28 passed
python -m unittest discover -s evals/planning-collector -v # 37 passed
python -m unittest discover -s evals/persistence -v        # 9 passed
python evals/controlled-coding/harness.py verify          # passed
python evals/planning-collector/offline_runner.py --security-probe NEW_DIR
# 30 passed outside the agent sandbox using previously authorized commands
python evals/controlled-coding/offline_eval.py --runtime PREPARED_RUNTIME --output NEW_DIR
# correct fixture: agent exit 0, 4/4 acceptance checks passed
# --variant wrong and --variant tamper: independent acceptance rejected both
python evals/controlled-coding/recovery_checks.py --runtime PREPARED_RUNTIME --output NEW_DIR
# kill + abort passed; four attempts each; interrupted exposure never released
python evals/planning-collector/offline_runner.py --scenario comprehensive \
  --runtime PREPARED_RUNTIME --rate-ledger EXISTING_DURABLE_LEDGER \
  --max-starts 3 --native-library-dir VERIFIED_RUNTIME_NATIVE_LIB_DIR
# native exit 0; 5 accounted attempts; compaction not_completed
python evals/controlled-coding/live_preflight.py
# LIVE_REFUSED, expected: not authorized, arming conflict, missing live integration
```

VERIFIED: Early development checks exposed a mount-on-symlink issue and a recovery
test querying lifecycle state in the wrong table. Both were corrected under evals
and their relevant checks subsequently passed. The second identical Arm A run was
**not executed** because automatic approval review reported its usage limit;
this was a review-service failure, not an unsafe-action determination. No approval
bypass was attempted. The current sandbox cannot perform namespace creation, so
its live-preflight current-isolation check correctly refuses despite the earlier
outside-sandbox security proof. No readiness claim substitutes that earlier proof.

## Exact remaining actions

VERIFIED blockers and required next actions:

1. Operator supplies compatible allocations satisfying the unchanged 80% gate.
2. When approval review is available, rerun the identical Arm A profile and compare
   normalized candidate, grading and ledger results; add protocol-specific positive
   controls, then rerun the current ENFORCED/canary probe in the authorized context.
3. Diagnose native compaction's not_completed status under the strict contract;
   test its actual HTTP attempts and deadlines without relaxing limits. Validate
   the approval callback against native question/submit APIs with labeled test
   fixtures, then complete the shared-ledger live planning integration under evals.
   The live preflight intentionally retains an explicit integration blocker.
4. Before separately approving paid work, verify availability of the exact
   deprecated model, confirm the supplied prices, prepare a dedicated provider key
   with provider-side spending cap, store it privately in the gateway zone, and
   provide a private expiring authorization file naming only api.openai.com.
5. Conduct new interviews through that controlled pipeline only after separate
   paid authority. Operator approves each new verbatim answer out of band with
   APPROVE <answer-hash>. Historical Phase 2M approvals cannot be invented/reused.
6. Run the single read-only preflight with explicit --live-transport,
   --authorization FILE and --approvals-manifest FILE. It must refuse until every
   prerequisite is independently satisfied. It never starts a run or authorizes
   spending. Recommend a first separately authorized tiny canary capped at $0.001,
   using a smaller defensible token bound and the same planning/aggregate ledger.

UNVERIFIED: Full persistence success, live schema, model availability and coding
performance. A successful remote code checkpoint does not back up private raw
artifacts or demonstrate paid readiness.
