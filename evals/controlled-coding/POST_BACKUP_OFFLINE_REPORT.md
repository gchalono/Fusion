# Post-backup offline milestone

VERIFIED: original development checkpoint b3bc7b0dc6c2751bb3b499d9ce6023b3e2c7284c
and its original recovery bundle remain untouched. All 35 source input hashes match.
Sanitized orphan b1542ac7f090f815c92a0ddd63830c5a33c0d2cd was pushed exclusively to
`gchalono/Fusion:backup/fusion-checkpoints`, independently fetched, then fresh-cloned.
The fresh clone passed inventory/history verification and 84 offline units, with 8
private/original-history-dependent checks explicitly skipped. Original local tests
passed all 92. Follow-up backup ba35658e50bc8182ecc1fb482cf02ff5199bc9b2 records
recovery and guarded milestone/20-minute checkpoint tooling. Full genuine experiment
recovery from the public branch is PARTIAL: 32 private inputs require protected archives.
No private database ancestry, raw approvals, provider records or credential contents
were published. Exact original-to-snapshot mapping is in backup/CHECKPOINT_INDEX.json.

## Scoped offline token activation

VERIFIED authorization source: the operator's current instruction, section 7:
"Activate the scoped token-bound revision after verification."
`task_manager_token_revision.py` applies that directive only through explicit
`--expanded-offline`. This is an execution receipt, not an agent-authored signed
operator approval. It does not modify the historical proposal or approval records.
The proposal hash must be 929ee7ad2952ab650ba8a70c0074a25d4c1c1cb25e5975324ab4600639951c9b.
The optional Experiment 2 cumulative conservative BYTE reservation is 144384 =
4*(32000+4096). Default experiment_contract and Experiment 1 remain unchanged.
No tokenizer counts are claimed. Per-request rounding gives 4*19354 = 77416
micro-USD ($0.077416), below unchanged $0.12/run. Shared synthetic maximum over
three arms is $0.232248; planning allocation $0.50 plus coding allocation $0.36
still satisfies the $1.60 arming threshold. Provider authorization remains $0.00.
Four underlying requests, native settings/retries, 512 active fixture output bound,
4096 contract maximum and security policies remain unchanged. Changed proposal,
limits or price arithmetic fail closed. No revised limit applies to paid preflight.

## Native offline A/B/C and reproducibility

VERIFIED actual unchanged Fusion/Pi sessions used exact frozen A/B/C prompt bytes,
the real native write tool, run-bound gateway and local TLS TEST DOUBLE only.
Each produced application.py, exited 0 and completed two underlying local requests.
Separate disposable test databases retained UNCERTAIN reservations because the local
stub intentionally omits provider usage; no actual billable usage is inferred.

| Arm | Requests | Reserved micro-USD | Result |
|---|---:|---:|---|
| A | 2 | 6278 | incomplete control |
| B | 2 | 10940 | incomplete control |
| C | 2 | 13040 | incomplete control |
| A repeat | 2 | 6278 | identical wires and patch |

VERIFIED repeat: both A raw wire files and patch hashes match byte-for-byte.
Patch SHA-256: 6b192be046e7ad73d560df5c7a3bbbbc8fbbeaa03c74ed62497f24f8c1e6a5b3.
These separate diagnostic databases are not a combined treatment experiment ledger.
A separate new unit uses ONE shared three-arm ledger, reserves four maximum attempts
per arm, rejects fifth attempts, and confirms $0.232248 survives process reopening.

VERIFIED independent grader rejected actual A/B/C captured code, as expected for
the deliberately incomplete 237-byte scaffold. A native C security session also
checked absent provider credential variable, hidden tests, cross-arm/private evidence
and forbidden direct egress while retaining the positive gateway path.
Evidence stays outside Git in `/workspace/tm-post-backup-native-*`; never mixed with
real model outputs. Real provider requests and cost: 0 / $0.00.

## Chromium and acceptance blocker

FAILED: rerun positive reference and repeat pass seven HTTP/SQLite operations but
fail at browser page creation. Existing capset-denying security filter is unchanged.
All three incorrect/tampering/fabricated-success controls are rejected. Positive
reference grading and browser-specific security tests remain BLOCKED, not passed.
No compatible Chromium profile is verified; no shim, syscall allowance, broad mount,
namespace exception or weakened negative test was introduced. Earlier capset diagnosis
remains in TASK_MANAGER_FEASIBILITY_REPORT.md. Further repair requires a compatible
browser runtime or reviewed boundary-preserving design. Full task-manager success
and complete implementation grading remain UNVERIFIED.

## Tests and commands

VERIFIED original workspace: 47 coding + 37 collector + 11 persistence tests =
95 passed, zero failures/skips. New tests verify default preservation, proposal hash
rejection, unchanged money/output/request controls and shared durable maximum bounds.

```sh
python -m unittest discover -s evals/controlled-coding
python -m unittest discover -s evals/planning-collector
python -m unittest discover -s evals/persistence
python evals/controlled-coding/task_manager_native.py --root NEW_PRIVATE_DIR --runtime /workspace/Fusion --arm A --expanded-offline
# Repeat with B/C; these are local TEST DOUBLE diagnostics, never paid calls.
python evals/controlled-coding/task_manager_controls.py --out NEW_PRIVATE_DIR
# Last command currently fails the positive browser gate; do not waive it.
```

Remote sanitized persistence does not satisfy original remote-backed paid execution
preflight. No live model, paid agent, production change, mission, task, merge, force
push, deployment, frozen-input edit or original-history publication occurred.
