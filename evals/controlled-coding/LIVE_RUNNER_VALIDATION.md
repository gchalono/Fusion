# Controlled live runner validation

Implementation baseline: `25e38461597daa5ea656f58212402ac026df3b54`.
Worktree: `/workspaces/Fusion-controlled-live-independent`.
Branch: `wip/controlled-live-independent`.

This is a new validation record for the separate experiment described in
`LIVE.md`, not a replacement for historical recovery records. The operator
directed that historical Phase 2N discrepancies do not gate this experiment.
No historical recovery pass is claimed. The original dirty checkout is preserved.

## What changed

Explicit task selection now produces the corresponding frozen fixture binding;
the default remains the first canonical task and unknown tasks fail closed.
Initialization uses the same selection. The coding launcher resolves the Node
interpreter symlink to match the interpreter exposed inside the sandbox.
No spending, approval, reservation, isolation or provider-cap checks were relaxed.

## Surface Enumeration

The shared fixture helper serves the live runner, offline initialization,
fixture description and input generation. Validation covers the default, every
registered frozen task, distinct task hashes and unknown-task refusal. The shared
launcher serves live and offline coding; the existing execution regression checks
that a symlinked interpreter resolves to the namespace runtime mount. The live
integration exercises the launcher through the actual sandbox and coding session.

## Symptom Verification

- Original symptom: the live runner and live tests failed on explicit fixture
  selection because the shared helper accepted no task argument.
- Exact reproduction: run `test_live.py` from the baseline worktree; selected
  tests failed in setup with `fixture_binding() takes 0 positional arguments`.
- Assertion it is gone: all 12 live tests pass after the fixes, including an
  end-to-end coding session, local TLS transport and independent grading. All
  registered fixture bindings are checked by a behavioral regression.

## Measured offline verification

Pinned pnpm 10.33.0 installed dependencies from the local cache using
`pnpm install --offline --frozen-lockfile --ignore-scripts`.
`pnpm --filter @fusion/core build` passed.

- `/usr/bin/python3 -B -m unittest discover -s evals/controlled-coding -p test_live.py -v`:
  12 passed, no skips. Only synthetic signing material and local TLS transport.
- `test_inputs` and `test_offline_execution`: 3 passed, no skips.
- `/usr/bin/python3 -B evals/controlled-coding/harness.py verify`: passed.
- Secret scan against the verified baseline and `git diff --check`: passed.

These results establish offline operational behavior, not provider availability,
actual billing behavior, a successful paid model run or permission to spend.

## Remaining live gates

Use this worktree for both the runner and `--runtime`; do not use the original
checkout path from the older example in `LIVE.md` for this experiment.

Before any paid request, the operator must independently verify a dedicated,
genuinely enforced $2 provider limit, the exact model's availability and current
conservative prices. `provider_side_cap_confirmed` remains mandatory. Option B
remains paused. A separately reviewed contract may be supplied via `--contract`;
historical parameters need not be rewritten.

Explicit paid authorization is still required. The runner must receive the
independently trusted public key, separately signed $0.12 run and $2 aggregate
authorizations, and private dedicated provider credentials, all outside public
runtime mounts. Both signatures bind the reviewed contract and the same durable
ledger path. A new experiment starts with a dedicated ledger; failures do not
authorize replacement ledgers, retries or refunds. Fresh output must be private
and outside the runtime mounts. See `LIVE.md` for the exact authorization schema.

No paid requests, real approvals, commits or pushes were performed.
