"""Reproduce discarded second-response causes without paid transport or secrets."""
import json
import unittest
from unittest.mock import patch

from contract import canonical
import test_live
from real_transport import RealTransport
from gateway import safe_failure_code


class GatewayFailureTests(unittest.TestCase):
    setUp = test_live.LiveTests.setUp
    openssl = test_live.LiveTests.openssl
    sign = test_live.LiveTests.sign
    ledger = test_live.LiveTests.ledger
    gateway = test_live.LiveTests.gateway
    request = test_live.LiveTests.request

    def response(self, finish='stop', prompt=1, output=1):
        return dict(model=self.contract.data['model'],
                    choices=[{'finish_reason': finish, 'message': {'role': 'assistant', 'content': 'SYNTHETIC_SECRET'}}],
                    usage={'prompt_tokens': prompt, 'completion_tokens': output, 'total_tokens': prompt+output})

    def second_failure(self, code, response, *, status=200, kind='application/json'):
        ledger = self.ledger()
        replies = iter([(200, 'application/json', canonical(self.response())), (status, kind, response)])
        contacts = []
        def transport(*args):
            contacts.append(1)
            return next(replies)
        gateway, abort = self.gateway(ledger, transport)
        self.assertEqual(gateway.handle(self.request())[0], 200)
        with self.assertRaisesRegex(Exception, code):
            gateway.handle(self.request())
        self.assertEqual(len(contacts), 2)
        self.assertEqual(gateway.failure_code, code)
        self.assertTrue(abort.is_set())
        failure = json.loads((self.root/'gateway/failure-0002.json').read_bytes())
        self.assertEqual(failure['code'], code)
        self.assertNotIn('SYNTHETIC_SECRET', json.dumps(failure))
        self.assertTrue((self.root/'gateway/result-0001.json').exists())
        self.assertFalse((self.root/'gateway/result-0002.json').exists())
        snapshot = ledger.snapshot()
        self.assertEqual(len(snapshot['reservations']), 2)
        self.assertEqual(snapshot['transitions'][-1]['state'], 'UNCERTAIN')
        self.assertEqual(snapshot['reserved_exposure_micro_usd'], sum(r['reserved_exposure_micro_usd'] for r in snapshot['reservations']))
        return failure

    def test_second_truncated_json_response_is_not_misreported_as_budget(self):
        self.second_failure('provider_output_truncated', canonical(self.response('length')))

    def test_second_truncated_stream_has_the_same_classification(self):
        raw = b'data: '+canonical(self.response('length'))+b'\n\ndata: [DONE]\n\n'
        self.second_failure('provider_output_truncated', raw, kind='text/event-stream')

    def test_second_http_error_preserves_only_numeric_status(self):
        failure = self.second_failure('provider_http_error', b'SYNTHETIC_SECRET', status=429)
        self.assertEqual(failure['http_status'], 429)

    def test_second_malformed_response_remains_rejected(self):
        self.second_failure('unsupported_response', b'SYNTHETIC_SECRET')

    def test_second_usage_bound_violation_is_not_an_output_limit_change(self):
        failure = self.second_failure('usage_exceeds_reserved_bound', canonical(self.response(output=17)))
        self.assertEqual(failure['output_token_upper_bound'], 16)
        self.assertEqual(failure['completion_tokens'], 17)

    def test_second_incomplete_stream_is_distinct_from_truncation(self):
        self.second_failure('incomplete_live_stream', b'data: '+canonical(self.response())+b'\n\n', kind='text/event-stream')

    def test_missing_usage_is_not_misreported_as_provider_http_failure(self):
        response = self.response(); response.pop('usage')
        self.second_failure('provider_usage_missing_or_ambiguous', canonical(response))

    def test_transport_exception_does_not_leak_arbitrary_text(self):
        ledger = self.ledger()
        def transport(*args):
            raise OSError('SYNTHETIC_SECRET')
        gateway, abort = self.gateway(ledger, transport)
        status, _, body = gateway.handle(self.request())
        self.assertEqual(status, 502)
        self.assertEqual(gateway.failure_code, 'provider_transport_failed')
        self.assertNotIn(b'SYNTHETIC_SECRET', body)
        self.assertIn(b'fusion_gateway_failure:provider_transport_failed', body)
        self.assertTrue(abort.is_set())

    def test_parent_authorization_failure_is_classified_before_worker_dispatch(self):
        transport = RealTransport.__new__(RealTransport)
        transport.config = {'live': True}
        with patch('real_transport.validate', side_effect=ValueError('SYNTHETIC_SECRET')), \
             patch('real_transport.subprocess.Popen') as spawn:
            with self.assertRaises(ValueError) as failure:
                transport('https://api.openai.com/v1/chat/completions', b'{}')
        spawn.assert_not_called()
        self.assertEqual(safe_failure_code(failure.exception), 'transport_authorization_failed')
