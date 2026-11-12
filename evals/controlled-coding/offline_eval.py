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


# Hand-authored scripted controls, never model-generated coding results.
IMPLEMENTATIONS = {
    'merge-intervals': {'correct': CORRECT, 'wrong': WRONG},
    'parse-duration': {
        'correct': '''import re
def parse_duration(text):
    remaining = text.strip()
    if not remaining:
        raise ValueError("empty duration")
    seconds = 0
    while remaining:
        component = re.match(r"([0-9]+)([hms])", remaining)
        if component is None:
            raise ValueError("invalid duration")
        seconds += int(component[1]) * {"h": 3600, "m": 60, "s": 1}[component[2]]
        remaining = remaining[component.end():].lstrip()
    return seconds
''',
        'wrong': 'def parse_duration(text):\n    return 0\n',
    },
    'stable-toposort': {
        'correct': '''def stable_toposort(nodes, edges):
    dependencies = {node: set() for node in nodes}
    for before, after in edges:
        if before not in dependencies or after not in dependencies:
            raise ValueError("unknown node")
        dependencies[after].add(before)
    ordered = []
    pending = list(nodes)
    while pending:
        available = next((node for node in pending if not dependencies[node]), None)
        if available is None:
            raise ValueError("cycle")
        pending.remove(available)
        ordered.append(available)
        for prerequisites in dependencies.values():
            prerequisites.discard(available)
    return ordered
''',
        'wrong': 'def stable_toposort(nodes, edges):\n    return list(nodes)\n',
    },
}


def start_stub(root, variant='correct', pause=None, *, task='merge-intervals'):
    code=IMPLEMENTATIONS[task]['correct' if variant in ('correct','repair') else 'wrong']
    if variant not in ('correct','wrong','tamper','repair'):raise ValueError('unknown_variant')
    if variant=='repair' and task!='parse-duration':raise ValueError('repair_control_task_required')
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
            if variant=='repair':
                # Four-request control: initial candidate, finish, one repair,
                # finish. Checks use the public objective, never acceptance code.
                repair_requested=any(m['role']=='user' and 'Local self-tests failed.' in str(m.get('content','')) for m in body['messages'])
                repaired=any(m.get('tool_call_id')=='REPAIR_WRITE_0' for m in tool_messages)
                if repaired or (already_tools and not repair_requested):
                    delta['content']='OFFLINE TEST DOUBLE: candidate submitted.';finish='stop'
                else:
                    compact="import re\ndef parse_duration(s):\n p=r'(\\d+)([hms])'\n if not s.strip() or re.sub(p+r'\\s*','',s.strip()):raise ValueError()\n return sum(int(n)*dict(h=3600,m=60,s=1)[u] for n,u in re.findall(p,s))\n"
                    calls=[('write',{'path':'solution.py','content':compact if repair_requested else IMPLEMENTATIONS[task]['wrong']})]
                    if not repair_requested:
                        calls.append(('write',{'path':'local_self_test.py','content':"import unittest\nfrom solution import parse_duration as f\nclass Cases(unittest.TestCase):\n def test_hour_and_zero(self):\n  self.assertEqual(f('1h'),3600)\n  self.assertEqual(f('0s'),0)\n"}))
                    prefix='REPAIR_WRITE_' if repair_requested else 'OFFLINE_WRITE_'
                    delta['tool_calls']=[{'index':i,'id':prefix+str(i),'type':'function','function':{'name':name,'arguments':json.dumps(arguments)}} for i,(name,arguments) in enumerate(calls)];finish='tool_calls'
            elif already_tools:delta['content']='OFFLINE TEST DOUBLE: plumbing completed.';finish='stop'
            else:
                if not tool_messages:
                    calls=[('read',{'path':'solution.py'}),('bash',{'command':"python3 -c \"from pathlib import Path; print('SUBPROCESS_OK'); print('HIDDEN_UNREACHABLE' if not Path('/checks/test_acceptance.py').exists() else 'HIDDEN_VISIBLE')\""})]
                    prefix='OFFLINE_READ_'
                else:
                    # Public smoke checks only: deliberate wrong controls can pass locally
                    # and still fail independent grading. Never copy acceptance cases.
                    smoke = {'merge-intervals': 'merge_intervals([]), []', 'parse-duration': "parse_duration('0s'), 0", 'stable-toposort': 'stable_toposort([], []), []'}[task]
                    local_test = 'import unittest\nfrom solution import *\nclass Smoke(unittest.TestCase):\n    def test_public_smoke(self):\n        self.assertEqual(' + smoke + ')\n'
                    calls=[('write',{'path':'solution.py','content':code}), ('write',{'path':'local_self_test.py','content':local_test})]
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
    p=argparse.ArgumentParser(description='Scripted test-double plumbing, not model coding performance');p.add_argument('--task',choices=sorted(IMPLEMENTATIONS),default='merge-intervals');p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--variant',choices=['correct','wrong','tamper'],default='correct');a=p.parse_args()
    binding=fixture_binding(a.task);print(json.dumps(binding),flush=True)
    initialize(a.output,task=a.task);server,contacts=start_stub(a.output,a.variant,task=a.task)
    try:
        report,candidate,workspace=execute_agent(a.output,a.runtime,binding['task_id']+':A')
        if report['exit_code']!=0 or report['timed_out'] or report.get('aborted',False):
            raise RuntimeError('coding_adapter_failed')
        from independent import evaluate_patch
        grading=evaluate_patch(binding['task_id'],(a.output/'candidate.patch').read_text(),a.output/'independent-check')
        (a.output/'test-double-coding-observation.json').write_bytes(canonical({'classification':'SYNTHETIC_TEST_DOUBLE_PLUMBING_NOT_CODING_PERFORMANCE','task':a.task,'variant':a.variant,'agent_exit_code':report['exit_code'],'timed_out':report['timed_out'],'candidate_sha256':__import__('hashlib').sha256(candidate).hexdigest(),'contacts':contacts,'workspace':str(workspace),'independent_acceptance':grading}))
        print('OFFLINE_AGENT_EXIT',report['exit_code'],'INDEPENDENT_ACCEPTANCE',grading['success'],flush=True)
        if grading.get('infrastructure_failure'):raise RuntimeError('independent_grader_failed')
        if grading['success']!=(a.variant=='correct'):raise RuntimeError('acceptance_control_failed')
    finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
