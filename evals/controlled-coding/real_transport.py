"""FNXC:OfflineFinal 2026-11-09-05:40:
Disabled-by-default HTTPS transport. Live requires explicit flag plus an exact
host/model/contract authorization; test-only loopback TLS overrides cannot enter
live mode. A scrubbed, owned worker enforces a hard whole-request timeout and
PDEATHSIG. No provider hosts are contacted by offline tests.
"""
import base64
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import ssl
import stat
import subprocess
import sys
import time
import threading
from urllib.parse import urlsplit
from urllib.request import build_opener,ProxyHandler,HTTPSHandler
from contract import Contract,micro


# FNXC:LiveCoding 2026-11-10-06:40: This Python omits Linux fcntl names;
# use the published ABI numbers, without adding syscalls or bypassing any filter.
ADD_SEALS=getattr(fcntl,'F_ADD_SEALS',1033);GET_SEALS=getattr(fcntl,'F_GET_SEALS',1034)
SEAL_REQUIRED=0x01|0x02|0x04|0x08

def sealed_credential(key):
    # FNXC:LiveCoding 2026-11-10-06:16: No persistent provider-key file; only the
    # gateway and explicitly inherited transport worker can reach this sealed FD.
    fd=os.memfd_create('fusion-gateway-credential',os.MFD_ALLOW_SEALING|os.MFD_CLOEXEC)
    try:
        os.fchmod(fd,0o600);os.write(fd,key.encode());fcntl.fcntl(fd,ADD_SEALS,SEAL_REQUIRED);return fd
    except BaseException:os.close(fd);raise

def validate_credential_fd(config):
    fd=config.get('credential_fd')
    if type(fd) is not int or fd<3:raise ValueError('gateway_credential_descriptor')
    required=SEAL_REQUIRED
    if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_mode&0o077 or fcntl.fcntl(fd,GET_SEALS)&required!=required:raise ValueError('sealed_gateway_credential_required')
    return fd

def validate(config):
    c=Contract(config.get('contract_path',Path(__file__).with_name('experiment-parameters.json')))
    if config.get('live') and config.get('test_mode'):raise ValueError('test_override_unavailable_live')
    if 'credential_fd' in config:validate_credential_fd(config)
    if config.get('test_mode'):
        marker=Path(config['test_root'])/'.offline-test'
        if not marker.is_file():raise ValueError('test_marker_required')
        url=config['test_url'];u=urlsplit(url)
        if u.scheme!='https' or u.hostname not in ('localhost','127.0.0.1') or u.path!='/v1/chat/completions' or u.username or u.query or u.fragment:raise ValueError('test_host_must_be_loopback')
        for name in ('test_ca','test_key_file'):
            if not Path(config[name]).resolve().is_relative_to(Path(config['test_root']).resolve()):raise ValueError('test_material_outside_root')
        return c,url
    if not config.get('live'):raise ValueError('real_transport_disabled')
    a_path=Path(config['authorization_file'])
    if a_path.is_symlink() or a_path.stat().st_mode & 0o077:raise ValueError('authorization_permissions')
    a=json.loads(a_path.read_text())
    if a.get('test_double') or a.get('live_authorized') is not True or a.get('model')!=c.data['model'] or a.get('contract_sha256')!=c.sha256:raise ValueError('authorization_mismatch')
    if a.get('approved_hosts')!=['api.openai.com'] or a.get('expires_at',0)<=time.time():raise ValueError('exact_host_authorization_required')
    errors=[e for e in c.arming_errors() if e!='NO_PAID_AUTHORIZATION']
    if a.get('model_availability_verified') and a.get('model_availability_evidence'):errors=[e for e in errors if e!='MODEL_AVAILABILITY_UNVERIFIED']
    if errors:raise ValueError(','.join(errors))
    # FNXC:Activation 2026-11-10-22:01: No provider hard-cap attestation; retain
    # exact signed risk acknowledgment propagated by the trusted supervisor.
    from operator_auth import require_risk_ack
    require_risk_ack(a)
    if not 0<a.get('authorized_spend_usd',0)<=2:raise ValueError('local_authorized_spend_required')
    if 'credential_fd' in config:
        if a.get('credential_fd')!=config['credential_fd']:raise ValueError('credential_descriptor_authorization_mismatch')
        return c,'https://api.openai.com/v1/chat/completions'
    key=Path(a['key_file'])
    if key.is_symlink() or not key.is_file() or key.stat().st_mode & 0o077:raise ValueError('gateway_key_permissions')
    return c,'https://api.openai.com/v1/chat/completions'


class RealTransport:
    def __init__(self, *, live=False, authorization_file=None, contract_path=None, test_mode=False, test_root=None, test_url=None, test_ca=None, test_key_file=None, timeout=60, credential_fd=None):
        self.config={k:str(v) if isinstance(v,Path) else v for k,v in locals().copy().items() if k not in ('self',) and v is not None}
        self.contract,self.url=validate(self.config)
        self.timeout=min(timeout,self.contract.data['request_seconds']);self.active=set();self._workers=threading.Lock();self._aborted=False

    def __call__(self, _ignored_policy_url, raw):
        validate(self.config)
        if _ignored_policy_url not in (self.url,'https://api.openai.com/v1/chat/completions'):raise ValueError('destination_mismatch')
        normalized,_=self.contract.prepare(raw)
        if normalized!=raw:raise ValueError('unprepared_request')
        env={'PATH':os.environ.get('PATH',os.defpath),'PYTHONDONTWRITEBYTECODE':'1'}
        for name in ('HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR'):
            if name in os.environ:env[name]=os.environ[name]
        request={'config':self.config,'raw':base64.b64encode(raw).decode(),'parent_pid':os.getpid()}
        with self._workers:
            if self._aborted:raise OSError('transport_revoked')
            child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,pass_fds=(self.config['credential_fd'],) if 'credential_fd' in self.config else ())
            self.active.add(child)
        try:
            output,_=child.communicate(json.dumps(request).encode(),timeout=self.timeout)
            if child.returncode:raise OSError('transport_worker_failed')
            result=json.loads(output)
            if 'error' in result:raise OSError('transport_failed')
            return result['status'],result['content_type'],base64.b64decode(result['body'])
        except subprocess.TimeoutExpired:
            child.kill();child.communicate();raise OSError('whole_request_deadline') from None
        finally:
            with self._workers:self.active.discard(child)

    def abort(self):
        with self._workers:
            self._aborted=True
            for child in list(self.active):
                if child.poll() is None:child.kill()


def worker():
    try:
        request=json.loads(sys.stdin.buffer.read(2000000));config=request['config']
        if ctypes.CDLL(None).prctl(1,signal.SIGKILL)!=0 or os.getppid()!=request['parent_pid']:raise ValueError('parent_gone')
        c,url=validate(config)
        raw=base64.b64decode(request['raw'])
        normalized,_=c.prepare(raw)
        if normalized!=raw:raise ValueError('unprepared_request')
        if 'credential_fd' in config:key=os.pread(validate_credential_fd(config),65536,0).decode().strip()
        if config.get('test_mode'):
            key=key if 'credential_fd' in config else Path(config['test_key_file']).read_text().strip()
            context=ssl.create_default_context(cafile=config['test_ca'])
            opener=build_opener(ProxyHandler({}),HTTPSHandler(context=context))
        else:
            approval=json.loads(Path(config['authorization_file']).read_text());key=key if 'credential_fd' in config else Path(approval['key_file']).read_text().strip();opener=None
        # FNXC:OfflineFinal 2026-11-09-05:40: Reuse the existing destination,
        # redirect and response-size boundary; external worker supplies deadline.
        sys.path.insert(0,str(Path(__file__).parent.parent/'planning-collector'))
        from gateway import Policy,HTTPSForwarder
        policy=Policy('OpenAI',c.data['model'],url,(urlsplit(url).hostname,),4,micro(c.data['per_run_coding_cap_usd']),400000,1600000,32000,4096,4096)
        if opener is not None:
            from urllib.request import HTTPRedirectHandler
            class NoRedirect(HTTPRedirectHandler):
                def redirect_request(self,*_args,**_kwargs):raise ValueError('redirect_forbidden')
            opener.add_handler(NoRedirect())
        if key and key.encode() in raw:raise ValueError('credential_in_request')
        status,content_type,body=HTTPSForwarder(policy,'Bearer '+key,opener=opener)(url,raw)
        if key and key.encode() in body:raise ValueError('credential_reflected')
        print(json.dumps({'status':status,'content_type':content_type,'body':base64.b64encode(body).decode()}))
    except Exception:print(json.dumps({'error':'transport_failure'}))


if __name__=='__main__':
    if sys.argv[1:]!=['--worker']:raise SystemExit('transport_disabled_without_gateway')
    worker()
