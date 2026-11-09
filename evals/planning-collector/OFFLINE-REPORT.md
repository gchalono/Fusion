# Phase 2A offline completion report

**Genuine pilot status: PILOT_BLOCKED. No paid inference authorized or performed.**

| Requirement | Evidence and status |
|---|---|
| Disposable native runner | **Verified:** real source interview/SDK and bundled PostgreSQL ran in a fresh-home, read-only-source, private network/PID namespace. No dashboard/heartbeat/autopilot was constructed. |
| No MCP | **Verified:** resolved servers and errors both empty before each tested interview. |
| Fixed identifier / rate limit | **Verified:** `fusion-phase2a-pilot`; five starts including debugging failures recorded durably; sixth attempt rejected before launching native code. No native limiter/clock changes. |
| Deterministic answers | **Verified:** comprehensive transcript contains the brief's PostgreSQL answer and exact fixed unknown reply. Protocol v2 and three representative briefs were committed in `cf2c6549a` before that test, and hashed before start. |
| DB isolation | **Verified:** all inspected schemas' table counts/row hashes changed only for `project.ai_sessions` (0 -> 1). No missions, tasks, features, agents, schedules or PR records appeared. |
| Filesystem/process isolation | **Verified:** comprehensive/mismatch evidence has no unapproved file changes or new non-PostgreSQL process. Real source/home were inaccessible for writes. A new local PG connection backend was allowed explicitly. |
| Native retries and compaction | **Verified:** comprehensive run forwarded seven requests, exactly seven reached the mock. Real SDK handled a 503; real interview performed JSON reformat retry; native manual SDK compaction completed via two further HTTP requests. No policy was disabled. |
| Fallback/mismatch | **Verified:** unauthorized model selected through native resolution was rejected by gateway; zero requests reached mock. **Not claimed:** an end-to-end successful authorized fallback or automatic context-threshold compaction trigger. |
| Bypass | **Verified:** direct local mock request without gateway capability returned 403; external address probe failed in network namespace. Source/dependency mounts were read-only, real home masked, child env cleared. |
| Streaming and non-streaming | **Verified:** real native SSE traversed gateway and mock HTTP hops; separate loopback/unit tests verify non-streaming JSON, missing usage, and length finish flags. **Limitation:** gateway buffers SSE, so timing equivalence is not claimed. |
| Missing usage / spending | **Verified:** all seven comprehensive responses omitted usage; full reservations remained 6,128,640 synthetic microdollars. Native SDK zeros were not treated as measured cost. No money was spent. |
| Native output limits | **Verified:** sent limits 16,384, 13,107 and 8,192 preserved byte-semantically; request hashes match reservations. Gateway never clamps them down. Too-tight optional caps reject before forwarding. Length finish flags are recorded in gateway tests. |

## Reproduction and evidence

See README for commands and rate-limit prerequisites. Evidence from this session:

- `/tmp/fusion-native-offline-zy45xq9z`: normal native interview, two HTTP requests.
- `/tmp/fusion-native-offline-x4yatwew`: comprehensive native path, seven requests,
  before/after snapshots, raw request/response artifacts, native summary/transcript,
  missing-usage reservations, no unexpected state changes.
- `/tmp/fusion-native-offline-ovyqi097`: expected wrong-model failure, no forwards.

These are labeled offline mock fixtures, NOT genuine plans or corpus entries.
`verify_evidence.py` independently rechecks the retained comprehensive and mismatch
snapshots, hashes, output limits, counters and native outcomes without another
start. Initial namespace-mount and payload-shape diagnostic failures are retained
separately; they were corrected, not represented as passes. The final snapshot
tool additionally records empty directories/modes and startup/teardown provenance;
those additive fields were helper/syntax checked after the native runs, without
bypassing the five-start limit for another full run.

## Tests

**Verified:** 33 collector unit/loopback tests passed with exit 0:

```bash
python -m unittest discover -s evals/planning-collector -p 'test_*.py' -v
```

**Verified:** five existing Fusion test files / 17 tests passed, exit 0, on the
unchanged source baseline:

```bash
export PATH=/workspace/.fusion-tools/node_modules/.bin:$PATH
VITEST_MAX_WORKERS=1 pnpm --filter @fusion/engine exec vitest run \
  --project engine-default \
  src/__tests__/custom-providers-openai-completions.test.ts \
  src/__tests__/custom-providers-openai-responses.test.ts \
  src/__tests__/pi-prompt-with-fallback-recursion.test.ts \
  src/__tests__/pi-prompt-section-compaction.test.ts \
  src/__tests__/fallback-model-observer.test.ts \
  --silent=passed-only --reporter=dot
```

No pre-existing failures observed in this selection. No full workspace suite or
paid-provider tests were run. Pure detector tests inject same-count task changes,
new agents, unauthorized files and durable processes and verify rejection.

## Remaining genuine-pilot blockers

**Verified missing:** explicit paid-inference permission and complete provider,
physical model, credential variable NAME, call cap, spend ceiling, pricing,
approved hosts, pilot goal/brief, answerer and turn cap. No real credentials were
inspected or accessed. No network permissions changed.

**Inferred requirements:** independently verify the exact pricing/token contract
in PRICING.md; build a separately authorized live transport with exclusive egress
and isolated credential injection; validate real provider identity, usage,
streaming/retry-header semantics and any authorized fallback. The offline CLI has
no live mode and must not be treated as an authorized paid launcher.

**Verified provenance:** native source stays at
`eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`; all changes are evaluation-only on
`eval/phase2a-collector`. `provenance.py` computes the final collector commit,
full binary patch SHA-256, and protocol hash after a clean commit. No production
source, lockfile, dependencies, global settings or platform egress policy changed.
