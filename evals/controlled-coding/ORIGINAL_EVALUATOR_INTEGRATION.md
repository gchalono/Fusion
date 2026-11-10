# Byte-exact original evaluator integration

VERIFIED authoritative source at40a06aa5cb932ddc0ed9bf232aca00999b355d96. Original
assertion code/thresholds/scenarios/selectors are unchanged, privately loaded from
/workspace/Fusion-phase2a/evals/implementation-evaluation. No hidden code is copied
to public Git. Hashes pinned in original_evaluator_adapter.py:
acceptance.py9bafe8c124fe97dfe6280220228d27a21366ef379673d9dfdab30d7d061bb753;
acceptance.mjs708c0230d42fb518a5f3442992241bdd9e5023b1c7f41505d4f0a5795a44d88a.

The old isolation.py is NOT executed. Assertions run in current namespace_command
with unshare-user/net/PID/IPC/UTS, UID65534, cap-dropALL, privileged-binary masking,
clearenv, existing mandatory seccomp, no host /workspace/home, and only this
independent evaluation's files plus read-only /checks originals. No provider vars.
Fixed start/stop/local-tests operations cross anonymous pipes to the existing
trusted host executor; no generic argv/path API, server, network gateway or new
budget/orchestration framework. Unknown actions rejected. Original HTTP assertions
use its original UnixHTTP requests against the existing byte-exact service relay.

Each application is a separate current filtered namespace with only read-only
native patch source at/app, its own writable DATA_DIR and relay socket directory,
ephemeral HOME/tmp, no hidden tests or unrelated private evidence. /app coding alias
is a symlink to the SAME existing/work mount, not another host mount. Candidate
capture rejects symlinks/unsafe paths; patch includes executable Git file modes.
Independent checkout source and modes checked before/after grading. Candidate
stdout goes to service logs, never assertion/result/control pipes.

The host lifecycle launcher is trusted, like existing execution.run_command. It
never interprets model commands and passes cleared env to app/evaluator; assertion
processes cannot read host credentials/files. No current filter/capability/network
permission was removed. Additional mounts are only the product's data/source and
one public HTTP relay script; hidden assertions never enter application namespaces.

Browser command returns a BLOCKED dependency result, not a mock browser success.
Original unchanged assertions retain a false browser category and completion=false;
adapter reports browser BLOCKED separately. Raw 90/100 with9 passed is NOT full
acceptance. All nine non-browser categories pass for the regenerated native A2.
