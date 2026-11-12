"""Renewal abuse controls using disposable signatures and a synthetic ledger only."""
import hashlib
import json
import sqlite3
import time
import unittest
from unittest.mock import patch

import live
import test_followup
import test_live
from contract import canonical
from live_authorization import claim, paid_gate, signed_document, verify_authority
from offline_eval import start_stub
from real_transport import RealTransport


class AggregateRenewalTests(unittest.TestCase):
    setUp = test_live.LiveTests.setUp
    openssl = test_live.LiveTests.openssl
    sign = test_live.LiveTests.sign

    def prepare(self):
        now = time.time()
        self.aggregate = dict(self.aggregate, issued_at=now-3600, expires_at=now-5)
        self.sign(self.args.aggregate_authorization, self.aggregate)
        ledger = test_followup.FollowupTests.prepare(self, amounts=[1770, 1908, 1908, 2323])
        self.previous = dict(self.aggregate)
        self.args.previous_aggregate_authorization = self.args.aggregate_authorization
        self.aggregate = dict(self.previous, issued_at=now-1, expires_at=now+900,
                              nonce='aggregate_renewal_nonce_001', renewal_version=1,
                              renews_nonce=self.previous['nonce'],
                              renews_sha256=hashlib.sha256(canonical(self.previous)).hexdigest(),
                              predecessor_expires_at=self.previous['expires_at'],
                              renewal_run_id='merge-intervals:B', budget_semantics='cumulative-existing-ledger')
        self.args.aggregate_authorization = self.root/'aggregate-renewed.json'
        self.run = dict(self.run, aggregate_nonce=self.aggregate['nonce'])
        self.sign(self.args.aggregate_authorization, self.aggregate)
        self.sign(self.args.authorization, self.run)
        self.config = live.configuration(self.args)
        return ledger

    def test_expired_predecessor_is_evidence_never_active_authority(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'context_or_time'):
            signed_document(self.args.previous_aggregate_authorization, self.public)
        self.assertEqual(signed_document(self.args.previous_aggregate_authorization, self.public,
                                        expired_predecessor=True), self.previous)
        with self.assertRaisesRegex(ValueError, 'context_or_time'):
            signed_document(self.args.aggregate_authorization, self.public, expired_predecessor=True)
        with self.assertRaisesRegex(ValueError, 'requires_B_predecessor'):
            verify_authority(dict(self.config, previous_aggregate_authorization_file=None), self.contract)

    def test_preflight_is_read_only_and_carries_all_7909_micro_usd(self):
        ledger = self.prepare()
        before = self.args.ledger.read_bytes()
        previous_bytes = self.args.previous_aggregate_authorization.read_bytes()
        with patch.object(live, 'RealTransport', side_effect=AssertionError('transport')), \
             patch.object(live, 'claim', side_effect=AssertionError('consumption')):
            result = live.execute(self.args, preflight=True)
        self.assertTrue(result['aggregate_renewal'])
        self.assertEqual(result['retained_reserved_micro_usd'], 7909)
        self.assertEqual(self.args.ledger.read_bytes(), before)
        self.assertEqual(self.args.previous_aggregate_authorization.read_bytes(), previous_bytes)
        self.assertFalse(self.args.output.exists())
        with ledger.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM live_authority').fetchone()[0], 2)

    def test_overlap_wrong_link_cap_contract_scope_and_semantics_are_rejected(self):
        self.prepare()
        for change in ({'issued_at': self.previous['expires_at']-1},
                       {'renews_sha256': '0'*64}, {'renews_nonce': 'unrelated_nonce_001'},
                       {'predecessor_expires_at': 1}, {'authorized_spend_usd': '4.00'},
                       {'contract_sha256': '0'*64}, {'ledger_path': str(self.root/'replacement.db')},
                       {'renewal_run_id': 'merge-intervals:A'}, {'renewal_version': True},
                       {'budget_semantics': 'additional-2-dollars'}, {'accept_no_provider_hard_cap': False}):
            with self.subTest(change=change):
                self.sign(self.args.aggregate_authorization, dict(self.aggregate, **change))
                with self.assertRaises(ValueError):
                    verify_authority(self.config, self.contract)

    def test_changed_predecessor_or_signature_cannot_replace_original_receipt(self):
        self.prepare()
        changed = dict(self.previous, nonce='different_original_nonce_001')
        self.sign(self.args.previous_aggregate_authorization, changed)
        renewed = dict(self.aggregate, renews_nonce=changed['nonce'],
                       renews_sha256=hashlib.sha256(canonical(changed)).hexdigest())
        self.sign(self.args.aggregate_authorization, renewed)
        with self.assertRaisesRegex(ValueError, 'original_aggregate'):
            verify_authority(self.config, self.contract)
        envelope = json.loads(self.args.previous_aggregate_authorization.read_bytes())
        envelope['payload']['expires_at'] -= 1
        self.args.previous_aggregate_authorization.write_bytes(canonical(envelope))
        with self.assertRaisesRegex(ValueError, 'signature_invalid'):
            verify_authority(self.config, self.contract)

    def test_new_signing_key_cannot_continue_original_signed_authority(self):
        self.prepare()
        other_key = self.root/'synthetic-other-key'
        other_public = self.root/'synthetic-other.pub'
        self.openssl('genpkey', '-algorithm', 'ED25519', '-out', str(other_key))
        self.openssl('pkey', '-in', str(other_key), '-pubout', '-out', str(other_public))
        other_public.chmod(0o600)
        self.signing = other_key
        self.sign(self.args.aggregate_authorization, self.aggregate)
        self.sign(self.args.authorization, self.run)
        before = self.args.ledger.read_bytes()
        # New documents verify with the substituted key, but the untouched
        # original predecessor cannot: the chain must use one trust anchor.
        with self.assertRaisesRegex(ValueError, 'signature_invalid'):
            verify_authority(dict(self.config, operator_public_key=str(other_public)), self.contract)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_nonce_collisions_and_A_replay_are_refused(self):
        self.prepare()
        renewal = dict(self.aggregate, nonce=self.original_run['nonce'])
        self.sign(self.args.aggregate_authorization, renewal)
        self.sign(self.args.authorization, dict(self.run, aggregate_nonce=renewal['nonce']))
        with self.assertRaisesRegex(ValueError, 'nonce_already_used'):
            verify_authority(self.config, self.contract)
        self.sign(self.args.aggregate_authorization, self.aggregate)
        self.sign(self.args.authorization, dict(self.run, nonce=self.aggregate['nonce']))
        with self.assertRaisesRegex(ValueError, 'nonce_collision'):
            verify_authority(self.config, self.contract)
        self.sign(self.args.authorization, dict(self.run, run_id='merge-intervals:A'))
        with self.assertRaisesRegex(ValueError, 'requires_B_predecessor'):
            verify_authority(dict(self.config, run_id='merge-intervals:A'), self.contract)

    def test_atomic_claim_rollback_and_fork_replay_protection(self):
        ledger = self.prepare()
        before = self.args.ledger.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):
            claim(ledger, dict(self.run, nonce=self.original_run['nonce']), self.aggregate,
                  previous_aggregate=self.previous)
        self.assertEqual(self.args.ledger.read_bytes(), before)
        claim(ledger, self.run, self.aggregate, previous_aggregate=self.previous)
        after = self.args.ledger.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):
            claim(ledger, self.run, self.aggregate, previous_aggregate=self.previous)
        self.assertEqual(self.args.ledger.read_bytes(), after)
        fork = dict(self.aggregate, nonce='forked_aggregate_nonce_001')
        self.sign(self.args.aggregate_authorization, fork)
        self.sign(self.args.authorization, dict(self.run, aggregate_nonce=fork['nonce']))
        with self.assertRaisesRegex(ValueError, 'fork_or_replay'):
            verify_authority(self.config, self.contract)
        self.assertEqual(self.args.ledger.read_bytes(), after)

    def test_renewal_does_not_restore_spent_budget(self):
        ledger = self.prepare()
        with ledger.connect() as db:
            db.execute("INSERT INTO reservations(stage,run,upper_micro) VALUES ('planning','prior-synthetic',1990000)")
        before = self.args.ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'insufficient_remaining_budget'):
            live.execute(self.args, preflight=True)
        self.assertEqual(self.args.ledger.read_bytes(), before)

    def test_current_expiry_and_scope_are_rechecked_at_dispatch(self):
        ledger = self.prepare()
        with self.assertRaisesRegex(ValueError, 'unclaimed_aggregate_renewal'):
            paid_gate(self.config, self.contract)
        claim(ledger, self.run, self.aggregate, previous_aggregate=self.previous)
        ledger.control_run('coding', self.args.run, 'start')
        ident = ledger.reserve('coding', self.args.run, 1000, token_bounds=(1, 1))
        ledger.transition(ident, 'FORWARDED', 'synthetic')
        self.assertEqual(paid_gate(self.config, self.contract), self.run)
        self.sign(self.args.aggregate_authorization, dict(self.aggregate, expires_at=time.time()-1))
        with self.assertRaisesRegex(ValueError, 'context_or_time'):
            paid_gate(self.config, self.contract)
        with self.assertRaisesRegex(ValueError, 'context_or_time'):
            RealTransport(**self.config)

    def test_renewed_B_local_tls_execution_preserves_original_rows(self):
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
        self.assertTrue(result['independent_acceptance']['success'])
        self.assertEqual(len(contacts), 3)
        self.assertEqual(ledger.snapshot()['reservations'][:4], prior)
        with ledger.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM run_controls WHERE run='merge-intervals:A'").fetchone(), ('INCOMPLETE',))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM live_authority WHERE kind='aggregate'").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM live_authority WHERE kind='aggregate-renewal'").fetchone()[0], 1)
