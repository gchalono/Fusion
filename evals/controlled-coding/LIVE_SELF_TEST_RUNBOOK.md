# Fresh-task self-test experiment: human operator procedure

This prepares `parse-duration:A`, design `controlled-live-local-self-test-v1`.
It is a fresh task in the existing registered task set, not a replay of either
merge-intervals run and not a historical Phase 2N arm comparison. The public
objective asks for a duration parser; it exercises repeated units, invalid input
and component parsing. No acceptance cases or expected answers are added to the
agent input. Frozen fixtures, acceptance tests and contract are unchanged.

The read-only preparation check observed cumulative reserved exposure of
**14115 micro-USD ($0.014115)**, A INCOMPLETE and B COMPLETE. Recheck this at
preflight; the observation is not a promise of future headroom. All reservations,
including uncertain exposure, remain charged against the **same cumulative $2**
ceiling and existing coding allocation. There is no additional allocation.
Run limits remain **$0.12, four gateway attempts, 300 seconds, 16000 cumulative
bounded tokens**, with the existing request deadline and 512-token adapter output
ceiling. The local loop adds tighter time/tool/output bounds; it grants no retries
of failed model calls. An exhausted budget can prevent repair or submission.

The prior B renewal was explicitly B-only. The new code permits exactly one
separately signed fresh-task continuation, linked to the original expired root
and the expired B renewal using the original public trust anchor. Both historical
receipts and consumed run identities must match the existing ledger. A and B
cannot be replayed. Nonce collisions, forks, changed limits/contracts, active
conflicts, changed implementation, unregistered or used task identities, and
insufficient headroom fail closed. No ledger bootstrap is allowed in this mode.
Only a subsequent human-authorized launch appends new authority/run records;
signing and preflight do not modify or consume the ledger or prior approvals.

The signed run pins hashes of the live adapter, self-test loop and trusted
execution/authority modules. Preflight, transport setup and each parent/worker
dispatch verify the binding. Edit those files after signing and the run refuses;
do not overwrite the approval to accommodate an edit. Stop and prepare a separate
human-reviewed proposal instead. This binds source code, not every runtime
dependency; changes to installed dependencies require offline revalidation.

The coding namespace mounts `live-agent.mts`, `self-test-session.mjs` and public
runtime only, plus the public objective and existing scoped gateway capability.
It does not mount this runbook, operator helper, approvals, contract, ledger,
provider credential, signing keys or acceptance fixtures. Agent-authored tests run
inside that namespace. After successful final submission, only the solution patch
enters a new independent grading namespace. Grading never feeds the coding agent.
Successful local checks are mandatory and recorded separately from acceptance.

## Human signing: no launch

Run in a private interactive terminal on this existing worktree. Do not paste
approvals, keys, passphrases or provider records into chat. Reuse the existing
encrypted signing key; do not generate another key or ledger. The helper reads
provider/signing-key metadata only; OpenSSL opens the signing key and prompts for
its passphrase in the human terminal. It never opens the provider credential.

Expected existing names under `$HOME/fusion-first-live-authority`:
`aggregate.json` (original root), `aggregate-renewal-B.json` (consumed B renewal),
`operator.pub`, `operator-private.pem`, `provider-key`, `contract.json`, and
`experiment.db`. If actual historical filenames differ, stop and inspect the
local helper configuration privately; do not rename or overwrite historical files.
Both historical aggregate documents must be expired. Their expiry is accepted
only as continuity evidence, never as active dispatch authority.

The operator must independently confirm exact-model availability and conservative
original pricing now. The helper asks for those verification references and an
explicit acknowledgment of the absence of a provider billing hard cap. It creates
only new `aggregate-self-test-003.{payload,sig,json}` and
`run-self-test-003.{payload,sig,json}` files, with one-hour validity. Any existing
filename, including a partial signing result, causes refusal. Preserve partial
artifacts and investigate; do not remove them to retry.

```bash
cd /workspaces/Fusion-controlled-live-independent
umask 077
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py sign \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-003"
```

## Human read-only preflight: no launch

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py preflight \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-003"
```

Require `RELIABILITY_PREFLIGHT_VERIFIED_NO_EXECUTION`, `parse-duration:A`, the
new design, the pinned implementation hash, cumulative retained exposure and
unchanged $2/$0.12/four-request/300-second limits. It checks an unused run and a new
output path without creating output or reading provider credential contents.
It is not evidence of current provider availability or a successful live run.
Stop on any refusal; do not change protected records, caps or test expectations.

## Human-only launch: paid execution, separate explicit action

Only after reviewing successful preflight and the spending/expiry constraints:

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py launch \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-003"
```

This rechecks preflight, then requires the human to type
`LAUNCH ONE FRESH SELF-TEST RUN`. It invokes exactly one
`live.py --arm-live --reliability --task parse-duration --run parse-duration:A`
with the new authority pair, original trust anchor, original contract and ledger,
and both historical aggregate paths. There is no automatic launch, replay,
resume, signing renewal, model substitution or paid retry. Failure preserves
consumption/exposure and leaves the run INCOMPLETE. Do not use a new output path
to replay a consumed identity.

Privately inspect `termination.json`, the separately recorded `local_self_test`
and `implementation_sha256` in `live-observation.json`, and independent acceptance.
`repairs: 0` means no supervisor repair was required, not that repair was tested by
that live run. `repairs: 1` records a supervisor continuation. Neither guarantees
test quality or general accuracy. Keep raw logs private; do not feed grading
output to another agent iteration. Preserve Runs A/B without rewriting results.

## Offline verification and limits

The live-path control uses the actual live adapter, Pi session/tools, local
Python tests, budget gateway and independent namespace grader. Only the paid
transport is replaced by a local TLS scripted test double. Its public-spec tests
fail on an initial candidate and the single continuation repairs it. This is
mechanical validation, not a genuine model performance measurement.

The initial control hit the unchanged cumulative token limit before final
submission. Prompt guidance and repair feedback were shortened to fit the
existing limits; no budget or assertion was relaxed. Feedback contains concise
local failure identifiers and exception lines (at most 256 characters), with
existing tools available for deeper inspection. A real model may still exhaust
its budget or produce weak tests. Model availability/pricing and genuine live
outcome remain unverified until the human performs the steps above.

```bash
python -B -W ignore::ResourceWarning -m unittest discover -s evals/controlled-coding -v
python -B -W ignore::ResourceWarning -m unittest discover -s evals/planning-collector -v
python -B -m unittest discover -s evals/persistence -v
node --test evals/controlled-coding/self-test-session.test.mjs
python -B evals/controlled-coding/harness.py verify
python -B evals/persistence/scan.py --base HEAD
git diff --check
```

Preparation verification passed: 87 controlled-coding tests (including nine new
fresh-run/live-path tests), 37 planning/gateway tests, nine persistence tests,
and all 11 separately reported Node orchestration cases. Frozen fixture
verification, credential-pattern scan, Python syntax and diff checks passed.
The genuine Pi/live-adapter synthetic control completed with one repair, four
local TLS requests and passing independent acceptance under the existing caps.
The final read-only ledger check still reported 14115 micro-USD, unchanged A/B
statuses, no `parse-duration:A` control record, no new signed authority files and
no new output directory.

No real authority was signed, provider credential read, paid call made, live run
launched, contract changed, ledger reset or historical artifact modified during
preparation. The baseline recovery exception remains the operator-authorized
scope from this conversation; no historical recovery status is reclassified.
