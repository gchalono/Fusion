# Phase 2N offline readiness

**PHASE_2N_PARTIALLY_READY** — native fixture and current validations pass; live gates remain outstanding.

VERIFIED: authorization is $0.00 provider spend, identifier fusion-phase2a-pilot,
maximum three native starts/hour, and reviewed pushes to eval/phase2n. Limited
unprivileged namespace commands outside the agent sandbox were explicitly approved;
no host-wide configuration, firewall or package changes are authorized/performed.

## Claim table

| Claim | Classification | Evidence pointer |
|---|---|---|
| External baseline 993af2bdf7a5fa223ca16bf233be399bc6fd9a86 matched GitHub and is an ancestor; initial tree clean | VERIFIED | preflight.json hash in readiness-evidence.json |
| Re-run baseline: 14 coding + 33 collector + 9 persistence = 56 passed, no discrepancy | VERIFIED | baseline logs indexed in readiness-evidence.json |
| Current suites: 20 coding + 37 collector + 9 persistence = 66 passed | VERIFIED | current test logs, readiness-evidence.json |
| Inner unshare/bwrap denied uid-map writes; approved outer unprivileged probes passed; rootless Docker available, host firewall not usable | VERIFIED | capability-probe.json and outer-probe.json hashes |
| Reference sandbox has user/net/PID/mount/IPC/UTS isolation, UID 65534, dropped capabilities, scrubbed environment and allowlisted read-only runtime files; only writable workspace/home/tmp and one inference Unix socket | VERIFIED | isolation.py:22; 20-case namespace summary |
| Direct Python/Node/curl, raw ICMP, DNS, IPv6, metadata, host loopback and proxy-tampering probes denied; each has a successful gateway HTTP control | VERIFIED | isolation.py:103; namespace results |
| All protocol-specific positive controls are identical to their negative protocols | UNVERIFIED | Raw ICMP/DNS/IPv6/metadata use Python HTTP gateway controls; not a full Step 4 matrix |
| Canary absent from observed environment values, process arguments, regular FDs and mounted writable/home/eval surfaces; positive controls plant it in gateway initial environment and an inheritable FD | VERIFIED | namespace credential case; fixture canary never persisted |
| No real provider credential exists anywhere outside a future gateway, or all possible files/FD types are proven secret-free | UNVERIFIED | Only fixture canary and declared surfaces tested; no real credential was loaded |
| Gateway token is local, revocable, bound to trusted run/caps; clients cannot select a new run/policy; policy hash is immutable per run | VERIFIED | isolation.py:68; budget.py:66; namespace revocation/cap cases |
| Protected files cannot be written through the granted namespace view; no admin interface exists | VERIFIED | filesystem and endpoint cases; isolation.py:22,68 |
| Each guarded request reserves and fsyncs before transport; observed usage, estimated charge and measured charge remain separate | VERIFIED | budget.py:75,113,141; lifecycle/crash tests |
| Missing/truncated/failed/interrupted requests retain worst-case exposure; restart marks unreconciled requests UNCERTAIN without refund | VERIFIED | budget.py:95,105; test_lifecycle.py; test_gateway_crash.py |
| Aggregate $2 / coding $0.15 / four-call limits serialize across processes; settlement never adds the same request a second time or releases exposure | VERIFIED | test_budget.py; test_lifecycle.py |
| Client auth cannot become upstream auth, output tokens clamp and are logged; unknown endpoint/host/model/client denied | VERIFIED | inference_socket and local stub controls; fixture auth only |
| Gateway shutdown leaves the namespace without fallback egress | VERIFIED | gateway-down case |
| A combined in-namespace mid-request kill, restart and authorized resume protocol is fully tested | UNVERIFIED | Host-side HTTP kill/recovery and namespace shutdown are separate tests |
| Fixture upstream contacts are exclusively local; real-host contact counter is zero | VERIFIED | namespace summary: local stub only; no real provider URL used |
| Host-wide packet capture or provider invoice establishes zero charges | UNVERIFIED | No packet capture/provider billing query; real transport never invoked, measured charge remains null |
| Genuine native PostgreSQL/ICU interview/session integration passed at source c8a302767001910b188d734b5f55f435319ea08b | VERIFIED | native-verified.json; seven local attempts, only project.ai_sessions changed |
| Production/live coding execution is forced through this reference boundary | UNVERIFIED | Reference namespace is not integrated into a live coding runner |
| Every future planning/coding run must reuse one fixed experiment ledger | UNVERIFIED | Atomicity proved for a selected shared DB; fixture DBs are not a paid supervisor |
| The initial verifier SQLite-variable shadowing failure was corrected and capture replay now passes | VERIFIED | native-verifier-infrastructure-error.log; test_verify_evidence.py, same immutable native capture |
| Historical Phase 2M plans, approvals, requests, costs or reported numbers are available/validated | UNVERIFIED | Fixed-location assessment only; no historical measurements reused |

## Scope and limits

VERIFIED: isolation tier is **PARTIAL** overall. OS enforcement passed for the
reference deterministic-command environment. No real coding agent, provider-backed
interview, MCP execution, mission or autopilot was started. Protection is scoped to
unprivileged commands within the granted namespace; privileged host attackers and
kernel/VM escapes are excluded. The old native harness remains a trusted local
fixture, not a proven untrusted coding environment. No new live supervisor exists.

VERIFIED: pricing contracts, model settings, bytes and usage in security fixtures
are test doubles. Their synthetic exposure is not provider spending or a measured
charge. Native fixture rates are explicitly synthetic and lowered to exercise the
shared $2 reservation cap without changing native context/output settings. Real
physical-model pricing/token bounds remain UNVERIFIED and block live readiness.

VERIFIED: ledger exposure remains the full reserved bound even after SETTLED
(estimated). This is conservative and intentionally offers no automatic refund.
UNCERTAIN cannot automatically become settled; manual operator reconciliation
requires separate work/authorization. Policy/ledger are outside the sandbox view.

## Architecture paths inspected

VERIFIED: native interview enters createResolvedAgentSession in
packages/dashboard/src/mission-interview.ts:41 and native-runner.mts:83. SDK retry,
format retry and compaction can each issue further HTTP requests. The evaluation
Gateway receives attempts individually; reference subprocesses have no host
routes/proxy/credential mounts. Source/client HTTP libraries, SDK fallback, proxy
variables, raw IP/DNS/IPv6/metadata, host localhost services, filesystem credentials,
/proc, inherited FDs and alternate namespace/container entry points were reviewed.

UNVERIFIED: outside this granted environment, production providers, host tools,
MCP/runtime plugins and supervisors may still reach paid endpoints. The platform
permits api.openai.com; destination allowlisting alone is not gateway-only routing.
AF_VSOCK and all privileged escape paths are not certified by these probes.

## Phase 2M and planning input process

VERIFIED: only the fixed paths listed in phase2m-fixed-locations.json were checked;
no repeated exhaustive search. Existing reusable implementation includes the
native runner/session persistence, native question/response APIs and summary
serialization (native-runner.mts:91,99,107; mission-interview.ts:1325,1392,1639),
plus existing Gateway and budget hooks. protocol.md/briefs.json are offline scripted
fixtures, not a human approval protocol or genuine evaluation plans.

UNVERIFIED: original Phase 2M objective/baseline, native plan, eight approvals,
transcript, nine request/response records and accounting/audit evidence remain
missing. Historical numbers are not planning cost/budget inputs.

INFERRED: minimum future reconstruction is a thin operator approval adapter around
existing native APIs, not a second planning architecture. Freeze each task first;
after separate paid approval generate a fresh native interview per task, pause for
each question, record the question hash, verbatim answer and explicit operator
approval before submit, then serialize the native summary and link its source
hashes. Stop on absent approval. Freeze B/C inputs after planning; B includes the
plan, C additionally the approved transcript. B/C measures presentation, since the
plan may incorporate answers. Record every new planning attempt/cost separately
and include it in end-to-end comparisons; never fabricate or reuse old approvals.

## Commands, evidence and next action

VERIFIED: Python 3.12.14, Node 24.22.1, Git 2.52.0 and genuine PostgreSQL 15.18/ICU
60 loader checks were inspected/rerun; no system changes. Commands:

```sh
python -m unittest discover -s evals/controlled-coding -v
python -m unittest discover -s evals/planning-collector -v
python -m unittest discover -s evals/persistence -v
python evals/planning-collector/offline_runner.py --security-probe NEW_PRIVATE_DIRECTORY
```

VERIFIED: raw evidence remains private at /workspace/work/native-isolation-evidence.
readiness-evidence.json contains reviewed summaries and SHA-256/size references;
no canary, local token, raw provider records or credential values are committed.
The initial verified remote anchor is 993af2bdf7a5fa223ca16bf233be399bc6fd9a86;
subsequent milestone tips are independently verified outside their own commits.

VERIFIED: the permitted native comprehensive fixture passed with --max-starts 3,
the same unchanged ledger and verified ICU directory. Independent replay verifies
its session/gateway accounting artifacts. The initial verifier failed because a
SQLite connection shadowed the DB-diff dictionary (infrastructure verification
bug, not a native application failure). Corrected it under evals, added two
regression tests, and replayed the same capture successfully; no test was skipped.
The native file is labeled native-test-double.json; it is not a genuine plan.

INFERRED: next engineering task is one integrated command-runner boundary and
combined interruption/restart test, complete protocol-appropriate positive
controls, and a fixed experiment-level ledger plus verified model pricing/input
bounds before proposing any paid pilot. The thin human approval adapter must
reject every unanswered/unapproved question; no missing Phase 2M component needs
to be reconstructed beyond these interfaces.

UNVERIFIED: no live approval is requested. Before the first live pilot: finish the
missing strict security controls and live-runner integration, verify pricing/input
bounds, specify human-approved fresh planning inputs and receive separate explicit
paid authorization (at most $2 aggregate), model/settings and execution limits.

VERIFIED: final code source c8a302767001910b188d734b5f55f435319ea08b also
passed the genuine comprehensive native fixture and independent capture verifier.
Seven local stub contacts matched seven gateway reservations; only
project.ai_sessions changed. All seven requests are UNCERTAIN because fixture
usage is deliberately absent, retaining 1,127 micro-USD of synthetic exposure,
not a provider charge. Prior start-ledger entries were unchanged; one start was
appended, leaving two active against the approved limit of three. No provider
requests, real credentials, genuine plans or approved task answers were produced.

VERIFIED: milestone 465151ee280c39a90e61b27fcd2a2de1f093700f passed fresh
remote-clone preflight and its 64-test suite. Final documentation-only checkpoint
preflight, fetch/ls-remote equality and 66-test recovery are recorded externally
after publication, avoiding a circular self-SHA in this file.
