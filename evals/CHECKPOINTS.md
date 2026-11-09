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
