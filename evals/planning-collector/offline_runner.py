"""Disposable namespace supervisor: real Fusion -> gateway -> local mock HTTP.

FNXC:PlanningEvaluation 2026-11-04-10:05:
FNXC:Persistence 2026-11-09-04:02:
Resolve source from this checkout and require an explicit persistent rate ledger
so recovered clones never depend on an older worktree or reset start accounting.
No paid transport or credentials. Mount a fresh home and temp tree, leave source
read-only, and remove non-loopback networking in a child namespace only.
"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gateway import Artifacts, Gateway, Policy, canonical, offline_server
from snapshots import database_diff, filesystem_diff, process_diff
from rate_limit import reserve_start

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1]
ROOT = Path('/run/fusion-eval')


def tree(root):
    result = {}
    for p in sorted(Path(root).rglob('*')):
        key = str(p.relative_to(root))
        if p.is_symlink():
            result[key] = {'symlink': os.readlink(p)}
        elif p.is_dir():
            result[key] = {'directory': True, 'mode': p.stat().st_mode & 0o777}
        elif p.is_file():
            h = hashlib.sha256()
            with p.open('rb') as f:
                while chunk := f.read(1 << 20): h.update(chunk)
            result[key] = {'sha256': h.hexdigest(), 'bytes': p.stat().st_size, 'mode': p.stat().st_mode & 0o777}
    return result


def save(name, value):
    with (ROOT / 'results' / name).open('x') as f:
        json.dump(value, f, indent=2)


def wait_for(marker, child, seconds=120):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if (ROOT / marker).exists(): return
        if child.poll() is not None: raise RuntimeError('native_child_exited_before_' + marker)
        time.sleep(.05)
    raise RuntimeError('native_child_timeout_' + marker)


def inside(scenario):
    if os.environ.get('FUSION_OFFLINE_NAMESPACE') != '1' or not (ROOT / '.offline-test').exists():
        raise RuntimeError('namespace_marker_missing')
    # The namespace has no external route; all requests below are loopback.
    save('network-namespace.json', {'route_table': Path('/proc/net/route').read_text(),
                                  'netns': os.readlink('/proc/self/ns/net')})
    save('source-provenance.json', {
        'source_commit': subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'], text=True).strip(),
        'collector_commit': subprocess.check_output(['git','-C',str(HERE),'rev-parse','HEAD'], text=True).strip(),
        'runner_sha256': hashlib.sha256((HERE/'native-runner.mts').read_bytes()).hexdigest(),
        'gateway_sha256': hashlib.sha256((HERE/'gateway.py').read_bytes()).hexdigest(),
        'classification': 'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS',
    })
    capability = secrets.token_hex(24)  # ephemeral LOCAL test-server capability, never a real credential
    mock_requests = []
    denied = []
    class Mock(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            if self.headers.get('X-Offline-Gateway') != capability:
                denied.append('direct_mock_bypass')
                self.send_response(403); self.end_headers(); return
            body = json.loads(raw)
            mock_requests.append(body)
            n = len(mock_requests)
            if scenario in ('upstream-retry', 'comprehensive') and n == 1:
                self.send_response(503); self.send_header('Content-Length', '0'); self.end_headers(); return
            compaction = any('summar' in str(m.get('content', '')).lower() and m.get('role') == 'system' for m in body['messages'])
            storage_answered = any('PostgreSQL' in str(m.get('content', '')) and m.get('role') == 'user' and 'Answer:' in str(m.get('content', '')) for m in body['messages'])
            unknown_answered = any('No preference; use your judgment.' in str(m.get('content', '')) for m in body['messages'])
            content = ('OFFLINE COMPACTION SUMMARY ONLY' if compaction else
                       'not JSON' if (scenario == 'format-retry' and n == 1) or (scenario == 'comprehensive' and n == 2) else
                       json.dumps({'type': 'question', 'data': {'id': 'quality', 'type': 'text', 'question': 'What color theme is required?', 'description': 'offline context fixture ' * 2500}})
                       if scenario == 'comprehensive' and storage_answered and not unknown_answered else
                       json.dumps({'type': 'question', 'data': {'id': 'storage', 'type': 'text', 'question': 'Which storage system?', 'description': 'offline context fixture ' * (2500 if scenario == 'comprehensive' else 0)}})
                       if not storage_answered else
                       json.dumps({'type': 'complete', 'data': {'missionTitle': 'OFFLINE MOCK ONLY', 'missionDescription': 'Transport test, excluded from corpus', 'milestones': [{'title': 'Mock phase', 'slices': [{'title': 'Mock slice', 'features': [{'title': 'Mock fixture', 'acceptanceCriteria': 'Offline transport checks only'}]}]}]}}))
            finish = 'length' if scenario == 'length' else 'stop'
            packet = {'id': 'offline', 'object': 'chat.completion.chunk', 'created': 0,
                      'model': 'offline-physical-model',
                      'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': content}, 'finish_reason': None}]}
            final = {'id': 'offline', 'object': 'chat.completion.chunk', 'created': 0,
                     'model': 'offline-physical-model', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}]}
            if scenario not in ('missing-usage', 'comprehensive'): final['usage'] = {'prompt_tokens': 20, 'completion_tokens': 30, 'total_tokens': 50}
            out = b'data: ' + canonical(packet) + b'\n\ndata: ' + canonical(final) + b'\n\ndata: [DONE]\n\n'
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(out))); self.end_headers()
            # Two writes verify SSE framing survives the gateway's buffering.
            self.wfile.write(out[:len(out)//2]); self.wfile.flush(); self.wfile.write(out[len(out)//2:])
    mock = ThreadingHTTPServer(('127.0.0.1', 0), Mock)
    threading.Thread(target=mock.serve_forever, daemon=True).start()
    artifacts_dir = Path('/tmp/gateway-artifacts'); artifacts_dir.mkdir()
    (artifacts_dir / '.offline-test').touch()
    p = Policy.from_config(dict(provider='offline-evaluation', model='offline-physical-model',
       upstream_url='https://offline.invalid/v1/chat/completions', approved_hosts=['offline.invalid'],
       api_type='openai-chat-completions', physical_model_verified=True,
       token_bound_evidence_sha256='0'*64, max_model_calls=8, spend_ceiling_usd='100',
       input_price_per_million='0.001', output_price_per_million='0.001', input_token_bound=128000,
       output_token_bound=32768, output_ceiling=None))
    from dataclasses import asdict
    save('gateway-policy.json',asdict(p))
    def transport(url, raw):
        if url != p.upstream_url: raise RuntimeError('unexpected_destination')
        c = http.client.HTTPConnection(*mock.server_address, timeout=10)
        try:
            c.request('POST', '/v1/chat/completions', raw, {'Content-Type': 'application/json', 'X-Offline-Gateway': capability})
            r = c.getresponse(); return r.status, r.getheader('Content-Type', 'application/json'), r.read(8_000_001)
        finally: c.close()
    sys.path.insert(0,str(HERE.parent/'controlled-coding'))
    from budget import AggregateBudget, guard_gateway
    shared_ledger=AggregateBudget(ROOT/'results'/'shared-budget.db')
    gateway = guard_gateway(Gateway(p, Artifacts(artifacts_dir, offline=True), transport),
                            shared_ledger,'planning','native-offline-'+scenario)
    proxy = offline_server(gateway, gateway.artifacts)
    threading.Thread(target=proxy.serve_forever, daemon=True).start()
    # Negative control: direct access to mock never generates a response fixture.
    c = http.client.HTTPConnection(*mock.server_address, timeout=2)
    c.request('POST', '/v1/chat/completions', b'{}'); r = c.getresponse(); bypass_status = r.status; r.read(); c.close()
    try:
        c = http.client.HTTPConnection('203.0.113.1', 9, timeout=.25)
        c.request('GET', '/'); c.getresponse()
        external_blocked = False
    except OSError:
        external_blocked = True
    finally: c.close()
    save('bypass-probes.json', {'direct_mock_status': bypass_status, 'external_route_blocked': external_blocked})
    env = dict(os.environ, FUSION_SOURCE_ROOT=str(SOURCE),
               FUSION_OFFLINE_GATEWAY=f'http://127.0.0.1:{proxy.server_port}',
               FUSION_OFFLINE_SCENARIO=scenario, FUSION_OFFLINE_PROTOCOL=str(HERE/'protocol.md'),
               FUSION_OFFLINE_BRIEFS=str(HERE/'briefs.json'))
    node = shutil.which('node')
    log = (ROOT/'results'/'native.log').open('xb')
    child = subprocess.Popen([node, '--import', str(SOURCE/'node_modules/tsx/dist/loader.mjs'),
                              str(HERE/'native-runner.mts')], env=env, cwd=ROOT/'project', stdout=log, stderr=log)
    try:
        wait_for('ready', child)
        save('filesystem-before.json', tree(ROOT))
        save('processes-before.json', subprocess.check_output(['ps','-eo','pid,ppid,comm'], text=True).splitlines())
        (ROOT/'go').touch()
        wait_for('settled', child, seconds=150)
        save('filesystem-after.json', tree(ROOT))
        save('processes-after.json', subprocess.check_output(['ps','-eo','pid,ppid,comm'], text=True).splitlines())
        before = json.loads((ROOT/'results'/'database-before.json').read_text())
        after = json.loads((ROOT/'results'/'database-after.json').read_text())
        changed = {k: [v, after['counts'].get(k)] for k,v in before['counts'].items() if v != after['counts'].get(k)}
        forbidden = {k:v for k,v in changed.items() if any(x in k for x in ['mission', 'task', 'agent', 'heartbeat', 'automation', 'pull_request', 'execution']) and not k.endswith('.ai_sessions')}
        hashes = {k for k,v in before['row_hashes'].items() if v != after['row_hashes'].get(k)}
        forbidden_hashes = [k for k in hashes if any(x in k for x in ['mission', 'task', 'agent', 'heartbeat', 'automation', 'pull_request', 'execution']) and not k.endswith('.ai_sessions')]
        db_diff = database_diff(before, after)
        fs_diff = filesystem_diff(json.loads((ROOT/'results'/'filesystem-before.json').read_text()), json.loads((ROOT/'results'/'filesystem-after.json').read_text()))
        proc_diff = process_diff(json.loads((ROOT/'results'/'processes-before.json').read_text()), json.loads((ROOT/'results'/'processes-after.json').read_text()))
        save('verification.json', {'classification': 'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS', 'scenario': scenario,
             'database_diff': db_diff, 'filesystem_diff': fs_diff, 'process_diff': proc_diff,
             'database_count_changes': changed, 'database_changed_tables': sorted(hashes),
             'forbidden_count_changes': forbidden, 'forbidden_row_changes': forbidden_hashes,
             'gateway_forwarded_attempts': gateway.budget.calls, 'mock_received_requests': len(mock_requests),
             'gateway_blocked_reasons': gateway.blocked_attempts,
             'request_count_match': gateway.budget.calls == len(mock_requests),
             'output_token_limits': [{k:v for k,v in b.items() if k in ('max_tokens','max_completion_tokens')} for b in mock_requests],
             'reserved_micro_usd_estimated': gateway.budget.reserved,
             'direct_mock_bypass_blocked': bypass_status == 403, 'external_route_blocked': external_blocked,
             'native_failure': (ROOT/'results'/'native-failure.json').exists()})
        if db_diff['forbidden'] or fs_diff['unexpected'] or proc_diff['unexpected'] or not external_blocked or bypass_status != 403:
            raise RuntimeError('offline_isolation_verification_failed')
        expected_failure = scenario in ('model-mismatch', 'length')
        if (ROOT/'results'/'native-failure.json').exists() != expected_failure:
            raise RuntimeError('native_outcome_did_not_match_scenario')
    finally:
        (ROOT/'shutdown').touch()
        try: child.wait(timeout=20)
        except subprocess.TimeoutExpired: child.terminate(); child.wait(timeout=5)
        log.close()
        mock.shutdown(); mock.server_close(); proxy.shutdown(); proxy.server_close()
    save('teardown.json', {'native_exit_code': child.returncode, 'namespace_services_stopped': True})
    if child.returncode != 0: raise RuntimeError('native_child_shutdown_failed')
    # Preserve a final content manifest; mock artifacts never enter corpus paths.
    save('artifact-manifest.json', tree(ROOT/'results'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['normal','format-retry','upstream-retry','missing-usage','model-mismatch','length','comprehensive'], default='normal')
    parser.add_argument('--inside', action='store_true')
    parser.add_argument('--rate-ledger', type=Path, help='Persistent offline start ledger outside disposable namespaces')
    parser.add_argument('--native-library-dir', type=Path, help='Verified native library directory inside this checkout (offline only)')
    parser.add_argument('--max-starts', type=int, default=3, help='Operator start cap per hour, never above native five-start limit')
    parser.add_argument('--security-probe', type=Path, help='Run deterministic Unix-gateway namespace probes; no native interview start')
    parser.add_argument('--security-child',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.security_probe is not None:
        # FNXC:NativeIsolation 2026-11-09-05:12: Fixture gateway receives only a
        # generated initial canary; no provider credential variables are inherited.
        if not args.security_child:
            env={'PATH':os.environ['PATH'],'HOME':tempfile.gettempdir(),
                 'PYTHONDONTWRITEBYTECODE':'1','CANARY_GATEWAY_CREDENTIAL':secrets.token_hex(32)}
            child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--security-probe',str(args.security_probe),'--security-child'],env=env)
            raise SystemExit(child.returncode)
        if set(os.environ)-{'PATH','HOME','PYTHONDONTWRITEBYTECODE','CANARY_GATEWAY_CREDENTIAL','LC_CTYPE'}:
            raise RuntimeError('unexpected_security_gateway_environment')
        sys.path.insert(0,str(HERE.parent/'controlled-coding'))
        from isolation import exercise
        summary=exercise(args.security_probe)
        print(json.dumps({'security_probes':len(summary['results']),'real_host_contacts':summary['counts']['real_host_contacts']}))
        return
    if args.inside:
        inside(args.scenario); return
    if args.rate_ledger is None:
        parser.error('--rate-ledger required; reuse one durable ledger across offline starts')
    # FNXC:Persistence 2026-11-09-04:22: Pass only an explicitly verified local
    # dependency directory; preserve network isolation and native start limits.
    library_env = []
    if args.native_library_dir is not None:
        library_dir = args.native_library_dir.resolve()
        if not library_dir.is_dir() or not library_dir.is_relative_to(SOURCE.resolve()):
            parser.error('--native-library-dir must be a directory inside this checkout')
        library_env = ['--setenv', 'LD_LIBRARY_PATH', str(library_dir)]
    reserve_start(args.rate_ledger, max_starts=args.max_starts)
    root = Path(tempfile.mkdtemp(prefix='fusion-native-offline-'))
    for d in ('home','scratch','project','database','results'): (root/d).mkdir()
    (root/'.offline-test').touch()
    # All mounts are child-only; no global home, proxy, permissions, or network policy changes.
    command = ['bwrap','--unshare-net','--unshare-pid','--ro-bind','/','/', '--tmpfs','/run', '--bind',str(root),str(ROOT),
       '--bind',str(root/'home'),'/home/agent','--bind',str(root/'scratch'),'/tmp',
       '--proc','/proc','--dev','/dev','--clearenv',
       '--setenv','HOME','/home/agent','--setenv','PATH',os.environ['PATH'],
       '--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','FUSION_OFFLINE_NAMESPACE','1',
       '--setenv','TMPDIR','/tmp',*library_env,'--',sys.executable,str(Path(__file__).resolve()),'--inside','--scenario',args.scenario]
    result = subprocess.run(command, timeout=300)
    print(json.dumps({'classification':'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS','evidence_directory':str(root), 'exit_code':result.returncode}))
    raise SystemExit(result.returncode)


if __name__ == '__main__': main()
