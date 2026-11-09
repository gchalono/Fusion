# Lightweight persistence

Baseline supplied independently by operator:
`9736d67e40c8656b56206eafd6b7bc615c1c5c3f`.

```sh
evals/persistence/preflight.sh --baseline "$EXPECTED_SHA" --branch eval/phase2n
evals/persistence/checkpoint.sh --baseline "$EXPECTED_SHA" --branch eval/phase2n
# Explicit local validation / commits / network write, respectively:
evals/persistence/checkpoint.sh --baseline "$EXPECTED_SHA" --branch eval/phase2n --validate
evals/persistence/checkpoint.sh --baseline "$EXPECTED_SHA" --branch eval/phase2n --commit
evals/persistence/checkpoint.sh --baseline "$EXPECTED_SHA" --branch eval/phase2n --push
```

Preflight fetches only the exact authorized fork branch, verifies the external
baseline/remote tip, cleanliness, documents and required artifact hashes.
REMOTE_BASELINE_UNVERIFIABLE is a failure, never an assumed up-to-date checkout.
Missing Phase 2M is a warning. Preflight never changes content or local branches.
Checkpoint's default dry run scans/displays operations; fetching remote refs is
its only repository mutation. --commit runs all evaluation offline unit suites,
commits eval-only implementation changes if present, then commits a record of
the validated implementation. --push is separate and never force pushes. Passing
unit tests does not imply fresh native integration or remote recovery succeeded.

Before pushing, inspect every introduced artifact and scan all commit versions.
The built-in scanner supplements manual review; it is not a comprehensive secret
scanner. No gitleaks/trufflehog was installed at the initial validation. Every
reviewed log/fixture hash is specific to manually reviewed non-sensitive offline
data; do not approve hashes for genuine provider records or private information.
Raw snapshots and evidence remain outside Git. No secure encryption recipient
was configured, so no encrypted sensitive archive was created or uploaded.

Fresh recovery: clone the fork if backed up, otherwise clone an independently
created bundle. Never clone the active worktree. Use a clean environment without
provider variables, a new HOME, and no .env files. Python 3.12+ and Git suffice
for unit tests; no network installation is needed. The native offline integration
additionally needs Linux bubblewrap, Node and pinned pnpm dependencies/builds:

```sh
pnpm install --frozen-lockfile  # pinned pnpm 10.33.0; requires registry access
python evals/planning-collector/offline_runner.py --scenario comprehensive \
  --rate-ledger /path/to/reused-private-offline-starts.json
python evals/planning-collector/verify_evidence.py NEW_EVIDENCE_DIRECTORY
```

The source checkout is discovered from the runner, not /workspace. Reuse the
same external start ledger across retries (five starts/hour). Do not inherit
credentials or mount the old worktree's untracked artifacts. Missing dependencies
or restricted namespaces are environment limitations, not passing native tests.
Do not install dependencies with unreviewed lifecycle scripts or start services
outside the existing explicitly offline harness. See the persistence report for
what was actually reproduced; installation instructions alone are not evidence.
