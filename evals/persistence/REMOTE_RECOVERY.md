# Verified remote code backup and recovery

GitHub reconnection resolved the write blocker. The reviewed eval/phase2n branch
was pushed to https://github.com/gchalono/Fusion.git and independently confirmed
with git ls-remote at:

`2d5e2577b822e72bc1abc99d9a6db5fa9544af7a`

This contains validated implementation
`463bf2a3d1538f3a5c141df474993cee835fa40e` and the original Phase 2N baseline
`9736d67e40c8656b56206eafd6b7bc615c1c5c3f`. Later documentation-only tips record
this verification; obtain the latest branch pointer independently. No circular
self-SHA is embedded in a checkpoint commit. Historical 403/failure reports remain
preserved and are superseded by this report for current backup status.

## Fresh remote verification

Cloned eval/phase2n directly from GitHub into a new directory, without a local
object reference, copied dependencies, inherited .env files or original worktree
artifacts. Validation ran with a fresh HOME and an allowlisted environment that
excluded provider credential variables.

- Recovery preflight: PASS, including external baseline, exact remote tip, clean
  tree, state documents, required artifact hashes and optional Phase 2M warning.
- Controlled coding: 14 tests passed.
- Planning collector: 33 tests passed.
- Persistence: 9 tests passed.
- Frozen input verification: PASS. Total: 56 passed, zero unit failures.

Python recovery required no dependency installation. Native prerequisites were
separately reconstructed in that remote clone: installed pinned pnpm 10.33.0 into
its fresh HOME, installed lockfile dependencies with --ignore-scripts, and built
@fusion/core and @fusion/engine. Registry network access was required. All steps
passed without using the earlier worktree's untracked dependency artifacts.

Prepared installed PostgreSQL binary permissions before the read-only namespace.
Supplied genuine ICU 60 files from the checksum-verified Ubuntu package described
in README.md. With the explicit dependency library path, postgres and initdb
--version both passed (PostgreSQL 15.18) in the remote clone. No system package,
production source or incompatible library symlink was changed.

Full native interview integration is still pending the existing five-start/hour
window. The earliest eligibility observed was 2026-11-09 04:54:58 UTC; always
consult the real reused ledger before starting. No counter, identifier or window
was reset. Dependency/binary checks are not full native integration evidence.

## Persistence dimensions and limitations

- Local snapshots: complete, with full and reviewed incremental bundles preserved.
- Remote code backup: VERIFIED at the SHA above; non-sensitive code, fixtures,
  manifests and reports are off the temporary VM on the authorized fork.
- Sensitive-artifact backup: NOT VERIFIED. Raw mock evidence/private inventories
  remain VM-local. Phase 2M evidence is still missing; no sensitive upload occurred.
- Fresh remote recovery: preflight, all 56 unit tests and artifact checks VERIFIED.
  Native environment setup/loader checks passed; full native integration PENDING.

The earlier chat output-folder permission failure no longer blocks code
preservation: GitHub now provides its durable copy. The reviewed incremental
bundle is an additional local fallback, not a claimed off-VM artifact backup.

## Reproduce and continue

```sh
git clone --single-branch --branch eval/phase2n https://github.com/gchalono/Fusion.git
cd Fusion
evals/persistence/preflight.sh \
  --baseline 9736d67e40c8656b56206eafd6b7bc615c1c5c3f \
  --branch eval/phase2n
python -m unittest discover -s evals/controlled-coding -v
python -m unittest discover -s evals/planning-collector -v
python -m unittest discover -s evals/persistence -v
```

Native setup/retest instructions are in README.md. Next: perform the existing
native comprehensive integration when its reused ledger allows, independently
verify evidence, then obtain the missing Phase 2M implementation/artifacts.
Gateway-only egress remains unproven; no paid inference or live coding experiment
is authorized. Sensitive-artifact preservation still requires an approved private
destination and secure key handling.

Local evidence (not relied on for fresh code recovery):
/workspace/work/blocker-resolution/remote-first-summary.json,
remote-native-environment.json and their test/install/build logs.
