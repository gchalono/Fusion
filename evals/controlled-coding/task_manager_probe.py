"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
TEST DOUBLE integration security probe. Reuse the existing run-bound inference
socket, namespace/bridge, seccomp and durable guard with exact Experiment 2 inputs.
No Pi session or provider contact. Boundary checks are not implementation trials.
"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import threading
from task_manager_adapter import load_arm,experiment_contract,TASK,sha
from contract import canonical
from budget import AggregateBudget,guard_gateway


def inside():
    request=json.loads(sys.stdin.read());token=Path('/run/local-token').read_text()
    prompt=Path('/run/objective.txt').read_bytes()
    def call(path='/v1/chat/completions',model=None,auth=token,tools=None):
        body={'model':model or request['model'],'messages':[{'role':'user','content':prompt.decode()}],'max_tokens':512}
        if tools is not None:body['tools']=tools
        c=http.client.HTTPConnection('127.0.0.1',39777,timeout=3)
        try:
            c.request('POST',path,json.dumps(body),{'Authorization':'Bearer '+auth,'Content-Type':'application/json'});r=c.getresponse();r.read();return r.status
        finally:c.close()
    if request.get('mode')=='revoked':
        assert call()==403
        print(json.dumps({'token_revocation_denied':True}));return
    if request.get('mode')=='gateway_down':
        try:call()
        except (OSError,http.client.HTTPException):
            print(json.dumps({'gateway_shutdown_fail_closed':True}));return
        raise AssertionError('gateway shutdown unexpectedly served a request')
    positive=call()==200
    checks={'exact_input':sha(prompt)==request['input_sha256'],
            'gateway_positive_control':positive,
            'wrong_endpoint_denied':call('/v1/responses')==403,
            'wrong_token_denied':call(auth='TEST DOUBLE invalid token')==403,
            'wrong_model_denied':call(model='TEST DOUBLE unauthorized model')==403,
            'unpriced_hosted_tool_denied':call(tools=[{'type':'web_search'}])==403,
            'private_canary_unmounted':not Path(request['canary_path']).exists(),
            'hidden_checks_unmounted':not Path('/checks').exists(),
            'host_workspace_unmounted':not Path('/workspace/Fusion').exists(),
            'all_other_arm_prompts_unmounted':not Path('/workspace/phase2n-evaluation').exists(),
            'host_credential_variables_absent':all(k not in os.environ for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','HTTP_PROXY','HTTPS_PROXY','TASK_MANAGER_CANARY')),
            'no_new_privs':next(line.split(':')[1].strip() for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('NoNewPrivs:'))=='1'}
    try:Path('/run/objective.txt').write_bytes(b'TEST DOUBLE tamper');checks['frozen_prompt_readonly']=False
    except OSError:checks['frozen_prompt_readonly']=True
    try:
        with socket.create_connection(('192.0.2.1',443),timeout=.2):pass
        checks['direct_non_gateway_route_denied']=False
    except OSError:checks['direct_non_gateway_route_denied']=True
    assert all(checks.values()),checks
    print(json.dumps({'classification':'TEST DOUBLE integrated boundary probe, NOT Pi or coding performance','checks':checks}))


def probe(evidence,prepared,arm,out,ledger_path=None):
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'planning-collector'))
    from gateway import Gateway,Policy,Artifacts
    from execution import run_command
    from isolation import inference_socket
    root=Path(out);root.mkdir(parents=True,exist_ok=False);(root/'.offline-test').touch()
    prompt=load_arm(evidence,prepared,arm);(root/'objective.txt').write_bytes(prompt)
    token=secrets.token_hex(32);(root/'local-token').write_text(token)
    canary=root/'host-only-canary';canary.write_text(secrets.token_hex(32))
    workspace=root/'isolated-work';workspace.mkdir()
    d=experiment_contract();run=TASK+':'+arm
    ledger_path=Path(ledger_path) if ledger_path is not None else root/'experiment2.db'
    ledger=AggregateBudget(ledger_path,experiment_contract=d);ledger.control_run('coding',run,'start')
    contacts=[]
    def transport(url,raw):
        contacts.append({'classification':'TEST DOUBLE local function, no network upstream','request_sha256':sha(raw)})
        return 200,'application/json',canonical({'model':d['model'],'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'TEST DOUBLE'}}]})
    policy=Policy('OpenAI',d['model'],'https://api.openai.com/v1/chat/completions',('api.openai.com',),4,120000,400000,1600000,32000,512,512)
    audit=root/'audit';audit.mkdir();(audit/'.offline-test').touch()
    def bounds(request):return (len(canonical(request)),512)
    def cost(request):
        import math
        i,o=bounds(request);return (i*400000+o*1600000+999999)//1000000
    g=guard_gateway(Gateway(policy,Artifacts(audit,offline=True,secrets=(token,)),transport),ledger,'coding',run,cost_bound=cost,token_bound=bounds)
    server=inference_socket(root/'gateway.sock',g,token);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        mounts=[(Path(__file__).resolve(),'/eval/task_manager_probe.py'),(Path(__file__).with_name('task_manager_adapter.py').resolve(),'/eval/task_manager_adapter.py'),(Path(__file__).with_name('budget.py').resolve(),'/eval/budget.py'),(Path(__file__).with_name('contract.py').resolve(),'/eval/contract.py'),(root/'objective.txt','/run/objective.txt'),(root/'local-token','/run/local-token')]
        # Inside code imports no provider transport. task_manager_adapter has no
        # live entry point and only the local contract/ledger module dependencies.
        p=run_command(root/'gateway.sock',workspace,[sys.executable,'-B','/eval/task_manager_probe.py','--inside'],mounts=mounts,timeout=20,stdin=canonical({'model':d['model'],'input_sha256':sha(prompt),'canary_path':str(canary)}))
        if p['exit_code'] or p['timed_out']:raise RuntimeError('integrated_boundary_probe_failed:'+p['stderr'].decode(errors='replace')[:1000])
        result=json.loads(p['stdout'])
        server.revoked.set()
        for mode in ('revoked','gateway_down'):
            if mode=='gateway_down':
                server.shutdown();server.server_close();thread.join()
            check=run_command(root/'gateway.sock',workspace,[sys.executable,'-B','/eval/task_manager_probe.py','--inside'],mounts=mounts,timeout=20,stdin=canonical({'model':d['model'],'input_sha256':sha(prompt),'canary_path':str(canary),'mode':mode}))
            if check['exit_code'] or check['timed_out']:raise RuntimeError('revocation_or_shutdown_probe_failed:'+check['stderr'].decode(errors='replace')[:500])
            result['checks'].update(json.loads(check['stdout']))
        snapshot=AggregateBudget(ledger_path).snapshot()
        run_reservations=[r for r in snapshot['reservations'] if r['run']==run]
        assert len(contacts)==len(run_reservations)==1
        assert snapshot['transitions'][-1]['state']=='UNCERTAIN' # usage deliberately missing
        result.update(arm=arm,input_sha256=sha(prompt),contacts=len(contacts),reservation_count=1,provider_contacts=0,ledger=snapshot,agent_sessions=0,ledger_path=str(ledger_path),run_reserved_micro_usd=sum(r['reserved_exposure_micro_usd'] for r in run_reservations))
        (root/'result.json').write_bytes(canonical(result));return result
    finally:
        server.revoked.set();server.shutdown();server.server_close();thread.join();ledger.recover_uncertain()
        ledger.control_run('coding',run,'INCOMPLETE');(root/'gateway.sock').unlink(missing_ok=True)

if __name__=='__main__':
    # Imports required for the outer supervisor are not exposed in the namespace.
    if sys.argv[1:]==['--inside']:inside()
    else:
        p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--arm',choices=list('ABC'),required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(probe(a.evidence,a.prepared,a.arm,a.out)))
