# Sanitized Fusion recovery

This branch is a history-free SOURCE snapshot, not the original development ancestry.
Initial root source checkpoint: b3bc7b0dc6c2751bb3b499d9ce6023b3e2c7284c.
Original history and local recovery bundles remain untouched. The old checkpoint and
operational database objects must not exist in this repository. Never merge or fetch
original development history into this backup clone.

`SOURCE_MAP.json` records each included source path, original blob and hash, plus
excluded paths/reasons. Production directories match already-public baseline
 eb7eef49d5a0fe3e84e99be30e8ed9622a694e35. The pattern scanner's reviewed exceptions
are ONLY exact hashes of manually inspected public synthetic redaction/auth test
literals; they are not actual credentials. Changed files require renewed review.
Three reviewed JSONL files are canned synthetic unit fixtures, not provider logs.
No operational DB, credential file, runtime log or original Git metadata is copied.

## Public versus private recovery

All 35 original frozen input hashes were verified before export. Only three safe
inputs are published byte-exact: objective, common instructions and Arm A prompt.
The other 32 are documented in FROZEN_DEPENDENCIES.json by hash and original path.
They include genuine plans/approvals/transcripts/provider evidence and B/C prompts.
**The full genuine experiment CANNOT be reconstructed from this public snapshot alone.**
Restore those byte-exact originals from separately protected archives, never invent
or rebuild approvals. No off-VM private-evidence backup is verified by this branch.

The original evals/artifact-manifest.json is preserved as provenance. It references
some intentionally excluded runtime artifacts. Use `python backup/verify.py` for
sanitized snapshot integrity; do not claim legacy preflight passed or paid readiness.
`python backup/offline_tests.py` records absent private/original-history-dependent
checks as SKIPPED. Run it with no original evidence mounted; dependencies must not
silently bleed in from an older workspace. Python 3.12+, Git, Node and OpenSSL are
needed for offline units. Native agent/runtime builds require locked dependencies.

Engineering state at the initial root (current state is SOURCE_MAP.json plus evals/PROJECT_STATE.md): native Pi Arm A plumbing/repeat/security controls verified
with TEST DOUBLES, but the generated scaffold is intentionally incomplete. Real
Chromium positive reference fails on capset under the mandatory security filter.
The token proposal was NOT ACTIVE at the initial root; later explicitly scoped offline revisions are recorded in evals/controlled-coding/POST_BACKUP_OFFLINE_REPORT.md. No paid inference,
model substitution, mission or autopilot is authorized by any backup operation.

## Checkpoint workflow

Use the sanctioned `backup/publish.py` command after source review and local commit:
before substantial work, after every meaningful milestone, at least every 20 minutes
of active development, before risks/restarts, after blocker resolution and before stop.
An interval due check is agent-driven; there is no daemon, hook or unattended service.
After long operations, checkpoint at the earliest safe opportunity.

Each export copies an allowlisted clean source tree into a NEW repository. The ONLY
permitted parent is the previously verified sanitized backup tip; source commit IDs
are metadata strings, never Git parents. No force pushes, merges, rebases, main or
upstream writes. Changed secret-looking fixtures or new runtime artifacts block export.
Every push must independently fetch/compare the remote SHA. Periodically fresh-clone
and run source-independent offline tests with private artifacts unmounted.

Remote branch: backup/fusion-checkpoints on exactly https://github.com/gchalono/Fusion.git.
Public publication is explicitly operator-authorized. That permission does NOT allow
credentials, private records, provider calls, deployments or frozen-input changes.
