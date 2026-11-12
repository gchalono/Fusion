# Live Run 5: self-test and repair

Run 5 uses the fresh registered identity `parse-duration:C` and the existing
`controlled-live-local-self-test-v1` design. It continues the same authorization
lineage through Run 4:

```text
original $2 aggregate → B renewal → Run 3 aggregate/run → Run 4 aggregate/run → Run 5
```

The helper cryptographically verifies each prior signed document against the
original public key and matches its digest/nonce to the durable ledger receipts.
It also verifies Run 3/4 run identities, shared contract/ledger, self-test
design, original-model continuity, missing-provider-cap acknowledgment, and
the original `$2.00` aggregate scope. Run 4's consumed identity cannot be
replayed. Existing reservations, including uncertain exposure, remain charged.

Run 4 is INCOMPLETE with zero reservations. The ledger's reserved exposure at
Run 5 preparation is `$0.018373`; the ledger is never replaced or reset. Run 5
keeps the `$0.12` per-run cap, four-request maximum, 300-second deadline, token
and output bounds, gateway-only inference, sandbox isolation, and independent
grading. No provider-enforced hard cap is claimed; the new aggregate and run
approvals must both retain the explicit acknowledgment of its absence.

## Stop condition before signing

At preparation time, the Run 4 aggregate and run approvals are still valid.
The renewal verifier requires a non-overlapping successor, so **do not sign
until both Run 4 approvals have expired**. The signing helper checks this and
fails closed without creating output documents if either is still active. Do
not adjust timestamps, edit approvals, or use an overlapping validity window.

Other stop conditions include any invalid signature or chain link, missing
receipt, unexpected ledger/run state, any Run 5 reservation or authority row,
changed contract/fixture/source binding, insufficient remaining budget,
active conflicting run, existing Run 5 output/approval filename, or an
authority window shorter than the full deadline. Preserve all records and
investigate privately if the helper refuses.

## Human-only signing

After the Run 4 approvals have expired, independently verify the exact model's
current availability and current conservative original pricing. In a private
interactive terminal on this worktree, run:

```bash
cd /workspaces/Fusion-controlled-live-independent
umask 077
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py sign \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-005"
```

The helper prompts verbatim:

```text
Current exact-model availability verification reference:
Current conservative original-price verification reference:
Type AUTHORIZE FRESH SELF-TEST RUN WITHIN THE SAME CUMULATIVE TWO DOLLARS WITHOUT PROVIDER HARD CAP:
```

Enter independently verified references for the first two prompts. At the
acknowledgment prompt, type exactly:

```text
AUTHORIZE FRESH SELF-TEST RUN WITHIN THE SAME CUMULATIVE TWO DOLLARS WITHOUT PROVIDER HARD CAP
```

OpenSSL prompts for the encrypted operator private-key passphrase in that
terminal. Keep both the signing key and provider credential outside agent
access. The helper checks their file metadata and does not read provider-key
contents. It creates only `aggregate-self-test-005` and `run-self-test-005`
payload/signature/envelope files and refuses to overwrite any preexisting
artifact. It does not contact the provider, launch inference, or mutate the
ledger. If signing creates partial artifacts, preserve them and stop.

## Read-only preflight

After privately reviewing the new signed documents, run:

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py preflight \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-005"
```

Proceed only if it reports `RELIABILITY_PREFLIGHT_VERIFIED_NO_EXECUTION`,
`parse-duration:C`, the current implementation hash, cumulative retained
exposure, and unchanged limits. It verifies the full historical chain and Run 5
unused state read-only. It creates no output, claims no authority, reads no
provider credential contents, and makes no network request.

## Separate human launch action

No Run 5 launch has been performed. Only after reviewing a successful preflight
and explicitly deciding to spend, the operator may run:

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py launch \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-005"
```

The helper reruns preflight and prompts:

```text
Type LAUNCH ONE FRESH SELF-TEST RUN:
```

Type exactly `LAUNCH ONE FRESH SELF-TEST RUN` only after reviewing that
preflight. This starts one Run 5 only. It does not retry, resume, replay Run 4,
or substitute a model. Any failure consumes Run 5 and retains all reservations.

## Offline verification

Offline scripted sessions and local TLS exercise the live adapter, Pi session,
self-test/repair loop, local Python checks, budget gateway, socket, and
independent grader. These use synthetic approvals and a local test transport;
they are not evidence of provider availability, live model quality, or billing
behavior. Historical Phase 2N recovery discrepancies remain documented; this
runbook does not claim that historical recovery preflight passed.
