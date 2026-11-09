"""FNXC:OfflineFinal 2026-11-09-05:40: Synthetic approvals never become human approvals."""
import json
from pathlib import Path
import tempfile
import unittest
from approvals import Approvals

class ApprovalTests(unittest.TestCase):
    def test_bound_test_approval_and_live_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.offline-test').touch();a=Approvals(root,test_double=True)
            q=a.persist_question('TEST DOUBLE QUESTION','session','merge-intervals','a'*64)
            record=a.test_approve(q,'{"answer":"TEST DOUBLE"}');calls=[]
            a.submit(record,question='TEST DOUBLE QUESTION',session_id='session',task_id='merge-intervals',preregistration_hash='a'*64,native_submit=calls.append,allow_test=True)
            self.assertEqual(calls,['{"answer":"TEST DOUBLE"}'])
            with self.assertRaises(ValueError):a.submit(record,question='TEST DOUBLE QUESTION',session_id='session',task_id='merge-intervals',preregistration_hash='a'*64,native_submit=calls.append)
            with self.assertRaises(ValueError):Approvals(root)

    def test_edited_and_ambiguous_records_never_submit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.offline-test').touch();a=Approvals(root,test_double=True)
            q=a.persist_question('question','s','t','p');record=a.test_approve(q,'answer');calls=[]
            with self.assertRaises(ValueError):a._record(q,'answer','yes','TEST_APPROVER_NOT_HUMAN')
            for field in ('answer','question_hash','session_id','task_id','preregistration_hash','channel_marker','test_double'):
                original=(root/record).read_text();changed=json.loads(original);changed[field]='edited';(root/record).write_text(json.dumps(changed))
                with self.assertRaises(ValueError):a.submit(record,question='question',session_id='s',task_id='t',preregistration_hash='p',native_submit=calls.append,allow_test=True)
                (root/record).write_text(original)
            with self.assertRaises(ValueError):a.submit(record,question='different',session_id='s',task_id='t',preregistration_hash='p',native_submit=calls.append,allow_test=True)
            self.assertEqual(calls,[])
