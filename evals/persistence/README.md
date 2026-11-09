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
pnpm install --frozen-lockfile --ignore-scripts  # pinned pnpm 10.33.0; registry access
pnpm --filter @fusion/core build
pnpm --filter @fusion/engine build
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

Recovered native runtime findings: installation and both package builds succeeded.
Before entering the read-only namespace, installed embedded-postgres native/bin
executables need their read/execute mode bits (a+rx). The recovered host then
failed loading libicui18n.so.60. Supply compatible ICU 60 runtime libraries
through supported environment/package setup; do not substitute incompatible ABI
symlinks or relax namespace isolation. Retest only after the existing shared
five-starts/hour ledger permits another start. These are recorded environment
requirements, not evidence of a passing native recovery.

## ICU 60 recovery clarification

The failing binary is the pinned `@embedded-postgres/linux-x64` PostgreSQL 15.18.
The earlier working checkout contained ICU 60 libraries in its native/lib, with
`libicuuc` RUNPATH `$ORIGIN`. This dependency setup was not in Git. The fresh
package installation omitted ICU; Debian 13 does not provide this old ABI by
default. Do not copy untracked libraries from an older worktree.

A verified rootless alternative is the genuine Ubuntu archive package:

- URL: `https://archive.ubuntu.com/ubuntu/pool/main/i/icu/libicu60_60.2-3ubuntu3.2_amd64.deb`
- SHA-256: `f01f61f57e63dc905e02e6441d10370fe0c79e43e70e6f5fe24b342fd2633209`
- Checksum was compared with Ubuntu's HTTPS bionic-updates/main amd64 package index.

Download/check the package, use `dpkg-deb -x` into a new recovery directory, and
copy its genuine `usr/lib/x86_64-linux-gnu/libicu*.so.60*` files into the fresh
installed PostgreSQL native/lib directory. This does not install system packages
or modify production source. With `LD_LIBRARY_PATH` set to that directory, both
`postgres --version` and `initdb --version` passed (15.18), and the missing ICU
libraries resolved. Standard package symlinks are genuine ABI aliases, not fake
shared libraries. This validates loading, not the full native integration.

Pass that same explicitly verified directory into the existing namespace:

```sh
python evals/planning-collector/offline_runner.py --scenario comprehensive \
  --rate-ledger /path/to/reused-private-offline-starts.json \
  --native-library-dir /fresh/checkout/node_modules/.pnpm/PACKAGE/native/lib
```

Resolve PACKAGE from the actual pinned install; the directory must be inside the
current checkout. This optional flag sets only LD_LIBRARY_PATH after clearenv;
network isolation, read-only source and five-starts/hour accounting stay intact.
Do not reset the ledger. Full native revalidation remains pending an eligible start.
