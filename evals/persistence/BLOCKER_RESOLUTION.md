# Persistence blocker resolution

Continues from `9334a9dd5d41da2936c33cd704106b13bb52b871`; no history rewrite,
main/upstream/tag push, paid inference, mission or live coding experiment.

## GitHub access

Fetch and push URLs both resolve exactly to
`https://github.com/gchalono/Fusion.git`. No pushurl override or URL rewriting.
Shell Git initially has no credential helper/askpass, stored netrc or git
credentials. GH_TOKEN is configured, but its value was never printed. GH_TOKEN
is used by gh; bare Git does not automatically use that environment variable.
An explicit, in-memory `gh auth git-credential` helper was tested for the exact
authorized branch. Push still returned HTTP 403, denied to gchalono.

The connected GitHub tool independently identifies gchalono and verifies fork
repository id 1445405267, public, not archived. Metadata reports owner-level push
and admin permission, but these describe the user's repository privileges, not
proof of this integration's Contents write authorization. A reviewed real Git
blob upload through that integration was denied 403, “Resource not accessible by
integration.” No remote object or branch was created. The original checkpoint
SHA is also absent from GitHub's commit API (422, no commit found).

Collaborator-permission and branch-rule inspection are denied, so policies cannot
be fully inspected. There is no evidence establishing that branch-creation policy
caused the push failure: the independent Git blob write fails before branch rules
apply. No rule was disabled or bypassed. No fake stale recovery branch was created.

Required user action: update/reconnect the GitHub connection/installation for
**gchalono/Fusion** with **Contents: Read and write**. If this integration cannot
request that permission, supply a write-capable GitHub connection or configure a
fine-grained token for this fork with Contents read/write in environment credential
settings. Do not paste token values into chat. Then retry the existing checkpoint
--push command and verify ls-remote before claiming backup success.

## Sanitized export

A reviewed incremental Git bundle is prepared locally after the final checkpoint.
It includes the complete introduced Phase 2A/2N/persistence history and code,
with exact Git commit identities. It excludes raw non-Git provider/native records,
private artifact manifests, credential files, runtime dependencies and unreviewed
upstream history. Nothing in the introduced evaluation code is silently omitted.

The explicit prerequisite is public fork baseline
`eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`; README/checksum/verification accompany
the bundle. This is not standalone: recover that baseline from the fork, then
fetch the reviewed bundle. Existing complete local bundles also remain intact.

All introduced commit blob versions, staged/index and working content are scanned
with the existing tooling. Reviewed offline logs/fixtures are hash-specific.
Bundle integrity and restore/unit/hash checks are independently verified locally.
No unreviewed full-history archive is exported. Preparing a file on this VM alone
is not off-VM backup. The designated chat export directory is unavailable under
the agent's filesystem ownership; no upload-capable generic artifact tool is
available. See the local export README for concrete paths and current result.

## Native ICU diagnosis and scoped fix

The failing binary is `@embedded-postgres/linux-x64` 15.18's native/bin/postgres,
loaded by the existing native offline planning runner. Fresh environment: Debian
13, Node 24.22.1, pnpm 10.33.0. The previously successful primary installation
contained ICU 60 libraries in native/lib, and libicuuc had RUNPATH `$ORIGIN`.
Those installed dependencies were never in Git; their original patch/provisioning
history is unknown. They were inspected, not copied into the recovered clone.

Obtained genuine Ubuntu libicu60 60.2-3ubuntu3.2 from archive.ubuntu.com. Its SHA256
matches the official HTTPS bionic-updates/main amd64 package index:
`f01f61f57e63dc905e02e6441d10370fe0c79e43e70e6f5fe24b342fd2633209`.
Extracted rootlessly with dpkg-deb; copied genuine ICU files into the fresh
recovered dependency directory. No system package or production source change.
The Ubuntu files differ from the earlier installation; they were not represented
as identical. Their transitive data library needs LD_LIBRARY_PATH because the
unmodified archive libs do not have the old installation's patched RUNPATH.

With that explicit library directory, postgres and initdb --version both passed
(PostgreSQL 15.18). The existing runner now accepts optional --native-library-dir,
validated to lie inside its own checkout, and passes it after clearenv. Default
behavior, read-only source, network isolation and rate ledger are preserved.
No fake library, incompatible ABI symlink or new supervisor was introduced.

Full native integration is not rerun: the shared five-starts/hour ledger is full.
At diagnosis, next eligibility was 2026-11-09 04:54:58 UTC (Nov 8, 8:54:58 p.m.
Pacific). Ledger/identifier were not changed. Loader checks are not substitutes
for native integration. Package/build/permission requirements remain documented
in persistence/README.md. Recheck only when the real ledger permits it.

## Verification and remaining state

All 56 unit tests passed: controlled coding 14, collector 33, persistence 9.
Manifest/frozen checks and secret review passed. Library option help and invalid
external-path rejection were checked without any native interview start.
Remote verification remains blocked; there is no verified remote eval/phase2n
SHA and therefore no fresh remote checkpoint recovery claim. Bundle recovery is
explicitly local-only. Phase 2M remains missing; gateway-only egress unproven.

Local evidence: /workspace/work/blocker-resolution. User involvement is needed
for GitHub write authorization and a permitted off-VM export/download route.
Full native rerun additionally awaits the preserved start window. No sensitive
material has been uploaded, and no full persistence success is claimed.
