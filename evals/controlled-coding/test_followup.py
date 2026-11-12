"""Synthetic B authority and existing-ledger checks. Never use operator material."""
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

import live
from budget import AggregateBudget
from contract import Contract, canonical
from live_authorization import FOLLOWUP_DESIGN, claim, paid_gate, verify_authority
from offline_eval import start_stub
from real_transport import RealTransport
import test_live


class FollowupTests(unittest.TestCase):
    setUp = test_live.LiveTests.setUp
    openssl = test_live.LiveTests.openssl
    sign = test_live.LiveTests.sign

    def prepare(self, amounts=None):
        binding = self.binding
        data = dict(self.contract.data, planning_run_ids=binding['canonical_order'],
                    coding_run_ids=[t+':'+a for t in binding['canonical_order'] for a in 'ABC'],
                    frozen_coding_token_limit=16000,
                    fixture_manifest_sha256=binding['frozen_manifest_sha256'])
        ledger = AggregateBudget(self.args.ledger, experiment_contract=data)
        self.args.ledger.chmod(0o600)
        claim(ledger, self.run, self.aggregate)
        ledger.control_run('coding', self.args.run, 'start')
        for amount in amounts or [1000]*4:
            ident = ledger.reserve('coding', self.args.run, amount, token_bounds=(1, 1))
            ledger.transition(ident, 'FORWARDED', 'synthetic')
            ledger.transition(ident, 'SETTLED', 'synthetic')
        ledger.control_run('coding', self.args.run, 'INCOMPLETE')
        self.original_run = dict(self.run)
        self.run = dict(self.run, run_id='merge-intervals:B', nonce='coding_run_nonce_002',
                        followup_authorized=True, experiment_design=FOLLOWUP_DESIGN,
                        historical_phase2n_arm=False, predecessor_run_id='merge-intervals:A')
        self.args.authorization = self.root/'run-B.json'
        self.args.run = self.run['run_id']
        self.args.followup = True
        self.sign(self.args.authorization, self.run)
        self.config = live.configuration(self.args)
        return ledger

    def test_followup_preflight_retains_every_byte_and_reservation(self):
        self.prepare()
        before = self.args.ledger.read_bytes()
        self.args.arm_live = False
        with patch.object(live, 'RealTransport', side_effect=AssertionError('transport')), \
             patch.object(live, 'claim', side_effect=AssertionError('authority consumption')):
            result = live.execute(self.args, preflight=True)
        self.assertEqual(result['classification'], 'FOLLOWUP_PREFLIGHT_VERIFIED_NO_EXECUTION')
        self.assertEqual(result['experiment_design'], FOLLOWUP_DESIGN)
        self.assertEqual(result['retained_reserved_micro_usd'], 4000)
        self.assertEqual(self.args.ledger.read_bytes(), before)
        self.assertFalse(self.args.output.exists())

    def test_signed_design_and_explicit_followup_are_required(self):
        self.prepare()
        for field, value in (('followup_authorized', False), ('experiment_design', 'phase2n-B'),
                             ('historical_phase2n_arm', True), ('predecessor_run_id', 'other')):
            self.sign(self.args.authorization, dict(self.run, **{field: value}))
            with self.assertRaisesRegex(ValueError, 'objective_only_followup'):
                verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, self.run)
        with self.assertRaisesRegex(ValueError, 'objective_only_followup'):
            verify_authority(dict(self.config, followup=False), self.contract)

    def test_followup_requires_authority_covering_the_run_deadline(self):
        import time
        self.prepare()
        self.sign(self.args.authorization, dict(self.run, expires_at=time.time()+60))
        before = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'expires_before_run_deadline'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_consumed_A_cannot_replay_or_use_followup_preflight(self):
        self.prepare()
        self.args.run = 'merge-intervals:A'
        self.args.followup = False
        self.sign(self.args.authorization, dict(self.original_run, nonce='new_but_replayed_A_001'))
        before = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'first_run_ledger_already_exists'):
            live.execute(self.args, preflight=True)
        with patch.object(live, 'RealTransport') as transport:
            with self.assertRaises(sqlite3.IntegrityError):
                live.execute(self.args)
        transport.assert_not_called()
        self.assertEqual(self.args.ledger.read_bytes(), before)
        self.args.followup = True
        with self.assertRaisesRegex(ValueError, 'unsupported_live_run_design'):
            live.execute(self.args, preflight=True)

    def test_B_consumption_nonce_and_prior_state_are_checked(self):
        ledger = self.prepare()
        self.sign(self.args.authorization, dict(self.run, nonce=self.original_run['nonce']))
        with self.assertRaisesRegex(ValueError, 'nonce_already_used'):
            live.execute(self.args, preflight=True)
        self.sign(self.args.authorization, self.run)
        claim(ledger, self.run, self.aggregate)
        before = self.args.ledger.read_bytes()
        self.args.output = self.root/'fresh-but-replayed-output'
        with self.assertRaisesRegex(ValueError, 'run_already_used'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_missing_ledger_and_changed_aggregate_cannot_bootstrap(self):
        self.prepare()
        missing = self.root/'rotated.db'
        self.args.ledger = missing
        run = dict(self.run, ledger_path=str(missing))
        aggregate = dict(self.aggregate, ledger_path=str(missing))
        self.sign(self.args.authorization, run)
        self.sign(self.args.aggregate_authorization, aggregate)
        with self.assertRaises(ValueError):
            live.execute(self.args, preflight=True)
        self.assertFalse(missing.exists())
        self.args.ledger = self.root/'ledger.db'
        self.sign(self.args.authorization, self.run)
        self.sign(self.args.aggregate_authorization, dict(self.aggregate, nonce='replacement_aggregate_001'))
        self.sign(self.args.authorization, dict(self.run, aggregate_nonce='replacement_aggregate_001'))
        with self.assertRaisesRegex(ValueError, 'original_aggregate'):
            live.execute(self.args, preflight=True)

    def test_changed_contract_and_insufficient_remaining_budget_are_refused(self):
        ledger = self.prepare()
        private_contract = self.root/'changed-contract.json'
        private_contract.write_bytes(canonical(dict(self.contract.data, pricing_verification_date='changed')))
        self.args.contract = private_contract
        changed = Contract(private_contract)
        self.sign(self.args.authorization, dict(self.run, contract_sha256=changed.sha256))
        self.sign(self.args.aggregate_authorization, dict(self.aggregate, contract_sha256=changed.sha256))
        with self.assertRaisesRegex(ValueError, 'immutable_contract_mismatch'):
            live.execute(self.args, preflight=True)
        self.args.contract = Path(live.ROOT/'experiment-parameters.json')
        self.sign(self.args.authorization, self.run)
        self.sign(self.args.aggregate_authorization, self.aggregate)
        with ledger.connect() as db:
            db.execute("INSERT INTO reservations(stage,run,upper_micro) VALUES ('coding','prior-synthetic-run',1000000)")
        before = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'insufficient_remaining_budget'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_followup_design_is_rechecked_at_dispatch(self):
        ledger = self.prepare()
        claim(ledger, self.run, self.aggregate)
        ledger.control_run('coding', self.args.run, 'start')
        ident = ledger.reserve('coding', self.args.run, 1000, token_bounds=(1, 1))
        ledger.transition(ident, 'FORWARDED', 'synthetic')
        self.assertEqual(paid_gate(self.config, self.contract), self.run)
        self.sign(self.args.authorization, dict(self.run, historical_phase2n_arm=True))
        with self.assertRaisesRegex(ValueError, 'objective_only_followup'):
            paid_gate(self.config, self.contract)
        with self.assertRaisesRegex(ValueError, 'objective_only_followup'):
            RealTransport(**self.config)

    def test_first_run_cli_cannot_be_repurposed_as_followup(self):
        import subprocess
        import sys
        self.prepare()
        before = self.args.ledger.read_bytes()
        command = [sys.executable, '-B', str(live.ROOT/'live.py'), '--preflight', '--followup',
                   '--task', 'merge-intervals', '--run', self.args.run]
        for name in ('runtime', 'output', 'ledger', 'authorization', 'aggregate_authorization', 'operator_public_key'):
            command += ['--'+name.replace('_', '-'), str(getattr(self.args, name))]
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'--preflight is first-run only', result.stderr)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_B_local_tls_execution_preserves_A_and_uses_original_objective(self):
        ledger = self.prepare()
        prior = ledger.snapshot()['reservations']
        stub = self.root/'synthetic-upstream'; stub.mkdir(); (stub/'.offline-test').touch()
        server, contacts = start_stub(stub)
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        transport = RealTransport(test_mode=True, test_root=stub,
                                  test_url=f'https://localhost:{server.server_port}/v1/chat/completions',
                                  test_ca=stub/'tls.crt', test_key_file=stub/'upstream-key')
        class LocalOnly:
            timeout = 60
            def __call__(inner, url, raw):
                paid_gate(self.config, self.contract)
                transport.timeout = inner.timeout
                return transport(url, raw)
            def abort(inner):
                transport.abort()
        with patch.object(live, 'RealTransport', return_value=LocalOnly()):
            result = live.execute(self.args)
        self.assertEqual(result['experiment_design'], FOLLOWUP_DESIGN)
        self.assertFalse(result['historical_phase2n_arm'])
        self.assertTrue(result['independent_acceptance']['success'])
        self.assertEqual(len(contacts), 3)
        self.assertEqual((self.args.output/'objective.txt').read_bytes(),
                         (live.ROOT/'fixtures/merge-intervals/objective.txt').read_bytes())
        self.assertEqual(ledger.snapshot()['reservations'][:4], prior)
        with ledger.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM run_controls WHERE run='merge-intervals:A'").fetchone(), ('INCOMPLETE',))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM live_authority WHERE kind='aggregate'").fetchone(), (1,))
        before = self.args.ledger.read_bytes()
        self.args.output = self.root/'fresh-but-replayed-output'
        with self.assertRaisesRegex(ValueError, 'run_already_used'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)
