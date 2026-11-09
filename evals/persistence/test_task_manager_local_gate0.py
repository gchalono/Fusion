"""FNXC:TaskManagerOfflineValidation 2026-11-09-20:38:
The scoped local-only exception refuses dirty/different roots and is not live authorization."""
import unittest
from pathlib import Path
from task_manager_local_gate0 import verify

class LocalGateTests(unittest.TestCase):
 def test_modified_or_advanced_worktree_cannot_repass_original_gate(self):
  root=Path(__file__).resolve().parents[2]
  with self.assertRaisesRegex(RuntimeError,'clean_before_changes|head_matches_operator_checkpoint'):
   verify(root,'/workspace/tm-original-recovery.bundle')
 def test_live_preflight_remains_remote_backed(self):
  root=Path(__file__).resolve().parents[2]
  text=(root/'evals/controlled-coding/live_preflight.py').read_text()
  self.assertIn('persistence/preflight.sh',text);self.assertNotIn('task_manager_local_gate0',text)
