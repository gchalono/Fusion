# Task-manager token and browser feasibility

VERIFIED scope: offline Experiment 2, branch `eval/phase2n-task-manager-offline`,
originating at `67749361f8aba2aac5559290975f946d3f34a5c9`. Provider authorization
remains **$0.00**. No production source, security filter, namespace builder,
frozen treatment, original answer/approval, active dollar cap or active token
bound changed. Model identity: `gpt-4.1-mini-2025-04-14`. Tokenizer: unavailable;
all token-related measurements below are explicitly conservative BYTE-based
reservation units, not measured tokenizer/provider tokens.

## Local-only Gate 0

VERIFIED: original remote preflight failed solely with
`REMOTE_BASELINE_UNVERIFIABLE`; worktree and artifact checks were clean. Its saved
record is `/workspace/tm-resume-evidence/original-remote-preflight-failure.json`.
The operator subsequently authorized local-only verification exclusively for this
offline task rooted at the supplied checkpoint. No approval artifact was fabricated.

VERIFIED: `evals/persistence/task_manager_local_gate0.py` is a separate wrapper;
default `preflight.sh`, `tooling.py`, live preflight and live authorization logic are
unchanged. The wrapper ran from `/tmp` BEFORE being copied into the clean repository,
so its clean-before-edits check was not waived. It passed **53 checks**, including
exact commit/HEAD/branch, clean worktree, existing bundle, bundle verification,
isolated fresh recovery, all four commit objects, complete Git connectivity,
recovered manifest equality, **35 input hashes**, original provenance and eight
approval bindings, frozen artifact inventory and unchanged local refs.

VERIFIED receipt: `/workspace/tm-resume-evidence/local-gate0-authorized.json`.
It explicitly states `valid_for_paid_preflight:false`, remote publication UNVERIFIED,
and provider authorization $0.00. It is a verification receipt, not a user approval
for inference or token changes. The original bundle remains unchanged; its convenient
alias is `/workspace/tm-original-recovery.bundle`.

VERIFIED independently checked references:

| Reference | SHA |
|---|---|
| Start checkpoint | 67749361f8aba2aac5559290975f946d3f34a5c9 |
| Infrastructure | 73dd29ab2237fb9e7c47458b9deb0b11d681f033 |
| Preparation | 40a06aa5cb932ddc0ed9bf232aca00999b355d96 |
| Reconciliation | 29d027ae80795e3803ff64ddb592bc8aad0762ee |
| Merge base of infrastructure/preparation | 3d92a302853c32472d2420d3835200ecc469905f |

## Chromium diagnosis and capability blocker

VERIFIED root cause, normal multiprocess profile: **Chromium's zygote children
attempt `capset(... effective=0, permitted=0, inheritable=0)`, the mandatory
seccomp filter returns EPERM, and Chromium's fatal credential check prevents
GPU/renderer creation and disconnects the browser before page creation.**
`security_filter.py:14-19` explicitly denies capset. The filter was not altered.

VERIFIED: a real minimal launch/context/page/close reproduction is preserved in
`browser_minimal.mjs`; it calls Chromium, not a mocked page. Evidence is under
`/workspace/tm-resume-evidence/browser-*`. Verbose browser logs show
`FATAL:sandbox/linux/services/credentials.cc:371`, zygote fork failures and
`GPU process isn't usable`. An outer diagnostic strace, without changing the
tracee's filter, records repeated all-zero capset calls returning EPERM in
`browser-syscalls.log`. Denied crash-reporter ptrace is a subsequent symptom.

VERIFIED hypothesis checks:

| Hypothesis | Observation |
|---|---|
| Premature teardown | launch and context succeeded; newPage failed before finally/close |
| Timeout / owner shutdown | failure occurred in ~1s with a 30s watchdog; not timed out or aborted |
| Child identity / seccomp | denied capset and matching fatal credential check directly observed |
| /dev/shm | Playwright already supplies disable-dev-shm-usage; no repair resulted |
| Missing fonts | read-only font configuration did not repair the in-process profile |
| Zygote/GPU profile | no-zygote/single-process/in-process-GPU profile also failed, with SIGTRAP |
| Basic executable/driver handshake | installed Chromium 155 / Playwright 1.60 created a context in normal profile |

UNVERIFIED: deeper compatibility of alternate profiles; their SIGTRAP is not
attributed to capset without evidence. No blanket claim that every dependency
or every browser version was tested is made.

BLOCKED: no compatible working browser profile has been demonstrated under the
unchanged mandatory filter. Browser gate did NOT pass. The positive reference was
rerun and FAILED; incorrect, tampering and forged-success controls were rejected.
Browser-specific page-level network/file/canary tests remain UNVERIFIED because
no page could be created; actual native coding-path negatives are reported separately.
No browser result was mocked and no permission check, mask, capability, namespace,
sandbox, network restriction or negative control was removed.

INFERRED smallest next action: supply/validate a browser runtime compatible with
this filter or a separately reviewed trusted-browser design preserving every
security property. This agent does not propose allowing capset or bypassing its
failure with a shim. The blocked browser gate does not prevent native execution.

## Quantities and measurements

VERIFIED source semantics: `budget.py:137-145` sums every persisted
`input_upper + output_upper` for the SAME coding run; it is not input-only, not a
per-request limit, and does not deduct completed, failed or uncertain attempts.
`contract.py:prepare` uses max(received JSON UTF-8 bytes, normalized JSON UTF-8
bytes) as its conservative input bound. The active cumulative ceiling remains
**16,000**. Four underlying requests and all original retry/compaction behavior
remain enabled, subject to the same budget, request and deadline gates.

VERIFIED two-request loop: request 1 contains system + exact frozen user input +
tool schemas and produces a tool call; the actual tool executes; request 2 resends
that context plus assistant tool-call message and tool result. Native A captured
both real requests at the local TLS double. B/C measurements replace only the
exact user-input field in COPIES of those captured templates: they are dry
projections, not B/C native executions or reconstructed plans/approvals.

VERIFIED: no model tokenizer/encoding table is installed. The contract's conservative
bound is used; UTF-8 length is never labeled measured model tokens. Raw measurement
metadata is `token_measurements.json`. Private native wire bytes remain outside Git.

VERIFIED component sizes (JSON bytes; component containers overlap framing, so
use full request sizes for reservations rather than summing these columns):

| Component | A | B dry | C dry |
|---|---:|---:|---:|
| Frozen initial prompt UTF-8 bytes | 3435 | 8943 | 11467 |
| Serialized prompt string | 3483 | 9311 | 11935 |
| System/developer message JSON | 168 | 168 | 168 |
| Tool schemas | 1661 | 1661 | 1661 |
| Assistant tool-call message | 456 | 456 | 456 |
| Actual tool-result message | 101 | 101 | 101 |
| Initial full request input bound | 5521 | 11349 | 13973 |
| Follow-up full request input bound | 6076 | 11904 | 14528 |
| Active offline output reserve per request | 512 | 512 | 512 |
| Two-request cumulative reserve | **12621** | **24277** | **29525** |
| Same captured inputs + two contract-max 4096 outputs | 19789 | 31445 | 36693 |

VERIFIED: the coding reply fixture is bounded to 449 serialized bytes before native
message conversion, below the unchanged 512 output bound. This is a deliberately
incomplete SQLite/HTTP coding CONTROL, not a finished task manager, real model output
or estimate of a real model's response distribution. The original 4096 pricing
contract maximum and the stricter active offline 512 profile are distinct.

VERIFIED reconciliation: prior B/C figures **17886 = 2*8943**, **22934 = 2*11467**
are correct prompt-only lower bounds. They omit system/tool/schema/JSON escaping,
assistant/tool history and output reservations. Full fixture bounds are higher by
**6391** and **6591** respectively. A's 12621 is verified against actual ledger
bounds `(5521,512)` and `(6076,512)` and fits 16000. B/C do not fit.

VERIFIED: native A had zero extra retry/format/compaction HTTP requests. Worst case
allows only four underlying attempts TOTAL, including those operations and errors;
a fifth is refused. Tool-result growth beyond 32000 serialized input bytes fails
closed rather than silently widening bounds. Largest projected request + offline
output is 15040, below configured native context 32000; even adding contract-max
4096 yields 18624. The supplied model context 1047576 was not independently queried;
actual provider model availability/context remains UNVERIFIED.

## Pricing and dollar feasibility

VERIFIED pricing configuration: `experiment-parameters.json`, operator-supplied
input $0.40/M, cached $0.10/M, output $1.60/M. Calculations use UNCACHED input only.
Provider usage is absent in these TEST DOUBLE streams; no cache savings or actual
billable token count is fabricated. Actual real-provider spending is $0.00.

VERIFIED monetary arming formula is `Contract.arming_errors`, lines 30-35:
`planning + coding_runs * per_run <= 0.8 * aggregate`.
For the separate three-run Experiment 2 contract:
`$0.50 + 3*$0.12 = $0.86 <= $1.60 = 0.8*$2.00`.
The actual Contract instance reports only MODEL_AVAILABILITY_UNVERIFIED and
NO_PAID_AUTHORIZATION, not an allocation violation. Planning/coding allocation
is unchanged; no dollar ceiling or allowance was increased.

VERIFIED budget table; token columns are conservative reservation units, NOT actual
model tokens. Worst-case dollars reserve FOUR full contract-sized requests,
including failures/retries/compaction; the current active bound can reject earlier.

| Arm | Prompt bound | Fixture min 2-request bound | Shared fixture reservation | Worst-case four-request $ | Fits $.12 | Fits $2 aggregate | Request cap 4 | Wall limit 300s |
|---|---:|---:|---:|---:|---|---|---|---|
| A native | 3435 | 12621 | $0.006278 | $0.077416 | yes | yes | 2 observed | finished under diagnostic 90s watchdog |
| B dry only | 8943 | 24277 | $0.010940 | $0.077416 | yes | yes | 2 projected | completion UNVERIFIED |
| C dry only | 11467 | 29525 | $0.013040 | $0.077416 | yes | yes | 2 projected | completion UNVERIFIED |

VERIFIED dual ledgers: legacy gateway reserves a fixed 32000-input/512-output
upper per attempt: 13620 micro-USD, 27240 for native A's two attempts. Shared
aggregate ledger uses captured conservative input bounds and retains **6278**
micro-USD. Neither figure is actual usage, an invoice or permission to spend.
Both remain under their respective unchanged caps; missing usage releases nothing.

VERIFIED full-contract maximum: per attempt
`ceil(32000*.40 + 4096*1.60) = 19354 micro-USD`; four attempts = **77416**
micro-USD. Three such runs + full $.50 planning = **$.732248**, below the $.86
planned allocation, $.12/run and $2 aggregate. Current stricter offline 512-output
profile has four-request fixed maximum **$.054480**. Every interrupted/failed
attempt counts and retains exposure. Four 60s request deadlines total 240s but
exclude other processing; the 300s run deadline still fails closed, and completion
at maximal timing is not guaranteed.

VERIFIED: **the cumulative token reservation bound, not $.12, binds B/C.**
No increase in dollar caps is necessary for the proposed conservative bound.

## PROPOSED, NOT ACTIVE

VERIFIED proposal file: `TOKEN_BOUND_PROPOSED_NOT_ACTIVE.json`.
SHA-256: `929ee7ad2952ab650ba8a70c0074a25d4c1c1cb25e5975324ab4600639951c9b`.
Its measurements hash explicitly uses sorted compact canonical JSON, not the
indented measurement-file bytes. No genuine operator approval artifact exists or
was supplied for this proposal; the agent did not create or sign one.

INFERRED proposal selection: **144384 = 4*(32000+4096)** is the smallest universal
cumulative bound covering EVERY allowed four-request trace at the existing
contract's full per-request maxima. It is deliberately NOT called the minimum
measured two-request fixture. That minimum is **29525**; the current stricter
512-output profile's universal four-request bound is **130048**. All three are
explicitly distinguished in the proposal. None guarantees a real implementation
will finish within four requests, and none is active.

VERIFIED unchanged: active cumulative bound 16000, actual offline output cap 512,
contract output maximum 4096, four requests, deadlines, durable reservations,
fail-closed behavior, admission, dollar caps and provider authorization zero.
B/C native execution remains BLOCKED until a genuine operator-authored approval
binds to the proposal hash AND someone other than this agent activates an approved
contract through trusted configuration. Existing immutable ledgers must not be
silently migrated, refunded or reset.
