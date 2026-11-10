# First real-model Arm A run — Phase3F, AWAITING_OPERATOR_SETUP

No inference is authorized. Operator signing key stays outside this environment.
Provider-side hard cap is NOT required. An exact signed acknowledgment accepts
unverified provider caps and potential billing beyond the local estimate; local
controls remain the only verified spending enforcement. Only ONE approved run.

Frozen task: `phase2m-personal-task-manager:A`; model `gpt-4.1-mini-2025-04-14`.
Objective SHA256 `4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0`.
Common instructions SHA256 `f6807d6bd0f165b0f4bcc97b0331a067adea348cb715a8c4335a970a36b4d6fa`.
Arm A prompt SHA256 `eeb98f4c68aa3ae99907cc8475b2e9ab97a4945cb7acf0942b72c033083f9495`.
Empty seed commit `f2a49cb3fc7e02cd225053d4e2d07c589b4c808b`.
Original evaluator hashes: acceptance.py `9bafe8c124fe97dfe6280220228d27a21366ef379673d9dfdab30d7d061bb753`;
acceptance.mjs `708c0230d42fb518a5f3442992241bdd9e5023b1c7f41505d4f0a5795a44d88a`.

The current complete six-step procedure (key generation, root-owned public trust
installation, prepare, sign, non-consuming preflight, execute) is in
[PHASE3E_ACTIVATION.md](PHASE3E_ACTIVATION.md). It includes independent signature
verification and the operator-side official pricing procedure. No obsolete provider
cap attestation or prepaid/billing setup is required.

Cloud safe PREPARE after final source/backup publication:
```sh
python -B evals/controlled-coding/live_supervisor.py prepare --out /workspace/arm-a-spec.json
```
Operator machine ONLY, after separate explicit paid authorization:
```sh
python -B evals/controlled-coding/operator_auth.py sign --spec arm-a-spec.json --metadata fresh-model-metadata.json --private operator-private/operator.key --public operator.pub --acknowledge-no-provider-cap --out operator-approval.json
```
Cloud non-consuming PREFLIGHT:
```sh
python -B evals/controlled-coding/activation_preflight.py --approval /workspace/operator-approval.json --metadata /workspace/fresh-model-metadata.json
```
PAID EXECUTE — OPERATOR ONLY; DO NOT RUN until separately explicitly authorized:
```sh
python -B evals/controlled-coding/live_supervisor.py run --approval /workspace/operator-approval.json --metadata /workspace/fresh-model-metadata.json --out /workspace/first-real-arm-a
```

4 underlying requests incl retries/compaction,32000 input/4096 output,300s run/60s
request,$0.12 run/$2 aggregate including11522 micro-USD retained;planning$0.50.
Atomic reservations,exclusive ownership,crash recovery and uncertainty retention,
exact model/endpoint and gateway-only credentials unchanged. Default service tier
is explicit. At configured rates worst77416 micro-USD;headroom1411062 micro-USD.
Current pricing unverified; operator must use the supported verifier, never edit flags.
No live key/trust/signature created, no provider calls/inference this phase.

Preserve partial result.json/transcript/source/evaluator/ledger/cleanup evidence.
Stop on any source/config/model/endpoint/anchor/witness mismatch,missing/expired/
consumed approval,missing signed risk acknowledgment,unverified pricing,budget or
clock exhaustion,cleanup failure. No native replay or automatic whole-run retry.
Operator reconciles ledger with provider usage and revokes/rotates key after run.
Cap-limited failure is inconclusive unless a model error is visible. A single
success shows initial functionality,not reliability. Private recovery remains local.
