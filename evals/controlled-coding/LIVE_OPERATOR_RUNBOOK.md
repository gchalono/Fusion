# First live task: operator preparation, signing and preflight

These commands are for the human operator. They have not been run with real
secrets or authority. Stop after the read-only preflight; do not launch paid
inference yet. Never paste credentials, signing keys or approval files into chat.

The baseline is `25e38461597daa5ea656f58212402ac026df3b54`, with uncommitted
runner fixes in `/workspaces/Fusion-controlled-live-independent`. The original
checkout's four uncommitted files remain untouched.

No provider hard cap exists for this experiment. Both signed documents explicitly
acknowledge this. Fusion reserves up to $2 aggregate and $0.12 for this run before
transport, with no refunds for uncertain requests. These are internal dispatch
limits, not a guarantee about provider billing or other credential use.

## 1. Create private operator material

Run these in a private operator terminal. `mkdir` intentionally fails if the
authority directory already exists: do not overwrite existing keys or ledgers.
The private key is encrypted; OpenSSL prompts for its passphrase. The agent must
never execute this block or access that private key.

```bash
set -euo pipefail
umask 077
export LIVE_REPO=/workspaces/Fusion-controlled-live-independent
export LIVE_AUTH="$HOME/fusion-first-live-authority"
mkdir -m 700 "$LIVE_AUTH"
openssl genpkey -algorithm ED25519 -aes-256-cbc -out "$LIVE_AUTH/operator-private.pem"
openssl pkey -in "$LIVE_AUTH/operator-private.pem" -pubout -out "$LIVE_AUTH/operator.pub"
chmod 600 "$LIVE_AUTH/operator-private.pem" "$LIVE_AUTH/operator.pub"
cp "$LIVE_REPO/evals/controlled-coding/experiment-parameters.json" "$LIVE_AUTH/contract.json"
chmod 600 "$LIVE_AUTH/contract.json"
```

Independently trust and retain this public verification key. Provision a dedicated
provider credential at `$LIVE_AUTH/provider-key` using your private secret manager,
with mode 0600. The signing/preflight commands below inspect its metadata only.
Keep the signing private key outside all runtime mounts and inaccessible to agents.

Independently verify that the contract's exact model is available and its input,
cached-input and output rates are current conservative bounds. Edit only the
private contract copy if needed. Do not silently substitute a model or overwrite
historical parameters. Keep the $2/$0.12 caps, four requests and 300-second deadline.

```bash
"${EDITOR:-vi}" "$LIVE_AUTH/contract.json"
```

## 2. Create and sign both documents

This command prompts for non-secret verification references and explicit risk
acceptance. Enter `I ACCEPT NO PROVIDER HARD CAP` only after understanding that
internal accounting does not enforce provider billing. It creates two independent
nonces and signatures, bound to one contract and one fixed new ledger path.
OpenSSL asks for the signing-key passphrase for each signature. Do not regenerate
authority or switch ledgers after a failed/started run to recover budget.

Canonical JSON is UTF-8 encoding of Python
`json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)`;
default `ensure_ascii=True` is retained. The detached Ed25519 signature covers
those exact bytes, with no trailing newline. Envelopes contain only `payload`
and the lowercase hexadecimal `signature`.

```bash
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
from live_authorization import private_file

private_file(auth/'provider-key')  # Metadata only; do not read credentials.
if (auth/'experiment.db').exists():
    raise SystemExit('Existing ledger: stop and investigate; do not replace it.')
for name in ('run.json', 'aggregate.json', 'run.payload', 'aggregate.payload',
             'run.sig', 'aggregate.sig'):
    if (auth/name).exists():
        raise SystemExit('Existing approval artifacts: stop; do not overwrite.')
c = Contract(auth/'contract.json')
availability = input('Exact-model availability verification reference: ').strip()
pricing = input('Current conservative pricing verification reference: ').strip()
if not availability or not pricing:
    raise SystemExit('Both verification references are required.')
if input('Type I ACCEPT NO PROVIDER HARD CAP: ') != 'I ACCEPT NO PROVIDER HARD CAP':
    raise SystemExit('Risk acknowledgment declined; nothing signed.')
now = int(time.time())
common = dict(schema='fusion-live-v1', test_double=False,
              issued_at=now, expires_at=now+3600,
              contract_sha256=hashlib.sha256(canonical(c.data)).hexdigest(),
              ledger_path=str(auth/'experiment.db'),
              accept_no_provider_hard_cap=True)
aggregate = dict(common, kind='aggregate-spending',
                 nonce=secrets.token_hex(24), authorized_spend_usd='2.00')
run = dict(common, kind='coding-run', nonce=secrets.token_hex(24),
           aggregate_nonce=aggregate['nonce'], authorized_spend_usd='0.12',
           run_id='merge-intervals:A', task_id='merge-intervals',
           fixture_sha256=fixture_binding('merge-intervals')['derived_fixture_sha256'],
           live_authorized=True, model=c.data['model'], approved_hosts=['api.openai.com'],
           provider_side_cap_confirmed=False,
           model_availability_verified=True, model_availability_evidence=availability,
           pricing_verified=True, pricing_verification_evidence=pricing,
           max_requests=4, max_seconds=300, key_file=str(auth/'provider-key'))
for name, payload in (('aggregate', aggregate), ('run', run)):
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
print('Both approvals created privately. No ledger, output or paid request created.')
PY
```

## 3. Read-only final preflight; stop here

This verifies both signatures, expiry, contract and fixture bindings, explicit
no-cap acknowledgment, limits, credential metadata, private mount boundaries,
built runtime dependencies and a new ledger/output path. It does not read the
provider credential contents, consume approvals, create a ledger/output, start
the coding agent or contact the provider. Signature verification uses disposable
temporary files. It does not certify model availability or provider billing.

```bash
cd "$LIVE_REPO"
/usr/bin/python3 -B evals/controlled-coding/live.py \
  --preflight --task merge-intervals --run merge-intervals:A \
  --runtime "$LIVE_REPO" \
  --output "$HOME/fusion-first-live-run-001" \
  --ledger "$LIVE_AUTH/experiment.db" \
  --authorization "$LIVE_AUTH/run.json" \
  --aggregate-authorization "$LIVE_AUTH/aggregate.json" \
  --operator-public-key "$LIVE_AUTH/operator.pub" \
  --contract "$LIVE_AUTH/contract.json"
```

Expected classification: `PREFLIGHT_VERIFIED_NO_EXECUTION`, with
`provider_hard_cap_confirmed: false`. A failed preflight is not permission to
change evidence, rotate a ledger, weaken a check or launch anyway. Paid launch
remains a separate explicit operator action; these commands do not run it.

## Historical recovery status

Historical Phase 2N preflight did not pass. It targets `eval/phase2n` at
`bf23a5ccbae2e7347cc533be00e38b89cef7c59a`, while the independently verified live
baseline is the commit above. At that clean live baseline, historical manifest
hashes differed for `independent.py`, `isolation.py` and `real_transport.py`.
Phase 2M evidence remains missing. None of those records or hashes was rewritten.
The operator explicitly scoped these as documented historical discrepancies,
not gates for this separate experiment. This new preflight validates only the
current signed live-run requirements and does not claim historical recovery.

## Offline validation for this change

All 96 offline tests passed: 50 controlled-coding, 37 planning-collector and 9
persistence. The controlled-coding suite includes positive execution with no
provider cap, both-document acknowledgment requirements, wrong types, missing
fields, contradictory declarations, signature tampering, constructor/parent/
worker dispatch refusal, durable approval binding, budget caps, request/deadline
limits, isolation and independent grading. The first-run preflight is tested for
no experiment-state mutation and refusal of invalid acknowledgment or an existing
ledger. Frozen fixture verification, credential-pattern scan and diff whitespace
checks also passed. Synthetic keys and local TLS were used; these are not genuine
approvals or paid model results.

The existing offline-task tests exposed missing scripted task implementations
in the verified baseline. The already-existing operator-checkout patch was
inspected and copied into this worktree to restore those controls; its source
file was not edited. Frozen task fixtures and acceptance criteria remain intact.
