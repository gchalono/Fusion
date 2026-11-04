# Required pricing contract for a future paid pilot

These are prerequisites, not authorization or current provider price claims.

1. Exact upstream provider, HTTPS path and physical model version; no opaque
   routers/virtual aliases. Response identity checks cannot undo prior billing.
2. Authoritative, dated hard input/output token bounds, including system/tool
   schemas, results, full history, retries and compaction. No byte/token guesses.
3. Maximum input/output dollars per million tokens for this account, including
   long-context tiers, reasoning, cache writes/reads, regional premiums and
   minimum charges. If other charges cannot fit this bound, fail closed. Hosted
   search/code execution and separately billed provider tools are unsupported.
4. Confirm output fields include all billed reasoning/output and that a hard
   model bound applies when the field is absent. Never shrink native limits to
   fund a request; refuse when its full worst case cannot be reserved.
5. Before every HTTP attempt reserve, rounded up to integer microdollars:
   `(input_bound * input_price_per_million + output_bound *
   output_price_per_million) / 1,000,000`. No refunds for failed/ambiguous calls,
   missing usage or caches. Include retries, compaction and any future answerer.
6. Keep reservations labeled estimated upper bounds and provider usage unverified
   until validated. Custom-provider native catalog prices are zero: SDK `cost:0`
   is not reliable invoice evidence. Never label missing usage as zero spending.
7. Freeze source/collector commits, full patch hash, protocol/brief hashes, config
   and pricing/bound evidence hashes before paid dispatch. A boolean/hash in a
   config file alone does not authenticate a provider contract.

Offline arithmetic fixtures use **$3/M input, $15/M output**, input bound 128,000
and output bound 32,768. These are synthetic, not a chosen model's quote. Each
mock attempt reserves 875,520 microdollars; seven reserve 6,128,640 microdollars.
No money was spent. All observed native output limits were preserved.

Paid runtime remains unmeasured: sum request/tool latencies, native backoff and
interview answer time. Starts obey five/hour and the one fixed identifier.
