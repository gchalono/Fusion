"""Offline live-path tests. All keys are disposable synthetic test material.

The full execution test substitutes only the paid transport with loopback TLS;
Pi coding tools and independent Bubblewrap grading remain real.
"""
import argparse
import json
import base64
import io
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from budget import AggregateBudget
from contract import Contract, canonical
from execution import run_command
import live
from live_authorization import claim, paid_gate, verify_authority
from offline_eval import start_stub
from real_transport import RealTransport
import real_transport


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='fusion-live-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.signing = self.root/'synthetic-signing-key'
        self.public = self.root/'operator.pub'
        self.openssl('genpkey', '-algorithm', 'ED25519', '-out', str(self.signing))
        self.openssl('pkey', '-in', str(self.signing), '-pubout', '-out', str(self.public))
        self.public.chmod(0o600)
        self.key = self.root/'synthetic-provider-key'
        self.key.write_text('SYNTHETIC-NOT-A-PROVIDER-CREDENTIAL'); self.key.chmod(0o600)
        self.contract = Contract()
        self.binding = live.fixture_binding('merge-intervals')
        common = dict(schema='fusion-live-v1', test_double=False, issued_at=time.time()-1,
                      expires_at=time.time()+600, contract_sha256=self.contract.sha256,
                      ledger_path=str(self.root/'ledger.db'))
        self.aggregate = dict(common, kind='aggregate-spending', nonce='aggregate_nonce_0001', authorized_spend_usd='2.00')
        self.run = dict(common, kind='coding-run', nonce='coding_run_nonce_001', aggregate_nonce=self.aggregate['nonce'],
                        authorized_spend_usd='0.12', run_id='merge-intervals:A', live_authorized=True,
                        model=self.contract.data['model'], approved_hosts=['api.openai.com'],
                        provider_side_cap_confirmed=False, accept_no_provider_hard_cap=True, model_availability_verified=True,
                        model_availability_evidence='SYNTHETIC OFFLINE TEST EVIDENCE', pricing_verified=True,
                        max_requests=4, max_seconds=300, key_file=str(self.key), task_id='merge-intervals',
                        fixture_sha256=self.binding['derived_fixture_sha256'])
        self.aggregate['accept_no_provider_hard_cap'] = True
        self.args = argparse.Namespace(arm_live=True, task='merge-intervals', run=self.run['run_id'],
                        runtime=Path.cwd(), output=self.root/'output', ledger=self.root/'ledger.db',
                        authorization=self.root/'run.json', aggregate_authorization=self.root/'aggregate.json',
                        operator_public_key=self.public, contract=Path(live.ROOT/'experiment-parameters.json'))
        self.sign(self.args.authorization, self.run)
        self.sign(self.args.aggregate_authorization, self.aggregate)
        self.config = live.configuration(self.args)

    def openssl(self, *args):
        subprocess.run(['openssl', *args], check=True, capture_output=True)

    def forbid_credential_read(self, path, *args, **kwargs):
        self.read_paths.append(path)
        if path == self.key:
            raise AssertionError('credential_read')
        return self.original_read_text(path, *args, **kwargs)

    def sign(self, path, payload):
        message = self.root/'synthetic-message'; signature = self.root/'synthetic-signature'
        message.write_bytes(canonical(payload))
        self.openssl('pkeyutl', '-sign', '-inkey', str(self.signing), '-rawin', '-in', str(message), '-out', str(signature))
        path.write_bytes(canonical(dict(payload=payload, signature=signature.read_bytes().hex())))
        path.chmod(0o600)

    def ledger(self):
        data = dict(self.contract.data, planning_run_ids=['merge-intervals'], coding_run_ids=['merge-intervals:A'], frozen_coding_token_limit=16000)
        ledger = AggregateBudget(self.args.ledger, experiment_contract=data)
        self.args.ledger.chmod(0o600)
        claim(ledger, self.run, self.aggregate)
        ledger.control_run('coding', self.run['run_id'], 'start')
        return ledger

    def test_no_provider_cap_requires_both_signed_acknowledgments(self):
        self.assertFalse(verify_authority(self.config, self.contract)[0]['provider_side_cap_confirmed'])
        for name, original in (('authorization', self.run), ('aggregate_authorization', self.aggregate)):
            for value in (None, False, 'true', 1, [], {}):
                with self.subTest(document=name, value=value):
                    changed = dict(original)
                    if value is None:
                        changed.pop('accept_no_provider_hard_cap')
                    else:
                        changed['accept_no_provider_hard_cap'] = value
                    self.sign(getattr(self.args, name), changed)
                    with self.assertRaisesRegex(ValueError, 'cap_acknowledgment'):
                        verify_authority(self.config, self.contract)
            self.sign(getattr(self.args, name), original)
        for value in (None, 'false', 0, True):
            changed = dict(self.run, provider_side_cap_confirmed=value)
            if value is None:
                changed.pop('provider_side_cap_confirmed')
            self.sign(self.args.authorization, changed)
            with self.assertRaisesRegex(ValueError, 'provider_cap_authority'):
                verify_authority(self.config, self.contract)

    def test_confirmed_provider_cap_remains_supported_without_contradiction(self):
        run = dict(self.run, provider_side_cap_confirmed=True)
        aggregate = dict(self.aggregate)
        for document in (run, aggregate):
            document.pop('accept_no_provider_hard_cap')
        self.sign(self.args.authorization, run)
        self.sign(self.args.aggregate_authorization, aggregate)
        self.assertTrue(verify_authority(self.config, self.contract)[0]['provider_side_cap_confirmed'])
        for name, document in (('authorization', run), ('aggregate_authorization', aggregate)):
            self.sign(getattr(self.args, name), dict(document, accept_no_provider_hard_cap=True))
            with self.assertRaisesRegex(ValueError, 'contradictory'):
                verify_authority(self.config, self.contract)
            self.sign(getattr(self.args, name), document)

    def test_changed_cap_acknowledgment_is_rejected_at_every_dispatch_boundary(self):
        transport = RealTransport(**self.config)
        ledger = self.ledger()
        ident = ledger.reserve('coding', self.args.run, 100, token_bounds=(10, 10))
        ledger.transition(ident, 'FORWARDED', 'synthetic')
        self.assertEqual(paid_gate(self.config, self.contract), self.run)
        envelope = json.loads(self.args.authorization.read_text())
        envelope['payload']['accept_no_provider_hard_cap'] = False
        self.args.authorization.write_bytes(canonical(envelope))
        with self.assertRaisesRegex(ValueError, 'signature_invalid'):
            verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, dict(self.run, accept_no_provider_hard_cap=False))
        for check in (lambda: RealTransport(**self.config),
                      lambda: transport('https://api.openai.com/v1/chat/completions', b'{}'),
                      lambda: paid_gate(self.config, self.contract)):
            with self.assertRaisesRegex(ValueError, 'cap_acknowledgment'):
                check()
        request = canonical({'config': self.config, 'parent_pid': os.getppid(),
                             'raw': base64.b64encode(b'{}').decode()})
        output = io.StringIO()
        self.original_read_text = Path.read_text
        self.read_paths = []
        with patch.object(real_transport.ctypes, 'CDLL') as library, \
             patch.object(real_transport.sys, 'stdin', type('Input', (), {'buffer': io.BytesIO(request)})()), \
             patch.object(real_transport.sys, 'stdout', output), \
             patch.object(Path, 'read_text', lambda path, *a, **kw: self.forbid_credential_read(path, *a, **kw)), \
             patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')) as network, \
             patch('live_authorization.verify_authority', wraps=verify_authority) as verified:
            library.return_value.prctl.return_value = 0
            real_transport.worker()
        network.assert_not_called()
        verified.assert_called_once()
        self.assertNotIn(self.key, self.read_paths)
        self.assertEqual(json.loads(output.getvalue()), {'error': 'transport_failure',
                                                       'code': 'transport_authorization_failed'})
        self.sign(self.args.authorization, dict(self.run, provider_side_cap_confirmed=True,
                                                accept_no_provider_hard_cap=False))
        aggregate = dict(self.aggregate, accept_no_provider_hard_cap=False)
        self.sign(self.args.aggregate_authorization, aggregate)
        with self.assertRaisesRegex(ValueError, 'unclaimed_aggregate'):
            paid_gate(self.config, self.contract)

    def test_preflight_is_read_only_and_does_not_consume_authority(self):
        self.args.arm_live = False
        self.original_read_text = Path.read_text
        self.read_paths = []
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        with patch.object(live, 'RealTransport', side_effect=AssertionError('dispatch')), \
             patch.object(live, 'claim', side_effect=AssertionError('claim')), \
             patch.object(Path, 'read_text', lambda path, *a, **kw: self.forbid_credential_read(path, *a, **kw)):
            result = live.execute(self.args, preflight=True)
        self.assertEqual(result['classification'], 'PREFLIGHT_VERIFIED_NO_EXECUTION')
        self.assertFalse(result['provider_hard_cap_confirmed'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})
        self.assertFalse(self.args.ledger.exists())
        self.assertFalse(self.args.output.exists())
        self.assertNotIn(self.key, self.read_paths)
        self.sign(self.args.authorization, dict(self.run, accept_no_provider_hard_cap=False))
        with self.assertRaisesRegex(ValueError, 'cap_acknowledgment'):
            live.execute(self.args, preflight=True)
        self.assertFalse(self.args.ledger.exists())
        self.assertFalse(self.args.output.exists())
        self.sign(self.args.authorization, self.run)
        self.ledger()
        ledger_bytes = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'ledger_already_exists'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), ledger_bytes)

    def test_each_frozen_task_has_its_own_binding(self):
        default = live.fixture_binding()
        hashes = set()
        for task in default['canonical_order']:
            with self.subTest(task=task):
                binding = live.fixture_binding(task)
                self.assertEqual(binding['task_id'], task)
                self.assertTrue(binding['stored_file_sha256'])
                self.assertTrue(all(path.startswith('fixtures/'+task+'/')
                                    for path in binding['stored_file_sha256']))
                self.assertEqual(binding['canonical_order'], default['canonical_order'])
                self.assertEqual(binding['frozen_manifest_sha256'], default['frozen_manifest_sha256'])
                hashes.add(binding['derived_fixture_sha256'])
        self.assertEqual(len(hashes), len(default['canonical_order']))
        self.assertEqual(default, live.fixture_binding(default['task_id']))
        with self.assertRaisesRegex(ValueError, 'unknown_frozen_task'):
            live.fixture_binding('unknown')

    def test_signed_authority_reservation_and_durable_replay(self):
        self.assertEqual(verify_authority(self.config, self.contract)[0], self.run)
        ledger = self.ledger()
        with self.assertRaises(ValueError):
            paid_gate(self.config, self.contract)
        ident = ledger.reserve('coding', self.args.run, 100, token_bounds=(10, 10))
        ledger.transition(ident, 'FORWARDED', 'test-only')
        self.assertEqual(paid_gate(self.config, self.contract), self.run)
        with self.assertRaises(sqlite3.IntegrityError):
            claim(AggregateBudget(self.args.ledger), self.run, self.aggregate)
        ledger.transition(ident, 'UNCERTAIN', 'test-only')
        with self.assertRaises(ValueError):
            paid_gate(self.config, self.contract)

    def test_missing_tampered_ambiguous_expired_and_wrong_binding(self):
        original = self.args.authorization.read_bytes()
        self.args.authorization.rename(self.root/'saved-approval')
        with self.assertRaises((OSError, ValueError)):
            verify_authority(self.config, self.contract)
        self.args.authorization.write_bytes(original); self.args.authorization.chmod(0o600)
        for change in ({'run_id': 'parse-duration:A'}, {'expires_at': 1}, {'authorized_spend_usd': '1.00'},
                       {'test_double': True}, {'aggregate_nonce': 'other'}, {'max_requests': 5},
                       {'max_seconds': 301}, {'pricing_verified': False}, {'key_file': str(self.root/'missing')}):
            with self.subTest(change=change):
                self.sign(self.args.authorization, dict(self.run, **change))
                with self.assertRaises((OSError, ValueError)):
                    verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, self.run)
        envelope = json.loads(self.args.authorization.read_text())
        envelope['payload']['live_authorized'] = False
        self.args.authorization.write_bytes(canonical(envelope))
        with self.assertRaisesRegex(ValueError, 'signature_invalid'):
            verify_authority(self.config, self.contract)
        self.args.authorization.write_bytes(original.replace(b'"payload":', b'"payload":{},"payload":', 1))
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            verify_authority(self.config, self.contract)

    def test_aggregate_requires_separate_signature_and_binding(self):
        for change in ({'authorized_spend_usd': '3.00'}, {'ledger_path': str(self.root/'other.db')}, {'kind': 'coding-run'}):
            with self.subTest(change=change):
                self.sign(self.args.aggregate_authorization, dict(self.aggregate, **change))
                with self.assertRaises(ValueError):
                    verify_authority(self.config, self.contract)

    def test_transport_constructor_refuses_unsigned_or_unarmed(self):
        with self.assertRaises(ValueError):
            RealTransport()
        self.args.authorization.write_text('{}')
        with self.assertRaises(ValueError):
            RealTransport(**self.config)
        self.args.arm_live = False
        with self.assertRaisesRegex(ValueError, 'explicit_arm'):
            live.execute(self.args)

    def gateway(self, ledger, transport):
        root = self.root/'gateway'; root.mkdir()
        abort = threading.Event()
        gateway = live.build_gateway(root, self.contract, ledger, self.args.run, transport, 'synthetic-local-token', abort)
        return gateway, abort

    def request(self):
        return canonical(dict(model=self.contract.data['model'], messages=[dict(role='user', content='SYNTHETIC')], max_tokens=16))

    def test_per_run_cap_prevents_transport(self):
        ledger = self.ledger()
        ledger.reserve('coding', self.args.run, 119999, token_bounds=(1, 1))
        calls = []
        gateway, abort = self.gateway(ledger, lambda *args: calls.append(args))
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertFalse(calls); self.assertTrue(abort.is_set())

    def test_aggregate_cap_prevents_transport(self):
        # Existing charged exposure is retained when the live contract is attached.
        seed = AggregateBudget(self.args.ledger)
        seed.reserve('planning', 'prior-authorized-run', 1999999)
        ledger = self.ledger()
        calls = []
        gateway, abort = self.gateway(ledger, lambda *args: calls.append(args))
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertFalse(calls); self.assertTrue(abort.is_set())

    def test_request_cap_and_deadline(self):
        ledger = self.ledger()
        for _ in range(4):
            ledger.reserve('coding', self.args.run, 100, token_bounds=(1, 1))
        with self.assertRaises(ValueError):
            ledger.reserve('coding', self.args.run, 100, token_bounds=(1, 1))
        with ledger.connect() as db:
            db.execute('UPDATE run_controls SET deadline=?', (time.time()-1,))
        with self.assertRaises(ValueError):
            ledger.remaining_seconds('coding', self.args.run)

    def test_transport_failure_is_terminal_and_exposure_retained(self):
        ledger = self.ledger()
        class Failure:
            def __call__(self, *args):
                raise OSError('synthetic transport failure')
        gateway, abort = self.gateway(ledger, Failure())
        gateway.handle(self.request())
        self.assertTrue(abort.is_set())
        snapshot = ledger.snapshot()
        self.assertGreater(snapshot['reserved_exposure_micro_usd'], 0)
        self.assertEqual(snapshot['transitions'][-1]['state'], 'UNCERTAIN')
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertEqual(len(ledger.snapshot()['reservations']), 1)

    def test_fifth_request_is_reported_without_another_provider_dispatch(self):
        ledger = self.ledger()
        calls = []
        def transport(*args):
            calls.append(1)
            response = dict(model=self.contract.data['model'],
                            choices=[{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'synthetic'}}],
                            usage={'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2})
            return 200, 'application/json', canonical(response)
        gateway, abort = self.gateway(ledger, transport)
        for _ in range(4):
            self.assertEqual(gateway.handle(self.request())[0], 200)
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertEqual(gateway.failure_code, 'call_cap')
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertEqual(gateway.failure_code, 'call_cap')
        self.assertTrue(abort.is_set())
        self.assertEqual(len(calls), 4)
        snapshot = ledger.snapshot()
        self.assertEqual(len(snapshot['reservations']), 4)
        self.assertEqual([t['state'] for t in snapshot['transitions']][-1], 'SETTLED')

    def test_missing_usage_is_terminal(self):
        ledger = self.ledger()
        class MissingUsage:
            def __call__(inner, *args):
                return 200, 'application/json', canonical(dict(model=self.contract.data['model'], choices=[]))
        gateway, abort = self.gateway(ledger, MissingUsage())
        with self.assertRaises(Exception):
            gateway.handle(self.request())
        self.assertTrue(abort.is_set())
        self.assertEqual(ledger.snapshot()['transitions'][-1]['state'], 'UNCERTAIN')

    def test_network_namespace_blocks_host_loopback_and_hides_controls(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen()
            workspace = self.root/'probe'; workspace.mkdir()
            script = """import socket, pathlib, os
assert not pathlib.Path('/trusted').exists()
assert not pathlib.Path('/run/admin.sock').exists()
assert not pathlib.Path('/run/local-token').exists()
assert os.getuid() == 65534
assert 'NoNewPrivs:\\t1' in pathlib.Path('/proc/self/status').read_text()
try:
 socket.create_connection(('127.0.0.1', PORT), timeout=.2)
except OSError:
 print('HOST_NETWORK_BLOCKED')
else:
 raise AssertionError('host network reachable')
""".replace('PORT', str(listener.getsockname()[1]))
            report = run_command(None, workspace, ['/usr/bin/python3', '-B', '-c', script], timeout=5)
            self.assertEqual(report['exit_code'], 0, report['stderr'])
            self.assertIn(b'HOST_NETWORK_BLOCKED', report['stdout'])

    def test_coding_then_independent_grading_through_local_tls(self):
        stub = self.root/'synthetic-upstream'; stub.mkdir(); (stub/'.offline-test').touch()
        server, contacts = start_stub(stub)
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        transport = RealTransport(test_mode=True, test_root=stub,
                    test_url=f'https://localhost:{server.server_port}/v1/chat/completions',
                    test_ca=stub/'tls.crt', test_key_file=stub/'upstream-key')
        # Preserve signature verification and durable paid_gate checks while
        # replacing only the final HTTPS destination with a local synthetic stub.
        class LocalOnly:
            timeout = 60
            def __call__(inner, url, raw):
                paid_gate(self.config, self.contract)
                transport.timeout = inner.timeout
                return transport(url, raw)
            def abort(inner):
                transport.abort()
        reports = []
        def record_command(*args, **kwargs):
            report = run_command(*args, **kwargs)
            reports.append(report)
            return report
        with patch.object(live, 'RealTransport', return_value=LocalOnly()) as factory, patch.object(live, 'run_command', side_effect=record_command):
            try:
                result = live.execute(self.args)
            except RuntimeError:
                self.fail('local-only execution failed: '+repr(reports))
        factory.assert_called_once_with(**self.config)
        self.assertTrue(result['independent_acceptance']['success'], result)
        self.assertEqual(len(contacts), 3)
        self.assertTrue(all(x['state'] == 'SETTLED' for x in result['ledger']['transitions'] if x['state'] in ('SETTLED', 'UNCERTAIN')))
        self.assertLessEqual(result['ledger']['reserved_exposure_micro_usd'], 120000)
        self.assertTrue(all(b'compat.js/utils/transcript' not in report['stderr'] for report in reports))
        termination = json.loads((self.args.output/'termination.json').read_bytes())
        self.assertEqual(termination['exit_code'], 0)
        self.assertFalse(termination['timed_out'])
        self.assertFalse(termination['gateway_aborted'])
        self.assertEqual(termination['gateway_attempts'], 3)
        with patch.object(live, 'RealTransport') as refused:
            self.args.output = self.root/'second-output'
            with self.assertRaises(sqlite3.IntegrityError):
                live.execute(self.args)
            refused.assert_not_called()

    def test_failed_process_records_termination_without_claiming_a_grade(self):
        report = dict(exit_code=1, timed_out=False, aborted=False, elapsed_seconds=2.5,
                      stdout=b'', stderr=b'SYNTHETIC agent failure')
        with patch.object(live, 'RealTransport'), patch.object(live, 'run_command', return_value=report), \
             patch.object(live, 'evaluate_patch') as grade:
            with self.assertRaisesRegex(RuntimeError, 'live_agent_failed_or_aborted'):
                live.execute(self.args)
        grade.assert_not_called()
        termination = json.loads((self.args.output/'termination.json').read_bytes())
        self.assertEqual(termination['exit_code'], 1)
        self.assertEqual(termination['elapsed_seconds'], 2.5)
        self.assertFalse(termination['timed_out'])
        self.assertFalse(termination['gateway_aborted'])
        self.assertEqual(termination['gateway_attempts'], 0)
        self.assertNotIn('stdout', termination)
        self.assertNotIn('stderr', termination)
        self.assertFalse((self.args.output/'live-observation.json').exists())
        with AggregateBudget(self.args.ledger).connect() as db:
            self.assertEqual(db.execute('SELECT status FROM run_controls').fetchone()[0], 'INCOMPLETE')


if __name__ == '__main__':
    unittest.main()
