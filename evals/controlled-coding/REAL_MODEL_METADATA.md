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
