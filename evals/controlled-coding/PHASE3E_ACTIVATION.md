# Phase 3E activation — AWAITING_OPERATOR_SETUP

No inference is authorized or performed. This package is for ONE Arm A run only.
VERIFIED baseline: development dc67ebdcaafdbeb6c2b460cf92dc0d0b5c617427,
sanitized backup 82428dc397d088264e03b04c7bc0f40abbb3f00c. Current source is the
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
Private receipts: /workspace/phase3e-evidence/ (not public backup contents).

Unchanged task phase2m-personal-task-manager:A, source objective/seed/evaluator,
Ed25519 supervisor, gateway, native Pi, seccomp, original historical evidence.
The only additive runtime utility is activation_preflight.py: read-only approval
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

## Provider spending controls (read-only assessment)

No permitted non-admin interface available here establishes a provider hard cap.
No admin credentials, provider management calls or billing changes were used.
- Local ledger: VERIFIED hard admission/reservation control for this gateway only;
  $0.12/run/$2 aggregate, 4 underlying requests including retries and compaction.
- Provider project budget/notifications: UNKNOWN here; treat any unverified budget
  as a soft alert, never a hard cap. Cannot sign a hard-cap attestation from it.
- Project key/model allowlist: UNKNOWN; isolation/allowlist is not a money cap.
- Provider hard cap: UNVERIFIED. No attestation has been fabricated.

Smallest operator choices (not activated; no numeric balance invented):
(a) small prepaid balance B with auto-recharge OFF: nominal funding B; delayed
billing/overage behavior unverified, therefore NO proven hard maximum B.
(b) dedicated project + project-scoped key + exact-model allowlist: reduces scope;
without provider-enforced cap, maximum project monetary exposure is UNKNOWN.
(c) both: tighter isolation/funding exposure, but no proven provider dollar maximum
until documented provider enforcement/overage behavior is independently confirmed.
If a provider-enforced project ceiling H is actually evidenced, exposure <=H under
those provider guarantees; record H/evidence before signing. The local single-run
bound remains $0.077416 at assumed rates. It is not a provider-side guarantee.
Existing transport REQUIRES truthful provider_side_cap_confirmed=true. None of
(a)-(c) alone waives it. If it cannot be evidenced, STOP for operator review; do
not change the supervisor, hard limits or meaning of that attestation.

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
python -B evals/controlled-coding/operator_auth.py sign --spec arm-a-spec.json --metadata fresh-model-metadata.json --private operator-private/operator.key --public operator.pub --confirm-provider-side-cap --out operator-approval.json
```
Use --confirm-provider-side-cap ONLY with verified provider enforcement evidence.
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
unverified pricing/provider cap/trust, expired/consumed approval, budget exhaustion,
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

5 new focused TEST-domain tests pass, plus all 10 existing operator_auth/capture
tests. Valid/expired/replayed/wrong-digest/unenrolled/TEST-in-LIVE cases verified.
Repeated read-only inspection leaves TEST DB/witness byte-identical. Live ledger
and witness also unchanged. No full-suite, browser or native coding rerun.
The existing operator suite first hit nested local-socket EPERM; outer retry passes.
No live trust currently installed. Pricing and provider hard-cap evidence unavailable.
Final status AWAITING_OPERATOR_SETUP. No signing, live preflight success or paid
execution claimed. Phase3E provider inference requests 0; new spending $0.00.
