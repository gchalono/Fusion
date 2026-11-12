# Live Run 4: self-test and repair

Run 4 is the fresh registered identity `parse-duration:B` for
`controlled-live-local-self-test-v1`. Run 3 (`parse-duration:A`) remains
consumed and INCOMPLETE, including its $0.004258 durable reserved exposure.
The existing ledger reports $0.018373 reserved across all prior runs; no amount
is refunded or reset. The original $2.00 cumulative ceiling, $0.12 run cap,
four-request limit, 300-second deadline, token bounds, output ceiling, signature
verification, replay protection, gateway-only inference, sandbox isolation and
independent grading remain in force. No provider-enforced hard cap is claimed;
both signed approvals must acknowledge that fact.

The new aggregate authorization is a non-overlapping continuation of the
already signed Run 3 aggregate. Validation also verifies the original root,
the B renewal, Run 3's signed aggregate and run approval, and the corresponding
immutable ledger receipts. Run 4 must have at least five minutes of validity at
preflight, use the current source binding, be unused in every run table and fit
inside all retained aggregate and task allocations. An uncertain Run 3
reservation remains charged and is not treated as a blocker by itself.

The operator helper reads approval documents only to verify their signatures
and public claims. It checks the private key and provider credential metadata;
it never reads the provider credential. OpenSSL prompts for the encrypted
operator key passphrase in the interactive terminal. Keep the signing key and
provider credential outside agent access. Never paste approvals, keys,
passphrases or provider records into chat.

## Human signing

First independently verify the exact model's current availability and current
conservative original pricing. Run this in a private interactive terminal from
this worktree:

```bash
cd /workspaces/Fusion-controlled-live-independent
umask 077
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py sign \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-004"
```

The operator helper asks these prompts verbatim:

```text
Current exact-model availability verification reference:
Current conservative original-price verification reference:
Type AUTHORIZE FRESH SELF-TEST RUN WITHIN THE SAME CUMULATIVE TWO DOLLARS WITHOUT PROVIDER HARD CAP:
```

Enter independently verified references at the first two prompts. At the third,
type exactly:

```text
AUTHORIZE FRESH SELF-TEST RUN WITHIN THE SAME CUMULATIVE TWO DOLLARS WITHOUT PROVIDER HARD CAP
```

The helper creates only the new `aggregate-self-test-004` and `run-self-test-004`
payload/signature/envelope files and refuses to overwrite any of them. It does
not launch inference or modify the ledger. If any output file already exists,
stop and preserve it for private investigation.

## Read-only final preflight

After reviewing both signed documents locally, run:

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py preflight \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-004"
```

Require `RELIABILITY_PREFLIGHT_VERIFIED_NO_EXECUTION`, run `parse-duration:B`,
the current implementation hash, retained exposure, and unchanged limits. This
preflight is read-only: it does not claim approvals, create output, read
credential contents, start the gateway or contact the provider. Stop on any
refusal; do not reset the database or alter prior records.

## Separate human launch action

No launch has been performed. Only after successful preflight and review of the
spending and expiry terms, the operator may explicitly launch one Run 4:

```bash
cd /workspaces/Fusion-controlled-live-independent
/usr/bin/python3 -B evals/controlled-coding/reliability_operator.py launch \
  --authority-dir "$HOME/fusion-first-live-authority" \
  --output "$HOME/fusion-self-test-live-run-004"
```

The helper reruns read-only preflight and prompts:

```text
Type LAUNCH ONE FRESH SELF-TEST RUN:
```

Proceed only by typing exactly `LAUNCH ONE FRESH SELF-TEST RUN`. The command
starts one fresh `parse-duration:B` run; it does not retry, resume, or substitute
another model. Any failure leaves its identity consumed and exposure retained.

## Offline evidence and limits

Offline scripted sessions and local TLS exercise the actual Pi coding session,
self-test/repair loop, Python checks, live transport adapter, budget gateway and
independent grader. These tests make no provider calls. They prove the workflow
can complete and that injected provider/transport failures retain safe,
classified diagnostics; they do not predict genuine model quality or current
provider availability.

Historical Phase 2N recovery discrepancies remain documented in the existing
historical records. This separate run does not claim those discrepancies were
resolved or that the historical recovery preflight passed.
