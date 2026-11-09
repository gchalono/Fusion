"""FNXC:OfflineFinal 2026-11-09-05:40: Exercise the real HTTPS worker against
local TLS only. Wire shapes follow installed OpenAI SDK types; no real-schema
fidelity or provider availability is claimed before a separately approved call.
"""
import json
from pathlib import Path
import secrets
import ssl
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from contract import Contract,canonical
from real_transport import RealTransport

class TLSTests(unittest.TestCase):
    def test_local_tls_streaming_nonstream_and_missing_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.offline-test').touch();key=secrets.token_hex(32)
            secret=root/'test-key';secret.write_text(key);secret.chmod(0o600)
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(root/'server.key'),'-out',str(root/'server.crt'),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            c=Contract();contacts=[]
            class Stub(BaseHTTPRequestHandler):
                def log_message(self,*_args):pass
                def do_POST(self):
                    self.server.case_body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    contacts.append(self.headers.get('Authorization')=='Bearer '+key)
                    body=self.server.case_body;usage={'prompt_tokens':5,'completion_tokens':3,'total_tokens':8,'prompt_tokens_details':{'cached_tokens':2}}
                    if body.get('stream'):
                        frames=[{'id':'TEST-DOUBLE','object':'chat.completion.chunk','created':0,'model':c.data['model'],'choices':[{'index':0,'delta':{'role':'assistant','content':'TEST DOUBLE'},'finish_reason':'stop'}]}]
                        if body.get('stream_options',{}).get('include_usage'):frames.append({'id':'TEST-DOUBLE','object':'chat.completion.chunk','created':0,'model':c.data['model'],'choices':[],'usage':usage})
                        payload=(''.join('data: '+json.dumps(x)+'\n\n' for x in frames)+'data: [DONE]\n\n').encode();kind='text/event-stream'
                    else:payload=canonical({'id':'TEST-DOUBLE','object':'chat.completion','created':0,'model':c.data['model'],'choices':[{'index':0,'message':{'role':'assistant','content':'TEST DOUBLE'},'finish_reason':'stop'}],'usage':usage});kind='application/json'
                    self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            server=ThreadingHTTPServer(('127.0.0.1',0),Stub);ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(root/'server.crt',root/'server.key');server.socket=ctx.wrap_socket(server.socket,server_side=True)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                transport=RealTransport(test_mode=True,test_root=root,test_url=f'https://localhost:{server.server_port}/v1/chat/completions',test_ca=root/'server.crt',test_key_file=secret)
                for stream,usage in ((False,False),(True,True),(True,False)):
                    body={'model':c.data['model'],'messages':[{'role':'user','content':'TEST DOUBLE'}],'stream':stream,'max_tokens':16}
                    if stream:body['stream_options']={'include_usage':usage}
                    raw,_=c.prepare(canonical(body));status,kind,response=transport('https://api.openai.com/v1/chat/completions',raw)
                    self.assertEqual(status,200);self.assertIn(b'TEST DOUBLE',response);self.assertNotIn(key.encode(),response)
                    if stream:self.assertEqual(b'"usage"' in response,usage)
                self.assertEqual(contacts,[True]*3)
                with self.assertRaises(ValueError):RealTransport(live=True,test_mode=True,test_root=root,test_url='https://localhost/')
                with self.assertRaises(ValueError):RealTransport()
                with self.assertRaises(ValueError):RealTransport(test_mode=True,test_root=root,test_url='https://api.openai.com/v1/chat/completions',test_ca=root/'server.crt',test_key_file=secret)
            finally:server.shutdown();server.server_close()
