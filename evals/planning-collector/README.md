# Phase 2A: external request-budget boundary (offline implementation)

**Status: PILOT_BLOCKED. No inference is authorized.**

This implements and tests the external gateway portion of an evaluation collector.
It is **not** a complete/live-enabled collector. No native driver, credential
loader, or live listener command is supplied. Do not interpret passing offline
tests as proof of a genuine plan, actual provider billing, or deployment isolation.

## Reproduce offline checks

Requires Python 3.12+ and its standard library; no installation or credentials:

```bash
python -m unittest discover -s evals/planning-collector -p 'test_*.py' -v
python evals/planning-collector/preflight.py evals/planning-collector/config.example.json
# Expected exit 2, PILOT_BLOCKED; no model calls.
python evals/planning-collector/provenance.py eb7eef49d5a0fe3e84e99be30e8ed9622a694e35
# Run provenance after committing, with a clean worktree.
```

Offline doubles use a marked `TemporaryDirectory` under the OS temp root. They
return transport acknowledgements, not plan-shaped data. They cannot use pilot
or corpus output directories. The only socket is loopback on an ephemeral port.

## Verified feasibility

Fusion supports a custom provider's `baseUrl` and registers it into Pi. The SDK's
OpenAI chat-completions client uses `model.baseUrl`. A future isolated custom
provider can point to `http://127.0.0.1:<ephemeral-port>/v1` with a non-secret
placeholder API key, while the supervisor alone holds upstream authentication.
Do not write these settings into the user's actual home or start a dashboard.

Source citations at `eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`:

- `packages/core/src/types/workflow/workflow-steps.ts:227`: CustomProvider fields.
- `packages/engine/src/auth/custom-provider-registry.ts:123`: baseUrl registration.
- `packages/engine/src/auth/custom-provider-registry.ts:98`: current custom models
  use 128k context / 16,384 output defaults and zero catalog costs. Those defaults
  are NOT verified billing/token bounds; the gateway never trusts them as prices.
- Installed Pi `dist/api/openai-completions.js:558`: SDK baseURL.
- Installed Pi `dist/api/openai-completions.js:582`: usage in streams; `:588`:
  max_tokens/max_completion_tokens serialization.

## Existing retry, compaction, and fallback configuration

Verified: Pi's settings schema supports `retry` and `compaction`, but Fusion's
session constructor supplies an in-memory settings manager with compaction enabled
and three retries (`packages/engine/src/pi.ts:2705`). The interview API does not
expose a retries-off switch. Native malformed-output reformat retry remains at
one (`packages/dashboard/src/mission-interview.ts:104`, `:1234`). Context and
reasoning-effort retries also remain intact (`packages/engine/src/pi.ts:3376`).
Nothing here disables or edits any of those paths. Each forwarded retry receives
a new reservation; rejected attempts can be retried locally by native code but
cannot be forwarded beyond the shared budget. This gateway itself never retries.
Transport failures preserve reservations and permit later native attempts within
the remaining budget; they are not retried inside the gateway. Unsafe model or
artifact failures are terminal. Upstream error status/body are retained so native
retry classification can still operate. Retry-related response headers are not
yet forwarded by the harness; that live-transport integration remains required.

Verified: configured primary/fallback pairs can select a fallback; without a
fallback pair a primary resolution error is thrown (`pi.ts:2715`). Explicit custom
provider/model selection and no fallback configuration are needed. A request for
any different model is rejected before forwarding. Provider-returned physical
model identity can only be checked after dispatch; a response mismatch ends the
run, not an imaginary retroactive cancellation of billing.

Verified: installed Pi `dist/core/agent-session.js:249` resolves summarization auth
from the selected model, and `:2144` passes that model into compaction. Inferred:
for a verified non-virtual custom model, these requests should reach the same
proxy. A native SDK/interview-to-proxy integration test is still required before
live use; label-only offline requests do not prove routing coverage.

## Enforcement implemented

- One shared lock-protected budget for all HTTP attempts, including any interview,
  answerer, format-retry, fallback, or compaction request that reaches this boundary.
- Exact destination and model authorization, no redirects, HTTPS upstream only,
  standard TLS verification and inherited environment proxy routing.
- Text-only OpenAI chat completions, one completion, function tools only, strict
  payload shape. Other dialects/modalities/billable extensions fail closed.
- Optional output ceiling preserves an existing lower cap; absent controls do not
  change the request object or returned bytes. Body canonicalization may change
  insignificant request JSON whitespace. Responses are buffered (bounded), so
  time-to-first-byte differs; this is not identical streaming latency behavior.
- Before each forward, reserve the **full independently verified model input-token
  bound** plus bounded output at supplied maximum prices, rounded upward to integer
  microdollars. This is more conservative than estimating input from bytes. Full
  reservations are never refunded, even on failed/disconnected/ambiguous requests
  or lower reported usage. Reservations are persisted before dispatch. A new Budget
  cannot reopen/reset the same run directory.
- Raw artifacts are created exclusively and hashed. Known sensitive raw content
  is refused rather than silently redacted into purportedly unmodified raw output.
  Failures expose fixed codes, never upstream exception text/headers/credentials.

Model-specific bounds must cover all billable input/output/reasoning/cache charges.
The example's evidence hash is only a declaration: code does not authenticate that
document. **No live supervisor may proceed based merely on a boolean/hash provided
in config.** Unsupported or unverifiable billing contracts remain blocked. Usage
is captured as `provider_reported_usage_unverified`; reservations are explicitly
`estimated_upper_bound`, not measured invoices.

## Mandatory prerequisites before the first genuine interview

1. Complete authorization: provider, physical model, credential variable NAME,
   call cap, spending ceiling, input/output prices, exact approved hosts, pilot
   goal, answerer, and turn cap. Paid inference is still expressly withheld.
2. Independently verify the provider's hard token limits, maximum billing rates,
   reasoning/cache accounting and token-ceiling semantics. Restrict routing/aliases
   to a fixed physical model; fail closed otherwise.
3. Build an isolated native supervisor: per-run temp project/settings/database;
   no dashboard, scheduler, autopilot, durable agents, heartbeat service or MCP.
   Verify resolved MCP is empty before session creation. Freeze/hash the brief and
   committed protocol first. The native start calls the model asynchronously, so
   the proxy and all safeguards must already be armed.
4. Prove exclusive model egress. A custom base URL alone does not prevent another
   provider/tool/runtime from bypassing it. The child must not inherit real auth
   files or upstream credentials. Enforce the approved destination boundary in a
   supported sandbox/network arrangement, not by weakening the platform allowlist.
   No network configuration or home-directory change has been performed here.
5. Wire a real HTTPS transport/credential boundary and model-accurate SDK-to-proxy
   tests, including format retry and automatic compaction. Respect inherited TLS
   trust/proxy credential injection; never expose raw credentials to the child.
6. Add baseline/after snapshots, outbound-host evidence, native transcript/summary
   capture, turn limits, and durable start accounting. Use exactly
   `fusion-phase2a-pilot`; no identifier variation or limiter resets. Native limit
   is inside `createMissionInterviewSession` (`mission-interview.ts:1343`).
7. Record `source_commit`, `collector_commit`, exact binary-diff `patch_sha256`,
   `protocol_sha256`, native/actual upstream model, UTC timestamps and per-request
   latency. `provenance.py` computes the full committed diff hash relative to the
   supplied source commit; it refuses a dirty worktree. No self-referential hash
   is embedded in the commit it hashes.

Until these are satisfied the supported executable behavior is **PILOT_BLOCKED**.
No before/after pilot diff or measured cost/runtime exists. Unmeasured reservation
formula is `calls * (input_bound * input_price + output_cap * output_price) / 1e6`.
Runtime is unmeasured; buffered responses must complete inside native turn guards.

## Why no native patch

Inferred: the external boundary can enforce request count/reservations without
changing native retry/compaction policy, for the supported contract and exclusive
routing deployment. A native production extension is therefore not yet justified.
If the remaining routing/contract proof fails for the selected provider, re-evaluate
an additive SDK-level authorization hook; do not replace native inference or
represent this offline prototype as production-ready.
