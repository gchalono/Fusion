# Phase 2N offline implementation report

Status: **blocked on Phase 2M recovery; experiment not executed**. No paid API
requests, live coding runs, fabricated approvals or replacement supervisor.

## A. Repository state and recovery

Inspected all local refs, tags, three worktrees, reflogs, all reachable commit
messages, evaluation path history, unreachable objects, available evidence
folders and the advertised remote heads/tags.

- Primary `/workspace/Fusion`: branch `work`, commit `eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`.
- Existing `/workspace/Fusion-phase2a`: `eval/phase2a-collector`, commit `3d92a302853c32472d2420d3835200ecc469905f`.
- Preserved Phase 2N worktree `/workspace/work/fusion-phase2n`: branch `eval/phase2n`, based on the Phase 2A commit.
- Origin is `https://github.com/gchalono/Fusion.git`. `git ls-remote --heads --tags origin` advertises only `main` at `eb7eef49d…`; no remote tags. No local tags.
- Phase 2A adds three local commits: `98bf91c7a`, `cf2c6549a`, `3d92a3028`. No Phase 2M commit found in refs/reflogs or reachable message/path searches.
- Full, non-shallow object store: fsck found seven unreachable blobs, no unreachable commits. Scanning those blobs found no Phase 2M markers.
- No Phase 2M artifacts found in searched workspace paths. The supplied request describes successful measurements but does not contain their underlying artifacts.

These findings cover the available repository and advertised remote refs, not
unavailable machines, deleted remote refs, or unknown commit hashes.

## B. Components implemented

Preserved three frozen fixtures, their independent acceptance tests, hashed
manifest, fixed seeded nine-run order, configuration-specific input builder,
null-preserving machine-readable dry-run results and reproduction instructions.

Completed the offline shared ledger and attached reservation guard for the
existing Gateway. SQLite BEGIN IMMEDIATE/FULL transactions enforce a $2 aggregate
exposure cap across processes/restarts and $0.15/four-request coding limits.
Every guarded HTTP attempt, including planning and retries, reserves before
transport. Audit/storage failures terminate the gateway before forwarding.
Committed reservations have no refund path, including uncertain responses.
Append-only observations distinguish raw usage, estimated charges and measured
charges with evidence references. No new supervisor was implemented.

These are offline components, not a completed native execution harness. Native
plan import/provenance validation, trusted run registration, coding-stage token
enforcement, live routing, code diff capture and live report generation still
require integration with the recovered supervisor.

## C. Validation and failures

- Phase 2N: **14 tests passed**, zero failures. Includes 20 concurrent processes
  admitting exactly 13 × $0.15 reservations ($1.95), restart persistence,
  per-run limits, process exit after commit, retry exposure, SQL immutability,
  accounting separation, database/audit failure before transport, arm inputs,
  freeze tampering, dry-run preservation and fixture positive/negative controls.
- Existing collector: **33 tests passed**, zero failures.
- Python compilation, frozen-manifest verification and Git whitespace check passed.
- Existing comprehensive native offline integration passed, then evidence was
  independently reverified: seven local mock HTTP attempts, native retries and
  compaction, no external route, direct mock bypass rejected, only the expected
  `project.ai_sessions` database table changed, services stopped successfully.
- First integration attempt failed with `bwrap: setting up uid map: Read-only file system`.
  A permitted retry outside the agent sandbox succeeded; no test was bypassed.
- The native mock uses legacy synthetic pricing and a $100 test policy: its
  $6.128640 reserved estimate is synthetic exposure, not provider spending and
  not a Phase 2N cap test. Shared-ledger integration is tested separately with
  fake transports. No actual provider endpoint was called.

All new/collector offline unit tests were run. The full Fusion product suite and
all seven native integration scenarios were not rerun; the comprehensive native
scenario covers retries, compaction and routing without consuming more starts.

Machine-readable status and logs are in `evidence/`; nine dry-run rows are in
`dry-run/results.json`. Native raw evidence remains at
`/tmp/fusion-native-offline-ozqq14o_`; its verifier summary is copied to evidence.

## D. Requirements before safe live execution

Supply the exact Phase 2M commit or Git bundle (including unpushed history), and
its supervisor/gateway configuration and launch instructions. Supply original
objective and repository baseline, native MissionPlanSummary, full ordered
question/answer transcript with all eight explicit human approvals, raw nine
request/response records, usage/cost records and audit/provenance hashes. No
specific missing commit hash can be inferred from the current checkout.

After recovery, verify gateway-only provider egress for every native operation.
Coding sandboxes must have no provider credentials or proxy route that bypasses
the gateway, no ledger write access, no acceptance tests and no other-arm data.
Negative bypass tests must establish these properties before live is enabled.
A Python guard alone cannot prevent an unguarded provider request.

Verify model-specific maximum charge bounds/current rates, attach the common
ledger to every planning/coding attempt and account separately for historical
Phase 2M planning costs. Determine whether that existing plan matches any frozen
task; do not reuse it merely because it succeeded. Obtain genuine native plans
and explicitly approved answers for unmatched tasks after paid approval. Enforce
identical coding token/time/permissions limits, register trusted run IDs, persist
full audit artifacts and derive final results from independent acceptance tests.

## E. Exact next steps and evaluation status

1. Recover the Phase 2M commit/bundle and evidence listed above. Inspect it before
   changing or replacing any missing execution infrastructure.
2. Integrate this ledger with its existing supervisor; test bypass rejection,
   reservation/transport ordering and interrupted restart recovery end to end.
3. Validate planning artifact compatibility, provenance and approvals; finish
   frozen task/run bindings, isolation and measured results aggregation.
4. Present the concrete live command, verified maximum exposure (at most $2),
   remaining limitations and offline evidence; request explicit paid approval.

Correctness improvement, incremental transcript value, least-resource arm and
whether planning costs outweigh savings are **all inconclusive: no experimental
arm has run**. Next implement recovery and integration, not architectural expansion.
The three pure-function tasks are candidates for free Stanford AI Playground
inference if available; that is a separate experiment requiring matched controls,
and does not replace this native-pipeline evaluation.
