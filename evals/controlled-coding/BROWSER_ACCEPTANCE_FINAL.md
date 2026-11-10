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

## Final independent repetition, regressions and cleanup

VERIFIED three fresh original-evaluator checkouts score100/100, every category
passed, with the same df383ba2... native patch and unchanged executable modes. The
terminal run includes the final no-host/no-hidden-source launch guard. No native
candidate was regenerated in this phase and no coding-model/provider call occurred.
Final browser security receipt passes ALL18 checks, including actual/dev/null masking
of the privileged helper. Four real browser processes inherit seccomp mode2,
no_new_privs and zero capabilities. Browser/proxy close in finally; evaluator service
relays stop and source hashes/modes are rechecked after grading. No syscall policy
or frozen assertion changed; normal multiprocess launch failure is preserved as an
infrastructure diagnostic, not concealed by the working configuration.

VERIFIED baseline110 local units, final114 (66+37+11), zero failures/skips locally.
Four new synthetic units exercise identity/tamper/masking/hash guards; they do NOT
mock real-browser acceptance. A new fixture initially tried to create setuid files
inside recovery isolation and correctly hit EPERM. It was corrected to use regular
synthetic files for integrity and test already-verified masking metadata separately;
real signed-helper masking is independently checked by the actual browser probe.
The outgoing checkpoint stopped before publication until that fixture issue was fixed.
The20-minute remote target was exceeded during this validation block; verified local
bundle/source/evidence were preserved and the exception recorded in CHECKPOINTS.md.

Accepted milestone dev8f737b97c... plus recovery-unit fix d78dda6b2997a344f1527dcdee368e6dc83dc3a8
maps to independently fetched remote b5335c10076a21a6f74577379e4cd7397f4f0b1d.
Terminal development/backup SHAs and fresh-clone results are resolved by the backup
SOURCE_MAP/CHECKPOINT_INDEX and final operator receipt; no self-hash is invented.
Final status BROWSER_ACCEPTANCE_VERIFIED; external private recovery still BLOCKED.
Provider spending EXACTLY$0.00. Production/native/default512/offline768/four-request/
$0.12/$2 settings remain unchanged. This is real-browser validation of a native
TEST DOUBLE implementation, not evidence of real-model coding quality or paid approval.

## Dependency recovery and executable command

Verified exact package URL:
https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_157.0.8103.50-1_amd64.deb .
Metadata: https://dl.google.com/linux/chrome/deb/dists/stable/Release plus
Release.gpg and main/binary-amd64/Packages.gz; public software key:
https://dl.google.com/linux/linux_signing_key.pub . Never skip TLS/signature/hash checks.
Protected850-file recovery package includes this exact verified.deb, metadata and
verified-runtime.json; no need to trust a mirror if the publisher rotates versions.
Re-extract only with dpkg-deb -x into a dedicated directory; preserve the same
chromium->chrome alias, remove write bits, restore the verified manifest, and call
verified_browser_runtime.verify before mounting. Privileged helper is always masked.

Run original evaluation in a NEW private directory:
`python evals/controlled-coding/original_evaluator_adapter.py --native-root /workspace/full768-native-A-current --out NEW_PRIVATE_DIR --browser-dependency /workspace/trusted-browser-dependencies/google-official` .
This requires separately restored private evaluator/native evidence, not public
source alone. Source/base114-test verification and fresh-clone recovery receipts
remain separate from real browser100/100 private results.
