# Offline self-test reliability upgrade

The six baseline grading subcases failed before candidate execution. A minimal
namespace probe reported:

```text
bwrap: execvp /home/codespace/.python/current/bin/python: No such file or directory
```

The sandbox mounts the resolved interpreter installation. The execution adapter
now also invokes that resolved path. The independent grader, frozen tests,
authentication, namespace policy, contract and budgets are unchanged. All six
correct/wrong controls subsequently produced their expected grading outcomes.

Both coding entry points use `self-test-session.mjs`. Prompt guidance asks the
agent to derive boundary, empty, invalid and interacting cases from the supplied
specification, write `local_self_test.py`, execute it with bash, inspect failures,
and preserve meaningful assertions when repairing code. The quality and
completeness of those cases remain model responsibilities.

Orchestration additionally executes the agent's unittest file inside the coding
sandbox after the first session response. Missing, empty, skipped or failing
tests cannot complete normally. One continuation may receive only local failure
output and repair the candidate. A second failure terminates. Command launch
failure, command timeout, model error, abort or budget refusal terminates without
a repair continuation. Automatic model retries and compaction are disabled for
these evaluation sessions; no fallback prompt method is used.

The added bounds are two local executions, five seconds per execution, one
repair continuation, 32 session tool calls, 8 KiB of local output, and a 60-second
session-loop deadline. Existing gateway request/token/spend limits and the outer
process deadline remain authoritative and can stop the loop earlier. This adds
no spending authority and performs no automatic retries of failed model calls.

Only the shared orchestration module is added to the coding mounts. Acceptance
fixtures, grader modules and private records remain outside that namespace.
After the coding process exits successfully, the existing grader receives only
the submitted solution patch in a fresh namespace. Local tests are not copied to
the grader, and acceptance results never feed a repair prompt. A real namespace
test proves a locally passing but incorrect duration parser still fails grading.

Deterministic scripted sessions exercise actual Python execution and repair for
interval merging and whitespace word counting, plus first-pass success, invalid
tests, tool failures, deadlines, tool caps, model/gateway refusal and feedback
redaction. These verify orchestration, not genuine model reasoning or improved
accuracy. Agent-authored tests remain untrusted and may be weak or misleading;
independent grading is still essential. No paid or live model run was performed.
The installed Pi session's end-to-end model behavior was not remeasured.

Offline verification from the repository root:

```sh
python -B -W ignore::ResourceWarning -m unittest discover -s evals/controlled-coding -v
node --test evals/controlled-coding/self-test-session.test.mjs
python -B evals/controlled-coding/harness.py verify
python -B evals/persistence/scan.py --base HEAD
git diff --check
```

The Python suite includes the Node orchestration tests and the real namespace
grading-independence check. The separate Node command gives individual case
results. Existing unclosed SQLite ResourceWarnings were observed in the baseline
Python tests; suppressing that warning category above only reduces output noise.

Historical runs A/B and their results are not rewritten or regraded. This is a
prospective behavior change; it is not evidence that any historical run improved.
