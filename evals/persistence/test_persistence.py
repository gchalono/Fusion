"""FNXC:Persistence 2026-11-09-04:02: Exercise recovery failures and history scans
using disposable repositories and mocked fork reads; never make network writes.
"""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tooling
from scan import inspect, scan


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='fusion-persistence-test-')
        self.original=Path.cwd(); self.repo=Path(self.temp.name); os.chdir(self.repo)
        self.run_git('init','-q','--initial-branch=eval/test')
        self.run_git('config','user.name','Offline fixture')
        self.run_git('config','user.email','fixture@example.invalid')
        self.run_git('remote','add','origin',tooling.FORK)
        (self.repo/'evals').mkdir()
        for name in ('AGENTS.md','PROJECT_STATE.md','CHECKPOINTS.md'):
            (self.repo/'evals'/name).write_text('Offline fixture\n')
        (self.repo/'fixture.txt').write_text('baseline\n')
        (self.repo/'evals/artifact-manifest.json').write_text(json.dumps({'artifacts':[{
            'path':'fixture.txt','size_bytes':9,'sha256':hashlib.sha256(b'baseline\n').hexdigest(),
            'required_for_phase2n_persistence':True}]}))
        self.run_git('add','.'); self.run_git('commit','-qm','baseline')
        self.baseline=self.run_git('rev-parse','HEAD')

    def tearDown(self):
        os.chdir(self.original); self.temp.cleanup()

    def run_git(self,*args):
        return subprocess.check_output(['git',*args],text=True).strip()

    def test_clean_preflight_and_missing_phase2m_warning(self):
        with patch.object(tooling,'remote_tip',return_value=self.baseline):
            before=self.run_git('status','--porcelain')
            result=tooling.preflight(self.baseline,'eval/test')
            self.assertEqual(result['status'],'PREFLIGHT_VERIFIED')
            self.assertTrue(result['warnings'])
            self.assertEqual(self.run_git('status','--porcelain'),before)

    def test_stale_head_rejected(self):
        future=subprocess.check_output(['git','commit-tree','HEAD^{tree}','-p','HEAD'],input='future\n',text=True).strip()
        with patch.object(tooling,'remote_tip',return_value=future):
            result=tooling.preflight(future,'eval/test')
            self.assertIn('STALE_CHECKOUT',result['failures'])
            self.assertIn('BASELINE_NOT_VERIFIED',result['failures'])

    def test_remote_unverifiable(self):
        with patch.object(tooling,'remote_tip',side_effect=RuntimeError('no connection')):
            result=tooling.preflight(self.baseline,'eval/test')
            self.assertIn('REMOTE_BASELINE_UNVERIFIABLE',result['failures'])

    def test_dirty_and_corrupt_artifacts(self):
        (self.repo/'fixture.txt').write_text('corrupt')
        with patch.object(tooling,'remote_tip',return_value=self.baseline):
            result=tooling.preflight(self.baseline,'eval/test')
            self.assertIn('WORKTREE_NOT_CLEAN',result['failures'])
            self.assertIn('ARTIFACT_VERIFICATION_FAILED',result['failures'])

    def test_upstream_and_pushurl_rejected(self):
        self.run_git('remote','set-url','--push','origin','https://github.com/Runfusion/Fusion.git')
        with self.assertRaisesRegex(RuntimeError,'FORK_URL_UNVERIFIED'): tooling.verify_fork()

    def test_external_full_baseline_required(self):
        with self.assertRaisesRegex(ValueError,'FULL_EXTERNAL_BASELINE_REQUIRED'):
            tooling.baseline_ok(self.baseline[:9])

    def test_history_secret_not_hidden_by_later_removal(self):
        p=self.repo/'credential.txt'; p.write_text('sk-'+'x'*30)
        self.run_git('add','.'); self.run_git('commit','-qm','unsafe offline fixture')
        p.write_text('removed\n'); self.run_git('add','.'); self.run_git('commit','-qm','remove fixture')
        result=scan(self.baseline)
        self.assertEqual(result['status'],'SCAN_BLOCKED')
        self.assertEqual(result['findings'][0]['path'],'credential.txt')
        self.assertNotIn('x'*30,json.dumps(result))

    def test_staged_secret_not_hidden_by_worktree(self):
        p=self.repo/'credential.txt';p.write_text('sk-'+'y'*30);self.run_git('add','credential.txt')
        p.write_text('removed\n')
        self.assertEqual(scan(self.baseline)['status'],'SCAN_BLOCKED')

    def test_logs_require_reviewed_content_hash(self):
        path='evals/offline.log';raw=b'unit tests passed\n'
        self.assertTrue(inspect(path,raw,{}))
        approved={path:[hashlib.sha256(raw).hexdigest()]}
        self.assertFalse(inspect(path,raw,approved))
        self.assertTrue(inspect(path,raw+b'changed',approved))
