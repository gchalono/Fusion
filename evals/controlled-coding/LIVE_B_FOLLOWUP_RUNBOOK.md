# Objective-only live follow-up B: operator commands

`merge-intervals:B` is registered in the original stored experiment contract.
Historical Phase 2N Arm B requires a native plan; it cannot honestly be used for
an objective-only measurement. The operator explicitly authorized a **separate
objective-only live follow-up** after that distinction was identified. Therefore
the new signed run document must declare
`experiment_design: controlled-live-objective-only-followup-v1` and
`historical_phase2n_arm: false`. The B suffix is its existing accounting identity,
not a claim that historical Arm B was executed. Frozen design records are intact.

The original contract, ledger, aggregate payload/signature, public verification
key, provider credential and encrypted signing key are reused unchanged. A is
consumed and remains INCOMPLETE; its four reservations totaling $0.007909 are
retained. No provider cap is claimed. Caps stay $2 aggregate, $0.12/run, four
requests and 300 seconds. This is not an automatic retry or a replay of A.

These commands are exclusively for the human in a private operator terminal.
The agent has not executed them or accessed approvals, credentials or private
keys. Do not paste their contents into chat. No key generation, aggregate signing,
ledger creation, migration, rotation or reset is needed or permitted here.

## 1. Sign only the distinct B run authorization

Use the same authority directory and original key paths as the first run. The
command verifies the existing aggregate signature against the existing public
key, checks its immutable ledger receipt, checks the original contract, and
refuses if B is used or the remaining budget cannot cover a complete $0.12 run.
It does not read the provider credential contents or write the ledger. It does
not read or modify A's approval. Only the human-operated OpenSSL process opens
the encrypted private key and asks for its passphrase.

```bash
set -euo pipefail
umask 077
export LIVE_REPO=/workspaces/Fusion-controlled-live-independent
export LIVE_AUTH="$HOME/fusion-first-live-authority"
cd "$LIVE_REPO"
/usr/bin/python3 -B - <<'PY'
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

repo = Path(os.environ['LIVE_REPO']).resolve()
auth = Path(os.environ['LIVE_AUTH']).resolve()
sys.path.insert(0, str(repo/'evals/controlled-coding'))
from contract import Contract, canonical
from pilot import fixture_binding
from live_authorization import (FOLLOWUP_DESIGN, private_file, signed_document,
                                verify_followup_ledger)

for name in ('run-B.json', 'run-B.payload', 'run-B.sig'):
    if (auth/name).exists():
        raise SystemExit('Existing B authorization artifacts: stop; do not overwrite.')
private_file(auth/'provider-key')  # Metadata only; no credential contents.
c = Contract(auth/'contract.json')  # Original private contract, never edited here.
aggregate = signed_document(auth/'aggregate.json', auth/'operator.pub')
now = int(time.time())
if aggregate['expires_at'] <= now+300:
    raise SystemExit('Original aggregate authority expires too soon; stop. Do not renew or replace it here.')
availability = input('Current exact-model availability verification reference: ').strip()
pricing = input('Current conservative pricing verification reference: ').strip()
if not availability or not pricing:
    raise SystemExit('Verification references are required.')
if input('Type AUTHORIZE OBJECTIVE-ONLY B FOLLOW-UP WITHOUT PROVIDER HARD CAP: ') != 'AUTHORIZE OBJECTIVE-ONLY B FOLLOW-UP WITHOUT PROVIDER HARD CAP':
    raise SystemExit('Follow-up not acknowledged; nothing signed.')
run = dict(schema='fusion-live-v1', test_double=False,
           issued_at=now, expires_at=min(now+3600, aggregate['expires_at']),
           nonce=secrets.token_hex(24), kind='coding-run',
           aggregate_nonce=aggregate['nonce'], contract_sha256=c.sha256,
           ledger_path=str(auth/'experiment.db'), authorized_spend_usd='0.12',
           run_id='merge-intervals:B', task_id='merge-intervals', live_authorized=True,
           fixture_sha256=fixture_binding('merge-intervals')['derived_fixture_sha256'],
           followup_authorized=True, experiment_design=FOLLOWUP_DESIGN,
           historical_phase2n_arm=False, predecessor_run_id='merge-intervals:A',
           model=c.data['model'], approved_hosts=['api.openai.com'],
           provider_side_cap_confirmed=False, accept_no_provider_hard_cap=True,
           model_availability_verified=True, model_availability_evidence=availability,
           pricing_verified=True, pricing_verification_evidence=pricing,
           max_requests=4, max_seconds=300, key_file=str(auth/'provider-key'))
config = dict(ledger_path=str(auth/'experiment.db'), run_id=run['run_id'], followup=True)
verify_followup_ledger(config, c, run, aggregate, unused=True)
message = auth/'run-B.payload'
with message.open('xb') as output:
    output.write(canonical(run))
subprocess.run(['openssl', 'pkeyutl', '-sign', '-rawin',
                '-inkey', str(auth/'operator-private.pem'),
                '-in', str(message), '-out', str(auth/'run-B.sig')], check=True)
signature = (auth/'run-B.sig').read_bytes()
if len(signature) != 64:
    raise SystemExit('Unexpected Ed25519 signature size; stop.')
with (auth/'run-B.json').open('xb') as output:
    output.write(canonical(dict(payload=run, signature=signature.hex())))
(auth/'run-B.json').chmod(0o600)
print('Only B authority created privately; original aggregate and ledger unchanged. No paid request.')
PY
```

Canonical encoding remains UTF-8
`json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)`
with default `ensure_ascii=True`, no trailing newline. OpenSSL signs those exact
bytes with Ed25519; the envelope has only `payload` and lowercase-hex `signature`.
The original aggregate authority must still be valid. Expiry is a real blocker:
this workflow does not silently renew it or change its immutable receipt.

## 2. Run only the read-only follow-up preflight

```bash
cd "$LIVE_REPO"
/usr/bin/python3 -B evals/controlled-coding/live.py \
  --followup-preflight --task merge-intervals --run merge-intervals:B \
  --runtime "$LIVE_REPO" \
  --output "$HOME/fusion-second-live-run-002" \
  --ledger "$LIVE_AUTH/experiment.db" \
  --authorization "$LIVE_AUTH/run-B.json" \
  --aggregate-authorization "$LIVE_AUTH/aggregate.json" \
  --operator-public-key "$LIVE_AUTH/operator.pub" \
  --contract "$LIVE_AUTH/contract.json"
```

Expected classification: `FOLLOWUP_PREFLIGHT_VERIFIED_NO_EXECUTION`; design is
`controlled-live-objective-only-followup-v1`, no provider hard cap, and retained
reserved exposure is 7909 micro-USD if no other authorized work has occurred.
The mode requires an existing ledger, identical stored contract, original
aggregate receipt, consumed INCOMPLETE A, unused B, no active conflicting run,
and sufficient remaining aggregate/coding allocations. Signatures, limits,
fixtures, private mount boundaries and runtime checks are unchanged. Checks make
no ledger/output/authority-consumption changes and never read credential contents.

The original `--preflight` stays first-run-only and rejects the existing ledger;
it cannot be combined with `--followup`. The new mode is not a switch to ignore
that rejection. At every eventual B dispatch, signature/design, original ledger,
aggregate, predecessor, active run and reservation checks remain mandatory.

Stop after preflight. No paid launch is included. Do not regenerate B to retry a
consumed identity, switch ledger paths, change caps or infer historical recovery.

## Preparation verification

All 111 offline tests passed: 65 controlled-coding (including 10 follow-up
regressions), 37 planning-collector and 9 persistence. Follow-up coverage includes
consumed A replay refusal, unchanged first-run CLI behavior, byte-for-byte
read-only preflight, immutable contract/aggregate checks, nonce/B reuse refusal,
expiry/headroom checks, dispatch-time design validation and actual local-TLS B
coding plus independent grading with all A reservations retained. Only disposable
synthetic test approvals and credentials were used. Frozen fixture verification,
secret scan, diff whitespace checks and command syntax checks passed.

The real ledger was inspected read-only without opening approval/secret files:
A remains INCOMPLETE, four reservations still total 7909 micro-USD, and B is
unused. The real aggregate's expiry has not been inspected; only the human-run
signing/preflight commands may verify it. No paid calls, genuine signatures,
approval reads, ledger/output modifications, commits or pushes were performed.
