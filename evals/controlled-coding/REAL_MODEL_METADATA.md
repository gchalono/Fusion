# Model metadata — non-inference check

VERIFIED: exactly one authenticated fixed-host,non-redirecting GET
https://api.openai.com/v1/models/gpt-4.1-mini-2025-04-14 returned HTTP200 and exact id.
Returned object=model,owned_by=system,created=1744317547. Gateway-only credential access;
no key/header/error body persisted. This does NOT establish inference permission,billing
or successful tool calls. Raw allowlisted receipt: /workspace/phase3d-evidence/model-metadata.json.

Official URL attempted: https://developers.openai.com/api/docs/models/gpt-4.1-mini .
Documentation was unreachable; no network permission was changed. Current independent
pricing/context/output/API support/deprecation verification remains UNVERIFIED.
Supplied earlier evidence:$0.40/M uncached input,$0.10/M cached,$1.60/M output;
context1047576,output32768,Chat Completions+Responses,streaming/function calls; supplied
deprecation status is historical evidence,not a fresh current claim. No substitution.

Configured-rate conservative maximum:4*ceil(32000*.40+4096*1.60)=77416 micro-USD.
The live command requires a fresh(<24h),operator-signature-bound receipt with pricing
verified before dispatch. Never change the receipt's verification flag manually to
make the preflight pass. Resolve official documentation access and repeat the authorized
metadata procedure,or obtain separately reviewed official verification evidence.
Provider metadata GETs1; inference requests0; new inference spend$0.00.

## Phase3E activation review (2026-11-10)

No new provider API requests or inference. Both official model documentation above
and https://openai.com/api/pricing/ remained unreachable on a credential-free retry
through the enforced proxy. pricing_verified remains false; no receipt modified.
Prior HTTP200 is historical snapshot visibility only, not inference access/credits.
Strict broker explicitly uses service_tier=default, rejects other tiers; uncached
configured-rate reservation 19,354 micro-USD/request, four attempts 77,416.
Headroom after history, $0.50 planning and this run: 1,411,062 micro-USD.
These rate-based bounds remain conditional on official pricing verification.
See PHASE3E_ACTIVATION.md for supported procedure and operator-only prerequisites.

## Phase3F (2026-11-10)

Credential-free official model/pricing URL retries remain unreachable, including
outer-executor retry. pricing_verified remains false, no receipt edited or new
provider GET performed. Use the operator-side existing collect procedure documented
in PHASE3E_ACTIVATION.md on a network that can reach official documentation; return
unedited verified receipt and source pages/URLs/date/hashes. Failure to parse is a
stop condition. No pricing bypass, substitution or rate change is authorized.
Default service_tier explicitly injected by strict broker; alternatives rejected.
Configured rates0.40/0.10/1.60 USD/M remain supplied,unverified assumptions.
Per-request ceil19354 micro-USD,four77416,remaining headroom1411062.
Provider cap attestation is removed by operator authorization; signed risk acceptance
is required instead. No provider billing change or prepaid requirement.
