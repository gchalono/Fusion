"""FNXC:OfflineFinal 2026-11-09-05:40:
Frozen unittest code runs in a protected process in the second sandbox. Candidate
imports execute only in a separate worker. A fresh private MAC authenticates the
grading envelope; untrusted stdout and exit codes cannot establish acceptance.
"""
import copy
import ctypes
import hashlib
import hmac
import importlib.util
import io
import json
import os
import subprocess
import sys
import types
import unittest

request=json.loads(sys.stdin.read(1000000))
if ctypes.CDLL(None).prctl(4,0)!=0:raise RuntimeError('grader_dumpability_guard_failed')
class Proxy(types.ModuleType):
    def __getattr__(self,name):
        if name.startswith('__'):raise AttributeError(name)
        def invoke(*args):
            p=subprocess.run([sys.executable,'-B','/eval/acceptance_worker.py'],input=json.dumps({'function':name,'args':args}).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,close_fds=True)
            if p.returncode or len(p.stdout)>1000000:raise RuntimeError('candidate_worker_failed')
            reply=json.loads(p.stdout)
            for original,changed in zip(args,reply.get('post_args',[])):
                if isinstance(original,list):original[:]=changed
                elif isinstance(original,dict):original.clear();original.update(changed)
            if 'exception' in reply:
                if reply['exception']=='ValueError':raise ValueError('candidate ValueError')
                raise RuntimeError('candidate exception')
            return reply['value']
        return invoke
sys.modules['solution']=Proxy('solution')
spec=importlib.util.spec_from_file_location('frozen_acceptance','/checks/test_acceptance.py');checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
suite=unittest.defaultTestLoader.loadTestsFromModule(checks);stream=io.StringIO();outcome=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
record={'classification':'INDEPENDENT_TEST_DOUBLE_PLUMBING_CHECK','tests':outcome.testsRun,'failed':len(outcome.failures),'errors':len(outcome.errors),'passed':outcome.testsRun-len(outcome.failures)-len(outcome.errors),'success':outcome.wasSuccessful(),'test_log':stream.getvalue()}
raw=json.dumps(record,sort_keys=True,separators=(',',':')).encode();tag=hmac.new(bytes.fromhex(request['grading_key']),raw,'sha256').hexdigest()
print(json.dumps({'record':record,'authentication':tag}))
