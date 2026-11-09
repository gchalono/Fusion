"""FNXC:OfflineFinal 2026-11-09-05:40: Execute only candidate behavior in a child.
No expected answers, grader key, credentials or test harness are passed to it.
"""
import importlib.util
import json
import sys
request=json.loads(sys.stdin.read(1000000));args=request['args']
try:
    spec=importlib.util.spec_from_file_location('candidate','/work/solution.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    value=getattr(module,request['function'])(*args)
    print(json.dumps({'value':value,'post_args':args},allow_nan=False))
except BaseException as error:
    print(json.dumps({'exception':type(error).__name__,'post_args':args}))
