# Phase 2A offline native interview collector

**Genuine pilot: PILOT_BLOCKED. Offline runner and gateway: tested.**

No paid inference, credential access, production edits or network-permission changes.
Real Fusion interview code and the installed Pi SDK execute against local HTTP mock
responses through the external budget gateway. All outputs are explicitly
`OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS`. The original pilot report is historical;
this README and OFFLINE-REPORT supersede it. Earlier feasibility text is retained
in Git history.

## Reproduce

Requires Linux bubblewrap with user/network/PID namespaces, Python 3.12+, Node 24,
and the prepared `/workspace/Fusion` source/dependencies at
`eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`. No packages were installed.
From `/workspace/Fusion-phase2a`, branch `eval/phase2a-collector`:

```bash
python -m unittest discover -s evals/planning-collector -p 'test_*.py' -v
python evals/planning-collector/offline_runner.py --scenario normal
python evals/planning-collector/offline_runner.py --scenario comprehensive
python evals/planning-collector/offline_runner.py --scenario model-mismatch
# Each prints a disposable evidence directory. Recheck without another start:
python evals/planning-collector/verify_evidence.py /tmp/fusion-native-offline-<id>
```

Use exactly `fusion-phase2a-pilot`. Supplemental durable accounting at
`/workspace/phase2a-evidence/offline-starts.json` enforces five starts/hour across
processes, including failures. Never delete/change the ledger to repeat tests.
A sixth start fails before namespace launch. Unit-test ledgers are temporary and
never start interviews. Three native debugging/normal starts preceded the final
comprehensive and mismatch runs; their actual start markers were retained in the
ledger. Two initial mount failures occurred before native start.

## Isolation and native path

The sandbox mounts source/dependencies read-only, a fresh empty home at the same
`/home/agent` path, and disposable project/settings/PostgreSQL/temp directories.
Child environment credentials are absent. Network and PID namespaces contain only
the supervisor, native child, mock/gateway HTTP servers and bundled PostgreSQL.
There is no external route. No global home or platform egress permission changes.
The mock requires a local capability held by the gateway transport: direct access
without it returns 403. No real credential loader or paid-run CLI exists.

`native-runner.mts` imports the real backend factory, AiSessionStore, MCP resolver,
and native start/respond/summary functions. It does not construct a dashboard,
scheduler, heartbeat service or autopilot. Effective MCP servers/errors must be
empty before start. Native AI sessions persist in the disposable PostgreSQL DB.
All services stop after evidence capture; state is retained under the printed
`/tmp` directory for review. Specific evidence directories can be deleted later;
the durable rate ledger must not be reset.

## Frozen deterministic protocol

`protocol.md` and `briefs.json` were committed together before the comprehensive
run; hashes are captured before start. Objectives cover idempotent APIs, worker
observability and accessible forms. The runner uses the API brief: storage gets
its PostgreSQL fact; unknown clarification gets exactly `No preference; use your
judgment.` No answerer model is used. Unknown confirm questions stop incomplete,
because native boolean formatting would otherwise invent a `No`. Turn cap: three.
Inputs are offline fixtures, not a proposed genuine evaluation corpus.

## Verified native HTTP integration

The comprehensive mock sequence returns 503, then malformed assistant content,
then two questions and a mock summary. Native manual SDK compaction makes two
additional requests. All seven go through gateway -> local mock HTTP. The actual
native SDK retry and JSON format-retry paths are unchanged. Compaction provider
routing was tested manually through native SDK compaction; the automatic
context-threshold trigger was not independently forced.

Wrong-model selection was passed through native resolution and rejected before
mock dispatch. No alternative model was dispatched. This is fail-closed selection,
not a test of successful switching to an authorized fallback provider. Relevant
existing fallback/compaction tests run separately with offline doubles.

Streaming SSE was verified through two local HTTP hops. The gateway buffers
bounded responses and returns unchanged bytes, so live first-byte latency
equivalence is not claimed. Non-streaming JSON, missing usage and length finish
flags are separately tested over loopback/unit tests. Native Pi always requests
streaming; no native non-streaming interview is claimed.

## Accounting and output limits

Each forwarded HTTP attempt reserves the full declared input/output bounds at
maximum prices before dispatch. Retries and compaction share call/money caps.
Reservations are never refunded for errors, missing/zero usage or cache discounts.
Usage remains unverified provider data; reservations are estimated upper bounds.

The gateway NEVER lowers native output limits. A configured ceiling requiring a
reduction (or inventing a missing limit) rejects before dispatch. Forwarded
artifacts record `output_limit_intervention:false` and parsed
`finish_reason:length`. Fusion emitted caps 16,384, 13,107 and 8,192; raw request
hashes show they were unchanged. Read PRICING.md before any future paid deployment.

Text strings/text-part arrays and function tools are supported. Images, hosted
paid tools, multiple completions, redirects, unknown extensions and model mismatch
fail closed. The HTTPS adapter preserves TLS/proxy trust but has not contacted a
real provider. No native retries, format retries or compaction settings changed.

## Snapshots, artifacts and provenance

Before/after DB snapshots cover all base-table row counts and sorted row hashes
in project/central/public schemas. Only `project.ai_sessions` may change;
same-count mutations are detected. Filesystem snapshots contain hashes/sizes,
symlink targets and, in final tooling, directory/mode metadata. An explicit
allowlist permits disposable DB, results/logs, gateway artifacts, module caches and
the isolated model catalog. New non-PostgreSQL processes are flagged. A lazy PG
connection backend is not an agent. Injected forbidden changes fail helper tests.

Comprehensive/mismatch evidence used hashes/sizes; directory/mode capture and extra
provenance/teardown fields were added afterward and checked at helper/syntax level
without taking a sixth native start. Read-only mounts prevent real-source/home
writes independently of snapshots. The model catalog and module cache are explicit
isolated session-support writes, not unexplained changes to user data.

Raw artifacts are write-once/hashed; partial failures remain. Sensitive raw data
is refused rather than silently edited. `verify_evidence.py` rechecks evidence
without running inference. `provenance.py` records exact source/collector commits,
full binary patch SHA-256 and protocol hash after a clean commit. Run inputs record
protocol/brief hashes before start. Final runner startup additionally captures
source/collector identity and runner/gateway executable hashes.

## Remaining genuine-pilot blockers

Complete explicit authorization, independently verified physical model/token/
pricing contracts, live TLS/credential-injection verification and an exclusive
paid-egress deployment are still needed. The offline namespace cannot contact
an upstream by design and is not silently repurposed into a live launcher.
Provider-reported model identity is checked only after dispatch: a trusted fixed
physical-model contract is required to rule out opaque server-side routing.
Provider-specific retry headers/streaming latency also need live integration
validation when authorized. No paid plan quality, price or runtime is verified.
