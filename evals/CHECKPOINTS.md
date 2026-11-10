# Validated checkpoints

## Phase 2N offline baseline — 2026-11-08 America/Los_Angeles

Implementation: `9736d67e40c8656b56206eafd6b7bc615c1c5c3f`.
Branch: `eval/phase2n`. Tests: controlled-coding unittest suite (14 passed),
planning-collector suite (33 passed), comprehensive native mock integration
(seven local mock requests) and independent evidence verification passed.
Historical native integration needed bubblewrap outside the agent sandbox.

Environment inspected during persistence work: Git 2.52.0 (also recorded in local
snapshot inventory), Python 3.12.14, Node v24.22.1. PATH pnpm 11.25.0 differs from
the repository-pinned pnpm 10.33.0; use the pinned version for dependency recovery.
Artifact reference: `evals/artifact-manifest.json` and controlled-coding/evidence.
Remote backup: INCOMPLETE, fork write denied HTTP 403; no remote eval/phase2n tip
confirmed. Snapshot/bundle is local-only. Phase 2M remains missing.

Future records reference preceding validated implementation commits. The remote
branch tip, independently verified after push, is authoritative for recovery.

## Validated checkpoint 2026-11-09T04:09:29.339600+00:00

Implementation: `15fad6de69f42565e9e230e5edd08a649a401b0d`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## Validated checkpoint 2026-11-09T04:12:29.520901+00:00

Implementation: `db6cf1deacbbb7c38ebcfa663062cd2bde7fa71d`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## Validated checkpoint 2026-11-09T04:24:54.193948+00:00

Implementation: `463bf2a3d1538f3a5c141df474993cee835fa40e`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## GitHub backup and fresh remote recovery — 2026-11-08 Pacific

Independently verified remote checkpoint:
`2d5e2577b822e72bc1abc99d9a6db5fa9544af7a`, eval/phase2n on gchalono/Fusion.
Validated implementation: `463bf2a3d1538f3a5c141df474993cee835fa40e`.
GitHub reconnection resolved the prior 403. Fresh GitHub clone: preflight, manifest,
frozen checks and all 56 unit tests passed (14 coding, 33 collector, 9 persistence).
Native dependency install/core+engine builds and PostgreSQL/initdb loader checks
passed with genuine ICU 60; full native interview awaits the retained rate window.
Environment: Python 3.12.14, Git 2.52.0, Node 24.22.1, pinned pnpm 10.33.0.
Manifest: evals/artifact-manifest.json. Evidence: persistence/REMOTE_RECOVERY.md.
Raw sensitive artifacts remain VM-local; Phase 2M remains missing.

## Validated checkpoint 2026-11-09T05:09:23.477540+00:00

Implementation: `ab571b9aa0115079a8866e3e9b0348c82253a881`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## Validated checkpoint 2026-11-09T05:22:42.141148+00:00

Implementation: `1976dfbc9f5dd7aea85a7d6ce19e5029415b7691`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## VERIFIED native/isolation readiness — 2026-11-08 Pacific

VERIFIED: code checkpoint c8a302767001910b188d734b5f55f435319ea08b on eval/phase2n.
VERIFIED: 66 unit tests pass (20 coding, 37 collector, 9 persistence); 20 scoped
namespace cases pass with local controls. Genuine native comprehensive fixture
and independent verifier pass: seven local model HTTP attempts, only
project.ai_sessions changed, empty MCP, all exposure retained under missing usage.
VERIFIED: immutable prior rate entries, same fusion-phase2a-pilot identifier,
three starts/hour cap; no provider requests or paid inference. The earlier verifier
shadowing bug was reproduced, fixed under evals and covered by two regression tests.
VERIFIED: isolation overall PARTIAL; untested live wiring/protocol/resume/pricing
controls remain UNVERIFIED. No original Phase 2M evidence or approvals recovered.
VERIFIED: evidence hashes and full limitations are in controlled-coding/readiness-evidence.json
and controlled-coding/PHASE_2N_READINESS.md. Raw artifacts remain private/local.

## Validated checkpoint 2026-11-09T10:02:08.066188+00:00

Implementation: `f7a5698477e26771966cc09da58346e335bde6e0`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## Validated checkpoint 2026-11-09T18:43:47.652010+00:00

Implementation: `d4ba7558fe28ada43c8bb5fe71e22387558b5b18`; branch `eval/phase2n`.
Tests: controlled-coding, collector and persistence unittest suites passed; frozen inputs and manifest verified.
Environment: Python 3.12.14; Git git version 2.52.0.
Manifest: `evals/artifact-manifest.json`. Remote: pending independent verification; remote tip is authoritative.

## Sanitized persistence and offline A/B/C milestone

Original b3bc7b0 checkpoint preserved; public orphan b1542ac7 verified by independent fetch and fresh clone (84 passed, 8 private-dependent skipped). Remote descendants remain sanitized-only. See controlled-coding/POST_BACKUP_OFFLINE_REPORT.md. Explicit offline Experiment 2 token revision verified; native A/B/C local test-double loops and A repeat completed; incomplete candidates rejected. Chromium positive reference remains blocked. Provider spending $0.00. Public recovery still requires 32 protected input dependencies for full experiment reproduction.

## Offline completion: private recovery and positive native A

Baseline 95 tests passed. Exact 32-file private archive/restore verified locally; off-environment durability blocked. New bounded native positive A used four local TEST DOUBLE requests, generated application.py and README through tools, passed seven unchanged HTTP/SQLite checks; browser gate still fails. See controlled-coding/PHASE_2N_OFFLINE_COMPLETION.md and related recovery/positive reports. Provider spending $0.00.

## Phase 2N final offline validation: FAILED target, useful partial evidence

Private 32-file archive/restore verified locally only. A/B/C partial core controls + A repeat used four local requests each; patch/wires identical for repeat. Original full contract has missing launchers/validation/UI hooks; seven legacy partial checks are not full acceptance. Complete proposed serialization requires six requests at512 or three replies at765+; limits NOT changed. Real Chromium profiles fail; official alternatives blocked HTTP403. Full original grader requires security-preserving integration, not reuse of older weak wrapper. Final103 local unit tests pass; browser failures separate. See controlled-coding/PHASE_2N_OFFLINE_COMPLETION.md. Provider spending $0.00.

## Authorized offline768: native full-contract A2 passes9 non-browser categories

Baseline103 tests passed. New explicit Experiment2-only output768 preserves defaults, four requests and all dollar/deadline/input bounds. Initial native candidate exposed SQLite commit-before-response defect; regenerated A2 fixes it and passes all9 original non-browser categories under isolated byte-exact evaluator assertions. Browser remains BLOCKED. Hidden evaluator contents remain outside Git; private archive unchanged/local-only. See new FULL_CONTRACT_RESULT, ORIGINAL_EVALUATOR_INTEGRATION and OFFLINE_768_TOKEN_VALIDATION reports.

## NON_BROWSER_ACCEPTANCE_VERIFIED: full native TEST DOUBLE

Native A final/repeat and B/C construct all5 files with executable launchers in4 requests at scoped offline768. Every original non-browser category passes (9/9); browser category remains BLOCKED and overall original completion=false. SQLite commit-before-response defect was fixed in fixture and regenerated natively. File/mode/patch and reservation/transition repeat confirmed; final wire timing/UUID differences normalize as declared.110 local units pass. Milestone source4c2fff724 maps to sanitized4b15d117; terminal mapping resolves backup SOURCE_MAP/CHECKPOINT_INDEX. Original35 hashes/8 approvals/private32 archive unchanged. Additional553 private evidence files locally archived/restored; no off-environment private durability. Security/budget/recovery probes pass; no paid calls, production changes or live readiness.

## Real browser gate VERIFIED, private remote recovery BLOCKED

Signed official Google Chrome157 from already allowed dl.google.com runs real pages with single-process/no-zygote under unchanged current seccomp/user/net/PID/mount/cap restrictions. Original accepted native patch scores100/100 in all10 original categories, independently repeated. Browser security negatives pass; no candidate edits/regeneration. No private destination/recipient authorization found;32/553 archives preserved,654-file local inventory identifies101 additions and13 budget backups. See BROWSER_ACCEPTANCE_FINAL, PRIVATE_REMOTE_RECOVERY_FINAL and FIRST_REAL_MODEL_PILOT_PROPOSAL. Provider spend$0.00; no paid pilot authorization.

Checkpoint exception: the browser milestone export correctly stopped before push when a NEW synthetic integrity unit attempted forbidden setuid creation inside recovery isolation. The fixture now verifies regular-file integrity and separately tests masking metadata; real-browser masking remains empirically checked. No permission/filter change. The20-minute remote target was exceeded while this safety gate was resolved; local source/evidence preserved and a recovery bundle prepared before further work.

## BROWSER_ACCEPTANCE_VERIFIED; PRIVATE_REMOTE_RECOVERY_BLOCKED

Unchanged native patch df383ba2... scores100/100 in3 independent original-evaluator fresh checkouts using signed Google Chrome157 with verified single-process/no-zygote configuration. All18 real-browser security checks pass; capset/seccomp/namespaces unchanged, helper masked. Baseline110 -> final114 local unit passes. Milestone d78dda6b2 remotely verified as b5335c10... after correcting unsafe synthetic setuid test fixture; checkpoint delay documented. Additional850-file PRIVATE package clean-restored, including122 historical manifest dependencies,8 approval bindings, exact seed and13 ledger integrity checks; original32/553 archives preserved. No approved external destination/recipient exists, no private upload. Pilot proposal is NOT approval; provider spend$0.00 and native/default/budget/frozen inputs unchanged.

## Phase 3 initial restore / rehearsal milestone

Original pinned dev9afbac61342d18a59b0d1cdd1111d6ef736f82c5 and independent remote
2963d4771debf153690d125507db721e956a6a6b verified before changes. Original recovery
bundle verified; original private archives unchanged/local-only. Separate4096 LOCAL
profile and failure-double hooks preserve existing defaults and frozen inputs.
120 offline units pass. Full native Arm A generated unchanged five-file patch in4
local requests. New matrix initially failed because its collector omitted the
full-native-result.json evaluator input; fixture receipt fixed, failed root retained.
Checkpoint before continued adversarial native work. Spending authorization$0.00.

## Phase 3 failure-handling code milestone

Sourcea8bfadda79117edb8a6e3a977f6358e6521cb5be independently backed up as
598d39f7a07ce63c507f7a5dabd678f7bc59deb2. Public source archive downloaded twice,
SHA2564aba2da64a3c996b8bd6539b1d2e865fb80abe29c335840c01b1f56126fc8261.
No private archive uploaded. Three original private archive checksums verified.
New reporting defects caught by local doubles fixed minimally: native exit0 after
model error; missing final newline in stopped candidate; usage without SSE DONE.
Failed attempt roots preserved.78+37+11 units pass. Both request-cap and monetary-cap
stops preserve evidence and still run original independent evaluator. Public nested
namespace units explicitly require outer executor and skip under mandatory recovery
filter; actual outer-executor probes pass. No security filter changes or paid traffic.

## Phase 3 terminal reports/freeze

Code ce51b94b6cfbfb6ba4c24527afd06909906c6bfd; original9afbac6 pin preserved ancestor.
Frozen canonical SHA2569460ff7b9cbf1c794c0512f6df78f711bc3c36877a40561971de143dbf9a5bb7
covers66 source/config hashes and unchanged objective/seed/limits.126 local units pass.
Twelve native cases validated; original browser not rerun. Current-rate/live-ledger/
credential/private-external dependencies explicitly BLOCKED. Terminal source-only
sanitized checkpoint and independent fresh-clone receipts resolve final SHAs; original
source history and private archives remain local, not merged into sanitized ancestry.
No paid authorization inferred from proposed commands. Provider spending$0.00.

## Phase 3C gate checkpoint

Starting dev6fa149d5c9cb14ab03bdb1db7048ec460d2df9fb,backup961c128db722d5b7210eca01bb9d3a28081cdbe1.
Original sealed journal all47 records verified before/after,11522 micro-USD retained;
independent recompute matches. New history adapter extends existing budget admission
without resetting/reopening original journal.19 new adapter +15 changed-module tests
pass. Real continuation only bootstrap/anchor,0 new requests. No private DB/raw records
in outgoing snapshot; source/hash receipts only. Gate permits Step6 only AFTER
independently re-fetched remote checkpoint. Metadata unverified; no paid authority.

Phase3C first gate source616a83e26adb43598e2b2f461861f0b68e0fd190 independently
refetched as1b2fdcfd241da8f2f3dbfb2f3ae90d4d4ad485b0. Public isolated recovery tests
pass; original objects/private data absent. Additional legacy-open bypass rejection,
deterministic SQLite close and gateway timeout/failure checks expand gate to21+15
focused passes. No Step6 execution before updated checkpoint is independently fetched.

## Phase3C completed gate and authorization-boundary handoff

Gate sourcee081c8450dc99de66c17ad59b72207e150aa4c10 independently refetched as
5450193d44e03ce27c62acd2865718d4b7f2c031.21 adapter+15 regressions pass;134 public
recovery passes,13 honest skips,0 failures. Only after that verified checkpoint,
Step6 inspected signing configuration and stopped: no operator verifier or approved
trust key,0 live authorizations; dev TEST keys cannot authorize live. Authoritative
ledger0 new requests,11522 historical exposure,original47 hashes/bytes unchanged.
Report-only terminal checkpoint follows. No new historical archives/private publication,
no paid inference,production,evaluator,seed,prompt,approval or isolation changes.

Phase3C reporting clarification: conservative headroom with full additional500000
planning withholding is1488478 micro-USD; remaining-allocation headroom1500000.
Neither is a second charge. Both exceed77416. Code/ledger/limits unchanged.

## Phase3D first implementation milestone

Baseline bde7035c3ffeb4fc342e9b8ad18547f07edd1827 and existing47/11522/0 journal/ledger
restored without new authority or re-import. External operator trust implementation,
real supervisor entry and safe capture complete for focused verification. Ed25519
stdin signing initially failed because OpenSSL needs a seekable one-shot input;
fixed with a private temporary payload file.4 focused tests +21 ledger regressions
pass. Checkpoint before real-entry synthetic native rehearsal. No live key/approval
created, no paid/provider inference. Detailed logs /workspace/phase3d-evidence/.

## Phase3D working-code acceptance and final handoff

Actual supervisor code aab233755ca008eea05e4ea210554772192c47ba passes15 TEST scenarios,
61 focused methods. Original ledger/journal/frozen inputs/evaluator/isolation unchanged;
no new authoritative request/charge. First intermediate source86e95a6... independently
backed up as419d0ad60a29cc741c05f7fe21785ada8062dea8; broker milestone9610b3a...
backed up asa15a41f3038311d2cf3550b000936ad5fa64e360. Final working code and report
checkpoints follow via scanned sanitized-only history. Raw TEST keys/approvals/ledgers/
provider artifacts remain outside Git. An automatic-review usage limit blocked a test
command without executing it; authorized resumed validation passes. One metadata GET200,
zero provider inference,$0 new spend. Pricing/enrollment remain external; no model
substitution,cap increase,global config or deployment. Private recovery not claimed.

## Phase3E activation package milestone

Preceding validated baseline dc67ebdcaafdbeb6c2b460cf92dc0d0b5c617427 maps to
independently verified sanitized82428dc397d088264e03b04c7bc0f40abbb3f00c.
Additive non-consuming preflight plus operator activation documentation:5 focused
TEST cases and10 existing operator tests pass. Original35 hashes/47-record anchor/
11522 retained and ledger+witness bytes preserved;7 isolation checks pass.
No full-suite repeat; no browser/runtime/evaluator change. Current official pricing,
provider hard-cap evidence and outside-agent live trust enrollment remain human
prerequisites. Final sanitized mapping is recorded by backup/SOURCE_MAP.json and
its independently fetched receipt. Generate unsigned spec only from final published
clean source. No nonce consumed, new ledger row, live signature or provider inference.

## Phase3F — signed risk acceptance, AWAITING_OPERATOR_SETUP

Restored development8459ba5c995901f131d0cb3fae1c5ff8284e8a37 / sanitized
backupa4603010e465051bc28fd1bd60a1d3a6fc2c95ba.35 frozen hashes,8 approvals,
47 historical records/11522 micro-USD/0 unresolved verified;ledger+witness unchanged.
Operator-authorized removal of provider hard-cap attestation; exact signed acknowledgment
of no verified provider cap and potential billing beyond local estimate is required.
All original local limits/accounting/credential/isolation/authorization retained.
30 focused tests plus7 native isolation checks pass;no benchmark/browser rerun.
Official docs unreachable,current pricing unverified,external live trust absent.
No live signing key/approval created,provider API/inference0,new spend$0.00.
Current procedure PHASE3E_ACTIVATION.md;final source/backup mapping in sanitized
SOURCE_MAP and private phase3f-evidence receipt. Stop at operator setup/signing boundary.
