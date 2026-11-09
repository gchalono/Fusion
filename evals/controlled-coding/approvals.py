"""FNXC:OfflineFinal 2026-11-09-05:40:
Operator approvals live outside the sandbox. Bind verbatim question/answer bytes
to session/task/preregistration/time, authenticate records, and recompute directly
before native submission. Test approvers are confined to marked paths and rejected
by live submission. This module never starts a planning interview.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time
from contract import canonical


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


class Approvals:
    def __init__(self, root, *, test_double=False):
        self.root=Path(root);self.test_double=test_double
        self.root.mkdir(parents=True,exist_ok=True);self.root.chmod(0o700)
        if not test_double and (self.root/'.offline-test').exists():raise ValueError('test_path_rejected_by_live')
        if test_double and not (self.root/'.offline-test').is_file():raise ValueError('test_paths_required')
        key=self.root/'approval-authentication-key'
        if not key.exists():
            fd=os.open(key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(secrets.token_bytes(32));stream.flush();os.fsync(stream.fileno())
        if key.is_symlink() or key.stat().st_mode & 0o077:raise ValueError('unsafe_approval_key')
        self.key=key.read_bytes()

    def persist_question(self, question, session_id, task_id, preregistration_hash):
        if not isinstance(question,str) or not question:raise ValueError('verbatim_question_required')
        record={'question':question,'question_hash':digest(question),'session_id':session_id,'task_id':task_id,'preregistration_hash':preregistration_hash,'timestamp':time.time(),'test_double':self.test_double}
        name=digest(canonical(record).decode())+'.question.json'
        with (self.root/name).open('x') as stream:json.dump(record,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        return name

    def _record(self, question_name, answer, command, channel):
        question=json.loads((self.root/question_name).read_text())
        if question['test_double']!=self.test_double:raise ValueError('approval_context_mismatch')
        if digest(question['question'])!=question['question_hash']:raise ValueError('question_edited')
        if command!='APPROVE '+digest(answer):raise ValueError('explicit_approval_required')
        record=dict(question,answer=answer,answer_hash=digest(answer),approval_command=command,channel_marker=channel,approved_at=time.time())
        record['authentication']=hmac.new(self.key,canonical(record),'sha256').hexdigest()
        name=hashlib.sha256(canonical(record)).hexdigest()+'.approval.json'
        with (self.root/name).open('x') as stream:json.dump(record,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        return name

    def test_approve(self, question_name, answer):
        if not self.test_double:raise ValueError('test_approver_disabled')
        return self._record(question_name,answer,'APPROVE '+digest(answer),'TEST_APPROVER_NOT_HUMAN')

    def approve_from_tty(self, question_name, answer):
        if self.test_double:raise ValueError('test_approval_not_live')
        with open('/dev/tty','r+') as tty:
            if not os.isatty(tty.fileno()):raise ValueError('operator_tty_required')
            tty.write((self.root/question_name).read_text()+'\nVERBATIM ANSWER (JSON-escaped):\n'+json.dumps(answer)+'\nType exactly APPROVE '+digest(answer)+'\n');tty.flush()
            command=tty.readline().rstrip('\n')
        return self._record(question_name,answer,command,'OPERATOR_TTY_V1')

    def submit(self, approval_name, *, question, session_id, task_id, preregistration_hash, native_submit, allow_test=False):
        if allow_test and not self.test_double:raise ValueError('test_mode_unavailable_in_live')
        record=json.loads((self.root/approval_name).read_text())
        authentication=record.pop('authentication',None)
        if not authentication or not hmac.compare_digest(authentication,hmac.new(self.key,canonical(record),'sha256').hexdigest()):raise ValueError('approval_edited')
        if record['test_double'] and not (self.test_double and allow_test):raise ValueError('test_approval_rejected_by_live')
        marker='TEST_APPROVER_NOT_HUMAN' if self.test_double else 'OPERATOR_TTY_V1'
        if record.get('channel_marker')!=marker:raise ValueError('approval_channel_missing')
        expected=(digest(question),session_id,task_id,preregistration_hash)
        actual=tuple(record[k] for k in ('question_hash','session_id','task_id','preregistration_hash'))
        if actual!=expected or record['question']!=question:raise ValueError('approval_binding_mismatch')
        if record['approved_at']<record['timestamp'] or record['approved_at']>time.time()+1:raise ValueError('approval_timestamp_invalid')
        # FNXC:OfflineFinal 2026-11-09-05:40: Last check is adjacent to submit.
        if digest(record['answer'])!=record['answer_hash'] or record['approval_command']!='APPROVE '+digest(record['answer']):raise ValueError('answer_changed')
        with (self.root/(approval_name+'.submitted')).open('x') as intent:
            intent.write(record['answer_hash']);intent.flush();os.fsync(intent.fileno())
        return native_submit(record['answer'])
