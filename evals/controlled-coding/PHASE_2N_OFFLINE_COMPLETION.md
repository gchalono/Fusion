> Historical512-profile report. Current authorized offline768 native/non-browser result is in TASK_MANAGER_FULL_CONTRACT_RESULT.md; original failures and evidence below are preserved.

# Phase 2N offline completion report

**OFFLINE_FAILED:** required real-browser validation failed. The complete-contract
native target remains unverified; output-budget and original-grader integration
blockers were identified without weakening requirements or increasing limits.

## State selection and persistence

VERIFIED selected development 4d96fd89186661e84dbd6725277414ecfc8df2c7 descends from
preserved b3bc7b0dc6c2751bb3b499d9ce6023b3e2c7284c. Public 83b0bcabacf5a8278775a669f0af72cbeba8cc97
is a separate sanitized lineage. Select development because private history, all
35 frozen inputs and original source-backed approvals are available, and baseline
95 units pass. Never use the public orphan as substitute private ancestry.

VERIFIED first checkpoint e663e79c0c374803f4ed1e30216337deae4bf00a, then native-A/private
recovery milestone d89ffc833c62e60fe78b4b7649e877c078726577 -> sanitized remote
beacd5ea69e35e4ca314e2761ddc5f12e12d5483, independently fetched/compared. Terminal
development and backup hashes are resolved from HEAD and backup/SOURCE_MAP.json /
CHECKPOINT_INDEX.json and stated in the final operator report; no self-hash invented.
Original history/bundle/recovery refs preserved; public history contains only sanitized
parents. No remote main/upstream writes, merge, force push or original-ancestry push.

Checkpoint command after reviewed local commit:
`python -B CURRENT_BACKUP/backup/publish.py --source /workspace/Fusion-phase2n-integration --destination NEW_SNAPSHOT --event milestone --milestone DESCRIPTION`.
Run after milestones, before risks/final report, and >=every20 minutes active work.
Outgoing scan: `python -B SNAPSHOT/backup/verify.py`, mandatory before every push.
Final fresh clone runs that scan and `backup/test_public.py` in the unchanged
namespace with original private evidence unmounted. No snapshot-process change.

## Private recovery

VERIFIED 32 exact originals plus clean local restore; see PRIVATE_RECOVERY_STATUS.md.
Archive SHA-256 7fba418bb08184e616269153b0027e092a2764add229979d293f4405d57d021e.
Mode-restricted local-only archive/restore; no external destination or encryption
key was provided. Off-environment PRIVATE_RECOVERY_VERIFIED remains BLOCKED.
All 35 original input hashes and original approval bindings remain unchanged.
The original hidden evaluator also exists byte-exact in original local preparation
commit 40a06aa5cb932ddc0ed9bf232aca00999b355d96, retained in recovery bundles; its
hidden contents are not added to public snapshots or the 32-file archive.

## Browser gate

FAILED installed Chromium155 multiprocess reference; prior verified cause is zero-
capability capset rejected by mandatory seccomp before renderer/page creation.
FAILED four additional real single-process/no-zygote profiles: minimal; in-process
GPU/no-proxy; network-feature selection; and initial-window selection. Public fonts
mounted read-only. Outer traces preserve exact tracee policy. Single-process avoids
the prohibited zygote call but terminates with a separate SIGTRAP, not attributed to
capset without evidence. No page created; browser-specific protected-file/credential/
egress negatives and original UI acceptance remain UNVERIFIED.

BLOCKED dependency: only installed Chromium155 available; apt has no Firefox
candidate. Installed Playwright1.60 identifies exact official Chromium headless-shell
and Firefox builds, but HEAD requests to cdn.playwright.dev return proxy HTTP403 / curl56.
No permission change was made. An outside-filter trusted browser was rejected as
an unproven security weakening, not relabeled equal protection. Narrow alternatives
remain unavailable. Evidence: /workspace/completion-browser-probes/ and original
reference logs. Investigation ended on concrete dependency/policy blockers within
45-minute maximum, rather than stalling remaining work. No syscall waiver/shim.

Smallest action: provide/authorize access to a compatible maintained official browser
binary, then prove page creation and all original browser/negative controls under
unchanged security. If a browser-only policy revision is proposed, require separate
review/approval: current userns nonroot, cap-drop ALL, no_new_privs, PID/net/mount
isolation and masked privileged binaries reduce escalation avenues, but granting
capset changes a previously explicit denial. Seccomp cannot safely inspect pointed-
to capability masks. No equality claim or policy revision was implemented.

## Native controls and original acceptance

VERIFIED partial A/B/C and A repeat: four local TLS model attempts each; native
read/write/bash, two files, real storage self-test/startup/HTTP/shutdown, fresh patch
application, seven partial HTTP/SQLite checks. All have FAILED real-browser step.
See TASK_MANAGER_POSITIVE_VALIDATION.md for exact units, exposures, provenance and
limitations. Scripted results imply nothing about treatment effectiveness.

FAILED contract compatibility of these controls: missing /app launchers, full field
validation and prescribed UI hooks. They are not complete task-manager submissions.
Original ten-category acceptance was NOT run through its old isolation.py: that
older wrapper lacks the current userns/cap-drop/seccomp protections. Running it
unchanged would weaken security. Existing task_manager_grader.py is only a partial
adapter and its dialog-style browser test differs from the original inline-edit
hooks. Neither evaluator was modified to fit the fixture. Full independent score
and complete implementation success remain UNVERIFIED.

BLOCKED full fixture: prepared, non-native five-file proposal is 6230-byte build /
1787 o200k source tokens. Current serializer needs six model requests at512, or
three tool replies at765+ and fourth final. Active cap remains FOUR /512. A 768
output-only proposal would fit worst-case $0.056116/run and131072 cumulative units,
but is NOT ACTIVE and requires explicit approval. These measurements are serializer-
specific, not proof no smaller program exists. /app alias, executable-mode-aware
multi-file capture and a safe adapter for UNCHANGED original acceptance also remain
integration prerequisites. Do not activate output proposal or run six requests.

## Security, recovery and reproducibility

VERIFIED final integrated diagnostics in /workspace/completion-integrated-security-final/:
actual native bash checks host credential variables, hidden/protected/cross-arm files
and direct reserved-address egress inaccessible; positive same-session gateway path
works. Unauthorized tool rejected. Positive fixture deliberately requests another
tool on response4; subsequent native assistant terminates with HTTP403 error while
upstream contacts and durable reservations stay FOUR. No timeout or fifth upstream.
Logging-only evaluation subscription records model_end; native generation/retries
unchanged. Budget/reconciliation defaults, output cap and all gateway guards intact.

VERIFIED interrupted first local upstream: broker killed after contact, native process
aborted, uncertain3028 micro-USD retained. Explicit broker-only resume rotates token,
preserves exposure and shuts down. No Pi conversation replay/recovery was performed;
complete Pi recovery remains UNVERIFIED. 16 owned gateway/admin endpoints closed.
Existing concurrent-budget, missing/streaming-usage, admission/deadline and restart
units rerun. Page-level security controls remain UNVERIFIED, not borrowed from bash.

VERIFIED A/repeat identical patch, all4 wire bodies, counts, reservations and ordered
ledger transitions; same partial acceptance observations. Not complete successful-
implementation reproducibility. Separate diagnostic ledgers are not one integrated
actual multi-arm spending ledger; shared caps are independently unit-tested.

## Tests, evidence and proposed live prerequisites

VERIFIED baseline95 tests (47 coding+37 collector+11 persistence), zero skips/failures.
Final103 tests (55+37+11), zero local skips/failures. Public recovery omits8 tests
requiring originals/private evidence and2 requiring the public tokenizer utility
outside its namespace; skipped is NOT passed. Browser integration failures are
reported separately from passing units. Exact public recovery totals in final receipt.

Commands: unittest discovery in evals/controlled-coding, planning-collector,
persistence; private_recovery.py; task_manager_positive.py --partial-diagnostic;
task_manager_positive_security.py; task_manager_contract_feasibility.mjs. Pin public
js-tiktoken1.0.21 from npm, ignore install scripts; no production dependency changed.
Raw local wire/approval/tool evidence remains outside Git. Proposed code is prepared
TEST DOUBLE material, never a native output or a hand-reconstructed genuine plan.

BLOCKED live prerequisites: protect off-environment private recovery; approved working
browser; original evaluator under current isolation; frozen /app/launcher/capture
interfaces; compatible approved output budget OR a genuinely smaller compliant
fixture under512; full native positive and original10-category acceptance; negative
browser controls; complete accepted repeat and integrated multi-arm ledger evidence.
Only then propose ONE real-model diagnostic at existing gpt-4.1-mini-2025-04-14,
four requests/$0.12 per run, unchanged planning$0.50/aggregate$2 and frozen treatments,
with separately verified provider/project/model availability and explicit paid
permission. No pilot is currently ready or authorized; no model substitution.

Provider spend: EXACTLY $0.00. Every diagnostic transport was TEST MODE with a
localhost TLS URL and generated local keys. No real provider authentication, model,
billing or quota endpoint was contacted. Missing stub usage is not actual zero tokens.
No mission, task, autopilot, production edit, paid call, deployment or frozen edit.
