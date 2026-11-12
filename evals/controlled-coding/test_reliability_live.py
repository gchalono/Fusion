"""Fresh-run preparation and live adapter proof, with synthetic authority/TLS only."""
import hashlib
import json
import re
import sqlite3
import socket
import time
import unittest
from unittest.mock import patch

import live
from contract import canonical
from live_authorization import claim, paid_gate, verify_authority
from reliability_authorization import DESIGN, PREVIOUS_RUN, RUN, RUN3_RUN, TASK, implementation_binding
import reliability_operator
from offline_eval import start_stub
from real_transport import RealTransport
import test_followup
import test_live
from budget import AggregateBudget


class ReliabilityLiveTests(unittest.TestCase):
    setUp = test_live.LiveTests.setUp
    openssl = test_live.LiveTests.openssl
    sign = test_live.LiveTests.sign

    def prepare(self):
        now = time.time()
        self.aggregate = dict(self.aggregate, issued_at=now-7200, expires_at=now-3600)
        self.sign(self.args.aggregate_authorization, self.aggregate)
        ledger = test_followup.FollowupTests.prepare(self, amounts=[1770, 1908, 1908, 2323])
        root = dict(self.aggregate)
        previous = dict(root, nonce='historical_B_aggregate_001', issued_at=now-3599,
                        expires_at=now-100, renewal_version=1, renews_nonce=root['nonce'],
                        renews_sha256=hashlib.sha256(canonical(root)).hexdigest(),
                        predecessor_expires_at=root['expires_at'], renewal_run_id='merge-intervals:B',
                        budget_semantics='cumulative-existing-ledger')
        historical_run = dict(self.run, aggregate_nonce=previous['nonce'], issued_at=now-3599, expires_at=now-100)
        with patch('live_authorization.time.time', return_value=now-200):
            claim(ledger, historical_run, previous, previous_aggregate=root)
        ledger.control_run('coding', 'merge-intervals:B', 'start')
        for amount in [2000, 2000, 2206]:
            ident = ledger.reserve('coding', 'merge-intervals:B', amount, token_bounds=(1, 1))
            ledger.transition(ident, 'FORWARDED', 'synthetic')
            ledger.transition(ident, 'SETTLED', 'synthetic')
        ledger.control_run('coding', 'merge-intervals:B', 'COMPLETE')
        self.args.original_aggregate_authorization = self.args.aggregate_authorization
        self.args.previous_aggregate_authorization = self.root/'historical-B-aggregate.json'
        self.sign(self.args.previous_aggregate_authorization, previous)
        run3_aggregate = dict(root, nonce='historical_run3_aggregate_001', issued_at=now-99,
                              expires_at=now-80, reliability_version=1,
                              continues_nonce=previous['nonce'],
                              continues_sha256=hashlib.sha256(canonical(previous)).hexdigest(),
                              renewal_run_id=RUN3_RUN, budget_semantics='cumulative-existing-ledger')
        self.args.run3_aggregate_authorization = self.root/'historical-run3-aggregate.json'
        self.sign(self.args.run3_aggregate_authorization, run3_aggregate)
        run3 = dict(self.run, nonce='historical_run3_run_001', issued_at=now-99,
                    expires_at=now-80, aggregate_nonce=run3_aggregate['nonce'], run_id=RUN3_RUN,
                    task_id=TASK, experiment_design=DESIGN, reliability_authorized=True,
                    historical_phase2n_arm=False, predecessor_run_id='merge-intervals:B',
                    implementation_sha256='e'*64,
                    fixture_sha256=live.fixture_binding(TASK)['derived_fixture_sha256'])
        self.args.run3_run_authorization = self.root/'historical-run3-run.json'
        self.sign(self.args.run3_run_authorization, run3)
        ledger.control_run('coding', RUN3_RUN, 'start')
        for amount, final in ((1853, 'SETTLED'), (2405, 'UNCERTAIN')):
            ident = ledger.reserve('coding', RUN3_RUN, amount, token_bounds=(1, 1))
            ledger.transition(ident, 'FORWARDED', 'synthetic-history')
            ledger.transition(ident, final, 'synthetic-history')
        ledger.control_run('coding', RUN3_RUN, 'INCOMPLETE')
        run4_aggregate = dict(root, nonce='historical_run4_aggregate_001', issued_at=now-79,
                              expires_at=now-50, reliability_version=2,
                              continues_nonce=run3_aggregate['nonce'],
                              continues_sha256=hashlib.sha256(canonical(run3_aggregate)).hexdigest(),
                              predecessor_run_nonce=run3['nonce'],
                              predecessor_run_sha256=hashlib.sha256(canonical(run3)).hexdigest(),
                              renewal_run_id=PREVIOUS_RUN, budget_semantics='cumulative-existing-ledger')
        self.args.previous_reliability_aggregate_authorization = self.root/'historical-run4-aggregate.json'
        self.sign(self.args.previous_reliability_aggregate_authorization, run4_aggregate)
        run4 = dict(self.run, nonce='historical_run4_run_001', issued_at=now-79,
                    expires_at=now-50, aggregate_nonce=run4_aggregate['nonce'], run_id=PREVIOUS_RUN,
                    task_id=TASK, experiment_design=DESIGN, reliability_authorized=True,
                    historical_phase2n_arm=False, predecessor_run_id=RUN3_RUN,
                    implementation_sha256='f'*64, fixture_sha256=live.fixture_binding(TASK)['derived_fixture_sha256'])
        self.args.previous_run_authorization = self.root/'historical-run4-run.json'
        self.sign(self.args.previous_run_authorization, run4)
        with ledger.connect() as db:
            db.execute('INSERT INTO live_authority VALUES (?,?,?,?)',
                       ('aggregate-reliability', run3_aggregate['nonce'], hashlib.sha256(canonical(run3_aggregate)).hexdigest(),
                        'aggregate-reliability:'+previous['nonce']))
            db.execute('INSERT INTO live_authority VALUES (?,?,?,?)',
                       ('run', run3['nonce'], hashlib.sha256(canonical(run3)).hexdigest(), RUN3_RUN))
        ledger.control_run('coding', PREVIOUS_RUN, 'start')
        ledger.control_run('coding', PREVIOUS_RUN, 'INCOMPLETE')
        with ledger.connect() as db:
            db.execute('INSERT INTO live_authority VALUES (?,?,?,?)',
                       ('aggregate-reliability-continuation', run4_aggregate['nonce'], hashlib.sha256(canonical(run4_aggregate)).hexdigest(),
                        'aggregate-reliability-continuation:'+run3_aggregate['nonce']))
            db.execute('INSERT INTO live_authority VALUES (?,?,?,?)',
                       ('run', run4['nonce'], hashlib.sha256(canonical(run4)).hexdigest(), PREVIOUS_RUN))
        self.aggregate = dict(root, nonce='reliability_aggregate_003', issued_at=now-1,
                              expires_at=now+900, reliability_version=3,
                              continues_nonce=run4_aggregate['nonce'],
                              continues_sha256=hashlib.sha256(canonical(run4_aggregate)).hexdigest(),
                              predecessor_run_nonce=run4['nonce'],
                              predecessor_run_sha256=hashlib.sha256(canonical(run4)).hexdigest(),
                              renewal_run_id=RUN, budget_semantics='cumulative-existing-ledger')
        self.binding = live.fixture_binding(TASK)
        self.run = dict(self.run, nonce='reliability_run_nonce_001', issued_at=now-1, expires_at=now+900,
                        aggregate_nonce=self.aggregate['nonce'], run_id=RUN, task_id=TASK,
                        experiment_design=DESIGN, reliability_authorized=True,
                        historical_phase2n_arm=False, predecessor_run_id=PREVIOUS_RUN,
                        implementation_sha256=implementation_binding()['sha256'],
                        fixture_sha256=self.binding['derived_fixture_sha256'])
        self.args.run = RUN
        self.args.task = TASK
        self.args.followup = False
        self.args.reliability = True
        self.args.aggregate_authorization = self.root/'new-aggregate.json'
        self.args.authorization = self.root/'new-run.json'
        self.sign(self.args.aggregate_authorization, self.aggregate)
        self.sign(self.args.authorization, self.run)
        self.config = live.configuration(self.args)
        return ledger

    def test_preflight_retains_all_exposure_and_has_no_side_effects(self):
        ledger = self.prepare()
        before = self.args.ledger.read_bytes()
        authorities = {p: p.read_bytes() for p in (self.args.authorization, self.args.aggregate_authorization,
                        self.args.original_aggregate_authorization, self.args.previous_aggregate_authorization,
                        self.args.run3_aggregate_authorization, self.args.run3_run_authorization,
                        self.args.previous_reliability_aggregate_authorization, self.args.previous_run_authorization)}
        original = type(self.key).read_bytes
        def no_credential(path):
            if path == self.key:
                raise AssertionError('credential read')
            return original(path)
        with patch.object(type(self.key), 'read_bytes', no_credential), \
             patch.object(live, 'RealTransport', side_effect=AssertionError('transport')), \
             patch.object(live, 'claim', side_effect=AssertionError('claim')):
            result = live.execute(self.args, preflight=True)
        self.assertEqual(result['classification'], 'RELIABILITY_PREFLIGHT_VERIFIED_NO_EXECUTION')
        self.assertEqual(result['run'], RUN)
        self.assertEqual(result['retained_reserved_micro_usd'], 18373)
        self.assertEqual(result['implementation_sha256'], implementation_binding()['sha256'])
        self.assertEqual(self.args.ledger.read_bytes(), before)
        self.assertFalse(self.args.output.exists())
        self.assertEqual({p: p.read_bytes() for p in authorities}, authorities)
        with ledger.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM run_controls WHERE run=?", (PREVIOUS_RUN,)).fetchone(), ('INCOMPLETE',))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM reservations WHERE run=?", (PREVIOUS_RUN,)).fetchone()[0], 0)

    def test_signed_design_task_implementation_and_scope_are_required(self):
        self.prepare()
        for change in ({'run_id':'merge-intervals:B'}, {'task_id':'merge-intervals'},
                       {'fixture_sha256':'0'*64}, {'implementation_sha256':'0'*64},
                       {'reliability_authorized':False}, {'experiment_design':'objective-only'},
                       {'historical_phase2n_arm':True}, {'predecessor_run_id':'merge-intervals:B'},
                       {'authorized_spend_usd':'0.24'}, {'max_requests':5}, {'max_seconds':301}):
            with self.subTest(change=change):
                self.sign(self.args.authorization, dict(self.run, **change))
                with self.assertRaises(ValueError): verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, self.run)
        for change in ({'reliability':False}, {'followup':True}, {'run_id':'parse-duration:D'}):
            with self.assertRaises(ValueError): verify_authority(dict(self.config, **change), self.contract)
        self.sign(self.args.authorization, dict(self.run, run_id=PREVIOUS_RUN))
        with self.assertRaisesRegex(ValueError, 'limits_or_evidence'):
            verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, self.run)

    def test_authority_chain_cannot_change_budget_root_or_predecessor(self):
        self.prepare()
        for change in ({'authorized_spend_usd':'4.00'}, {'continues_sha256':'0'*64},
                       {'continues_nonce':'unrelated_nonce_0001'}, {'renewal_run_id':'stable-toposort:A'},
                       {'budget_semantics':'additional-allocation'}, {'reliability_version':True},
                       {'ledger_path':str(self.root/'replacement.db')}, {'nonce':self.original_run['nonce']}):
            with self.subTest(change=change):
                aggregate = dict(self.aggregate, **change)
                self.sign(self.args.aggregate_authorization, aggregate)
                self.sign(self.args.authorization, dict(self.run, aggregate_nonce=aggregate['nonce']))
                with self.assertRaises(ValueError): verify_authority(self.config, self.contract)

    def test_run3_run4_approvals_and_receipts_are_all_required(self):
        ledger = self.prepare()
        run4_path = self.args.previous_reliability_aggregate_authorization
        original = run4_path.read_bytes()
        envelope = json.loads(original)
        envelope['payload']['expires_at'] -= 1
        run4_path.write_bytes(canonical(envelope))
        with self.assertRaisesRegex(ValueError, 'signature_invalid'):
            verify_authority(self.config, self.contract)
        run4_path.write_bytes(original)
        with ledger.connect() as db:
            db.execute("INSERT INTO live_authority VALUES (?,?,?,?)",
                       ('aggregate-reliability-continuation', 'forked_run4_nonce_001', '0'*64, 'forked-run4-receipt'))
        with self.assertRaisesRegex(ValueError, 'continuation_fork_or_replay'):
            live.execute(self.args, preflight=True)

    def test_history_must_be_settled_complete_and_budget_available(self):
        ledger = self.prepare()
        with ledger.connect() as db:
            db.execute("UPDATE run_controls SET status='INCOMPLETE' WHERE run='merge-intervals:B'")
        with self.assertRaisesRegex(ValueError, 'historical_runs'): live.execute(self.args, preflight=True)
        with ledger.connect() as db:
            db.execute("UPDATE run_controls SET status='COMPLETE' WHERE run='merge-intervals:B'")
            db.execute("INSERT INTO reservations(stage,run,upper_micro) VALUES ('planning','synthetic-extra',1900000)")
        before = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'insufficient_remaining_budget'): live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_expiry_missing_ledger_and_changed_history_fail_closed(self):
        self.prepare()
        before = self.args.ledger.read_bytes()
        self.sign(self.args.authorization, dict(self.run, expires_at=time.time()+100))
        with self.assertRaisesRegex(ValueError, 'expires_before_deadline'): live.execute(self.args, preflight=True)
        self.sign(self.args.authorization, self.run)
        envelope = json.loads(self.args.previous_aggregate_authorization.read_text())
        envelope['payload']['expires_at'] -= 1
        self.args.previous_aggregate_authorization.write_bytes(canonical(envelope))
        with self.assertRaisesRegex(ValueError, 'signature_invalid'): verify_authority(self.config, self.contract)
        self.assertEqual(self.args.ledger.read_bytes(), before)
        self.args.ledger = self.root/'absent.db'
        with self.assertRaises(ValueError): live.execute(self.args, preflight=True)
        self.assertFalse(self.args.ledger.exists())

    def test_operator_commands_are_separate_and_signing_requires_terminal(self):
        self.prepare()
        import argparse
        args = argparse.Namespace(authority_dir=self.root, output=self.root/'new-output')
        before = self.args.ledger.read_bytes()
        with patch('sys.stdin.isatty', return_value=False), patch.object(reliability_operator, 'signed_document') as read:
            with self.assertRaisesRegex(ValueError, 'private_operator_terminal'):
                reliability_operator.sign(args)
            read.assert_not_called()
        preflight = reliability_operator.command(args, '--reliability-preflight')
        launch = reliability_operator.command(args, '--arm-live')
        self.assertIn('--reliability-preflight', preflight)
        self.assertNotIn('--arm-live', preflight)
        self.assertIn('--arm-live', launch)
        self.assertIn('--reliability', launch)
        self.assertIn(RUN, preflight)
        self.assertIn(str(self.root/'experiment.db'), preflight)
        self.assertIn(str(self.root/'aggregate.json'), preflight)
        self.assertTrue(any('aggregate-self-test-004.json' in item for item in preflight))
        self.assertTrue(any('run-self-test-004.json' in item for item in preflight))
        self.assertTrue(any('aggregate-self-test-003.json' in item for item in preflight))
        self.assertTrue(any('run-self-test-003.json' in item for item in preflight))
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_transport_accepts_and_preserves_reliability_continuation_context(self):
        self.prepare()
        with patch('real_transport.validate', return_value=(self.contract, 'https://api.openai.com/v1/chat/completions')):
            transport = RealTransport(**self.config)
        self.assertEqual(transport.config['previous_reliability_aggregate_authorization_file'],
                         self.config['previous_reliability_aggregate_authorization_file'])
        self.assertEqual(transport.config['previous_run_authorization_file'],
                         self.config['previous_run_authorization_file'])
        self.assertEqual(transport.config['run3_reliability_aggregate_authorization_file'],
                         self.config['run3_reliability_aggregate_authorization_file'])
        self.assertEqual(transport.config['run3_run_authorization_file'],
                         self.config['run3_run_authorization_file'])
        transport.abort()

    def test_transport_setup_type_error_gets_safe_durable_stage_record(self):
        self.prepare()
        secret_marker = 'SYNTHETIC_SECRET_EXCEPTION_TEXT'
        with patch.object(live, 'RealTransport', side_effect=TypeError(secret_marker)):
            with self.assertRaisesRegex(TypeError, secret_marker):
                live.execute(self.args)
        diagnostic_path = self.args.output/'failure-diagnostic.json'
        diagnostic = json.loads(diagnostic_path.read_text())
        self.assertEqual(diagnostic, {
            'classification':'LIVE_FAILURE_DIAGNOSTIC', 'run':RUN,
            'failure_stage':'transport_setup', 'failure_code':'transport_setup_type_error',
            'exception_family':'type_error', 'termination_record_written':False})
        self.assertNotIn(secret_marker, diagnostic_path.read_text())
        self.assertFalse((self.args.output/'termination.json').exists())
        self.assertFalse((self.args.output/'gateway.sock').exists())
        with sqlite3.connect(self.args.ledger.resolve().as_uri()+'?mode=ro', uri=True) as db:
            db.execute('PRAGMA query_only=ON')
            self.assertEqual(db.execute("SELECT status FROM run_controls WHERE stage='coding' AND run=?", (RUN,)).fetchone(), ('INCOMPLETE',))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM reservations WHERE stage='coding' AND run=?", (RUN,)).fetchone()[0], 0)

    def test_failure_diagnostic_survives_socket_cleanup(self):
        self.prepare()
        class StubTransport:
            def abort(self): self.aborted = True
        transport = StubTransport()
        with patch.object(live, 'RealTransport', return_value=transport), \
             patch.object(live, 'run_command', side_effect=RuntimeError('SYNTHETIC_SECRET_EXECUTION_TEXT')):
            with self.assertRaisesRegex(RuntimeError, 'SYNTHETIC_SECRET_EXECUTION_TEXT'):
                live.execute(self.args)
        diagnostic_path = self.args.output/'failure-diagnostic.json'
        diagnostic = json.loads(diagnostic_path.read_text())
        self.assertEqual(diagnostic['failure_stage'], 'agent_execution')
        self.assertEqual(diagnostic['failure_code'], 'agent_execution_other_error')
        self.assertFalse(diagnostic['termination_record_written'])
        self.assertNotIn('SYNTHETIC_SECRET_EXECUTION_TEXT', diagnostic_path.read_text())
        self.assertTrue(transport.aborted)
        self.assertTrue((self.args.output/'gateway.sock').exists())
        with socket.socket(socket.AF_UNIX) as client:
            self.assertNotEqual(client.connect_ex(str(self.args.output/'gateway.sock')), 0)

    def test_success_exit_without_live_self_test_evidence_never_grades(self):
        self.prepare()
        report = dict(exit_code=0, timed_out=False, aborted=False, elapsed_seconds=0.01,
                      stdout=b'candidate submitted without self-test audit\n', stderr=b'')
        with patch.object(live, 'RealTransport'), patch.object(live, 'run_command', return_value=report), \
             patch.object(live, 'evaluate_patch') as grader:
            with self.assertRaisesRegex(ValueError, 'live_audit_required'):
                live.execute(self.args)
        grader.assert_not_called()
        self.assertFalse((self.args.output/'live-observation.json').exists())

    def test_claim_rollback_replay_fork_and_dispatch_binding(self):
        ledger = self.prepare()
        before = self.args.ledger.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):
            claim(ledger, dict(self.run, nonce=self.original_run['nonce']), self.aggregate, reliability_config=self.config)
        self.assertEqual(self.args.ledger.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'unclaimed_reliability'): paid_gate(self.config, self.contract)
        claim(ledger, self.run, self.aggregate, reliability_config=self.config)
        with self.assertRaisesRegex(ValueError, 'run_already_used'): live.execute(self.args, preflight=True)
        with self.assertRaises(sqlite3.IntegrityError): claim(ledger, self.run, self.aggregate, reliability_config=self.config)
        ledger.control_run('coding', RUN, 'start')
        ident = ledger.reserve('coding', RUN, 1000, token_bounds=(1, 1))
        ledger.transition(ident, 'FORWARDED', 'synthetic')
        self.assertEqual(paid_gate(self.config, self.contract), self.run)
        with patch('reliability_authorization.implementation_binding', return_value={'sha256':'changed'}):
            with self.assertRaisesRegex(ValueError, 'implementation'): paid_gate(self.config, self.contract)
        aggregate = dict(self.aggregate, nonce='forked_reliability_nonce_001')
        self.sign(self.args.aggregate_authorization, aggregate)
        self.sign(self.args.authorization, dict(self.run, aggregate_nonce=aggregate['nonce']))
        with self.assertRaisesRegex(ValueError, 'fork_or_replay'): verify_authority(self.config, self.contract)

    def test_actual_live_adapter_repairs_using_four_local_tls_requests(self):
        ledger = self.prepare()
        prior = ledger.snapshot()['reservations']
        stub = self.root/'synthetic-upstream'
        stub.mkdir(); (stub/'.offline-test').touch()
        server, contacts = start_stub(stub, 'repair', task=TASK)
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        transport = RealTransport(test_mode=True, test_root=stub,
                    test_url=f'https://localhost:{server.server_port}/v1/chat/completions',
                    test_ca=stub/'tls.crt', test_key_file=stub/'upstream-key')
        class LocalOnly:
            def __init__(inner, live_transport):
                inner.live_transport = live_transport
                inner.timeout = 60
            def __call__(inner, url, raw):
                paid_gate(self.config, self.contract)
                transport.timeout = inner.timeout
                return transport(url, raw)
            def abort(inner):
                inner.live_transport.abort()
                transport.abort()
        def local_only_factory(**config):
            # Exercise the real live constructor/authority validation, but route
            # inference through the separate local-TLS-only transport below.
            return LocalOnly(RealTransport(**config))
        attempted_bounds = []
        reserve = AggregateBudget.reserve
        def observed_reserve(instance, stage, run, amount, **kwargs):
            if run == RUN: attempted_bounds.append(kwargs.get('token_bounds'))
            return reserve(instance, stage, run, amount, **kwargs)
        with patch.object(live, 'RealTransport', side_effect=local_only_factory), \
             patch.object(AggregateBudget, 'reserve', observed_reserve):
            try:
                result = live.execute(self.args)
            except RuntimeError:
                # This directory contains only disposable synthetic test state.
                diagnostic = (self.args.output/'agent-stderr.txt').read_text()
                diagnostic = re.sub(r'[0-9a-f]{32,}', '[redacted]', diagnostic)
                with ledger.connect() as db:
                    bounds = db.execute('SELECT input_upper,output_upper FROM request_bounds b JOIN reservations r ON r.id=b.reservation_id WHERE r.run=?', (RUN,)).fetchall()
                self.fail(diagnostic[-4000:] + '\n' + (self.args.output/'termination.json').read_text() + '\n' + repr(contacts) + '\n' + repr(bounds) + '\n' + repr(attempted_bounds))
        self.assertEqual(len(contacts), 4)
        self.assertEqual(result['local_self_test'], {'localSelfTest':'passed', 'repairs':1})
        self.assertTrue(result['independent_acceptance']['success'])
        self.assertEqual(result['ledger']['reservations'][:len(prior)], prior)
        self.assertLessEqual(result['ledger']['reserved_exposure_micro_usd'], 2000000)
        self.assertEqual(result['implementation_sha256'], implementation_binding()['sha256'])
        audit = (self.args.output/'agent-stdout.txt').read_text()
        self.assertIn('LIVE_AGENT_AUDIT ', audit)
        # The mounted live adapter, Pi tools, local Python tests and independent
        # grader are real. Only the paid transport is replaced by local TLS.
        self.assertEqual(json.loads((self.args.output/'termination.json').read_text())['gateway_attempts'], 4)
