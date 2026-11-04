# Fixed client-brief answer protocol, version 2

This is evaluation input policy, not generated output. Commit this document and
the selected brief and record their SHA-256 hashes before any inference request.

1. A human or deterministic scripted answerer uses only facts in the frozen brief.
2. Unknown facts receive exactly: `No preference; use your judgment.`
3. Never invent scope, platform requirements, deadlines, budgets, or decisions.
4. Record the native question, selected option identifiers, verbatim answer, and
   referenced brief fact identifiers in order. The structured native question ID
   is the response-map key. Additional text uses native `_comment` / `_other`.
5. Do not alter native prompts or structured output. Do not auto-complete a plan.
6. Stop at the authorized turn cap; retain an incomplete transcript as incomplete.
7. This version does not support an LLM answerer. Enabling one requires explicit
   authorization and routing every answerer HTTP request through the SAME budget.
8. Use the one rate-limit identifier `fusion-phase2a-pilot`. Preserve the native
   five-starts-per-hour limit. The eventual supervisor also needs durable start
   accounting across process restarts; it must never vary identifiers/reset clocks.
9. Pilot input and output are excluded from any later evaluation corpus.
10. `briefs.json` contains representative engineering objectives and fixed
    clarification answers for OFFLINE tests only. These are not genuine plans
    or a proposed evaluation corpus. Unknown questions receive the fixed reply.
11. For an unknown native confirm question, stop as incomplete: native formatting
    would otherwise turn missing boolean input into `No`, inventing a preference.
12. The offline supervisor maintains durable five-starts/hour accounting under
    the same identifier across disposable namespaces, including failed starts.

## Blank brief template

```json
{
  "goal": "<pilot goal>",
  "excluded_from_corpus": true,
  "facts": [
    {"id": "F1", "topic": "<topic>", "value": "<user-provided fact>"}
  ],
  "unknown_reply": "No preference; use your judgment."
}
```
