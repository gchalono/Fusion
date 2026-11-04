# Phase 2A feasibility and offline implementation report

## Status

**PILOT_BLOCKED.** Verified: no real model request, native interview, mission,
implementation task, dashboard, heartbeat service, or MCP server was started.
No credential file/value was read. No network permission changed. No push,
merge, publication, or deployment occurred.

Verified: source baseline is `eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`.
Changes are additive files under `evals/planning-collector/`, on
`eval/phase2a-collector` in `/workspace/Fusion-phase2a`. Primary checkout remains
on `work`. Production code, dependencies, lockfile, default retries, format retries,
compaction and fallback behavior remain untouched.

## Feasibility conclusion

Verified from source: custom provider base URLs reach the SDK HTTP client; default
compaction uses the selected model/auth. See README source references. Inferred:
a sole-egress proxy is a viable enforcement boundary for a verified direct,
text-only OpenAI chat-completions model. It does not require changing native
planning prompts, parser, retry policy or compaction policy.

Verified by offline tests: the implemented gateway reserves before dispatch,
counts each arriving HTTP request, applies an optional output ceiling, retains
reservations after failures, rejects model mismatch, bounds transport reads,
does not follow redirects, and preserves raw response bytes. Inferred limitation:
these unit/loopback tests do not prove actual native retry/compaction traffic will
all reach it. Provider routing, hard token/billing bounds, and real TLS/proxy
credential injection remain unverified. Raw SSE is buffered; first-byte latency
is changed, although native response content is not rewritten.

The safest implemented state is therefore an offline gateway with no live
supervisor. `preflight.py` always blocks inference and reports unmet conditions;
supplying a config boolean does not activate a paid run. No native extension was
implemented because proxy infeasibility has not been established.

## Gate 0 revalidation

1. Verified: five starts/hour is inside the exported function, not just HTTP:
   `packages/dashboard/src/mission-interview.ts:1343`. Use the fixed identifier
   `fusion-phase2a-pilot`; no native starts occurred. Durable start accounting in
   a future supervisor must also survive restarts without resetting the limiter.
2. Verified: summary completion only persists the draft at
   `mission-interview.ts:1293`; mission creation begins separately in
   `mission-routes.ts:1025`. No such creation API is imported here.
3. Verified: start implicitly launches background initialization and a first
   prompt (`mission-interview.ts:1375`, `:908`), plus module cleanup timers (`:495`).
   A dashboard is unnecessary and unsafe as a sole guard: UI-only startup still
   arms heartbeats (`packages/cli/src/commands/dashboard.ts:2738`). Resolved MCP
   must be empty before start; no assertion about a live resolved config is made.
4. Verified: runtime fallback/retries exist, with the configuration distinctions
   documented in README. The gateway rejects wrong outgoing model IDs; a wrong
   physical model reported by upstream can only be detected after dispatch.
5. Verified: backend factory accepts isolated root/settings/PostgreSQL paths
   (`packages/core/src/postgres/startup-factory.ts:740`). Persistent AI sessions
   require an AsyncDataLayer (`packages/dashboard/src/ai-session-store.ts:104`).
   Inferred: a future temp-directory supervisor can use them without a production
   database, but it must also isolate auth/settings discovery and all writes.
6. Verified: the SDK exposes cumulative usage (`agent-session.d.ts:201`, `:873`)
   and requests stream usage (`openai-completions.js:582`). Native interview
   summary responses omit usage. Gateway reservations are estimated upper bounds;
   provider-reported usage is not labeled measured until independently validated.

## Tests

Verified commands/results:

```text
python -m unittest discover -s evals/planning-collector -p 'test_*.py' -v
22 tests passed; exit 0

python evals/planning-collector/preflight.py evals/planning-collector/config.example.json
PILOT_BLOCKED; model_calls=0; exit 2 (expected)

VITEST_MAX_WORKERS=1 pnpm --filter @fusion/engine exec vitest run \
  --project engine-default \
  src/__tests__/custom-providers-openai-completions.test.ts \
  src/__tests__/custom-providers-openai-responses.test.ts \
  src/__tests__/pi-prompt-with-fallback-recursion.test.ts \
  --silent=passed-only --reporter=dot
3 files, 5 tests passed; exit 0
```

Verified: existing tests ran against the unchanged baseline primary checkout,
whose production source matches this branch. Their credential fixture is
in-memory with `allowModelNetwork:false`; completions use stubbed fetch. No
pre-existing failures were observed in this selection. Full suites were not run.
The tests show optional controls do not change request objects/response bytes
when absent; no production default behavior can change from this additive patch.

## Pilot verification

Verified: pilot did not start. No before/after database, filesystem, process or
outbound-host snapshots were collected, and no diff or plan is fabricated.
All test artifacts were temporary, marked offline, and deleted by the harness;
none entered pilot/corpus paths. There are no measured pilot costs or latency.

Unmeasured estimate formula: `calls * (input_bound * input_price_per_million +
output_cap * output_price_per_million) / 1,000,000`. Counts include all retries,
compaction and any future answerer requests. Full reservations are deliberately
not reduced by cache discounts or lower/absent usage. No numeric estimate is
defensible before provider/model/prices are authorized.

## Required before a genuine interview

Verified missing authorization: provider, model, credential variable NAME, call
cap, ceiling, input/output pricing, approved hostnames, pilot goal, answerer,
turn cap, and explicit paid-inference permission. Credential usability has not
been tested; exact network additions cannot be selected without a provider.

Remaining engineering (inferred requirements, not verified capabilities): isolated
native driver and snapshots; exclusive egress/auth-file isolation; model-specific
billing/token contract validation; SDK-through-proxy retry/compaction integration;
durable start accounting; brief freezing and native raw/summary capture. These
must complete offline/provider-specifically before an authorized pilot. Protocol
v1 supports factual human/scripted answers only; LLM answerers are not implemented.

Verified provenance mechanism: after a clean commit, run `provenance.py` as in
README to record exact base commit, collector commit, full binary patch SHA-256,
and protocol SHA-256. The final handoff includes the computed values. Do not
substitute a patch hash covering only selected files or embed a self-referential
hash in the commit being hashed.
