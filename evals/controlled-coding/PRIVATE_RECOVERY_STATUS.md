# Private recovery status

VERIFIED local-only: all 32 original private dependencies match the SHA-256 values
in backup/FROZEN_DEPENDENCIES.json. No bytes were reconstructed. A permission-0700
local directory contains the exact-byte archive and receipt:
`/workspace/fusion-private-recovery-completion/private-dependencies.tar.gz`.
Archive SHA-256: `7fba418bb08184e616269153b0027e092a2764add229979d293f4405d57d021e`.
Mapping SHA-256: `a0feccbd76fd7fb462178144bca21b160d507047dce3a20c666b2aa147007b21`.
The archive has 32 workspace-relative originals plus RECOVERY_MAPPING.json.

VERIFIED independent local restore: `/workspace/fusion-private-recovery-restored`;
all 32 restored file hashes match. Archive and files are mode 0600; roots are 0700.
Credential-pattern, database-content, filename, duplicate/path and hash checks run
before archive creation. No real credential was accessed. The archive is NOT Git
tracked, NOT included in public allowlists, and NOT encrypted because it remains
inside the trusted local environment. Originals, original bundle and refs remain.

BLOCKED off-environment durability: no authorized protected external destination or
encryption-key custody is configured. This is NOT off-environment
PRIVATE_RECOVERY_VERIFIED. Smallest action: operator supplies an authorized protected
destination and authenticated-encryption/key-custody method. Never publish this archive
on the public backup branch. B/C originals ARE available and verified locally.

Reproduce locally into NEW paths:
`python evals/controlled-coding/private_recovery.py --mapping PATH_TO_BACKUP/FROZEN_DEPENDENCIES.json --output NEW_PRIVATE_ARCHIVE_DIR --restore NEW_PRIVATE_RESTORE_DIR`.
