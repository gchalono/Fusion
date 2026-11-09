"""FNXC:OfflineFinal 2026-11-09-06:40:
Read-only live refusal check. No inference, interview, credential output, ledger
mutation or authorization creation. OS probes use disposable local test paths.
Fetches only the authorized GitHub fork through the existing recovery preflight.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from contract import Contract,canonical
from real_transport import validate
# FNXC:BlockerResolution 2026-11-09-18:27: Pin refusal-mode recovery to
# the newly supplied independent checkpoint, not the older milestone.
BASELINE='73dd29ab2237fb9e7c47458b9deb0b11d681f033'
EARLIER='993af2bdf7a5fa223ca16bf233be399bc6fd9a86'
ROOT=Path(__file__).resolve().parents[2]


def check_approvals(manifest):
    entries=json.loads(Path(manifest).read_text())
    if {e['task_id'] for e in entries}!={'merge-intervals','parse-duration','stable-toposort'}:raise ValueError('all_three_tasks_required')
    for entry in entries:
        path=Path(entry['record']);key=Path(entry['authentication_key'])
        if path.is_symlink() or key.is_symlink() or key.stat().st_mode & 0o077:raise ValueError('approval_permissions')
        record=json.loads(path.read_text());tag=record.pop('authentication')
        if not hmac.compare_digest(tag,hmac.new(key.read_bytes(),canonical(record),'sha256').hexdigest()):raise ValueError('approval_edited')
        digest=lambda value:hashlib.sha256(value.encode()).hexdigest()
        if record.get('test_double') is not False or record.get('channel_marker')!='OPERATOR_TTY_V1':raise ValueError('not_human_approval')
        for name in ('session_id','task_id','preregistration_hash','question_hash'):
            if not entry.get(name) or entry[name]!=record.get(name):raise ValueError('approval_binding')
        if digest(record['question'])!=record['question_hash'] or digest(record['answer'])!=record['answer_hash'] or record['approval_command']!='APPROVE '+record['answer_hash']:raise ValueError('approval_hash')
        if not record['timestamp']<=record['approved_at']<=time.time():raise ValueError('approval_timestamp')
        if (path.parent/(path.name+'.submitted')).exists():raise ValueError('approval_already_consumed')


def main():
    p=argparse.ArgumentParser();p.add_argument('--live-transport',action='store_true');p.add_argument('--authorization',type=Path);p.add_argument('--approvals-manifest',type=Path);a=p.parse_args()
    failures=Contract().arming_errors();checks={}
    result=subprocess.run([str(ROOT/'evals/persistence/preflight.sh'),'--baseline',BASELINE,'--branch','eval/phase2n'],cwd=ROOT,capture_output=True,text=True)
    checks['recovery_preflight']=result.returncode==0
    if result.returncode:failures.append('RECOVERY_PREFLIGHT_FAILED')
    result=subprocess.run(['git','merge-base','--is-ancestor',EARLIER,BASELINE],cwd=ROOT,capture_output=True)
    checks['earlier_ancestor']=result.returncode==0
    if result.returncode:failures.append('EARLIER_CHECKPOINT_NOT_ANCESTOR')
    try:validate({'live':a.live_transport,'authorization_file':str(a.authorization)})
    except Exception:failures.append('TRANSPORT_AUTHORIZATION_OR_ARMING_INVALID')
    try:
        if not a.approvals_manifest:raise ValueError('missing')
        check_approvals(a.approvals_manifest)
    except Exception:failures.append('REQUIRED_HUMAN_APPROVALS_MISSING_OR_INVALID')
    with tempfile.TemporaryDirectory(prefix='fusion-live-preflight-') as scratch:
        output=Path(scratch)/'probe';env={'PATH':os.environ['PATH'],'HOME':scratch,'PYTHONDONTWRITEBYTECODE':'1'}
        result=subprocess.run([sys.executable,str(ROOT/'evals/planning-collector/offline_runner.py'),'--security-probe',str(output)],env=env,capture_output=True,timeout=60)
        try:
            proof=json.loads((output/'summary.json').read_text())
            checks['isolation_enforced_now']=result.returncode==0 and proof['isolation_tier']=='ENFORCED' and proof['gateway_initial_canary_verified'] and proof['counts']['real_host_contacts']==0
        except Exception:checks['isolation_enforced_now']=False
    if not checks['isolation_enforced_now']:failures.append('CURRENT_ENFORCED_ISOLATION_AND_CANARY_REQUIRED')
    # No executable live pipeline is exposed yet; this prevents a transport-only
    # check being mistaken for integrated authorization of planning/coding.
    failures.append('INTEGRATED_LIVE_PLANNING_PIPELINE_NOT_VALIDATED')
    print(json.dumps({'status':'LIVE_REFUSED','classification':'READ_ONLY_NO_EXECUTION','checks':checks,'failures':sorted(set(failures))},indent=2))
    return 1
if __name__=='__main__':sys.exit(main())
