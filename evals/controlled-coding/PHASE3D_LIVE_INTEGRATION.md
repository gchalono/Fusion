# Phase 3D — CONDITIONALLY_READY

VERIFIED: the real executable supervisor completes an end-to-end unpaid rehearsal.
No paid inference was performed. Operator enrollment and current pricing verification
remain external prerequisites; the live command refuses them when absent.

## Actual command and operator procedure

Run from /workspace/Fusion-phase2n-integration, after reviewing the final source SHA:

```bash
python -B evals/controlled-coding/live_supervisor.py prepare --out /workspace/arm-a-spec.json
python -B evals/controlled-coding/live_supervisor.py run --approval /workspace/operator-approval.json --metadata /workspace/verified-model-metadata.json --out /workspace/first-real-arm-a
```

The second command is REAL execution, not a proposal; DO NOT run it until a separate
explicit paid authorization is given. It has no live-flag shortcut. Fresh output paths
are required. Missing/invalid trust,signature,source/config,ledger/anchor,expiry,model,
metadata or credential refuses dispatch. Do not bootstrap a replacement ledger.
All details and exact outside-agent enrollment/signing commands: FIRST_REAL_MODEL_RUN.md.

## Trust boundary

operator_auth.py implements Ed25519 detached verification over the canonical payload:
exact spec plus metadata SHA and explicit existing-transport cap attestation. Spec binds
snapshot,ArmA,objective/seed,source+config hashes,ledger ID,anchor digest,limits,nonce,
expiry. The adapter consumes it atomically and persists single-use/terminal state.
LIVE trust is fixed at /etc/fusion-eval/operator-trust.json with matching operator.pub;
root ownership,no group/other write,no symlinks and Ed25519 DER fingerprint are checked.
Enrollment is performed by the operator OUTSIDE the development-agent boundary.
No live operator private key/trust anchor/approval was created or selected by Codex.

TEST enrollment uses marked private TEST directories and TEST-domain Ed25519 keys.
It cannot enter LIVE. Rehearsal sidecars replay the same original historical anchor,
are explicitly TEST-domain and never replace/reinitialize the authoritative ledger.
The optional TEST-verifier seam preserves the adapter's old HMAC test behavior; the
LIVE verifier remains mandatory. No ledger redesign or new agent framework.

## Actual execution path and implementation

Operator signature -> live_supervisor.py -> existing pilot.make_inference_server
(shared original broker protocol) -> existing Gateway/guard_gateway bound through
HistoryBudget -> existing RealTransport worker -> native Pi session in coding-agent.mts
-> unchanged execution/namespace/seccomp -> source capture -> original evaluator.
MCP disabled; native read/write/bash only,merger purpose,in-memory session,fresh HOME.
No planner interview,TaskExecutor,mission/task creation,autopilot or fallback transport.

One existing ledger owner and one adapter admission decision enforce four underlying
attempts incl retries/compaction,32k conservative input,4096 output,300s coding session,
60s/request,$0.12/run,$2 aggregate. Published configured-rate worst is77416 micro-USD.
Historical11522 is retained once; no re-import. Planning allocation$0.50 unchanged.
Only default service tier is allowed on the approved route; auto/priority/flex are
rejected so the configured default-price reservation cannot silently buy another tier.
Independent post-run grading is separately bounded; it never authorizes model calls.

Fusion's custom-provider registry ignores supplied maxTokens and registers16384.
The runner therefore applies APPROVED4096 through Pi's public setModel API, retaining
same snapshot/provider/context and default retry/compaction logic. The strict broker
rejects output-limit intervention; no silent truncation/clamping on the approved path.
Legacy512/768 paths remain separate and cannot authorize a live run. One legacy native
full-contract regression still produces the exact original five-file patch in4 local calls.

Only the trusted gateway reads the live provider credential, AFTER signature/accounting
and metadata checks. It removes it from its environment and puts it in a sealed anonymous
memfd passed ONLY to RealTransport worker via explicit pass_fds. No provider-key file is
written. No credential FD reaches the coding child; /proc and network are namespaced.
Subprocesses for Git/OpenSSL and coding receive scrubbed environments. RealTransport
checks exact destination,no redirects,response model,secret reflection,size and60s deadline.
Abort is terminal and synchronized with worker creation; PDEATHSIG/die-with-parent
stop descendants on gateway death. Auth/quota/billing errors revoke the gateway;
ordinary native rate retries still count against the same four slots.

## Capture and evaluator

source_capture.py is shared by both supervisors and legacy native collector. It accepts
.py,.js,.mjs,.json,.sql,.html,.css plus existing text/script formats and launchers.
Traversal/symlink/hardlink,special/prohibited paths,setuid,binary and secret content
are refused. Source/file1MB,total8MB/runtime SQLite8MB ceilings fail closed. Valid SQLite
header identifies runtime data: hash+size recorded,never included in a source patch.
No host Git invocation on candidate-controlled configuration. Partial/empty files
retain applicable patch encoding and executable modes. Evaluator assertions unchanged.

The successful rehearsal generated exact accepted patch
 df383ba28a82be9f2a07b36d188a4f4bec11f551f1013634186c3752c2b0ba6c.
All9 non-browser assertions run and pass. The original browser attestation is explicitly
REUSED for unchanged patch/evaluator/browser/isolation; raw evaluator90/completion=false
is preserved,not rewritten as100. Different viable real candidates use the verified
browser dependency and original browser assertions. Browser suite was not rerun here.
Partial candidates still invoke the original evaluator; empty patches can produce a
recorded evaluator exception,not a fabricated grade.

## Measured verification

61 focused unit methods pass (10 approval/capture/broker/descriptor/tier/error,
21 ledger,24 gateway,5 contract,1 TLS transport),zero final failures. Full actual-entry
matrix:15 scenarios pass at code commit aab233755ca008eea05e4ea210554772192c47ba:

| Scenario | Measured outcome |
|---|---|
| Full coding |4 local TLS attempts; native read/write/bash; accepted patch;9 checks pass|
| Cap stop |4 attempts; next refused; partial/evidence retained;evaluator passes9;inconclusive: cap-limited|
| Interrupted stream |4 accounted attempts; incomplete SSE retained as uncertain;no false completion|
| Native credential/egress |2 attempts; actual bash probe succeeds;all6 checks true|
| Crash/concurrent/restart |SIGKILL after first dispatch;other owner rejected;0 owned processes running;1 full retained slot;replay refused|
| Invalid/expired approval |Rejected before dispatch|
| Wrong source/config/ledger/model |Rejected before dispatch|
| Wrong endpoint/missing credential/over-budget approval |Rejected before dispatch|
| Provider auth failure |1 attempt;gateway revoked;no retry/new model call|

Full and cap-stop outcomes are distinct from model capability. Scripted responses do
NOT demonstrate real-model ability. Original journal47/677906 bytes/SHA
9e7953105d6cb33dee33b9982d351e3ee348f78d07096c03a28e9435675a4363,
historical retained11522/unresolved0,authoritative continuation+witness and all35
frozen input hashes are preserved. Authoritative new requests/approvals remain0.

Private logs/receipts: /workspace/phase3d-evidence/;
final real-entry rehearsals: /workspace/phase3d-terminal-rehearsal/.
Initial glue failures and invalid TEST attempts were preserved. A security probe first
incorrectly assumed /workspace absent despite public runtime mounts; corrected to
verify only the allowlisted runtime view and protected-path exclusion,then actual
native tool success/all checks. No isolation weakening. A review-service usage-limit
interruption prevented a command from executing; resumed authorized tests pass.

## Metadata, remaining external prerequisites and limits

One authorized non-inference GET /v1/models/gpt-4.1-mini-2025-04-14 returnedHTTP200,
exact model id. No inference/billing permission is claimed from metadata. Official
pricing documentation unreachable; pricing/context/output/deprecation/API support are
not freshly independently verified. Configured$0.40/$0.10/$1.60 rates are supplied
evidence; live command explicitly rejects pricing_verified=false. See REAL_MODEL_METADATA.md.

Operator enrollment is NOT performed. Required before real execution: operator-controlled
public trust installation; fresh verified pricing/model metadata; truthful signed
provider-side-cap confirmation required by existing RealTransport; explicit paid-run
approval/signature for this exact source/spec. Never send the private signing key to
Codex or install TEST material as LIVE. Do not change caps or substitute models.

This phase: provider metadata requests1; provider inference requests0; actual new
inference spending$0.00. Raw evidence/ledger/private dependencies remain local-only;
public backups contain scanned source/hash receipts,not private records or signing keys.
