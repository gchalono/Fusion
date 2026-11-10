# Phase 3 real-model readiness — BLOCKED

Provider requests/spending this phase: **0 / $0.00**. No production or historical
result/prompt/approval/seed changes. Claims below are VERIFIED locally unless marked
UNVERIFIED/BLOCKED. Scripted responses do **not** demonstrate real-model ability.

## Restore and persistence

Pinned clean dev9afbac61342d18a59b0d1cdd1111d6ef736f82c5 and ancestor b3bc7b0 verified;
runtime eb7eef49d5a0fe3e84e99be30e8ed9622a694e35 clean. Read the five prior reports:
BROWSER_ACCEPTANCE_FINAL, PRIVATE_REMOTE_RECOVERY_FINAL, FIRST_REAL_MODEL_PILOT_PROPOSAL,
TASK_MANAGER_FULL_CONTRACT_RESULT, ORIGINAL_EVALUATOR_INTEGRATION. Restore receipt:
/workspace/phase3-readiness/restore.json. All35 frozen-input hashes,122 historical
manifest entries,8 approval bindings, seed identity, accepted five-file hashes,
original evaluator hashes and budget settings verified. Approved token revision
remains offline-only, defaults unchanged. No browser acceptance rerun: accepted
patch, evaluator, browser runtime and isolation/filter bytes unchanged.

Initial remote2963d4771debf153690d125507db721e956a6a6b independently confirmed.
Milestone sourcea8bfadda79117edb8a6e3a977f6358e6521cb5be maps to independent remote
598d39f7a07ce63c507f7a5dabd678f7bc59deb2. Source-only GitHub archive downloaded twice,
identical SHA2564aba2da64a3c996b8bd6539b1d2e865fb80abe29c335840c01b1f56126fc8261.
No additional archive uploaded. Only allowlisted/scanned source Git blobs published;
full reachable sanitized history scanned by backup/verify.py. Original ancestry never
published. Terminal mapping/scan/recovery lives in backup SOURCE_MAP/CHECKPOINT_INDEX
and the terminal receipt, independently fetched SHA reported to operator.

Backed up: safe source/tests/manifests/public objective/common instructions and state.
Omitted from public: keys, tokens, sessions, live DBs, raw approvals/provider evidence,
unclear runtime files. Local-only: original recovery bundles and three private archives,
all checksum-verified against prior reports. No authorized protected destination or
key-custody configuration exists; external private recovery remains BLOCKED. Step1
initial source backup/archive verification finished inside30-minute timebox; private
omissions are deliberate, not silently treated as remotely recoverable.

## Local model/API check (no provider network)

VERIFIED configured exact ID gpt-4.1-mini-2025-04-14 in experiment-parameters.json and
coding-agent.mts. Fusion custom-provider mapping is
packages/engine/src/auth/custom-provider-registry.ts:47-58: openai-compatible maps to
openai-completions. Shared native Pi registration accepts the explicit model; actual
local wire confirms Chat Completions messages/tools/stream/max_tokens. Fusion sandbox
uses http://127.0.0.1:39777/v1; broker fixes upstream
https://api.openai.com/v1/chat/completions; LOCAL transport substitutes only loopback
TLS. This custom-provider path is distinct from installed Pi's default OpenAI Responses
provider. No substitution or catalog assumption. Native tool/retry path verified locally;
real provider acceptance, project access and continued dated-model availability UNVERIFIED.

Configured operator-supplied prices: input$0.40/M, cached$0.10/M, output$1.60/M.
Current official prices UNVERIFIED (config provenance operator_supplied_not_fetched).
Historical supplied context1,047,576/output32,768 and deprecation are supplied evidence,
not freshly verified. Effective experiment limits32000 conservative input units and
4096 output are VERIFIED local settings, not claimed provider catalog maxima. Byte
bounds are not provider token measurements. Exact future authorization:
`AUTHORIZE_METADATA_CHECK` — official documentation plus non-inference project/model
metadata only; no inference. No alternate model needed for local integration; recommend
no substitution while actual availability is unknown.

## Pipeline and budget evidence

126 local units pass:78 controlled-coding,37 planning-collector,11 persistence;
zero local failures/skips. Logs /workspace/phase3-readiness/*tests*.log retain exact
runs. Eleven-case native matrix /workspace/phase3-validated-native/matrix.json plus
separate final full /workspace/phase3-terminal-full and monetary exhaustion
/workspace/phase3-aggregate-validated. Native matrix contains31 LOCAL TLS requests;
these are not provider usage/cost. Other diagnostic/failed attempts remain separate.

| Case | Verified observation |
|---|---|
| Full native Arm A |4 requests; exact accepted five-file/mode patch;9 non-browser checks pass|
| Request-cap mid-run |4 upstream requests; fifth refused; incomplete, terminated-by-budget; evaluator still runs|
| Monetary aggregate mid-run |Synthetic prior1980000 micro-USD;2 new requests18723; exposure1998723; next rejected; partial graded and correctly fails|
| Parallel tools |Two independent writes through actual native tools;2 requests|
| Malformed/partial JSON arguments |Native tool errors, no invented writes; final local stop;2 requests each|
| finish_reason=length |Native length stop; no successful-completion claim;1 request|
| Oversized tool output |Native tool truncation/bounded subsequent input;2 requests|
| Nonterminating tool loop |4 requests; next denied; no completed-loop claim|
| HTTP429/500 |Native retries retained;4 upstream requests each, all reserved|
| Compaction |Default SESSION_TOO_SMALL; separate explicitly synthetic eligible control completes;2 requests; native summary limit2048 preserved|

Compaction control temporarily reduces retained tail ONLY in an explicitly marked
disposable local control. It is not a paid setting or proof that a real run will
compact. No paid-path settings changed. Gateway buffers bounded SSE responses; frame
content survives but incremental real-time delivery is not claimed. Unit tests cover
nonstreaming/streaming/missing usage, actual TLS errors/timeouts, crash after dispatch,
restart recovery, concurrent atomic admission, per-run fifth refusal, aggregate cap,
unapproved model/endpoint, synthetic credential reflection, actual namespace/proc/env/
egress boundaries and process-tree cleanup. Interrupted SSE carrying usage now stays
UNCERTAIN unless DONE terminator is present. Reservations are NEVER refunded; reliable
usage is recorded separately and SETTLED, retaining worst-case exposure. Conservative
no-refund settlement fits this pilot; usage is not fabricated as measured billing.

Historical budget-events.json is read-only reconciled:5341 prior +6181 rounded
interview micro-USD =11522 retained. Source SHA256
ef94225c9875d424c6b878eac22c7905c6c411b13585d1c9cce973af2f491744.
Detailed receipt history-reconciliation.json. No original ledger reset/migration.
This verifies frozen history, NOT a live authoritative shared-ledger connection.

Per-request worst case at configured prices:
ceil(32000*0.40 +4096*1.60)=19354 micro-USD.
Four=77416 ($0.077416), below$0.12. With frozen retained11522, exposure88938
($0.088938), below$2. Cached savings never assumed. Total input+output upper144384;
300s total/60s per request/four attempts including retries and compaction unchanged.
Actual current-pricing worst case UNVERIFIED until authorized metadata verification.
The768 profile explicitly rejects paid/production;4096 readiness profile also LOCAL-only.

## Repairs and security

Evaluation-only changes: explicit local4096 profile; failure-double hooks and native
rehearsal/preflight; correct model-error versus OS exit0 completion classification;
applicable patches for partial/empty files; fixed-code denial evidence; incomplete-SSE
settlement guard. Newline serializer preserves accepted full candidate's patch hash.
No security_filter/isolation/evaluator assertions/frozen source changed. Failed early
collector/partial-patch attempts retained, not overwritten or represented as passes.
No new agent framework. No mission/task/autopilot creation.

Actual sandbox probes: provider env names absent; host/workspace/home/hidden tests
absent; host processes not visible through PID namespace; direct egress denied;
owned descendant cannot write after timeout. Generated LOCAL key reflection is rejected
and captured output scanned against generated keys. No real API-key value read.
Runtime metadata reports OPENAI_API_KEY configured, but this does NOT prove only a
future gateway can read it. Existing broker children have minimal env; future live
credential handoff and real-key-exclusive ownership remain UNVERIFIED. Public recovered
suite explicitly skips two outer-executor namespace probes: mandatory outer filter
forbids nested unshare. They pass on actual outer executor; skips are not passes.

## Exact blockers

1. Current official pricing/API/model/project availability needs AUTHORIZE_METADATA_CHECK.
2. Existing coding CLI is strictly TEST MODE. No reviewed live supervisor command binds
   ONE run/exclusive admission, exact source/config, existing authoritative historical
   ledger and real transport. Do not rename a local profile into live authorization.
3. Live gateway-only credential provisioning/ownership is unverified; no real key read.
4. Private essential evaluator/approval/evidence dependencies still lack authorized
   protected off-environment storage and independently tested external recovery.
5. Capture allowlist currently rejects JSON/MJS/SQL source artifacts. A valid non-Python
   implementation could fail collection; review this evaluation interface before live
   approval, without changing frozen task requirements or weakening content/security checks.

Local pipeline/security evidence is strong; **READY_FOR_PAID_PILOT is not established**.
No paid command is invented. FIRST_REAL_MODEL_RUN.md records exact available commands,
prospective authorization and stop conditions. Frozen artifact: PHASE3_FROZEN.md.
