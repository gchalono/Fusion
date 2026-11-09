"""FNXC:OfflineFinal 2026-11-09-05:40:
Scripted OpenAI wire upstream exercises a genuine Fusion coding session, never
agent capability. All artifacts stay in explicit test-double directories. Frozen
criteria are unchanged. The broker and experiment ledger are outside the sandbox.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from contract import Contract,canonical
from pilot import initialize,execute_agent,fixture_binding

CORRECT='''def merge_intervals(intervals):
    out = []
    for a, b in sorted(intervals):
        if a > b:
            raise ValueError("reversed interval")
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out
'''
WRONG='def merge_intervals(intervals):\n    return []\n'


def start_stub(root, variant='correct', pause=None):
    root=Path(root);key=secrets.token_hex(32);key_file=root/'upstream-key';key_file.write_text(key);key_file.chmod(0o600)
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(root/'tls.key'),'-out',str(root/'tls.crt'),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    contract=Contract();contacts=[]
    class Stub(BaseHTTPRequestHandler):
        def log_message(self,*_args):pass
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']));body=json.loads(raw)
            valid=self.headers.get('Authorization')=='Bearer '+key
            contacts.append({'gateway_auth_valid':valid,'model':body.get('model'),'max_tokens':body.get('max_tokens'),'bytes':len(raw)})
            if not valid:self.send_error(403);return
            if pause is not None and len(contacts)==1:pause[0].set();pause[1].wait(20)
            tool_messages=[m for m in body['messages'] if m['role']=='tool']
            already_tools=any(m.get('tool_call_id')=='OFFLINE_WRITE_0' for m in tool_messages)
            delta={'role':'assistant'}
            if already_tools:delta['content']='OFFLINE TEST DOUBLE: plumbing completed.';finish='stop'
            else:
                if not tool_messages:
                    calls=[('read',{'path':'solution.py'}),('bash',{'command':"python3 -c \"from pathlib import Path; print('SUBPROCESS_OK'); print('HIDDEN_UNREACHABLE' if not Path('/checks/test_acceptance.py').exists() else 'HIDDEN_VISIBLE')\""})]
                    prefix='OFFLINE_READ_'
                else:
                    calls=[('write',{'path':'solution.py','content':CORRECT if variant=='correct' else WRONG})]
                    if variant=='tamper':calls.append(('write',{'path':'test_acceptance.py','content':'raise SystemExit(0)\n'}))
                    prefix='OFFLINE_WRITE_'
                delta['tool_calls']=[{'index':i,'id':prefix+str(i),'type':'function','function':{'name':name,'arguments':json.dumps(arguments)}} for i,(name,arguments) in enumerate(calls)];finish='tool_calls'
            first={'id':'OFFLINE_TEST_DOUBLE','object':'chat.completion.chunk','created':0,'model':contract.data['model'],'choices':[{'index':0,'delta':delta,'finish_reason':None}]}
            end={'id':'OFFLINE_TEST_DOUBLE','object':'chat.completion.chunk','created':0,'model':contract.data['model'],'choices':[{'index':0,'delta':{},'finish_reason':finish}]}
            usage={'id':'OFFLINE_TEST_DOUBLE','object':'chat.completion.chunk','created':0,'model':contract.data['model'],'choices':[],'usage':{'prompt_tokens':5,'completion_tokens':10,'total_tokens':15,'prompt_tokens_details':{'cached_tokens':0}}}
            payload=(''.join('data: '+json.dumps(v)+'\n\n' for v in (first,end,usage))+'data: [DONE]\n\n').encode()
            try:self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            except OSError:pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Stub);ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(root/'tls.crt',root/'tls.key');server.socket=ctx.wrap_socket(server.socket,server_side=True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    (root/'stub.json').write_bytes(canonical({'url':f'https://localhost:{server.server_port}/v1/chat/completions','classification':'SYNTHETIC_TEST_DOUBLE_NOT_MODEL_OUTPUT'}))
    return server,contacts


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--variant',choices=['correct','wrong','tamper'],default='correct');a=p.parse_args()
    binding=fixture_binding();print(json.dumps(binding),flush=True)
    if binding['task_id']!='merge-intervals':raise ValueError('scripted_fixture_not_supported_do_not_substitute')
    initialize(a.output);server,contacts=start_stub(a.output,a.variant)
    try:
        report,candidate,workspace=execute_agent(a.output,a.runtime,binding['task_id']+':A')
        from independent import evaluate_patch
        grading=evaluate_patch(binding['task_id'],(a.output/'candidate.patch').read_text(),a.output/'independent-check')
        (a.output/'test-double-coding-observation.json').write_bytes(canonical({'classification':'SYNTHETIC_TEST_DOUBLE_PLUMBING_NOT_CODING_PERFORMANCE','agent_exit_code':report['exit_code'],'timed_out':report['timed_out'],'candidate_sha256':__import__('hashlib').sha256(candidate).hexdigest(),'contacts':contacts,'workspace':str(workspace),'independent_acceptance':grading}))
        print('OFFLINE_AGENT_EXIT',report['exit_code'],'INDEPENDENT_ACCEPTANCE',grading['success'],flush=True)
        if grading['success']!=(a.variant=='correct'):raise RuntimeError('acceptance_control_failed')
        if report['exit_code']!=0:raise RuntimeError('coding_adapter_failed')
    finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
