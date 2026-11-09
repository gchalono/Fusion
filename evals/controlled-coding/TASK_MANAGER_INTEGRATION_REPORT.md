# Experiment 2 task-manager offline integration

<!-- FNXC:TaskManagerIntegration 2026-11-09-19:52: Preserve genuine frozen inputs, keep spending authorization zero, reuse the secured runner boundary, and report blocked native loops and failed grading without substituting offline controls for coding results. -->

**TASK_MANAGER_FAILED** — VERIFIED: required positive-reference browser validation
was run and failed. Independent native-loop budget incompatibilities also block
complete A/B/C integration. No paid readiness or native coding result is claimed.

## Gate 0 and immutable sources

VERIFIED: dedicated worktree `/workspace/Fusion-phase2n-integration`, branch
`eval/phase2n-task-manager-offline`. Origin fetch/push URLs both identify only
`https://github.com/gchalono/Fusion.git`. Managed runtime was running/connected.
Required full persistence preflight passed before edits on the clean `eval/phase2n`
worktree; only then was the dedicated integration branch created. Evidence:
`/workspace/phase2n-reconciliation-evidence/integration-gate0-preflight.json`.
No Gate 0 failure was bypassed.

VERIFIED references:

| Reference | Full SHA |
|---|---|
| Infrastructure checkpoint | 73dd29ab2237fb9e7c47458b9deb0b11d681f033 |
| Recovered preparation | 40a06aa5cb932ddc0ed9bf232aca00999b355d96 |
| Resolved reconciliation | 29d027ae80795e3803ff64ddb592bc8aad0762ee |
| Recomputed common ancestor | 3d92a302853c32472d2420d3835200ecc469905f |
| Independently fetched integration baseline | bf23a5ccbae2e7347cc533be00e38b89cef7c59a |

VERIFIED: neither requested development checkpoint is ancestor of the other.
Original branches, recovery refs and original verified Git bundle remain intact.
Preparation ZIP SHA-256 `e774b5dca79faad9c3b9f8afba03b43f1f48c940b99275ec11da311c155e4679`
was rechecked; ZIP manifest and A/B/C prompt bytes match the recovered originals.
No merge, rebase, cherry-pick, reset, clean or push was performed.

VERIFIED baseline unit tests: controlled-coding **29**, collector **37**, persistence
**9** = **75 passed, 0 failed, 0 skipped**. Post-change totals: **37 + 37 + 9 = 83
passed, 0 failed, 0 skipped**. Commands and fresh logs are under
`/workspace/tm-integration-evidence/`: `baseline-*.log`, `final-*.log`.
The separate isolated reference local test also passed one test. Passing unit
suites does not override the failed browser integration check.

## Provenance, treatments and manifest

VERIFIED: `TASK_MANAGER_EXPERIMENT_MANIFEST.json` contains source SHAs, all selected
input paths/hashes, original question identity hashes, eight answer/approval/command
hash bindings, model/environment settings and a separate Experiment 2 budget identity.
`task_manager_adapter.py:verify_sources` verifies original manifest hashes/lengths,
PILOT_SUCCESS source, complete chained human audit, exported question identities,
explicit approved commands and exact submitted answers. All eight historical native
answers were also revalidated through the preserved pure JS validator. The adapter
refuses Python benchmark task IDs, changed inputs and cross-arm contamination.

VERIFIED: this is the frozen personal-task-manager objective, not one of the three
Python fixtures. Genuine native plan SHA-256:
`f35c276d3a69484914e5581f8c1548b6f29b34449add117a87578bfae5d34456`.
Historical Phase 2M planning source is `eb7eef49d5a0fe3e84e99be30e8ed9622a694e35`,
collector `eb189ace34f375e3e40e25975c276c448083e8f7`. Historical approvals are genuine
chat-backed task-manager records; they are not new approvals, not Python-task
approvals and not fabricated TTY/HMAC records. No raw approval text or provider record
is introduced into Git by this integration. Private source files remain outside Git.

VERIFIED input reproduction:

| Arm | Bytes | Exact prompt SHA-256 | Material |
|---|---:|---|---|
| A | 3435 | eeb98f4c68aa3ae99907cc8475b2e9ab97a4945cb7acf0942b72c033083f9495 | Frozen common instructions + objective |
| B | 8943 | d00040330c3361836bb7e768172a89af0147d6c0884de0ec0de271baadc555a7 | A + unedited native plan |
| C | 11467 | 22c0339f292f8a6c69b2d539a6789c902e4783908e0fc51c48393986b0f0d8bb | B + eight original approved answer JSON byte sequences |

VERIFIED: no plan, answer, approval, prompt, original acceptance criterion or original
hash changed. New source-manifest drafts were preserved outside Git before replacing
the integration draft; original frozen preparation artifacts were never overwritten.
Order B/A/C, seed 20261104, is preserved. All arms require identical settings and
criteria. Inputs are mounted read-only individually in boundary probes; other arm
inputs, approval files and hidden checks are absent from the namespace.

## Reuse and scope of implemented adapter

VERIFIED: existing `execution.run_command`, `isolation.namespace_command`,
`inference_socket`, `security_filter.export_filter`, `Gateway`, `guard_gateway`,
`AggregateBudget` and private-MAC grading pattern are reused unchanged. Existing
Pi entry remains `coding-agent.mts` and native engine helper remains unchanged.
No production file, Python fixture, existing budget configuration, or existing
runner source was edited. No alternate coding orchestration framework was added.

VERIFIED new evaluation-only files:

- `task_manager_adapter.py`: read/verify original inputs, task-bound import,
  distinct offline contract, byte-exact input loading, pre-dispatch feasibility proof.
- `task_manager_probe.py`: exact-input non-agent namespace/gateway/ledger tests,
  wrong-endpoint/model/token/hosted-tool refusal, revocation and shutdown checks.
- `task_manager_grader.py`, `task_manager_browser.mjs`: prototype independent,
  fresh-Git-checkout observation of original core behaviors, authenticated result;
  candidate subprocess gets no real credential or grading key.
- `task_manager_reference.py`: clearly labeled TEST DOUBLE reference control.
  It is never a treatment plan, agent-generated implementation or approved answer.
- `task_manager_controls.py`: explicit positive/negative reference controls and repeat.
- `test_task_manager_adapter.py`: eight source/budget/task-isolation regression tests.

UNVERIFIED: these are not a completed native Pi dispatch adapter. The reused Pi
entry was not launched because shared experiment preflight cannot admit complete
unchanged B/C tool loops. No automatic limit increase or prompt shortening was used.
The original preparation expects `/app`; the runner mounts `/work`. A future minimal
trusted workspace alias must preserve the exact prompt and containment; it is not
silently assumed in this phase. Multi-file implementation collection and general
candidate launch/test adapters remain absent; the current grader controls use an
explicit reference-specific `application.py`/`--test` observation interface.

## Budget findings: separate Experiment 2 identity

VERIFIED: inherited `Contract` supports separate JSON contracts and `AggregateBudget`
binds a separate database immutably to the experiment. The adapter derives ONLY an
offline Experiment 2 identity; Python benchmark JSON, nine-run ledger and approvals
are untouched. No combined allowance or $6 proposal is introduced.

VERIFIED arithmetic from the operator's stated offline limits:

`3 × $0.12 + $0.50 = $0.86 ≤ 80% × $2.00 = $1.60`.

VERIFIED: aggregate ceiling $2, planning allocation $0.50, coding allocation $0.36,
per-run cap $0.12, unallocated headroom $1.14, four coding requests/run, 300s run,
60s request, inherited 16,000 cumulative token upper bound. No limit was raised.
The 512-output setting belongs to the existing offline wire TEST DOUBLE profile;
4096 remains its contract upper ceiling. It is not a newly approved live profile.
No allocation is undefined in this explicitly derived OFFLINE three-arm contract;
**paid authorization remains $0.00**. No future paid DB or paid experiment was armed.
Historical planning charges were not imported, refunded or combined with this test DB.

VERIFIED blocker: under `budget.py:reserve`, cumulative `input_upper+output_upper`
is limited to 16,000. `contract.py:prepare` conservatively bounds each input by
serialized bytes. A native tool result requires another request retaining the
unchanged user input. Even ignoring all system/tool/schema/output overhead:

| Arm | Two-request prompt-only lower bound | Result |
|---|---:|---|
| A | 6870 | UNVERIFIED: actual native/tool overhead not measured |
| B | 17886 | BLOCKED: exceeds 16000 |
| C | 22934 | BLOCKED: exceeds 16000 |

VERIFIED: a regression replays these B/C bounds against the actual shared-ledger
implementation: first reservation admitted, second rejected with
`frozen_coding_token_limit`; no second dispatch occurs. This is an expected
fail-closed test, not a failed unit test, tokenizer estimate or model capability claim.
INFERRED: a complete native multi-request implementation loop cannot pass the
unchanged conservative contract for B/C. The dollar cap passing does not fix this.

## A/B/C: required twelve checks

VERIFIED observations are from TEST DOUBLE boundary probes, not coding interviews.
No secured Pi session or coding tool execution is represented as having occurred.
Full native dispatch was not started for A either: shared all-arm feasibility and
positive grading validation failed. Zero actual model/agent sessions were started.

| Check | A | B | C |
|---|---|---|---|
| 1 Exact frozen input loaded | VERIFIED | VERIFIED | VERIFIED |
| 2 Secured Pi session created | BLOCKED common preflight | BLOCKED token cap | BLOCKED token cap |
| 3 Gateway-only inference | VERIFIED probe only; native UNVERIFIED | Same | Same |
| 4 Real credential unavailable | VERIFIED probe | VERIFIED probe | VERIFIED probe |
| 5 Only authorized input readable | VERIFIED probe | VERIFIED probe | VERIFIED probe |
| 6 Expected coding tools executed | UNVERIFIED, no Pi | UNVERIFIED, no Pi | UNVERIFIED, no Pi |
| 7 Code changes captured | UNVERIFIED, no Pi | UNVERIFIED, no Pi | UNVERIFIED, no Pi |
| 8 Independent candidate acceptance | UNVERIFIED, no candidate | UNVERIFIED, no candidate | UNVERIFIED, no candidate |
| 9 Reservation for every request | VERIFIED one local probe request | VERIFIED one local probe request | VERIFIED one local probe request |
| 10 Ledger survives interruption | VERIFIED adapter ledger test; Pi UNVERIFIED | Same | Same |
| 11 Agent/descendant containment | VERIFIED non-agent processes; Pi UNVERIFIED | Same | Same |
| 12 Resource cleanup | VERIFIED probe sockets/threads/children | VERIFIED probe | VERIFIED probe |

VERIFIED raw evidence: `/workspace/tm-integration-evidence/integrated-security-A.json`,
`integrated-security-B.json`, `integrated-security-C.json`. These tests use one shared
Experiment 2 TEST DOUBLE ledger under `/tmp/fusion-tm-boundary-suite/`.
Each authorized local request got one reservation; missing usage retains UNCERTAIN
exposure. A/B/C reserved 2250/4581/5630 micro-USD respectively, 12461 total. This is
synthetic conservative exposure, **not provider spend**. Revoked/shutdown requests
created no new reservation or local upstream contact. Earlier standalone probe DBs
are labeled disposable fixtures, not independent paid allowances per arm.

## Acceptance controls and root-cause limits

VERIFIED: isolated reference HTTP core checks pass: creation, retrieval, editing,
completion, due dates, actual SQLite rows and process-restart persistence, deletion
and local web response. A standalone real unittest exercises CRUD and SQLite in the
same hardened namespace: one passed (`reference-unit.log`). Original scope alone is
being observed; no dark-mode, title-length, reopening, error-code or styling criterion
is added. Routes/entry filenames are explicit control-interface assumptions, not
claimed requirements from the original objective or a universal grader.

VERIFIED: known-incorrect, hidden-test-tampering and fabricated-success controls are
rejected; agent stdout/exit status cannot authenticate acceptance. Trusted test source
is mounted read-only and result MAC key remains in a nondumpable protected process.
Those negative rejections are expected successes of the controls.

VERIFIED FAILURE: complete positive reference validation did not pass. Chromium
closes before creating a page (and, with an alternate trusted browser launch profile,
before launch completes). Final controls preserve reference and repeat failure rather
than converting seven HTTP checks into task success. Evidence: `final-controls.log`,
`final-controls/reference/grader-stderr.txt`, `final-controls/results.json` when present;
prior attempts remain under `full-reference-controls*` and `browser-*` directories.

VERIFIED diagnostics include missing fontconfig configuration, a SIGTRAP on one
profile, and denied ptrace in crash reporting. INFERRED: browser/runtime compatibility
with the current narrow mount/seccomp view needs diagnosis. UNVERIFIED: which event
causes the page closure; ptrace denial may be a post-crash symptom. A read-only font
configuration mount did not fix it and was not retained. A single-process trusted
browser profile did not fix it and was not retained. No seccomp, namespace, capabilities
or coding permissions were weakened. No system package or network policy changed.

BLOCKED: full browser/candidate acceptance and a generally applicable multi-file
candidate adapter. Smallest repair is to diagnose the trusted browser through the
existing isolated-browser bridge pattern or supply its verified read-only runtime
requirements, then validate complete original-objective observations without changing
coding security. Do not use hidden acceptance-interface conventions as extra product
requirements. Until then Step 5 grading remains UNVERIFIED.

## Security, recovery and reproducibility

VERIFIED on the input adapter plus reused boundary for all three arms: exact-input
hash, gateway positive control, wrong endpoint/token/model/hosted-tool denial, frozen
prompt write denial, hidden-check/host-workspace/other-input denial, real provider env
and inherited proxy absence, no_new_privs, denied non-gateway network route, token
revocation and gateway shutdown fail-closed. All 16 measured assertions passed per arm.
No real provider destination was contacted, even for a negative control.

VERIFIED at the adapter/ledger layer: interrupted FORWARDED requests reopen as
UNCERTAIN, retain exposure, refuse implicit continuation and require explicit active
run resume; concurrent reservations admit only three $0.04 reservations within a
$0.12 run cap; cross-experiment IDs and contract migration are rejected. Existing
unit suites cover aggregate, streaming/missing usage, local TLS, lifecycle and crash
handling. These unit results are not fresh native Pi security/recovery runs.

UNVERIFIED integrated native checks: actual Pi unauthorized-tool dispatch, descendants,
transport interruption while coding, full worker crash/restart and authorized native
resume, protocol-identical DNS/IPv6/raw/direct-provider controls, live credential sole
egress and live service fidelity. Minimum next action: repair stated preflight/grade
failures, wire the minimal native adapter, then run the existing controls through that
actual path with explicit local doubles. Do not relabel old standalone checks.

VERIFIED: A boundary probe was repeated from the same frozen prompt in fresh test
state. Before comparison normalization excludes timestamps, temp paths and unrelated
arm rows; compare input SHA, check booleans, run exposure, request/reservation counts
and transition states. They match: one contact/reservation, 2250 micro-USD and
RESERVED/FORWARDED/UNCERTAIN. Partial reference HTTP observations also repeated.
UNVERIFIED: a complete native arm repeat, normalized implementation patches, successful
full acceptance or complete native evidence-hash reproducibility. No claim of coding
reproducibility follows from these smaller repeated controls.

## Persistence, reproduction and next actions

VERIFIED commands (run from this dedicated worktree):

```sh
# Gate 0 command was run on clean upstream eval/phase2n BEFORE branch creation:
evals/persistence/preflight.sh --baseline 73dd29ab2237fb9e7c47458b9deb0b11d681f033 --branch eval/phase2n
python -m unittest discover -s evals/controlled-coding -v
python -m unittest discover -s evals/planning-collector -v
python -m unittest discover -s evals/persistence -v
python evals/controlled-coding/harness.py verify
python evals/persistence/scan.py --base bf23a5ccbae2e7347cc533be00e38b89cef7c59a
# Local-only control commands require new destinations; never overwrite evidence:
python evals/controlled-coding/task_manager_controls.py --out NEW_PRIVATE_DIRECTORY
python evals/controlled-coding/task_manager_probe.py --evidence /workspace/phase2m-genuine-success --prepared /workspace/phase2n-evaluation/frozen --arm A --out /tmp/NEW_MARKED_PROBE_DIRECTORY
```

VERIFIED: the initial scanner flagged three descriptive evidence-directory paths
as credential-pattern matches; manual inspection found no credential in those lines.
Shorter filesystem aliases now give readable report paths without matching that
pattern. The scanner and its policy were not weakened or allowlisted.
VERIFIED: scanner covers new current files and introduced commit blob versions;
manual review confirms no credentials, raw approvals or raw provider records are
introduced. Existing Python frozen manifest verifies unchanged. The dedicated local
branch has no remote counterpart; final remote persistence preflight is expected to
refuse remote backup claims, never authorize a push. Code checkpoint and local Git
bundle paths are supplied in the operator summary. Same-VM bundles are local recovery,
not verified off-VM backup. No private evidence is added to a downloadable code package.

BLOCKED next decisions/work, in smallest order:

1. Repair and rerun the failed trusted-browser reference control without weakening
   the coding boundary; then finish neutral multi-file/launch/test observation adapters.
2. Operator must explicitly resolve the separate Experiment 2 cumulative token-bound
   incompatibility. No new value is invented here: the unchanged B/C prompts alone
   establish lower bounds, not sufficient live limits. Choose a revised Experiment 2
   resource contract only after measuring full native request overhead, or explicitly
   authorize a new frozen experiment definition. This phase cannot raise limits or
   shorten existing inputs. The $2/$0.12 dollar limits need not increase.
3. Add the trusted /app workspace alias, minimal native Pi input/capture adapter,
   integrated crash/security controls and complete all-arm repeat after gates permit.
   Existing Pi, gateway and ledger implementation should be reused, not replaced.
4. Before any later paid pilot: separately approve paid execution, verify exact model
   availability/current prices, provider-side ceiling and private authorization,
   gateway-only live credential routing, full live/schema/compaction compatibility,
   all gates and durable private-evidence backup. Current provider authorization stays zero.

VERIFIED final provider spending is **$0.00**: all new upstream behavior is an injected
local function TEST DOUBLE or local reference application; baseline TLS tests use
loopback doubles. No real provider transport or Pi session is invoked by new commands.
No billing measurement is claimed. No mission, task, autopilot, production-code change,
paid interview, live coding trial, push, merge or deployment occurred.
