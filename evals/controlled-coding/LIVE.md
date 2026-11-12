# First controlled live coding run

`live.py` is a separate, explicitly armed entry point. It does not run the
historical Phase 2N experiment, reconstruct Phase 2M, or change the offline pilot.
Offline verification is not evidence of a successful real-model run.

## Operator preparation

Keep authority and credentials in an operator-owned private directory outside
the public runtime mounts. Never put them in `packages`, `node_modules`, `plugins`,
system interpreter directories, or a coding workspace. Use mode 0700 for the
directory and 0600 for the approval files, ledger and provider key file. The
public verification key must not be writable by other users. The operator must
independently trust that public key; an approval cannot select its own signer.
The runner never generates approvals or reads the signing private key.

Before signing, verify model availability, current conservative prices and the
spending-risk declaration below. A provider hard cap is not required when both
signed documents explicitly accept its absence. The existing contract has operator-supplied
prices and unverified availability; its presence supplies no spending authority.
An operator may provide a separately reviewed contract with `--contract`; both
signatures must bind its canonical SHA-256. Do not edit historical evidence or
substitute a model silently. Missing Phase 2M remains a historical dependency,
not an approval for this new experiment. Recovery preflight failures must remain
visible; this entry point does not certify recovery or remote persistence.

Two independently signed documents are required: a run authorization for $0.12
and aggregate spending authorization for $2. Use a **new dedicated ledger path**
for this experiment, then retain that same path for every authorized run. Never
rotate or copy ledgers to recover budget. Existing ledgers require exactly the
same immutable contract. Interrupted/failed reservations are never refunded.
The first run consumes its approval durably even if startup fails; there is no
automatic retry or resume. A failed run needs operator investigation, not a new
output directory or approval to repeat the same run.

Each approval file is exactly `{"payload": {...}, "signature": "<hex>"}`.
Sign `contract.canonical(payload)` bytes using Ed25519 detached signatures
(`openssl pkeyutl -sign -rawin`); `signature` is the 128-character lowercase hex
encoding of the 64-byte signature. Duplicate JSON keys and nonfinite values are
rejected. Supply the operator's independently trusted Ed25519 public key with
`--operator-public-key`. Signing is an operator action outside the coding runner.

Both payloads require:

| Field | Value |
| --- | --- |
| `schema` | `fusion-live-v1` |
| `test_double` | `false` |
| `issued_at`, `expires_at` | Unix seconds, current time inside this interval |
| `nonce` | Unique 16–128 ASCII letters/digits/underscore/hyphen |
| `contract_sha256` | SHA-256 of canonical contract JSON |
| `ledger_path` | Exact absolute resolved durable ledger path |

For this experiment both payloads also require `accept_no_provider_hard_cap: true`.
The run must explicitly set `provider_side_cap_confirmed: false`. Missing,
nonboolean or contradictory declarations fail verification at setup and each
paid dispatch, including the transport worker. Confirmed provider caps remain
supported separately; they cannot be combined with acceptance of an absent cap.

Aggregate payload additionally requires `kind: "aggregate-spending"` and
`authorized_spend_usd: "2.00"`.

Run payload additionally requires:

| Field | Value |
| --- | --- |
| `kind` | `coding-run` |
| `aggregate_nonce` | Nonce of separately signed aggregate authority |
| `authorized_spend_usd` | `0.12` (string) |
| `run_id`, `task_id` | `merge-intervals:A`, `merge-intervals` for first run |
| `fixture_sha256` | `derived_fixture_sha256` from `pilot.py describe-fixture` |
| `live_authorized` | `true` |
| `model` | Exact model from the signed contract |
| `approved_hosts` | `["api.openai.com"]` |
| `provider_side_cap_confirmed` | `false` for this experiment; no provider hard cap is claimed |
| `accept_no_provider_hard_cap` | `true` in **both** signed payloads, accepting that internal reservations cannot enforce provider billing |
| `model_availability_verified` | `true`, after operator verification |
| `model_availability_evidence` | Nonempty reference to operator's verification |
| `pricing_verified` | `true`, after operator verification of signed prices |
| `max_requests`, `max_seconds` | `4`, `300` |
| `key_file` | Absolute path to private dedicated provider credential file |

The gateway verifies signatures before setup and immediately before each paid
transport, including inside the transport worker. The worker also checks the
consumed approval, active deadline and durable forwarded reservation. Changed,
missing, expired, ambiguous and replayed authority fails closed. Pricing errors,
unknown billable features, absent/invalid usage, truncated output and transport
failures terminate the run; worst-case exposure remains charged against limits.
The aggregate cap covers reservations, not merely reported usage.

See [the operator runbook](LIVE_OPERATOR_RUNBOOK.md) for exact private-key,
canonical signing and read-only first-run preflight commands. No provider-enforced
cap is claimed; the internal $2 aggregate and $0.12 run reservation caps remain.

## Launch command — operator only, after separate authorization

Dependencies must already be installed in this checkout with pinned pnpm 10.33.0
and `pnpm --filter @fusion/core build` completed. Use system Python: the PATH
Python installation may not run inside the existing namespace mounts.

```sh
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/live.py \
  --arm-live --task merge-intervals --run merge-intervals:A \
  --runtime /workspaces/Fusion-controlled-live-independent \
  --output "$HOME/fusion-first-live/run-001" \
  --ledger "$HOME/fusion-live-authority/experiment.db" \
  --authorization "$HOME/fusion-live-authority/run.json" \
  --aggregate-authorization "$HOME/fusion-live-authority/aggregate.json" \
  --operator-public-key "$HOME/fusion-live-authority/operator.pub"
```

The output directory must not exist. The signed ledger path must resolve to the
path in this command. The sandbox receives only its inference socket/token,
objective, starting solution and public runtime. It gets no provider credential,
authority, ledger, admin endpoint, host network or hidden grading tests. The
run deadline is 300 seconds including setup and grading; independent grading
uses at most 30 seconds, capped by the remaining run time. Only `solution.py` is captured as a patch.
`live-observation.json` records the independently authenticated grade and durable
budget snapshot; agent self-reports do not establish success. Output artifacts
are private and must not be committed or treated as historical evidence.

## Offline verification

```sh
/usr/bin/python3 -B -m unittest discover -s evals/controlled-coding -p 'test_*.py' -v
/usr/bin/python3 -B evals/controlled-coding/harness.py verify
/usr/bin/python3 -B evals/persistence/scan.py --base HEAD
```

The integration test replaces only paid HTTPS transport with a local TLS stub.
It exercises signed authorization, durable reservations, the real Pi coding
session, Bubblewrap/seccomp and independent grading. All signing/credential
material in these tests is disposable synthetic data. No paid call is needed.

## Separately authorized objective-only follow-up

The operator-authorized follow-up uses the existing registered accounting ID
`merge-intervals:B` while explicitly declaring that it is **not** historical
Phase 2N Arm B. It receives the original objective only. The signed design is
`controlled-live-objective-only-followup-v1`; the frozen native-plan Arm B design
is unchanged. See [the B follow-up runbook](LIVE_B_FOLLOWUP_RUNBOOK.md) for exact
operator-only signing and read-only `--followup-preflight` commands.

This mode requires the original existing ledger/contract/aggregate authority,
consumed INCOMPLETE A and unused B. It retains all prior reservations. It cannot
bootstrap a ledger or reuse A. The original `--preflight` remains first-run-only
and rejects the existing ledger; combining it with `--followup` is rejected.
No new genuine approval or paid request is produced by preparation or preflight.

If the original aggregate has expired, it remains invalid. The separate
[aggregate renewal runbook](LIVE_AGGREGATE_RENEWAL_RUNBOOK.md) describes the
explicit signed B-only successor, its non-overlapping validity and original-root
digest binding. The same ledger and cumulative $2 ceiling persist. Renewal adds
an immutable receipt with B's claim only on an authorized launch; preflight never
records or consumes a renewal. Original approvals and earlier reports stay intact.
