# VERIFIED real browser acceptance — 100/100

VERIFIED: the unchanged native candidate patch
df383ba28a82be9f2a07b36d188a4f4bec11f551f1013634186c3752c2b0ba6c
passes ALL TEN original acceptance categories, independently repeated in two fresh
checkouts. Both raw original scores100/100, completion=true. No candidate regeneration
or direct edit; all five source hashes/modes still match the recorded native output.
Actual original assertion hashes at40a06aa5cb932ddc0ed9bf232aca00999b355d96 remain unchanged.

## Binary provenance and unchanged boundary

VERIFIED preferred Playwright1.60 metadata pins headless-shell148.0.7778.96/r1223.
No compatible local cache exists; current enforced policy still excludes its CDN,
so previously blocked endpoints were NOT retried. One maintained official alternative
was obtained from already permitted dl.google.com, without changing permissions.
Google Chrome stable157.0.8103.50-1, amd64, archive147674220 bytes:
SHA25692148bd14dc05823a64061c2fafcf20d4d82b3fc56f5831206f16d2ac9ee3f79.
Signed Google Release verifies Packages.gz SHA256
3cfd93a4a4b594a52fc4f9192660ce3e1698c64b56383177194a6798b0816b27;
its package entry verifies the exact archive. GPG verification exits0, active
signing subkey0E225917414670F4442C250DFD533C07C264648F under known Google primary
EB4C1BFD4F042F6DDDCCEC917721F63BD38B4796. The public key came over official HTTPS;
no local web-of-trust certification is claimed. Old expired subkeys are not the
active signer; active signing subkey valid through epoch1830876781.

VERIFIED extracted with dpkg-deb -x only: no package installation, maintainer scripts,
cron/service changes or global configuration. ELF x86-64 matches host; ldd inside
current isolation exits0 with no missing dependencies. Package resource bytes were
compared to the verified archive. Binary SHA:
cce8581219e59c17bcc60bff0cdfdcb2405a6d63acb1f3c32670a40814ba558c.
Pinned254-entry resource tree SHA:
b8d98bc3996b64d36eb90d517797c7c2d66a05c9631e5c74bf676c5433cefec1.
Resources read-only; setuid chrome-sandbox is explicitly overmounted with/dev/null
AFTER the resource mapping. No capset allowance, syscall shim or policy exception.

FAILED normal multiprocess launch, as expected for the capability-drop conflict.
VERIFIED single-process/no-zygote/no-proxy-server launch creates a real page and
runs original UI assertions. All outer user/mount/net/PID/IPC/UTS namespaces,
nonroot65534, cap-dropALL, no_new_privs, seccomp and privileged-helper masking remain.
Baseline already used --no-sandbox; no additional browser security layer was removed.

## Original evaluator integration and results

Only trusted launch options/resource mapping changed. Original acceptance.py and
acceptance.mjs are byte-exact, with selectors/thresholds/scenarios unchanged. Hidden
browser assertion bytes arrive via anonymous stdin, are SHA-checked, consumed and
stdin replaced by/dev/null BEFORE Chrome starts. The bytes execute as an in-memory
ES module, not a file mounted for the browser or code in process arguments. The
browser namespace has no/checks or host/workspace; app never receives hidden tests.
The existing fixed lifecycle adapter gained only a browser operation, no new
orchestration system, model gateway or budget component.

VERIFIED both original runs pass: creation_retrieval, editing,
completion_reopening, deletion_persistence, sqlite_restart, offline_operation,
browser_functionality, invalid_input, local_automated_tests,
prohibited_features_services. Actual browser checks create/date, inline title/date
edit, completion/reopening, reload persistence, deletion and literal markup/no-XSS
using exact original data-testid selectors; external request list is empty. Original
restart and invalid-input categories separately verify persistence/errors. Real local
assertion tests run three times with stable positive count. No mocked browser pass.

VERIFIED browser-specific negatives: actual page/web context cannot access Node
process, protected file or hidden file; outside network request aborted; namespace
cannot see host workspace/hidden tests/provider variables; direct kernel egress denied.
Same-filter child verifies capset/unshare still EPERM. Four actual browser processes
show no_new_privs, zero capabilities and seccomp mode2. Cleanup closes browser/proxy;
final fresh-clone and final security receipt are recorded at completion.

Private raw evidence: /workspace/final-browser-probe/, /workspace/final-browser-original-A/,
/workspace/final-browser-original-A-repeat/. Public reports contain hashes/status,
not raw private evidence or hidden assertion contents. Binary/provenance metadata
remains /workspace/trusted-browser-dependencies/google-official/.
