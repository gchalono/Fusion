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
