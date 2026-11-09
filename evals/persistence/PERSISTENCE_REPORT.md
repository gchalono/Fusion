# Persistence and recovery report

Overall status: **PERSISTENCE_FAILED** — the attempted native recovery did not
complete. Its concrete environmental cause is missing ICU 60 shared libraries;
all offline unit suites passed. Remote backup independently remains incomplete
because fork write access was denied HTTP 403. No paid inference or live coding.

## Four persistence dimensions

| Dimension | Verified result |
|---|---|
| Local snapshot | Completed: independent refs bundle, patches, non-sensitive untracked archive, inventories and SHA-256 manifest outside worktrees. Same-VM only. |
| Remote code backup | Not verified. Authorized fork push denied 403; independent ls-remote advertised no eval/phase2n branch. REMOTE_BACKUP_INCOMPLETE. |
| Sensitive-artifact backup | Not verified. Raw native mock evidence/private artifact inventory remains VM-local; Phase 2M evidence is missing. No upload or encryption key invented. |
| Fresh-environment recovery | Bundle clone and 56 unit tests/hash checks succeeded. Native integration environment reconstruction failed; fresh GitHub recovery was impossible. |

## Repository and implementation

Minimum Phase 2N baseline: `9736d67e40c8656b56206eafd6b7bc615c1c5c3f`.
Validated persistence implementation: `db6cf1deacbbb7c38ebcfa663062cd2bde7fa71d`.
Its preceding implementation is `15fad6de69f42565e9e230e5edd08a649a401b0d`.
The separate checkpoint record `a75e7e7b6badcf1a5d631e502405f9f3dd833de4`
references the validated implementation, avoiding a circular self-SHA.
Branch/worktree: eval/phase2n, /workspace/work/fusion-phase2n.
No new commits are confirmed on GitHub; there is no verified remote branch tip.
All persistence work remains local until write access is restored.

Added evals/AGENTS.md, PROJECT_STATE.md, CHECKPOINTS.md, artifact-manifest.json,
read-only preflight, explicit dry-run-first checkpoints, hash-based artifact
verification and whole-introduced-history/index/worktree secret checks. Native
offline runner now resolves its own checkout and requires an explicit reused
start ledger. Root AGENTS.md and production application behavior are unchanged.

Snapshot path: /workspace/work/persistence-snapshot. Initial bundle includes all
available refs before edits; later bundles preserve persistence checkpoints.
Initial tracked changes/untracked files/stashes were absent in all three worktrees.
Snapshot inventory records branch/HEAD, remotes, worktrees, branches, reflogs,
stashes and environment versions. Git 2.52.0, Python 3.12.14, Node 24.22.1,
pinned pnpm 10.33.0; PATH pnpm 11.25.0 was not used for recovery installation.

The exact push URL was verified as https://github.com/gchalono/Fusion.git.
No force/main/upstream/tag push was attempted. Manual artifact review and the
built-in scanner found no secrets among all 61 initially introduced blob
versions or relevant changes. Existing logs are hash-reviewed offline test and
Git metadata, not real provider transcripts. No gitleaks/trufflehog was installed.
A scan is a bounded review, not a general proof that arbitrary content is safe.
The fork push failed with `Permission to gchalono/Fusion.git denied to gchalono`.
GitHub metadata API access also returned Forbidden. No unsafe retry was made.

## Recovery evidence and limitations

Independent bundle clone: /workspace/work/fusion-recovery-3yq6n4j5/repo.
Used fresh HOME and an allowlisted environment without provider credentials or
inherited .env files. No original worktree's dependencies or untracked artifacts
were copied. Python unit suites need only the standard library; no network
installation was required for them. Native dependencies were installed from the
lockfile with pinned pnpm and --ignore-scripts; this required registry network
access and completed successfully. Core and engine builds both passed.

Unit results: 14 controlled-coding + 33 collector + 9 persistence = **56 passed**.
Manifest hashes and frozen fixtures verified. Tests demonstrate stale checkout
rejection, independent full baseline enforcement, remote-unavailable failure,
upstream push-URL rejection, dirty/mismatched artifacts and history/index secrets.
New agents can read the state documents and identify the next task without chat.

Preflight exited 1 solely for REMOTE_BASELINE_UNVERIFIABLE in the clean recovered
clone: the remote eval branch does not exist. Missing Phase 2M was a warning,
not an artifact-validation failure. Local-only checks were not represented as
successful remote preflight or fresh GitHub recovery.

Native recovery failed in three recorded stages:

1. Missing @fusion/core dist outputs after a clean dependency install. Resolved by
   successfully building @fusion/core and @fusion/engine in the recovered clone.
2. Embedded PostgreSQL attempted chmod on a read-only namespace dependency.
   Prepared required executable permissions before re-entering the namespace.
3. PostgreSQL failed loading `libicui18n.so.60`. Compatible ICU 60 runtime remains
   an environment prerequisite; no incompatible-library workaround was used.

The reused native-start ledger reached five starts/hour. No reset, alternate
identifier or extra interview start was used. Native request/response generation
did not begin in these failed starts. This is an environment reconstruction
failure, not an acceptance-test assertion or a measured coding outcome. The
historical native pass on the old VM setup is not fresh recovery evidence.

Logs/summary: /workspace/work/persistence-snapshot and
/workspace/work/fusion-recovery-3yq6n4j5. Failed raw native captures remain private
under their generated temporary directories; private inventory is local-only.
A final bundle-based smoke recheck and hashes are recorded in the local snapshot.

## Artifact preservation and exact next steps

Code, fixtures, hash manifests, offline summaries and instructions are in local
Git/bundles. Raw mock evidence, private inventory and all bundles remain on the
temporary VM. GPG is installed, but no approved encryption recipient or secure
key-handling method was configured, so no sensitive encrypted archive was made.
Provide an authorized private durable destination and encryption recipient before
backing up restricted artifacts; do not publish them to the fork.

Phase 2M still missing: original implementation/supervisor, original objective and
baseline, native MissionPlanSummary, eight explicit human approvals/transcript,
nine provider request/response records, accounting and audit/provenance evidence.
No repeated exhaustive search or fabricated recovery was performed.

Minimum next persistence task: restore fork write access. Then execute:

```sh
evals/persistence/checkpoint.sh \
  --baseline 9736d67e40c8656b56206eafd6b7bc615c1c5c3f \
  --branch eval/phase2n --push
git ls-remote https://github.com/gchalono/Fusion.git refs/heads/eval/phase2n
```

Independently clone the confirmed remote tip into a clean environment and run
preflight/unit tests. Supply compatible ICU 60 libraries before the next eligible
native offline test. No remote persistence claim is valid until those steps pass.

After persistence: recover the Phase 2M bundle/evidence, then integrate the shared
ledger with its supervisor and prove gateway-only egress with bypass tests.
Gateway bypass prevention remains unresolved. Live coding token/time limits,
plan/approval binding and measured end-to-end results remain incomplete.
No paid inference, missions or live experiments are authorized by this task.
