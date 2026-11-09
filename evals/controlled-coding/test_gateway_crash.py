"""FNXC:NativeIsolation 2026-11-09-04:44: Kill an owned fixture gateway after
upstream contact and recover its durable FORWARDED reservation as UNCERTAIN.
"""
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from budget import AggregateBudget


class GatewayCrashTests(unittest.TestCase):
    def test_kill_after_upstream_contact_never_releases(self):
        contacted=threading.Event();release=threading.Event()
        class Stub(BaseHTTPRequestHandler):
            def log_message(self,*_args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']));contacted.set();release.wait(5)
                try:self.send_response(200);self.end_headers();self.wfile.write(b'{}')
                except OSError:pass
        stub=ThreadingHTTPServer(('127.0.0.1',0),Stub)
        threading.Thread(target=stub.serve_forever,daemon=True).start()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.offline-test').touch()
            code='''import sys,http.client
from pathlib import Path
from budget import AggregateBudget,guard_gateway
from gateway import Policy,Gateway,Artifacts
from isolation import inference_socket
root=Path(sys.argv[1]);port=int(sys.argv[2])
policy=Policy('offline','offline-model','https://offline.invalid/v1/chat/completions',('offline.invalid',),4,150000,1000000,1000000,100,100,100)
def transport(url,body):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
 c.request('POST','/v1/chat/completions',body)
 r=c.getresponse();return r.status,'application/json',r.read()
b=AggregateBudget(root/'ledger.db');g=guard_gateway(Gateway(policy,Artifacts(root,offline=True),transport),b,'coding','A')
s=inference_socket(root/'gateway.sock',g,'local-fixture-token');s.serve_forever()
'''
            paths=os.pathsep.join([str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent.parent/'planning-collector')])
            child=subprocess.Popen([sys.executable,'-u','-c',code,str(root),str(stub.server_port)],env={'PATH':os.defpath,'PYTHONPATH':paths,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                deadline=time.monotonic()+5
                while not (root/'gateway.sock').exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue((root/'gateway.sock').exists())
                def request():
                    try:
                        c=http.client.HTTPConnection('local',timeout=5)
                        c.connect=lambda: setattr(c,'sock',socket.socket(socket.AF_UNIX)) or c.sock.connect(str(root/'gateway.sock'))
                        c.request('POST','/v1/chat/completions',json.dumps({'model':'offline-model','messages':[{'role':'user','content':'fixture'}],'max_tokens':100}),{'Authorization':'Bearer local-fixture-token'})
                        c.getresponse().read()
                    except (OSError,http.client.HTTPException):pass
                client=threading.Thread(target=request);client.start()
                self.assertTrue(contacted.wait(5),'local stub did not receive request')
                ledger=AggregateBudget(root/'ledger.db')
                self.assertEqual(ledger.snapshot()['transitions'][-1]['state'],'FORWARDED')
                child.terminate();child.wait(timeout=5);client.join(timeout=5)
                recovered=AggregateBudget(root/'ledger.db')
                self.assertEqual(recovered.recover_uncertain(),1)
                snap=recovered.snapshot()
                self.assertEqual(snap['transitions'][-1]['state'],'UNCERTAIN')
                self.assertEqual(snap['reserved_exposure_micro_usd'],200)
                self.assertEqual(recovered.recover_uncertain(),0)
            finally:
                if child.poll() is None:child.terminate();child.wait(timeout=5)
                if child.stderr:child.stderr.close()
                release.set();stub.shutdown();stub.server_close()
