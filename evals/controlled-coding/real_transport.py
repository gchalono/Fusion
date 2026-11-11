"""FNXC:OfflineFinal 2026-11-09-05:40:
Disabled-by-default HTTPS transport. Live requires explicit flag plus an exact
host/model/contract authorization; test-only loopback TLS overrides cannot enter
live mode. A scrubbed, owned worker enforces a hard whole-request timeout and
PDEATHSIG. No provider hosts are contacted by offline tests.
"""
import base64
import ctypes
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
from urllib.parse import urlsplit
from urllib.request import build_opener,ProxyHandler,HTTPSHandler
from contract import Contract,micro


def validate(config):
    c=Contract(config.get('contract_path',Path(__file__).with_name('experiment-parameters.json')))
    if config.get('live') and config.get('test_mode'):raise ValueError('test_override_unavailable_live')
    if config.get('test_mode'):
        marker=Path(config['test_root'])/'.offline-test'
        if not marker.is_file():raise ValueError('test_marker_required')
        url=config['test_url'];u=urlsplit(url)
        if u.scheme!='https' or u.hostname not in ('localhost','127.0.0.1') or u.path!='/v1/chat/completions' or u.username or u.query or u.fragment:raise ValueError('test_host_must_be_loopback')
        for name in ('test_ca','test_key_file'):
            if not Path(config[name]).resolve().is_relative_to(Path(config['test_root']).resolve()):raise ValueError('test_material_outside_root')
        return c,url
    if not config.get('live'):raise ValueError('real_transport_disabled')
    from live_authorization import verify_authority
    verify_authority(config,c)
    return c,'https://api.openai.com/v1/chat/completions'


class RealTransport:
    def __init__(self, *, live=False, authorization_file=None, contract_path=None, test_mode=False, test_root=None, test_url=None, test_ca=None, test_key_file=None, timeout=60, operator_public_key=None, aggregate_authorization_file=None, run_id=None, ledger_path=None):
        self.config={k:str(v) if isinstance(v,Path) else v for k,v in locals().copy().items() if k not in ('self',) and v is not None}
        self.contract,self.url=validate(self.config)
        self.timeout=min(timeout,self.contract.data['request_seconds']);self.active=set()

    def __call__(self, _ignored_policy_url, raw):
        validate(self.config)
        if self.config.get('live'):
            from live_authorization import paid_gate
            paid_gate(self.config,self.contract)
        if _ignored_policy_url not in (self.url,'https://api.openai.com/v1/chat/completions'):raise ValueError('destination_mismatch')
        normalized,_=self.contract.prepare(raw)
        if normalized!=raw:raise ValueError('unprepared_request')
        env={'PATH':os.environ.get('PATH',os.defpath),'PYTHONDONTWRITEBYTECODE':'1'}
        for name in ('HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR'):
            if name in os.environ:env[name]=os.environ[name]
        request={'config':self.config,'raw':base64.b64encode(raw).decode(),'parent_pid':os.getpid()}
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True)
        self.active.add(child)
        try:
            output,_=child.communicate(json.dumps(request).encode(),timeout=self.timeout)
            if child.returncode:raise OSError('transport_worker_failed')
            result=json.loads(output)
            if 'error' in result:raise OSError('transport_failed')
            return result['status'],result['content_type'],base64.b64decode(result['body'])
        except subprocess.TimeoutExpired:
            child.kill();child.communicate();raise OSError('whole_request_deadline') from None
        finally:self.active.discard(child)

    def abort(self):
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
        if config.get('test_mode'):
            key=Path(config['test_key_file']).read_text().strip()
            context=ssl.create_default_context(cafile=config['test_ca'])
            opener=build_opener(ProxyHandler({}),HTTPSHandler(context=context))
        else:
            from live_authorization import paid_gate
            approval=paid_gate(config,c);key=Path(approval['key_file']).read_text().strip();opener=None
            if not key:raise ValueError('missing_gateway_credential')
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
