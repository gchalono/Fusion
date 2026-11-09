"""FNXC:BlockerResolution 2026-11-09-18:27:
SYNTHETIC native-bridge test approver. Refuses any unmarked directory. Uses the
existing approval implementation, including durable submission intent. Never
creates human approvals, opens a TTY, or performs provider transport.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from approvals import Approvals,digest
from contract import canonical


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--operation',choices=['prepare','crash','replay','consume'],required=True);a=p.parse_args()
    if not (a.root/'.offline-test').is_file():raise ValueError('SYNTHETIC_marker_required')
    context=json.loads(sys.stdin.read());store=Approvals(a.root,test_double=True)
    kwargs={k:context[k] for k in ('question','session_id','task_id','preregistration_hash')}
    name_file=a.root/'pending-approval-name'
    if a.operation=='prepare':
        q=store.persist_question(**kwargs);answer=context['answer']
        try:store._record(q,answer,'APPROVE wrong-hash','TEST_APPROVER_NOT_HUMAN')
        except ValueError:explicit=True
        else:raise AssertionError('explicit_approval_bypassed')
        name=store.test_approve(q,answer);path=a.root/name;original=path.read_bytes();record=json.loads(original);record['answer']+='EDITED';path.write_bytes(canonical(record))
        try:store.submit(name,**kwargs,native_submit=lambda _:(_ for _ in ()).throw(AssertionError('edited_submitted')),allow_test=True)
        except ValueError:edited=True
        else:raise AssertionError('edited_accepted')
        path.write_bytes(original)
        try:store.submit('missing.approval.json',**kwargs,native_submit=lambda _:None,allow_test=True)
        except FileNotFoundError:missing=True
        else:raise AssertionError('missing_accepted')
        try:store.submit(name,**kwargs,native_submit=lambda _:None)
        except ValueError:synthetic=True
        else:raise AssertionError('SYNTHETIC_accepted_in_live')
        name_file.write_text(name)
        print(json.dumps({'classification':'SYNTHETIC','question_hash':digest(context['question']),'answer_hash':digest(answer),'checks':{'explicit_approval_verification':explicit,'edited_approval_rejection':edited,'missing_approval_rejection':missing,'synthetic_live_rejection':synthetic}}))
    else:
        name=name_file.read_text()
        if a.operation=='crash':store.submit(name,**kwargs,native_submit=lambda _:os._exit(23),allow_test=True)
        elif a.operation=='replay':
            try:store.submit(name,**kwargs,native_submit=lambda _:(_ for _ in ()).throw(AssertionError('replay_callback')),allow_test=True)
            except FileExistsError:print(json.dumps({'classification':'SYNTHETIC','restart_replay_rejected':True}))
            else:raise AssertionError('replay_accepted')
        else:
            answer=store.submit(name,**kwargs,native_submit=lambda value:value,allow_test=True)
            print(json.dumps({'classification':'SYNTHETIC','answer':answer,'answer_hash':digest(answer)}))
if __name__=='__main__':main()
