"""FNXC:NativeIsolation 2026-11-09-04:44:
Offline reference boundary only: untrusted commands get a network-less/PID/user
namespace, an allowlisted filesystem and one inference-only Unix socket. No
provider transport/credential loader or admin interface is exposed. The host,
privileged attackers and kernel escapes are outside the threat model.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import select
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler


def namespace_command(socket_path, workspace, arguments, *, seccomp_fd, command_override=None, readonly_mounts=()):
    command=['bwrap','--unshare-user','--unshare-net','--unshare-pid','--unshare-ipc','--unshare-uts',
             '--die-with-parent','--new-session','--uid','65534','--gid','65534','--cap-drop','ALL','--clearenv']
    for directory in ('/usr','/lib','/lib64','/bin'):
        if Path(directory).exists():command += ['--ro-bind',directory,directory]
    # Only public interpreter installations, never /opt or the host home wholesale.
    for executable in (sys.executable,shutil.which('node')):
        if executable:
            runtime=Path(executable).resolve().parent.parent
            if not str(runtime).startswith('/usr'):
                command += ['--ro-bind',str(runtime),str(runtime)]
    from security_filter import privileged_binaries
    for path in privileged_binaries():command += ['--ro-bind','/dev/null',path]
    command += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/run','--dir','/home',
                '--tmpfs','/home/sandbox',
                '--bind',str(workspace),'/work','--dir','/eval',
                '--ro-bind',str(Path(__file__).resolve()),'/eval/isolation.py',
                '--setenv','HOME','/home/sandbox','--setenv','PATH',os.environ['PATH'],
                '--setenv','PYTHONDONTWRITEBYTECODE','1','--chdir','/work',
                ]
    if socket_path is not None:command += ['--ro-bind',str(socket_path),'/run/gateway.sock']
    for source,target in readonly_mounts:command += ['--ro-bind',str(source),str(target)]
    command += ['--remount-ro','/','--seccomp',str(seccomp_fd),'--',*(command_override or [sys.executable,'-B','/eval/isolation.py',*arguments])]
    return command


class Bridge(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True


class Relay(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            with socket.socket(socket.AF_UNIX) as upstream:
                upstream.connect('/run/gateway.sock')
                pair=(self.request,upstream)
                while True:
                    ready,_,_=select.select(pair,[],[],3)
                    if not ready:return
                    for source in ready:
                        data=source.recv(65536)
                        if not data:return
                        (upstream if source is self.request else self.request).sendall(data)
        except OSError:return


class UnixServer(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):
    daemon_threads=True


def inference_socket(path, gateway, token, *, normalize_request=None):
    """Trusted, run-bound HTTP adapter; no admin paths and no transport retry."""
    lock=threading.Lock()
    events=[]
    revoked=threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_args):pass
        def do_POST(self):
            status=403;response=b'{"error":"denied"}';content_type='application/json'
            try:
                if self.path!='/v1/chat/completions':raise ValueError('endpoint')
                if self.headers.get('Host','').lower() not in ('127.0.0.1:39777','localhost:39777','local'):raise ValueError('host')
                auth=self.headers.get('Authorization','')
                if revoked.is_set() or not hmac.compare_digest(auth,'Bearer '+token):raise ValueError('client')
                if self.headers.get('Transfer-Encoding'):raise ValueError('encoding')
                lengths=self.headers.get_all('Content-Length',[])
                if len(lengths)!=1 or not lengths[0].isdigit() or not 0<int(lengths[0])<=1000000:raise ValueError('length')
                raw=self.rfile.read(int(lengths[0]))
                if normalize_request is not None:raw=normalize_request(raw)
                body=json.loads(raw)
                cap=gateway.policy.output_ceiling or gateway.policy.output_token_bound
                requested=body.get('max_tokens',cap)
                if type(requested) is not int or requested<=0 or 'max_completion_tokens' in body:raise ValueError('limit')
                body['max_tokens']=min(requested,cap)
                with lock:events.append({'requested_max_tokens':requested,'forwarded_max_tokens':body['max_tokens']})
                status,content_type,response=gateway.handle(json.dumps(body).encode())
            except Exception:
                pass  # No exception/body/header values escape the trust boundary.
            self.send_response(status);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(response)));self.end_headers()
            try:self.wfile.write(response)
            except OSError:pass
    server=UnixServer(str(path),Handler)
    server.events=events;server.revoked=revoked
    return server


def child_probe(token, case, sink_port, context=None):
    """Deterministic clients, not a coding agent or a model-backed interview."""
    import http.client
    bridge=Bridge(('127.0.0.1',39777),Relay)
    threading.Thread(target=bridge.serve_forever,daemon=True).start()
    body=json.dumps({'model':'offline-model','messages':[{'role':'user','content':'OFFLINE TEST DOUBLE'}],'max_tokens':1000})
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
    def positive(client):
        url='http://127.0.0.1:39777/v1/chat/completions'
        if client=='curl':
            r=subprocess.run(['curl','-sS','--max-time','3','--noproxy','*','-X','POST',url,'-H','Authorization: Bearer '+token,'-H','Content-Type: application/json','--data',body],capture_output=True)
            return r.returncode==0 and b'OFFLINE TEST DOUBLE' in r.stdout
        if client=='node':
            script="const h=require('http');let r=h.request(process.argv[1],{method:'POST',headers:JSON.parse(process.argv[2])},s=>{let b='';s.on('data',x=>b+=x);s.on('end',()=>process.exit(s.statusCode===200&&b.includes('OFFLINE TEST DOUBLE')?0:1))});r.on('error',()=>process.exit(2));r.end(process.argv[3])"
            return subprocess.run([shutil.which('node'),'-e',script,url,json.dumps(headers),body],capture_output=True,timeout=5).returncode==0
        c=http.client.HTTPConnection('127.0.0.1',39777,timeout=3)
        c.request('POST','/v1/chat/completions',body,headers);r=c.getresponse();data=r.read();c.close()
        return r.status==200 and b'OFFLINE TEST DOUBLE' in data
    result={'case':case,'no_new_privs':next(x.split(':')[1].strip() for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('NoNewPrivs:')),'namespace_uid':os.getuid(),'uid_map':Path('/proc/self/uid_map').read_text().strip(),'mechanism':'user+net+pid+mount namespace; Unix gateway socket only'}
    client='curl' if case=='proxy' else case if case in ('curl','node') else 'python'
    result['positive_control']=positive(client)
    try:
        if case in ('unshare','setns','mount','ptrace','runtime-socket','setuid','clone-ns','vsock','other-unix','abstract-unix'):
            import ctypes
            libc=ctypes.CDLL(None,use_errno=True)
            if case=='unshare':rc=libc.unshare(0x10000000)
            elif case=='mount':rc=libc.mount(b'none',b'/tmp',b'tmpfs',0,None)
            elif case=='ptrace':rc=libc.ptrace(0,0,None,None)
            elif case=='setns':
                fd=os.open('/proc/1/ns/net',os.O_RDONLY)
                try:rc=libc.setns(fd,0)
                finally:os.close(fd)
            elif case=='clone-ns':
                seccomp=ctypes.CDLL('libseccomp.so.2');nr=seccomp.seccomp_syscall_resolve_name(b'clone')
                rc=libc.syscall(nr,0x10000000|17,0,0,0,0)
                if rc==0:os._exit(99)
                if rc>0:os.waitpid(rc,0)
            elif case=='vsock':rc=libc.socket(40,1,0)
            elif case in ('other-unix','abstract-unix'):
                address=context['unix'] if case=='other-unix' else '\0'+context['abstract']
                with socket.socket(socket.AF_UNIX) as s:s.connect(address)
                rc=0
            elif case=='runtime-socket':
                with socket.socket(socket.AF_UNIX) as s:s.connect('/run/docker.sock')
                rc=0
            else:
                rc=subprocess.run(['/usr/bin/su','-c','id'],capture_output=True).returncode
                result['blocked']=rc!=0
            if case not in ('runtime-socket','setuid','other-unix','abstract-unix'):
                result['denial_errno']=ctypes.get_errno();result['blocked']=rc==-1 and ctypes.get_errno()==1
        elif case=='raw':
            with socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP):pass
            result['blocked']=False
        elif case in ('python','metadata','loopback'):
            address='169.254.169.254' if case=='metadata' else '127.0.0.1'
            with socket.socket() as s:s.settimeout(.3);s.connect((address,sink_port))
            result['blocked']=False
        elif case=='ipv6':
            with socket.socket(socket.AF_INET6) as s:s.settimeout(.3);s.connect(('::1',sink_port))
            result['blocked']=False
        elif case=='dns':
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
                s.settimeout(.3);s.connect(('192.0.2.53',53));s.send(b'OFFLINE DNS PROBE');s.recv(100)
            result['blocked']=False
        elif case=='curl':
            r=subprocess.run(['curl','-sS','--max-time','1','--noproxy','*',f'http://127.0.0.1:{sink_port}/'],capture_output=True)
            result['blocked']=r.returncode!=0
        elif case=='node':
            script="let s=require('net').connect(+process.argv[1],'127.0.0.1');s.on('connect',()=>process.exit(1));s.on('error',()=>process.exit(0));setTimeout(()=>process.exit(0),600)"
            result['blocked']=subprocess.run([shutil.which('node'),'-e',script,str(sink_port)],capture_output=True,timeout=2).returncode==0
        elif case=='filesystem':
            attempts={}
            for path in ('/trusted/ledger.db','/trusted/policy.json','/eval/isolation.py'):
                try:
                    with open(path,'wb') as f:f.write(b'probe')
                    attempts[path]=False
                except OSError:attempts[path]=True
            result['blocked']=all(attempts.values());result['write_denials']=attempts
        elif case=='credentials':
            hashes=[]
            for p in Path('/proc').glob('[0-9]*/environ'):
                try:
                    for field in p.read_bytes().split(b'\0'):
                        if b'=' in field:hashes.append(hashlib.sha256(field.split(b'=',1)[1]).hexdigest())
                except OSError:pass
            import stat
            for process in Path('/proc').glob('[0-9]*'):
                try:hashes.extend(hashlib.sha256(x).hexdigest() for x in (process/'cmdline').read_bytes().split(b'\0') if x)
                except OSError:pass
            for fd in Path('/proc/self/fd').iterdir():
                try:
                    if stat.S_ISREG(fd.stat().st_mode):hashes.append(hashlib.sha256(fd.read_bytes()[:65536]).hexdigest())
                except OSError:pass
            for directory in ('/home','/work','/eval','/tmp'):
                for file in Path(directory).rglob('*'):
                    try:
                        if file.is_file() and not file.is_symlink():hashes.append(hashlib.sha256(file.read_bytes()[:65536]).hexdigest())
                    except OSError:pass
            result['environment_value_hashes']=hashes
            result['host_paths_hidden']=not Path('/trusted').exists() and not Path('/home/agent/.netrc').exists()
            result['blocked']=result['host_paths_hidden']
        elif case=='proxy':
            env=dict(os.environ,http_proxy=f'http://127.0.0.1:{sink_port}',https_proxy=f'http://127.0.0.1:{sink_port}',ALL_PROXY=f'http://127.0.0.1:{sink_port}')
            result['blocked']=subprocess.run(['curl','-sS','--max-time','1','http://192.0.2.1/'],env=env,capture_output=True).returncode!=0
        elif case in ('revocation','gateway-down'):
            import time
            Path('/work/control-ready').touch()
            deadline=time.monotonic()+8
            while not Path('/work/control-done').exists() and time.monotonic()<deadline:time.sleep(.02)
            if not Path('/work/control-done').exists():raise RuntimeError('control_timeout')
            try:refused=not positive('python')
            except (OSError,http.client.HTTPException):refused=True
            result['gateway_refused']=refused
            try:
                with socket.create_connection(('127.0.0.1',sink_port),timeout=.3):direct=False
            except OSError:direct=True
            result['blocked']=refused and direct
        elif case in ('per-run-cap','aggregate-cap','request-cap','bad-client','endpoint','model','host'):
            if case=='request-cap':
                result['first_four_succeeded']=all(positive('python') for _ in range(3))
                if not result['first_four_succeeded']:raise RuntimeError('premature_cap')
            c=http.client.HTTPConnection('127.0.0.1',39777,timeout=3)
            changed=dict(headers)
            if case=='bad-client':changed['Authorization']='Bearer invalid-client'
            if case=='host':changed['Host']='unapproved.invalid'
            request_body=json.loads(body)
            if case=='model':request_body['model']='unapproved-model'
            c.request('POST','/admin' if case=='endpoint' else '/v1/chat/completions',json.dumps(request_body),changed)
            response=c.getresponse();response.read();c.close()
            result['rejection_status']=response.status
            result['blocked']=response.status==403
    except OSError:result['blocked']=True
    finally:bridge.shutdown();bridge.server_close()
    print(json.dumps(result))


if __name__=='__main__':
    child_probe(sys.argv[1],sys.argv[2],int(sys.argv[3]),json.loads(sys.argv[4]) if len(sys.argv)>4 else {})


def exercise(output):
    """OS-level security probe routed from the existing offline runner."""
    import tempfile
    import secrets
    import http.client
    import time
    from dataclasses import asdict
    from http.server import ThreadingHTTPServer
    from gateway import Gateway, Artifacts, Policy, canonical
    from budget import AggregateBudget, guard_gateway
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    counts={'stub_contacts':0,'untrusted_stub_contacts':0,'real_host_contacts':0}
    canary=os.environ.get('CANARY_GATEWAY_CREDENTIAL') or secrets.token_hex(32)  # Local fixture only.
    canary_hash=hashlib.sha256(canary.encode()).hexdigest()
    initial_canary_present=('CANARY_GATEWAY_CREDENTIAL='+canary).encode() in Path('/proc/self/environ').read_bytes()
    if not initial_canary_present:raise RuntimeError('gateway_initial_canary_required')
    previous_canary=os.environ.get('CANARY_GATEWAY_CREDENTIAL')
    os.environ['CANARY_GATEWAY_CREDENTIAL']=canary
    class Stub(BaseHTTPRequestHandler):
        def log_message(self,*_args):pass
        def do_POST(self):
            counts['stub_contacts']+=1
            authorized=hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+canary)
            if not authorized:counts['untrusted_stub_contacts']+=1
            self.rfile.read(int(self.headers.get('Content-Length','0')))
            data=canonical({'model':'offline-model','choices':[{'message':{'role':'assistant','content':'OFFLINE TEST DOUBLE'},'finish_reason':'stop'}],'usage':{'prompt_tokens':5,'completion_tokens':5}})
            self.send_response(200 if authorized else 403);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    upstream=ThreadingHTTPServer(('127.0.0.1',0),Stub)
    threading.Thread(target=upstream.serve_forever,daemon=True).start()
    results=[]
    try:
        with tempfile.TemporaryDirectory(prefix='fusion-security-') as temporary:
            private=Path(temporary);(private/'decoy-credential').write_text(canary)
            sockets=[]
            for address in (str(private/'outside.sock'),'\0fusion-offline-'+secrets.token_hex(8)):
                listener=socket.socket(socket.AF_UNIX);listener.bind(address);listener.listen(20)
                with socket.socket(socket.AF_UNIX) as positive:positive.connect(address)
                sockets.append(listener)
            context={'unix':str(private/'outside.sock'),'abstract':sockets[1].getsockname()[1:].decode() if isinstance(sockets[1].getsockname(),bytes) else sockets[1].getsockname()[1:]}
            ledger=AggregateBudget(private/'ledger.db')
            for number,case in enumerate(('python','node','curl','raw','dns','ipv6','metadata','loopback','proxy','filesystem','credentials','per-run-cap','aggregate-cap','request-cap','bad-client','endpoint','model','host','revocation','gateway-down','unshare','setns','mount','ptrace','runtime-socket','setuid','clone-ns','vsock','other-unix','abstract-unix')):
                run=private/f'run-{number}';run.mkdir();(run/'.offline-test').touch()
                workspace=private/f'workspace-{number}';workspace.mkdir()
                input_bound=80000 if case=='per-run-cap' else 40000 if case=='aggregate-cap' else 100
                # Global exhaustion runs in an isolated ledger so later controls remain meaningful.
                case_ledger=AggregateBudget(private/f'cap-{number}.db') if case in ('per-run-cap','aggregate-cap') else ledger
                if case=='aggregate-cap':case_ledger.reserve('planning','fixture-seed',1950000)
                policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',('offline.invalid',),4,150000,1000000,1000000,input_bound,100,100)
                artifacts=Artifacts(run,offline=True,secrets=(canary,))
                artifacts.write('policy.json',canonical(asdict(policy)))
                def transport(url,raw):
                    if url!=policy.upstream_url:raise ValueError('destination')
                    connection=http.client.HTTPConnection('127.0.0.1',upstream.server_port,timeout=3)
                    try:
                        connection.request('POST','/v1/chat/completions',raw,{'Authorization':'Bearer '+canary,'Content-Type':'application/json'})
                        response=connection.getresponse();return response.status,'application/json',response.read()
                    finally:connection.close()
                gateway=guard_gateway(Gateway(policy,artifacts,transport),case_ledger,'coding',f'probe-{number}')
                token=secrets.token_hex(24)
                server=inference_socket(private/f'gateway-{number}.sock',gateway,token)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                control_thread=None
                if case in ('revocation','gateway-down'):
                    def control():
                        deadline=time.monotonic()+10
                        while not (workspace/'control-ready').exists() and time.monotonic()<deadline:time.sleep(.02)
                        if not (workspace/'control-ready').exists():return
                        if case=='revocation':server.revoked.set()
                        else:server.shutdown();server.server_close()
                        (workspace/'control-done').touch()
                    control_thread=threading.Thread(target=control,daemon=True);control_thread.start()
                try:
                    from security_filter import export_filter
                    filter_file=tempfile.TemporaryFile()
                    export_filter(filter_file)
                    command=namespace_command(private/f'gateway-{number}.sock',workspace,[token,case,str(upstream.server_port),json.dumps(context)],seccomp_fd=filter_file.fileno())
                    # Only scrubbed env inherited; no real credential values are read.
                    env={'PATH':os.environ['PATH'],'HOME':str(private)}
                    assert os.environ['CANARY_GATEWAY_CREDENTIAL']==canary
                    with (private/'decoy-credential').open('rb') as secret_fd:
                        assert secret_fd.read()==canary.encode()
                        os.set_inheritable(secret_fd.fileno(),True)
                        child=subprocess.run(command,env=env,capture_output=True,text=True,timeout=20,close_fds=True,pass_fds=(filter_file.fileno(),))
                    filter_file.close()
                    if child.returncode:
                        # Persist error diagnostics only after checking the canary.
                        if canary in child.stderr:raise RuntimeError('canary_in_diagnostic')
                        (output/f'error-{case}.txt').write_text(child.stderr)
                        raise RuntimeError('namespace_probe_failed:'+case)
                    result=json.loads(child.stdout)
                    hashes=result.pop('environment_value_hashes',[])
                    if case=='credentials':result['canary_absent_from_observed_environments']=canary_hash not in hashes
                    result['expected_output_limit']=100
                    result['clamp_verified']=server.events[-1]=={'requested_max_tokens':1000,'forwarded_max_tokens':100}
                    result['stub_only']=counts['untrusted_stub_contacts']==0 and counts['real_host_contacts']==0
                    if not result.get('positive_control') or not result.get('blocked') or not result['clamp_verified'] or not result['stub_only'] or result.get('canary_absent_from_observed_environments') is False:
                        raise RuntimeError('security_assertion_failed:'+case)
                    if result['no_new_privs']!='1':raise RuntimeError('no_new_privs_missing')
                    if result['namespace_uid']!=65534:raise RuntimeError('namespace_uid_mismatch')
                    (output/f'ledger-{case}.json').write_text(json.dumps(case_ledger.snapshot(),indent=2)+'\n')
                    preserved=output/'gateway-artifacts'/case;preserved.mkdir(parents=True)
                    for artifact in run.iterdir():
                        if artifact.is_file() and not artifact.name.startswith('.'):
                            raw=artifact.read_bytes()
                            if canary.encode() in raw:raise RuntimeError('canary_in_artifact')
                            (preserved/artifact.name).write_bytes(raw)
                    results.append(result)
                finally:
                    server.shutdown();server.server_close();thread.join(timeout=3)
                    if control_thread:control_thread.join(timeout=2)
            for listener in sockets:listener.close()
            snapshot=ledger.snapshot()
            (output/'ledger.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    finally:
        upstream.shutdown();upstream.server_close()
        if previous_canary is None:os.environ.pop('CANARY_GATEWAY_CREDENTIAL',None)
        else:os.environ['CANARY_GATEWAY_CREDENTIAL']=previous_canary
    summary={'isolation_tier':'ENFORCED','classification':'SYNTHETIC_OFFLINE_TEST_DOUBLE_NOT_A_PLAN_OR_CODING_RESULT','results':results,'counts':counts,'gateway_initial_canary_verified':initial_canary_present,'inheritable_canary_fd_positive_control':True,
             'scope':'deterministic clients in reference namespace; privileged host/kernel attacks excluded',
             'limitations':['Not integrated with a live coding runner','Raw ICMP/DNS/IPv6/metadata share a Python HTTP gateway positive control, not a protocol-identical positive control','Namespace gateway shutdown and token revocation tested; mid-request kill recovery tested independently; combined restart/resume protocol not yet exercised']}
    raw=json.dumps(summary,indent=2)+'\n'
    if canary in raw:raise RuntimeError('canary_in_artifact')
    (output/'summary.json').write_text(raw)
    return summary
