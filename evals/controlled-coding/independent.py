"""FNXC:OfflineFinal 2026-11-09-05:40: Fresh fixture checkout plus generated
allowlisted patch; immutable tests in a second no-network/no-credential sandbox.
Never import candidate code in the host harness or trust agent self-evaluation.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from contract import canonical
from execution import run_command
from harness import ROOT,verify


def evaluate_patch(task, patch, private_root, *, timeout=30):
    verify();root=Path(private_root);root.mkdir(parents=True,exist_ok=False)
    checkout=root/'checkout';checkout.mkdir();shutil.copyfile(ROOT/'fixtures'/task/'initial/solution.py',checkout/'solution.py')
    home=root/'home';home.mkdir();env={'HOME':str(home),'PATH':os.defpath}
    def git(*args,cwd=checkout):subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=cwd,env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    git('init','-q','--initial-branch=wip/fixture')
    # The index supplies the frozen comparison without creating fixture commits.
    git('add','solution.py')
    patch_path=root/'candidate.patch';patch_path.write_text(patch)
    if patch:
        git('apply','--check',str(patch_path),cwd=checkout);git('apply',str(patch_path),cwd=checkout)
    # The caller generates this one-file patch; reject any additional tracked path.
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=checkout,env=env,text=True).splitlines()
    if any(p!='solution.py' for p in changed):raise ValueError('patch_scope_violation')
    before=(ROOT/'fixtures'/task/'acceptance/test_acceptance.py').read_bytes();key=secrets.token_bytes(32)
    mounts=[(ROOT/'acceptance_runner.py','/eval/acceptance_runner.py'),(ROOT/'acceptance_worker.py','/eval/acceptance_worker.py'),(ROOT/'fixtures'/task/'acceptance','/checks')]
    run=run_command(None,checkout,[sys.executable,'-B','/eval/acceptance_runner.py'],mounts=mounts,timeout=min(30,timeout),stdin=canonical({'grading_key':key.hex()}))
    (root/'grader-stderr.txt').write_bytes(run['stderr'])
    if run['exit_code']!=0 or run['timed_out']:return {'success':False,'infrastructure_failure':'isolated_grader_failed','exit_code':run['exit_code']}
    envelope=json.loads(run['stdout']);record=envelope['record']
    if not hmac.compare_digest(envelope['authentication'],hmac.new(key,canonical(record),'sha256').hexdigest()):raise ValueError('untrusted_grade_envelope')
    if before!=(ROOT/'fixtures'/task/'acceptance/test_acceptance.py').read_bytes():raise ValueError('frozen_tests_changed')
    (root/'independent-test-observation.json').write_bytes(canonical(record))
    return record
