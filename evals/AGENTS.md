# Evaluation recovery instructions

Before editing, obtain the expected full implementation SHA from the operator or
an independently verified remote checkpoint. Run:

```sh
evals/persistence/preflight.sh --baseline FULL_SHA --branch eval/phase2n
```

Read PROJECT_STATE.md, CHECKPOINTS.md and artifact-manifest.json. A stale checkout,
missing required artifact, dirty tree or unavailable remote verification is not
a successful recovery. Phase 2M is missing; report it as a development dependency
without failing Phase 2N persistence solely for its absence. Never reconstruct
its plan, answers, approvals or measurements from assumptions.

Work only on `eval/*` or `wip/*` branches in isolated worktrees. Leave root
AGENTS.md unchanged. Never reset hard, clean, force checkout/push, rebase, merge,
prune, delete worktrees/branches or create tags for this workflow. Never push
main or upstream. Verify fetch AND push URLs refer to gchalono/Fusion; a remote
name alone is insufficient. Fetch and independently compare remote tips.

Do not print credentials or commit .env files, auth files, raw provider records,
transcripts or sensitive logs. Run scan.py over every introduced commit version
and current changes. Hash-reviewed artifacts must be manually inspected before
adding hashes to reviewed-artifacts.json; an allowlist entry is not authorization
to publish sensitive information. Stop on a history secret; do not rewrite it.

No paid inference, live coding runs, missions or autopilot without explicit human
approval. All provider operations must pass a gateway reservation before transport.
Gateway-only egress remains unverified: never infer it from the Python guard.
Keep real credentials, ledgers, hidden tests and other arms out of coding sandboxes.

Checkpoint tooling defaults to dry run. Use --validate for offline tests,
--commit for explicit eval-only implementation and checkpoint commits, and
--push only when authorized. No auto-push hooks/jobs. A checkpoint record references
a preceding validated implementation, never itself. Preserve failed work as
unvalidated. A 403 means REMOTE_BACKUP_INCOMPLETE; fix fork write access before retry.

Verify GitHub persistence with git ls-remote, then recover into a new directory
from the fork. If unavailable, use an independently created Git bundle and label
recovery local-only. Same-VM snapshots are not durable storage. Distinguish local
snapshot, remote code backup, sensitive-artifact backup and fresh recovery.
Report only measured test outcomes; native offline mocks are not genuine plans.
