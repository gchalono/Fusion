import json
import tempfile
import unittest
import re
from pathlib import Path
from gateway import Blocked
from rate_limit import reserve_start
from snapshots import database_diff, filesystem_diff, process_diff
from offline_runner import tree


class SnapshotTests(unittest.TestCase):
    def test_native_runner_has_no_execution_entrypoints(self):
        source = Path(__file__).with_name('native-runner.mts').read_text()
        bridge=Path(__file__).parent.parent/'controlled-coding/planning-approval-bridge.mts'
        bridge_source=bridge.read_text()
        # FNXC:BlockerResolution 2026-11-09-18:27: Submission moved behind the
        # approval bridge; retain the exact native API allowlist across both.
        calls = set(re.findall(r'native\.([A-Za-z]+)\(', source))
        self.assertIn('submitApprovedNativeAnswer(context',source)
        self.assertRegex(bridge_source,r'await submitMissionInterviewResponse\(')
        calls |= {'submitMissionInterviewResponse'}
        self.assertEqual(calls, {'setAiSessionStore', 'getMissionInterviewSession',
            'createMissionInterviewSession', 'submitMissionInterviewResponse', 'getMissionInterviewSummary'})
        for symbol in ('createMission', 'activateSlice', 'startAutopilot', 'executeHeartbeat', 'createTask'):
            self.assertIsNone(re.search(r'\b' + symbol + r'\s*\(', source+bridge_source))
        paths = re.findall(r'\$\{source\}(/packages/[^`]+)', source)
        self.assertEqual(set(paths), {'/packages/core/src/index.ts',
            '/packages/dashboard/src/mission-interview.ts', '/packages/dashboard/src/ai-session-store.ts',
            '/packages/engine/src/mcp/mcp-resolution.ts'})
    def test_tree_captures_empty_directories_modes_and_symlinks(self):
        with tempfile.TemporaryDirectory(prefix='fusion-offline-tree-') as d:
            root = Path(d)
            (root/'empty').mkdir()
            (root/'file').write_text('offline')
            (root/'link').symlink_to('file')
            state = tree(root)
            self.assertTrue(state['empty']['directory'])
            self.assertIn('mode', state['file'])
            self.assertEqual(state['link']['symlink'], 'file')
            self.assertEqual(len(state['file']['sha256']), 64)
    def test_row_mutation_detected_even_when_counts_match(self):
        before = {'counts': {'project.tasks': 1, 'project.ai_sessions': 0},
                  'row_hashes': {'project.tasks': 'a', 'project.ai_sessions': 'x'}}
        after = {'counts': {'project.tasks': 1, 'project.ai_sessions': 1},
                 'row_hashes': {'project.tasks': 'b', 'project.ai_sessions': 'y'}}
        diff = database_diff(before, after)
        self.assertEqual(diff['forbidden'], ['project.tasks'])

    def test_new_agent_or_mission_table_detected(self):
        b = {'counts': {}, 'row_hashes': {}}
        a = {'counts': {'central.agents': 1}, 'row_hashes': {'central.agents': 'x'}}
        self.assertEqual(database_diff(b, a)['forbidden'], ['central.agents'])

    def test_filesystem_detects_unapproved_path(self):
        diff = filesystem_diff({}, {'results/log': {}, 'project/source.ts': {}})
        self.assertEqual(diff['unexpected'], ['project/source.ts'])

    def test_durable_process_detected(self):
        before = ['PID PPID COMMAND', '1 0 python']
        after = before + ['2 1 postgres', '3 1 node', '4 1 ps']
        self.assertEqual(process_diff(before, after)['unexpected'], {'3': 'node'})

    def test_start_limit_survives_new_reader_and_identifier_fixed(self):
        with tempfile.TemporaryDirectory(prefix='fusion-offline-rate-') as d:
            p = Path(d) / 'ledger.json'
            for _ in range(5): reserve_start(p, now=1000)
            with self.assertRaisesRegex(Blocked, 'native_start_self_limit'):
                reserve_start(p, now=1001)
            self.assertEqual(len(json.loads(p.read_text())), 5)
            reserve_start(p, now=4601)
            entries = json.loads(p.read_text())
            self.assertEqual(len({e['identifier'] for e in entries}), 1)


class StricterRateTests(unittest.TestCase):
    def test_new_cap_preserves_old_starts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json'
            for _ in range(4): reserve_start(p,now=1000)
            before=p.read_bytes()
            with self.assertRaisesRegex(Blocked,'native_start_self_limit'):
                reserve_start(p,now=1001,max_starts=3)
            self.assertEqual(p.read_bytes(),before)
            reserve_start(p,now=4601,max_starts=3)

    def test_cannot_raise_native_cap(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(Blocked,'invalid_native_start_cap'):
                reserve_start(Path(d)/'ledger.json',max_starts=6)
