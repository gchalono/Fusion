"""FNXC:OfflineFinal 2026-11-09-05:40:
Minimal offline pilot plumbing. A gateway broker owns one durable experiment DB;
coding commands receive only a run socket/token, source input and public runtime.
No live coding or paid operation is exposed. Explicit abort/resume are control-
plane commands outside the sandbox. Restart defaults to INCOMPLETE, never resume.
"""
import argparse
import base64
import copy
import difflib
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
from gateway import Gateway,Policy,Artifacts,canonical
from budget import AggregateBudget,guard_gateway
from contract import Contract,micro
from harness import verify,ROOT as FIXTURES_ROOT,inputs
from isolation import UnixServer,namespace_command
from execution import run_command,runtime_mounts,coding_command
from real_transport import RealTransport

ROOT=Path(__file__).resolve().parent


def fixture_binding():
    frozen=verify();names=sorted({Path(p).parts[1] for p in frozen['files']})
    selected=names[0]
    entries={k:v for k,v in frozen['files'].items() if k.startswith('fixtures/'+selected+'/')}
    return {'task_id':selected,'stored_file_sha256':entries,'derived_fixture_sha256':hashlib.sha256(canonical(entries)).hexdigest(),'frozen_manifest_sha256':hashlib.sha256((ROOT/'frozen.json').read_bytes()).hexdigest(),'canonical_order':names}


def initialize(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False);root.chmod(0o700);(root/'.offline-test').touch()
    contract=Contract();data=copy.deepcopy(contract.data);binding=fixture_binding()
    data.update(planning_run_ids=binding['canonical_order'],coding_run_ids=[t+':'+a for t in binding['canonical_order'] for a in 'ABC'],frozen_coding_token_limit=verify()['settings']['coding_token_limit'],fixture_manifest_sha256=binding['frozen_manifest_sha256'])
    (root/'experiment.json').write_bytes(canonical(data));(root/'fixture-binding.json').write_bytes(canonical(binding))
    AggregateBudget(root/'experiment.db',experiment_contract=data)
    return binding


def request_admin(root,action):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5);s.connect(str(Path(root)/'admin.sock'));s.sendall(canonical({'action':action})+b'\n');return json.loads(s.recv(4096))


# FNXC:LiveCoding 2026-11-10-06:45: Share the actual native broker protocol;
# no namespace/seccomp change. Approved mode rejects output-limit intervention.
def make_inference_server(socket_path,*,c,transport,ledger,run,gateway,token,artifacts,output_limit,bounds=None,revoked=None,strict=False):
    bounds=bounds or threading.local();revoked=revoked or threading.Event();events=[]
    from http.server import BaseHTTPRequestHandler
    class Inference(BaseHTTPRequestHandler):
        def log_message(self,*_args):pass
        def do_POST(self):
            status=403;payload=b'{"error":"denied"}';kind='application/json';stage='headers'
            try:
                if revoked.is_set() or self.path!='/v1/chat/completions' or self.headers.get('Host','')!='127.0.0.1:39777':raise ValueError('endpoint_or_revoked')
                if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token):raise ValueError('client')
                if self.headers.get('Transfer-Encoding'):raise ValueError('encoding')
                lengths=self.headers.get_all('Content-Length',[])
                if len(lengths)!=1 or not lengths[0].isdigit() or not 0<int(lengths[0])<=32000:raise ValueError('request_length')
                stage='request_schema';raw=self.rfile.read(int(lengths[0]));c.prepare(raw);body=json.loads(raw)
                requested=body.get('max_tokens',body.get('max_completion_tokens',4096))
                for field in ('max_tokens','max_completion_tokens'):body.pop(field,None)
                if type(requested) is not int or requested<=0:raise ValueError('output_limit')
                if strict and requested>output_limit:raise ValueError('output_limit_intervention_forbidden')
                body['max_tokens']=min(requested,output_limit);body['temperature']=0
                events.append({'requested_max_tokens':requested,'forwarded_max_tokens':body['max_tokens']})
                normalized,metadata=c.prepare(canonical(body));metadata['input_token_upper_bound']=max(len(raw),metadata['input_token_upper_bound'])
                from decimal import Decimal,ROUND_CEILING
                metadata['reserved_micro_usd']=int((Decimal(metadata['input_token_upper_bound'])*Decimal('.40')+Decimal(metadata['output_token_upper_bound'])*Decimal('1.60')).to_integral_value(rounding=ROUND_CEILING))
                bounds.value=metadata
                stage='deadline';transport.timeout=min(60,ledger.remaining_seconds('coding',run))
                stage='gateway';status,kind,payload=gateway.handle(normalized)
            except Exception as error:
                # FNXC:RealModelReadiness 2026-11-10-05:09: Fixed denial codes,
                # never raw exceptions/credentials; evidence cannot authorize retry.
                code=str(error)
                if code not in {'aggregate_spend_cap','experiment_request_cap','coding_run_cap','stage_allocation_cap','frozen_coding_token_limit','model_call_cap','spend_ceiling'}:code='request_denied'
                artifacts.write('denied-'+secrets.token_hex(8)+'.json',canonical({'code':code,'stage':stage,'error_type':type(error).__name__}))
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)));self.end_headers()
            try:self.wfile.write(payload)
            except OSError:
                ledger.control_run('coding',run,'INCOMPLETE')
    server=UnixServer(str(socket_path),Inference)
    server.events=events;server.revoked=revoked
    return server


def broker(root,run,action,stub_url,ca,key):
    root=Path(root)
    if not (root/'.offline-test').is_file():raise ValueError('offline_experiment_required')
    from readiness_profile import ceiling
    c=Contract();data=json.loads((root/'experiment.json').read_text());output_limit=ceiling(data,offline=True);ledger=AggregateBudget(root/'experiment.db',experiment_contract=data)
    with ledger.connect() as db:old=db.execute('SELECT status FROM run_controls WHERE stage=? AND run=?',('coding',run)).fetchone()
    if old and action=='start':
        ledger.recover_uncertain();ledger.control_run('coding',run,'INCOMPLETE');raise ValueError('INCOMPLETE_EXPLICIT_RESUME_REQUIRED')
    ledger.control_run('coding',run,'resume' if action=='resume' else 'start')
    ledger.recover_uncertain()
    for name in ('gateway.sock','admin.sock'):
        path=root/name
        if path.exists():path.unlink()  # Only owned socket entries, never worktrees/history.
    token=secrets.token_hex(32);(root/'local-token').write_text(token);(root/'local-token').chmod(0o600)
    transport=RealTransport(test_mode=True,test_root=root,test_url=stub_url,test_ca=ca,test_key_file=key)
    audit=root/('gateway-'+secrets.token_hex(4));audit.mkdir();(audit/'.offline-test').touch()
    # The offline fixture requests a stricter 512 output ceiling, identically
    # across arms, preserving the frozen 16000 total-token run limit.
    policy=Policy('OpenAI',c.data['model'],'https://api.openai.com/v1/chat/completions',('api.openai.com',),4,micro(c.data['per_run_coding_cap_usd']),400000,1600000,32000,output_limit,output_limit)
    artifacts=Artifacts(audit,offline=False,secrets=(token,Path(key).read_text().strip()))
    artifacts.write('policy.json',canonical(asdict(policy)))
    bounds=threading.local()
    gateway=guard_gateway(Gateway(policy,artifacts,transport),ledger,'coding',run,cost_bound=lambda _:bounds.value['reserved_micro_usd'],estimator=c.estimate,token_bound=lambda _:(bounds.value['input_token_upper_bound'],bounds.value['output_token_upper_bound']))
    revoked=threading.Event();stop=threading.Event()
    server=make_inference_server(root/'gateway.sock',c=c,transport=transport,ledger=ledger,run=run,gateway=gateway,token=token,artifacts=artifacts,output_limit=output_limit,bounds=bounds,revoked=revoked)
    class Admin(socketserver.StreamRequestHandler):
        def handle(self):
            message=json.loads(self.rfile.readline(4096))
            if message.get('action') not in ('abort','finish'):self.wfile.write(b'{"ok":false}\n');return
            revoked.set();transport.abort()
            ledger.recover_uncertain()
            ledger.control_run('coding',run,'COMPLETE' if message['action']=='finish' else 'INCOMPLETE')
            self.wfile.write(b'{"ok":true}\n');self.wfile.flush();stop.set()
    admin=UnixServer(str(root/'admin.sock'),Admin)
    for s in (server,admin):threading.Thread(target=s.serve_forever,daemon=True).start()
    (root/'ready').write_text('offline gateway ready')
    try:stop.wait()
    finally:
        revoked.set();transport.abort();server.shutdown();server.server_close();admin.shutdown();admin.server_close()


def spawn_broker(root, run, *, resume=False):
    root=Path(root);ready=root/'ready'
    if ready.exists():ready.unlink()
    settings=json.loads((root/'stub.json').read_text())
    env={'PATH':os.environ['PATH'],'PYTHONDONTWRITEBYTECODE':'1'}
    log=(root/('broker-'+secrets.token_hex(4)+'.log')).open('wb')
    process=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'gateway','--experiment',str(root),'--run',run,'--action','resume' if resume else 'start','--stub-url',settings['url'],'--ca',str(root/'tls.crt'),'--key',str(root/'upstream-key')],env=env,stdout=log,stderr=log,close_fds=True)
    deadline=time.monotonic()+10
    while not ready.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.02)
    if not ready.exists():process.wait(timeout=5);log.close();raise RuntimeError('gateway_start_failed_or_incomplete')
    return process,log


def execute_agent(root,runtime,run,*,resume=False, broker_hook=None):
    root=Path(root);binding=json.loads((root/'fixture-binding.json').read_text());task=binding['task_id']
    workspace=root/('workspace-'+secrets.token_hex(4));workspace.mkdir()
    shutil.copyfile(ROOT/'fixtures'/task/'initial/solution.py',workspace/'solution.py')
    objective=root/'objective.txt';objective.write_text((ROOT/'fixtures'/task/'objective.txt').read_text())
    if resume and (root/'partial-solution.py').is_file():shutil.copyfile(root/'partial-solution.py',workspace/'solution.py')
    process,log=spawn_broker(root,run,resume=resume)
    ledger=AggregateBudget(root/'experiment.db');c=Contract()
    completed=False
    abort_event=threading.Event();watch_stop=threading.Event()
    def watch():
        while not watch_stop.wait(.05):
            if process.poll() is not None:abort_event.set();return
    threading.Thread(target=watch,daemon=True).start()
    if broker_hook:broker_hook(process)
    try:
        mounts=[(ROOT/'coding-agent.mts','/eval/coding-agent.mts'),(root/'local-token','/run/local-token'),(objective,'/run/objective.txt'),*runtime_mounts(runtime)]
        report=run_command(root/'gateway.sock',workspace,coding_command(runtime,c.data['model']),mounts=mounts,timeout=min(300,ledger.remaining_seconds('coding',run)),abort_event=abort_event)
        token=(root/'local-token').read_text().strip().encode();secret=(root/'upstream-key').read_text().strip().encode()
        if any(s and s in report[k] for s in (token,secret) for k in ('stdout','stderr')):raise ValueError('credential_in_collected_output')
        (root/'agent-stdout.txt').write_bytes(report['stdout']);(root/'agent-stderr.txt').write_bytes(report['stderr'])
        candidate=workspace/'solution.py'
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size>1000000:raise ValueError('invalid_candidate')
        raw=candidate.read_bytes()
        if any(s and s in raw for s in (token,secret)):raise ValueError('credential_in_candidate')
        (root/'partial-solution.py').write_bytes(raw)
        patch=''.join(difflib.unified_diff((ROOT/'fixtures'/task/'initial/solution.py').read_text().splitlines(True),raw.decode().splitlines(True),fromfile='a/solution.py',tofile='b/solution.py'))
        (root/'candidate.patch').write_text(patch)
        if process.poll() is None:
            request_admin(root,'finish' if report['exit_code']==0 and not report['timed_out'] and not report['aborted'] else 'abort')
        else:
            ledger.recover_uncertain();ledger.control_run('coding',run,'INCOMPLETE')
        completed=True
        return report,raw,workspace
    finally:
        watch_stop.set()
        if not completed and process.poll() is None:
            try:request_admin(root,'abort')
            except Exception:process.terminate()
        process.wait(timeout=5);log.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['describe-fixture','gateway','abort','resume']);p.add_argument('--experiment',type=Path);p.add_argument('--run');p.add_argument('--runtime',type=Path);p.add_argument('--action',choices=['start','resume'],default='start');p.add_argument('--stub-url');p.add_argument('--ca',type=Path);p.add_argument('--key',type=Path);a=p.parse_args()
    if a.command=='describe-fixture':print(json.dumps(fixture_binding(),indent=2));return
    if a.command=='gateway':broker(a.experiment,a.run,a.action,a.stub_url,a.ca,a.key)
    elif a.command=='abort':print(json.dumps(request_admin(a.experiment,'abort')))
    elif a.command=='resume':execute_agent(a.experiment,a.runtime,a.run,resume=True)

if __name__=='__main__':main()
