# Phase 3F activation — AWAITING_OPERATOR_SETUP

No inference is authorized or performed. This package is for ONE Arm A run only.
VERIFIED restored baseline: development 8459ba5c995901f131d0cb3fae1c5ff8284e8a37,
sanitized backup a4603010e465051bc28fd1bd60a1d3a6fc2c95ba. Current source is the
clean final activation commit recorded in CHECKPOINTS and the backup SOURCE_MAP.
Always derive a fresh spec AFTER final publication. Do not sign the old baseline.

## Restore and boundaries (VERIFIED)

Original private state is available. Read-only verification: 35 frozen inputs,
8 original approval bindings, 13 Phase3D source-freeze files, 47 journal records,
11,522 micro-USD retained, zero unresolved, zero new reservations/authorizations.
Ledger/witness byte hashes unchanged; native anchor/hash-chain/state verified.
The existing native isolation probe passes all seven checks: provider environment,
proc and descriptors absent; protected host paths/hidden evaluator absent;
only public runtime mounted; direct egress denied. No isolation code changed.
A first nested executor probe could not run; outer-executor retry passed.
Private receipts: /workspace/phase3f-evidence/ (not public backup contents).

Unchanged task phase2m-personal-task-manager:A, source objective/seed/evaluator,
Ed25519 authorization, local gateway budgets, native Pi, seccomp, original historical
evidence. Phase3F changes only operator_auth, supervisor metadata/transport-permit
checks and transport admission to replace the cap assertion with signed risk acceptance.
Phase3E added activation_preflight.py: read-only approval
inspection, no reservation, nonce consumption, authorization row or transport.
Execution still repeats all original gates; preflight grants no execution right.

## Official pricing and model evidence

Attempted 2026-11-10, WITHOUT credentials:
- https://developers.openai.com/api/docs/models/gpt-4.1-mini
- https://openai.com/api/pricing/

Both were unreachable through the inherited proxy, including the approved outer
executor retry. Current official standard-tier/Chat Completions rates remain
UNVERIFIED. No flag was edited. Existing supported gateway_metadata.collect
procedure alone sets pricing_verified after parsing official model-page evidence;
it remains false in the preserved receipt. Do not manufacture a receipt or attest
that an offline fixture verifies official pricing. Resolve documentation access
through operator configuration/review, then use the supported metadata procedure
under AUTHORIZE_METADATA_CHECK. This phase did NOT repeat the provider GET.

Prior Phase3D one GET /v1/models/gpt-4.1-mini-2025-04-14 returned 200/exact id.
This verifies snapshot visibility AT THAT TIME ONLY. It proves neither inference
permission, credits, current access nor inference rate limits. Execution requires
fresh (<24h) signed metadata, unchanged model, and pricing_verified=true.

Configured/supplied assumptions (NOT newly verified pricing), USD per million:
uncached input 0.40; cached input 0.10; output 1.60. Standard Chat Completions
endpoint https://api.openai.com/v1/chat/completions. strict native broker sends
service_tier="default" explicitly (standard); contract rejects auto/flex/priority.
Reservation always uses UNCACHED input; no cache discount is assumed.
Integer calculation, independently recomputed from current continuation contract:
ceil((32000*400000 + 4096*1600000)/1000000) = 19,354 micro-USD per attempt;
4*19,354 = 77,416 micro-USD = $0.077416 <= $0.12/run.
2,000,000 - 11,522 - 500,000 - 77,416 = 1,411,062 micro-USD >= 0.
These are conditional cost bounds at configured rates, not measured API spending.

## Signed no-provider-cap acknowledgment — operator approved policy

No provider-enforced hard cap is required, asserted or verified. No prepaid credits,
provider budget configuration, admin credential or billing change is required.
The operator must explicitly sign this exact transport acknowledgment:

```json
{"provider_hard_cap_verified":false,"accepts_provider_billing_above_local_estimate":true,"local_controls_only_verified_spending_enforcement":true,"authorized_runs":1}
```

It is stored under payload.transport.no_provider_cap_acknowledgment, alongside
metadata_sha256. The existing Ed25519 signature covers the ENTIRE payload (spec +
transport); missing, unsigned or changed acknowledgment fails closed. Old cap
attestations alone are insufficient. The trusted supervisor propagates only the
verified acknowledgment to its private transport permit. No provider cap is invented.
Only one approved run; no automatic successor, whole-run retry or model fallback.
Local budgets remain the only VERIFIED spending enforcement, limited to this gateway.
Provider billing can exceed local estimates. The operator explicitly accepts this risk.
All original reservation, accounting, exclusive ownership, uncertainty retention,
credential, model/endpoint and authorization gates remain active.

## Operator-side pricing procedure if cloud documentation is inaccessible

On an operator-controlled machine with official documentation access, independently
review BOTH URLs above for this snapshot's current STANDARD pricing and API shape.
Retain the official pages, URLs, UTC retrieval dates and SHA256 hashes as evidence.
Run the reviewed existing gateway_metadata.py with the funded project's provider key
configured privately on that machine (never put a value on the command line):

```sh
PYTHONPATH=evals/controlled-coding python -B - <<'PYCODE'
from pathlib import Path
from gateway_metadata import collect
r=collect(Path('fresh-model-metadata.json'))
print({k:r[k] for k in ('model_access','http_status','pricing_verified','provider_metadata_requests','inference_requests')})
PYCODE
```

This supported procedure fetches the official model page, parses the expected rates,
and performs one NON-INFERENCE snapshot GET; it sets its own verification flag.
It does not change billing. Require pricing_verified=true, model_access=VERIFIED,
HTTP200 and exact snapshot. Return the unedited receipt plus official source evidence;
no provider or signing private key. Receipt's hash is signed in the approval. If the
parser cannot establish the current rates, STOP; never edit a flag. A changed rate
requires separate review, not silently signing the configured old rates. Metadata
must remain <24h old at execution; this procedure has NOT been run in Phase3F.

## Enrollment — operator machine / administrator ONLY

No live private key, trust or approval was generated by this phase. On the operator's
trusted machine, with reviewed operator_auth.py/contract.py and OpenSSL:

```sh
umask 077
mkdir -m 700 operator-private
openssl genpkey -algorithm ED25519 -out operator-private/operator.key
openssl pkey -in operator-private/operator.key -pubout -out operator.pub
python -B evals/controlled-coding/operator_auth.py trust-config --public operator.pub --out operator-trust.json
openssl pkey -pubin -in operator.pub -outform DER | sha256sum
```

Private key NEVER enters this environment, chat, agent workspace or backups.
Administrator (outside the agent boundary) installs ONLY public files:

```sh
sudo install -d -o root -g root -m 755 /etc/fusion-eval
sudo install -o root -g root -m 444 operator.pub /etc/fusion-eval/operator.pub
sudo install -o root -g root -m 444 operator-trust.json /etc/fusion-eval/operator-trust.json
openssl pkey -pubin -in /etc/fusion-eval/operator.pub -outform DER | sha256sum
```

Compare fingerprint out-of-band with trusted operator copy. Refuse mismatch,
symlinks, non-root ownership or group/other write. TEST-domain keys never enroll
as LIVE. Only TEST keys were generated for automated validation.

## Four commands — fresh final source, no execution by Codex

Cloud working directory: /workspace/Fusion-phase2n-integration. Obtain fresh
model/pricing metadata through the existing supported procedure first. No metadata
flag editing. After final source commit and sanitized remote verification:

1. PREPARE (safe; no inference, produces UNSIGNED proposal only):
```sh
python -B evals/controlled-coding/live_supervisor.py prepare --out /workspace/arm-a-spec.json
```
Spec prints canonical SHA256 and records actual final clean source, config, model,
arm, objective/seed, ledger id/anchor, all limits, nonce and 30-minute expiry
(existing stricter one-hour maximum). The complete JSON file is canonical input.
Transfer exact spec + metadata to operator machine; independently re-derive:
```sh
python -B -c 'import json,hashlib; p="arm-a-spec.json"; b=json.dumps(json.load(open(p)),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); print(hashlib.sha256(b).hexdigest()); print(b.decode())'
```
Compare against cloud receipt, intended final source/config and ledger anchor.
Do not sign any undocumented difference or expired spec.

2. SIGN (OPERATOR MACHINE ONLY, after separate explicit paid authorization):
```sh
python -B evals/controlled-coding/operator_auth.py sign --spec arm-a-spec.json --metadata fresh-model-metadata.json --private operator-private/operator.key --public operator.pub --acknowledge-no-provider-cap --out operator-approval.json
```
This required flag explicitly accepts the exact no-provider-cap risk statement above.
It does not attest that a provider cap exists.
Return only approval and bound public metadata. Never transfer private key.
Independent detached-signature verification on operator machine:
```sh
python -B - <<'PY'
import json,base64
v=json.load(open('operator-approval.json'))
open('approval-payload.bin','wb').write(json.dumps(v['payload'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
open('approval-signature.bin','wb').write(base64.b64decode(v['signature'],validate=True))
PY
openssl pkeyutl -verify -pubin -inkey operator.pub -rawin -in approval-payload.bin -sigfile approval-signature.bin
```

3. PREFLIGHT (safe, read-only; consumes no nonce/reservation/slot):
```sh
python -B evals/controlled-coding/activation_preflight.py --approval /workspace/operator-approval.json --metadata /workspace/fresh-model-metadata.json
```
Checks external trust/signature, expiry, exact scope/limits, clean source/runtime,
original prompt/seed/evaluator, original anchor/chain/witness, prior admission,
budget headroom, bound fresh verified metadata and credential NAME presence only.
Never reads the credential VALUE. Repeated successful inspection is permitted;
already-consumed approval is rejected. Failure never repairs or initializes state.

4. EXECUTE — PAID, OPERATOR-RUN ONLY, REQUIRES EXPLICIT AUTHORIZATION; NOT RUN:
```sh
python -B evals/controlled-coding/live_supervisor.py run --approval /workspace/operator-approval.json --metadata /workspace/fresh-model-metadata.json --out /workspace/first-real-arm-a
```
Provision key through existing gateway environment binding only. Gateway removes
it from environment and passes a sealed anonymous FD solely to transport worker.
No key file. Sandbox children receive scrubbed environment and no credential FD.
No missions, tasks, autopilot, resolver, fallback or further interview authorized.

## Limits, stop conditions and post-run

4 requests INCLUDING retries/compaction, 32,000 conservative input, 4,096 output,
300s coding, 60s/request, $0.12 run/$2 cumulative including retained history;
planning allocation $0.50 unchanged. Old 512/768-token profiles cannot enter LIVE.
Stop: ledger/anchor/witness mismatch, incorrect model/endpoint/source/config,
unverified pricing, absent risk acknowledgment/trust, expired/consumed approval, budget exhaustion,
300s deadline, process cleanup failure. Never replay or restart a native session.

Expected private outputs: result.json, approval/spec, request/transport/response
artifacts, source manifest/patch, tool transcript, runtime-data hashes, isolation,
evaluator raw results and cleanup receipt. Ledger retains uncertainty at full
reservation; only verified usage settles it. Reconcile against provider usage page
(operator read-only review, allow billing delay; investigate discrepancies).
Operator revoke/rotate provider key afterwards; confirm gateway revoked and approval
terminal/consumed. Preserve partial output. Request-cap failure is
"inconclusive: cap-limited" unless transcript shows model error. A single success
shows initial functionality, not reliability. No new ability claim from scripted tests.

## Validation / activation boundary

30 focused TEST-domain methods pass:4 risk/transport admission,5 preflight,10
operator_auth/capture,1 local TLS transport,10 selected budget/recovery regressions.
Valid/expired/replayed/wrong-digest/unenrolled/TEST-in-LIVE cases verified.
Repeated read-only inspection leaves TEST DB/witness byte-identical. Live ledger
and witness also unchanged. No full-suite, browser or native coding rerun.
Local socket/TLS and namespace checks used the outer executor; all pass.
No live trust currently installed. Current official pricing remains unavailable.
Provider cap is NOT required; signed risk acceptance replaces that gate.
Final status AWAITING_OPERATOR_SETUP. No signing, live preflight success or paid
execution claimed. Phase3F provider inference requests 0; new spending $0.00.
