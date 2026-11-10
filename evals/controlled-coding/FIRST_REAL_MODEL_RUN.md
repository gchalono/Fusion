# First real-model Arm A run — executable, CONDITIONALLY_READY

No paid inference is authorized yet. Technical rehearsal passed; operator enrollment,
current pricing verification and explicit signed paid-run approval remain required.

Frozen task: `phase2m-personal-task-manager:A`; model `gpt-4.1-mini-2025-04-14`.
Objective SHA256 `4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0`.
Common instructions SHA256 `f6807d6bd0f165b0f4bcc97b0331a067adea348cb715a8c4335a970a36b4d6fa`.
Arm A prompt SHA256 `eeb98f4c68aa3ae99907cc8475b2e9ab97a4945cb7acf0942b72c033083f9495`.
Empty seed commit `f2a49cb3fc7e02cd225053d4e2d07c589b4c808b`.
Original evaluator hashes: acceptance.py `9bafe8c124fe97dfe6280220228d27a21366ef379673d9dfdab30d7d061bb753`;
acceptance.mjs `708c0230d42fb518a5f3442992241bdd9e5023b1c7f41505d4f0a5795a44d88a`.
The previous historical proposal/incomplete-command notes remain in Git history;
the procedure below is the current implementation.


Status CONDITIONALLY_READY. The real supervisor entry has passed15 TEST-domain
synthetic scenarios,including actual native Pi/read/write/bash,anchored accounting,
capture,evaluation,cap stop and crash/replay/security negatives. No paid run occurred.
Code checkpoint aab233755ca008eea05e4ea210554772192c47ba; final report-only descendants
are mapped in backup SOURCE_MAP. Prepare fresh specs from the actual approved clean HEAD;
do not reuse old Phase3/3C signatures/hashes. Original task/seed/evaluator unchanged.

### Enrollment — OPERATOR ONLY, outside the development-agent trust boundary

On a trusted operator machine,using reviewed operator_auth.py and OpenSSL:

```bash
umask 077
mkdir -m 700 operator-private
openssl genpkey -algorithm ED25519 -out operator-private/operator.key
openssl pkey -in operator-private/operator.key -pubout -out operator.pub
python -B evals/controlled-coding/operator_auth.py trust-config --public operator.pub --out operator-trust.json
openssl pkey -pubin -in operator.pub -outform DER | sha256sum
```

Keep operator-private/operator.key on that trusted machine. NEVER send it to Codex,
copy it into the coding environment,or publish it. Transfer ONLY the public files;
the operator/cloud administrator installs them OUTSIDE the agent session:

```bash
sudo install -d -o root -g root -m 755 /etc/fusion-eval
sudo install -o root -g root -m 444 operator.pub /etc/fusion-eval/operator.pub
sudo install -o root -g root -m 444 operator-trust.json /etc/fusion-eval/operator-trust.json
```

Verify the DER fingerprint against the operator's trusted copy. These commands were
NOT executed by Codex. No live key or trust anchor has been generated/selected by it.
TEST-domain material is rejected for live use,even with a valid TEST signature.

### Prepare, sign, and authorize ONE run

On cloud,from /workspace/Fusion-phase2n-integration,with a clean reviewed HEAD:

```bash
python -B evals/controlled-coding/live_supervisor.py metadata --out /workspace/fresh-model-metadata.json
python -B evals/controlled-coding/live_supervisor.py prepare --out /workspace/arm-a-spec.json
```

Metadata is non-inference,within AUTHORIZE_METADATA_CHECK. The present receipt has
pricing_verified=false and will NOT arm live execution. Obtain current official
verification; never edit a flag to bypass it. Exact model must remain
 gpt-4.1-mini-2025-04-14. GET visibility is not billing/inference proof.

Transfer spec and metadata bytes to the trusted operator machine. After separate
EXPLICIT paid authorization for this exact spec,operator signs there:

```bash
python -B evals/controlled-coding/operator_auth.py sign --spec arm-a-spec.json --metadata fresh-model-metadata.json --private operator-private/operator.key --public operator.pub --confirm-provider-side-cap --out operator-approval.json
```

Use --confirm-provider-side-cap ONLY if the existing RealTransport's dedicated key/
project cap requirement is truthfully verified. It is a signed attestation,not an
automatic assumption. If unmet,stop and obtain separate review; do not waive the check.
Return ONLY operator-approval.json; keep it in a private directory. Spec expires in30
minutes and is single-use. Rejected/expired approvals do not justify an automatic retry
or replacement paid run. Source/config/ledger/anchor/model/task/limits are signed.

The actual authorized cloud run command is:

```bash
python -B evals/controlled-coding/live_supervisor.py run --approval /workspace/operator-approval.json --metadata /workspace/fresh-model-metadata.json --out /workspace/first-real-arm-a
```

DO NOT execute now: paid inference remains unauthorized. There is no --live shortcut.
Only the gateway accesses OPENAI_API_KEY after gates; it uses sealed anonymous FD
inheritance to the real worker,not a provider-key file. Sandbox receives a distinct
run token only. No model fallback,mission,TaskExecutor,autopilot or planning interview.

Limits remain4 requests incl retries/compaction,32000 conservative input/4096 output,
300s coding/60s request,$0.12 run,$2 aggregate incl11522 retained;planning$0.50.
Default service tier only. At configured rates,max77416 micro-USD. Unknown/missing
usage retains full reservation; verified settlements replace reservations,no double
charge. On provider auth/quota/billing errors,the gateway revokes. Native rate retries
remain native within the same request budget. Real dispatch count is marked unknown
when transport failure makes it unmeasurable; reservation upper bound is separate.

Expected private outputs: approval/spec,raw request/transport/response artifacts,
provider usage/ledger lifecycle,tool transcript,source hashes+modes+patch,runtime DB
hashes,size,isolation receipt,evaluator raw output and cleanup/terminal-state receipt.
Always inspect result.json. Cap-only failures are inconclusive: cap-limited unless
transcript shows a model error. Scripted rehearsal is not real-model performance.
Original evaluator still runs after a budget stop. Reuse browser attestation only for
identical accepted patch; other candidates use original full browser grading.

After gateway/process crash,NO native replay/restart. An operator may classify retained
outstanding exposure and terminalize the old run without inference:

```bash
python -B evals/controlled-coding/live_supervisor.py recover
```

Recovery does not create an approval or a replacement run. Missing/corrupt ledger or
witness requires restoring the exact verified continuation+witness; never initialize
a new ledger or re-import spending. Private recovery is local-only,not claimed verified
externally. Rehearsal command (TEST state/keys/local transport only):

```bash
python -B evals/controlled-coding/rehearse_live_supervisor.py --out /workspace/new-phase3d-rehearsal
```
