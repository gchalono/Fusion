"""Local relay and disconnect regressions; no inference or real time waits."""
import io
import json
from email.message import Message
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from isolation import Relay, inference_socket


class InferenceBridgeTests(unittest.TestCase):
    def test_failure_reply_uses_only_safe_code_not_exception_text(self):
        for cause, expected in (('provider_output_truncated', 'provider_output_truncated'),
                                ('SYNTHETIC_SECRET', 'gateway_failure')):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as tmp:
                gateway = MagicMock()
                gateway.policy.output_ceiling = 512
                gateway.failure_code = None
                gateway.handle.side_effect = ValueError(cause)
                server = inference_socket(Path(tmp)/'inference.sock', gateway, 'synthetic-token')
                try:
                    handler = server.RequestHandlerClass.__new__(server.RequestHandlerClass)
                    handler.path = '/v1/chat/completions'
                    handler.headers = Message()
                    raw = b'{"model":"synthetic","messages":[]}'
                    for name, value in (('Host', 'local'), ('Authorization', 'Bearer synthetic-token'),
                                        ('Content-Length', str(len(raw)))):
                        handler.headers[name] = value
                    handler.rfile = io.BytesIO(raw)
                    handler.wfile = io.BytesIO()
                    handler.send_response = MagicMock()
                    handler.send_header = MagicMock()
                    handler.end_headers = MagicMock()
                    handler.do_POST()
                    handler.send_response.assert_called_once_with(403)
                    reply = handler.wfile.getvalue()
                    self.assertEqual(json.loads(reply)['error']['code'], expected)
                    self.assertIn(('fusion_gateway_failure:'+expected).encode(), reply)
                    self.assertNotIn(b'SYNTHETIC_SECRET', reply)
                finally:
                    server.server_close()

    def test_idle_bridge_preserves_later_bytes_in_both_directions(self):
        for direction in ('request', 'response'):
            with self.subTest(direction=direction):
                client = MagicMock()
                upstream = MagicMock()
                source, target = (client, upstream) if direction == 'request' else (upstream, client)
                source.recv.side_effect = [b'late synthetic bytes', b'']
                handler = Relay.__new__(Relay)
                handler.request = client
                with patch('isolation.socket.socket') as socket, \
                     patch('isolation.select.select', side_effect=[([], [], []),
                           ([source], [], []), ([source], [], [])]) as select:
                    socket.return_value.__enter__.return_value = upstream
                    handler.handle()
                target.sendall.assert_called_once_with(b'late synthetic bytes')
                # The outer process/transport deadlines own waiting; idle is not EOF.
                self.assertTrue(all(len(call.args) == 3 for call in select.call_args_list))

    def test_disconnected_client_during_headers_or_body_never_retries(self):
        for stage in ('headers', 'body'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                gateway = MagicMock()
                gateway.policy.output_ceiling = 512
                gateway.handle.return_value = (200, 'application/json', b'{}')
                server = inference_socket(Path(tmp)/'inference.sock', gateway, 'synthetic-token')
                try:
                    handler = server.RequestHandlerClass.__new__(server.RequestHandlerClass)
                    handler.path = '/v1/chat/completions'
                    handler.headers = Message()
                    raw = b'{"model":"synthetic","messages":[{"role":"user","content":"test"}]}'
                    for name, value in (('Host', 'local'), ('Authorization', 'Bearer synthetic-token'),
                                        ('Content-Length', str(len(raw)))):
                        handler.headers[name] = value
                    handler.rfile = io.BytesIO(raw)
                    handler.wfile = MagicMock()
                    handler.send_response = MagicMock()
                    handler.send_header = MagicMock()
                    handler.end_headers = MagicMock()
                    if stage == 'headers':
                        handler.end_headers.side_effect = BrokenPipeError()
                    else:
                        handler.wfile.write.side_effect = ConnectionResetError()
                    handler.do_POST()
                    gateway.handle.assert_called_once()
                finally:
                    server.server_close()
