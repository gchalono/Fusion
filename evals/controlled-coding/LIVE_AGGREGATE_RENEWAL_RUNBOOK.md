# Expired aggregate authority: human-only renewal for objective-only B

This is a new authorization procedure, not a correction of historical evidence.
The original aggregate is expired and cannot authorize any paid dispatch.
`merge-intervals:B` remains the separately labeled objective-only follow-up
(`controlled-live-objective-only-followup-v1`), not historical plan-assisted Arm B.

The renewal continues the same experiment: same immutable contract, existing
ledger, original public verification key and encrypted private signing key.
`authorized_spend_usd: "2.00"` means the **same cumulative $2 ceiling**, including
all prior reservations. It does not grant another $2. A remains consumed and
INCOMPLETE, with $0.007909 retained. B keeps $0.12/four requests/300 seconds.
No provider hard cap is claimed; both new documents acknowledge its absence.

The mechanism permits one successor to the original root authority, scoped only
to B. It does not authorize automatic renewal chains or future task identities.
All future authority must still use this ledger's cumulative reservation totals.
Forked successors cannot both be consumed. A renewal receipt is appended together
with B's one-time claim in one transaction only on a separately authorized launch.
Signing and read-only preflight do not consume or record either new authority.

## Human: sign two new documents using the existing encrypted key

Run this only in a private operator terminal. The agent must never execute it,
open authority files or receive keys/passphrases. The human-operated script reads
the expired original approval solely to verify its signature and continuity,
never to revive its validity. It reads only credential metadata. OpenSSL opens
the existing encrypted signing key and prompts for its passphrase twice.

Do not overwrite any prior approval, key, contract, ledger or output directory.
The new file names below are deliberately distinct from previous B proposals.
If they already exist, stop and investigate rather than deleting or replacing them.
Verify that the exact model is still available and the immutable contract's
prices remain conservative. If that is false, stop; this renewal does not permit
contract changes or a silent model substitution.

```bash
set -euo pipefail
umask 077
export LIVE_REPO=/workspaces/Fusion-controlled-live-independent
export LIVE_AUTH="$HOME/fusion-first-live-authority"
cd "$LIVE_REPO"
/usr/bin/python3 -B - <<'PY'
import hashlib
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
                                validate_renewal, verify_followup_ledger)

names = ('aggregate-renewal-B', 'run-B-renewed')
for name in names:
    for suffix in ('.json', '.payload', '.sig'):
        if (auth/(name+suffix)).exists():
            raise SystemExit('Existing renewal artifacts: stop; do not overwrite.')
private_file(auth/'provider-key')  # Metadata only; no credential contents.
c = Contract(auth/'contract.json')  # Existing original contract; never edited.
previous = signed_document(auth/'aggregate.json', auth/'operator.pub',
                           expired_predecessor=True)
availability = input('Current exact-model availability verification reference: ').strip()
pricing = input('Current conservative original-price verification reference: ').strip()
if not availability or not pricing:
    raise SystemExit('Verification references are required.')
ack = 'RENEW THE SAME CUMULATIVE TWO DOLLAR LIMIT FOR OBJECTIVE-ONLY B WITHOUT PROVIDER HARD CAP'
if input('Type '+ack+': ') != ack:
    raise SystemExit('Continuity/risk acknowledgment declined; nothing signed.')
now = int(time.time())
aggregate = dict(previous, issued_at=now, expires_at=now+3600,
                 nonce=secrets.token_hex(24), renewal_version=1,
                 renews_nonce=previous['nonce'],
                 renews_sha256=hashlib.sha256(canonical(previous)).hexdigest(),
                 predecessor_expires_at=previous['expires_at'],
                 renewal_run_id='merge-intervals:B',
                 budget_semantics='cumulative-existing-ledger')
validate_renewal(aggregate, previous)
run = dict(schema='fusion-live-v1', test_double=False,
           issued_at=now, expires_at=aggregate['expires_at'], nonce=secrets.token_hex(24),
           kind='coding-run', aggregate_nonce=aggregate['nonce'],
           contract_sha256=c.sha256, ledger_path=str(auth/'experiment.db'),
           authorized_spend_usd='0.12', run_id='merge-intervals:B', task_id='merge-intervals',
           live_authorized=True,
           fixture_sha256=fixture_binding('merge-intervals')['derived_fixture_sha256'],
           followup_authorized=True, experiment_design=FOLLOWUP_DESIGN,
           historical_phase2n_arm=False, predecessor_run_id='merge-intervals:A',
           model=c.data['model'], approved_hosts=['api.openai.com'],
           provider_side_cap_confirmed=False, accept_no_provider_hard_cap=True,
           model_availability_verified=True, model_availability_evidence=availability,
           pricing_verified=True, pricing_verification_evidence=pricing,
           max_requests=4, max_seconds=300, key_file=str(auth/'provider-key'))
config = dict(ledger_path=str(auth/'experiment.db'), run_id=run['run_id'], followup=True,
              operator_public_key=str(auth/'operator.pub'),
              previous_aggregate_authorization_file=str(auth/'aggregate.json'))
retained = verify_followup_ledger(config, c, run, aggregate, unused=True)
print('Existing durable reserved exposure (micro-USD):', retained)
for name, payload in zip(names, (aggregate, run)):
    message = auth/(name+'.payload')
    with message.open('xb') as output:
        output.write(canonical(payload))
    subprocess.run(['openssl', 'pkeyutl', '-sign', '-rawin',
                    '-inkey', str(auth/'operator-private.pem'),
                    '-in', str(message), '-out', str(auth/(name+'.sig'))], check=True)
    signature = (auth/(name+'.sig')).read_bytes()
    if len(signature) != 64:
        raise SystemExit('Unexpected Ed25519 signature size; stop.')
    with (auth/(name+'.json')).open('xb') as output:
        output.write(canonical(dict(payload=payload, signature=signature.hex())))
    (auth/(name+'.json')).chmod(0o600)
print('Renewal and B documents created privately. Original files and ledger unchanged; no paid request.')
PY
```

Canonical encoding is UTF-8 of
`json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)`
with default `ensure_ascii=True`, without a trailing newline. Ed25519 detached
signatures cover those exact bytes. Each envelope contains only `payload` and
lowercase hexadecimal `signature`.

Both signatures use the original independently trusted public-key anchor. The
expired predecessor's signature and original ledger digest must also match.
New `issued_at` must be at or after the old `expires_at`; overlap, an unexpired
predecessor, wrong scope, changed limits or a mismatched root is refused.

## Human: read-only preflight; stop after this command

```bash
cd "$LIVE_REPO"
/usr/bin/python3 -B evals/controlled-coding/live.py \
  --followup-preflight --task merge-intervals --run merge-intervals:B \
  --runtime "$LIVE_REPO" \
  --output "$HOME/fusion-second-live-run-002" \
  --ledger "$LIVE_AUTH/experiment.db" \
  --authorization "$LIVE_AUTH/run-B-renewed.json" \
  --aggregate-authorization "$LIVE_AUTH/aggregate-renewal-B.json" \
  --previous-aggregate-authorization "$LIVE_AUTH/aggregate.json" \
  --operator-public-key "$LIVE_AUTH/operator.pub" \
  --contract "$LIVE_AUTH/contract.json"
```

Expected: `FOLLOWUP_PREFLIGHT_VERIFIED_NO_EXECUTION`, `aggregate_renewal: true`,
`retained_reserved_micro_usd: 7909` if no other authorized work occurred, and
unchanged $2/$0.12/four-request/300-second limits. Signature verification uses
disposable temporary files; experiment state, approval consumption and output
remain unchanged. The original first-run preflight is not bypassed or weakened.
It still cannot approve an existing-ledger run.

No paid launch is included. A must never be replayed. If B is consumed, the root
receipt differs, a successor has already been committed, the ledger is missing,
or validity/headroom checks fail, stop. Do not rotate a ledger, extend validity
in-place, replace an approval or refund any prior exposure to make checks pass.

## Surface Enumeration and Symptom Verification

The current and historical signatures are separately validated at setup,
parent transport dispatch and worker dispatch. Only historical-continuity reads
accept an expired document; active authority never does. Ledger checks cover
unclaimed versus committed successors, original-root matching, single-successor
fork protection, replay/colliding nonces, unchanged aggregate/coding allocations,
consumed A and unused B. Claim rollback covers renewal plus run consumption.

Original symptom: an expired root prevented B, while silently replacing the root
would lose the original authority chain. Reproduction: synthetic expired root
with A's four reservations, a signed B-scoped successor and a read-only preflight.
Assertion: valid continuity passes without state mutation, the expired root is
still rejected as active authority, abusive successors fail, and local-TLS B
execution retains all 7909 micro-USD of original reservations.

Earlier reports and the original expired-authority workflow remain historical
records. This procedure explicitly adds renewal; it does not claim historical
recovery discrepancies were resolved or that a genuine renewed run has occurred.

## Verification performed

All 121 offline tests passed: 75 controlled-coding (including 10 renewal abuse
and integration tests), 37 planning-collector and 9 persistence. Coverage includes
expired-versus-active authority, non-overlap, root hash/signature and original-key
continuity, wrong scope/caps/contract/ledger, nonce collisions, fork/replay,
transaction rollback, no restored budget, read-only preflight, dispatch-time expiry
and actual local-TLS B coding/grading. Synthetic root reservations total exactly
7909 micro-USD and survive renewal and B execution unchanged.

Frozen fixture verification, credential-pattern scan, diff whitespace checks and
human-command shell/Python syntax checks also passed. Only disposable synthetic
keys and signatures were used for tests. The real ledger was inspected read-only:
A is INCOMPLETE, four reservations still total 7909 micro-USD and renewal receipt
count is zero. No real approval/secret/token was opened, genuine authority signed,
paid call made, run launched, historical artifact modified, commit or push made.

Changed implementation: `live_authorization.py`, `live.py`, `real_transport.py`.
Tests: new `test_aggregate_renewal.py` and the shared fixture in `test_followup.py`.
Operational documentation: `LIVE.md` and this new runbook. Earlier runbooks and
diagnostic reports remain preserved. A real renewed preflight still requires the
human to create the two new documents above and invoke the read-only command;
the agent has not run it against operator approval files.
