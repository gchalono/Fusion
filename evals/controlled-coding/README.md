# Phase 2N offline scaffold

Status: live blocked. No paid execution command is implemented. Preserve the
Phase 2M evidence and recover its supervisor before wiring native coding runs.

From the worktree root:

```sh
python -m unittest discover -s evals/controlled-coding -v
python -m unittest discover -s evals/planning-collector -v
python -m py_compile evals/controlled-coding/*.py
python evals/controlled-coding/harness.py verify
python evals/controlled-coding/harness.py dry-run --output /tmp/phase2n-new-dry-run
```

The dry-run destination must not already exist. `frozen.json` freezes objectives,
starting code, acceptance tests, proposed coding settings and execution order
(seed 20261109). Do not regenerate it after inference. New tasks are interval
merging, duration parsing and stable topological sorting. References in unit
tests are offline positive controls, never model solutions or experimental runs.

`acceptance.py TASK CANDIDATE` runs frozen independent tests in a fresh temporary
directory. It is a trusted local verifier, **not a sandbox for model code**.
Never mount acceptance tests, references, other arms or results in a coding
sandbox. The recovered supervisor must enforce these restrictions.

A receives the original objective. B additionally receives the native plan.
C additionally receives explicitly human-approved clarification answers. Until
native plans and approval evidence exist, B/C dry-run inputs are JSON null.
Missing measurements remain null. Nothing in the dry run measures correctness.
Plan content may incorporate clarifications; B/C compares transcript presentation.
Three tasks provide descriptive pilot results, not statistical significance.

## Shared gateway budget

`guard_gateway` attaches `AggregateBudget` to the existing planning collector's
Gateway before HTTP transport. Use a single trusted absolute ledger path for
ALL planning/coding requests, native retries and compaction. Assign run IDs in
the trusted supervisor; agents must not choose run IDs, ledger paths, rates or
model bounds. The guard is offline-tested, not wired into a live supervisor.

Every attempt first persists the original gateway reservation, then commits a
shared worst-case reservation, then persists the audit link. Any failure stops
transport and marks the gateway terminal. The original gateway derives exposure
from verified full input/output token bounds and conservative prices. Those
provider contracts and current rates still need verification before live use.

The shared ledger serializes writers with BEGIN IMMEDIATE and commits using
SQLite synchronous=FULL. It caps aggregate exposure at $2 and each coding run at
$0.15/four attempts. There is no refund API. Errors, timeouts and crashes retain
committed exposure; observations cannot lower it. SQLite triggers reject update
or deletion of reservations and observations through normal SQL. This assumes
trusted storage, not a defense against an operator replacing the database.
No agent may access the ledger, its directory, or real provider credentials.

`snapshot()` separates reserved exposure from raw provider-reported usage,
price-based estimated charges, and measured charges. `observe()` appends evidence
references; the caller must supply real evidence for measured charges. Repeated
observations are history, not amounts to sum into a fabricated invoice total.
No observation is automatically promoted from an estimate to a measured charge.

The current cloud permits api.openai.com and has an inference credential binding.
Removing an environment variable alone does not prove gateway-only inference.
Live execution remains unavailable until the recovered supervisor demonstrates
sole egress with negative bypass tests, including through inherited proxies.

## Existing offline native integration

```sh
python evals/planning-collector/offline_runner.py --scenario comprehensive
python evals/planning-collector/verify_evidence.py EVIDENCE_DIRECTORY
```

This requires bubblewrap namespaces and may need the normal sandbox escalation.
It preserves the existing five-starts/hour limit. Its scripted answers and
synthetic model/rates are offline test doubles; never use them as approved Phase
2N planning artifacts. It exercises the legacy gateway, not the shared ledger.
