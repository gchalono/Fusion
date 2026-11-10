# Native positive TEST DOUBLE validation — in progress

VERIFIED Arm A: exact frozen input, native Fusion/Pi read/write/bash tools, four
underlying local TLS requests, three tool replies plus final reply. The model and
native output ceiling remain gpt-4.1-mini-2025-04-14 / 512 tokens; context 32000,
request cap four, offline output reservation 512, cumulative reservation 144384,
per-run $0.12 and aggregate $2 remain unchanged. No fixture source is mounted into
the coding view or copied from the reference solution. New, separate scripted code
is transmitted solely in the native tool arguments. All behavior is TEST DOUBLE,
never evidence of relative A/B/C treatment effectiveness or real-model capability.

VERIFIED output sizing: pinned user-local js-tiktoken 1.0.21, o200k_base. Token
counts for complete serialized deltas are 496, 496, 493, with 16 additional reserved
framing tokens each, all <=512. These are local encoding measurements, NOT
provider-reported usage or proof of live provider framing. Encoding rank SHA-256:
`a9e8a0c1f332c58f1a9cef2f8d7be59b31bb4b42531a3a0a64d9ad3b3d19033b`.
Native/default fixture behavior is unchanged; only this separate positive fixture
uses exact token measurement instead of the earlier stricter 512-byte fixture check.

VERIFIED output: application.py + README.md created through native tools; native
storage self-test passed; application startup/HTTP smoke and cleanup ran through
native bash. The captured multi-file patch applies to a fresh empty Git checkout,
and its file hashes equal the native captures. The UNCHANGED independent grader
passed local web page, create/due date, view, edit, complete, SQLite restart/persistence
and delete. Independent browser page creation FAILED due the existing Chromium
infrastructure defect. Independent automated-test check is after that gate and was
not reached; native self-test evidence is separate. Full acceptance remains UNVERIFIED.
Self-test quality is narrow storage coverage; independent HTTP coverage is stronger.

Evidence: `/workspace/completion-native-positive-A/positive-result.json`,
`fixture-plan.json`, `candidate.patch`, `agent-stdout.txt`, `native-wire-*.json`,
`independent-acceptance/`; local TEST DOUBLE evidence, never public raw provider logs.

Public dependency setup (no provider requests):
`npm install --ignore-scripts --no-audit --no-fund --prefix /workspace/fusion-offline-tokenizer js-tiktoken@1.0.21`.
Native run:
`python evals/controlled-coding/task_manager_positive.py --root NEW_PRIVATE_DIR --runtime /workspace/Fusion --tokenizer /workspace/fusion-offline-tokenizer/node_modules/js-tiktoken/dist/index.js --arm A`.

Reproducibility normalization declared BEFORE repeat: compare patch and candidate
hashes exactly; omit only run-root paths, timestamps and wall time. Compare wire
request counts and reservation/transition values exactly; normalize the unittest
elapsed-time text in tool results, documenting any other residual differences.
No hidden test, acceptance requirement or security policy was modified.
