"""Offline doubles exercise gateway mechanics, never mission output."""
import ast
import concurrent.futures
import hashlib
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from gateway import Artifacts, Blocked, Gateway, Policy, HTTPSForwarder, canonical, offline_server


def config(**changes):
    value = dict(provider="offline-test-provider", model="offline-test-model", api_type="openai-chat-completions",
                 upstream_url="https://test.invalid/v1/chat/completions", approved_hosts=["test.invalid"],
                 physical_model_verified=True, token_bound_evidence_sha256="0" * 64,
                 max_model_calls=3, spend_ceiling_usd="1", input_price_per_million="3",
                 output_price_per_million="15", input_token_bound=1000, output_token_bound=100,
                 output_ceiling=None)
    return value | changes


def request(**changes):
    return canonical(dict(model="offline-test-model", messages=[{"role": "user", "content": "offline transport check"}]) | changes)


def response(model="offline-test-model"):
    # Deliberately no plan-shaped content, no mission vocabulary in the payload.
    return canonical({"model": model, "choices": [], "usage": {"prompt_tokens": 4, "completion_tokens": 2}})


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fusion-offline-gateway-")
        self.root = Path(self.tmp.name)
        (self.root / ".offline-test").touch()
        self.artifacts = Artifacts(self.root, offline=True)
        self.sent = []

    def tearDown(self):
        self.tmp.cleanup()

    def transport(self, url, raw):
        self.sent.append((url, json.loads(raw)))
        return 200, "application/json", response()

    def gateway(self, **changes):
        return Gateway(Policy.from_config(config(**changes)), self.artifacts, self.transport)

    def test_missing_invalid_authorization(self):
        for key in config():
            if key == "output_ceiling":
                continue
            c = config()
            del c[key]
            with self.subTest(key=key), self.assertRaises((Blocked, TypeError)):
                Policy.from_config(c)
        for value in [0, -1, True, "nan", "Infinity", None]:
            with self.subTest(price=value), self.assertRaises(Blocked):
                Policy.from_config(config(input_price_per_million=value))

    def test_bad_hosts_urls_and_virtual_model_rejected(self):
        for c in [config(upstream_url="http://test.invalid/v1/chat/completions"),
                  config(approved_hosts=["other.invalid"]), config(physical_model_verified=False),
                  config(upstream_url="https://user:pass@test.invalid/v1/chat/completions"),
                  config(upstream_url="https://test.invalid/v1/chat/completions?key=placeholder")]:
            with self.assertRaises(Blocked):
                Policy.from_config(c)

    def test_absent_optional_ceiling_preserves_request_and_response(self):
        g = self.gateway()
        body = request(max_completion_tokens=90)
        status, kind, raw = g.handle(body)
        self.assertEqual((status, kind, raw), (200, "application/json", response()))
        self.assertEqual(self.sent[0][1], json.loads(body))

    def test_ceiling_refuses_reduction_and_preserves_lower_native_limit(self):
        g = self.gateway(output_ceiling=50)
        with self.assertRaisesRegex(Blocked, "output_limit_intervention_forbidden"):
            g.handle(request(max_tokens=90))
        g.handle(request(max_completion_tokens=20))
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][1]["max_completion_tokens"], 20)

    def test_request_model_mismatch_no_forward(self):
        g = self.gateway()
        with self.assertRaisesRegex(Blocked, "model_mismatch"):
            g.handle(request(model="fallback"))
        self.assertEqual(self.sent, [])

    def test_response_model_mismatch_terminal_after_one_attempt(self):
        g = self.gateway()
        g.transport = lambda *_: (200, "application/json", response("fallback"))
        with self.assertRaises(Blocked):
            g.handle(request())
        with self.assertRaisesRegex(Blocked, "run_terminal"):
            g.handle(request())
        self.assertEqual(g.budget.calls, 1)

    def test_call_cap_counts_all_clients_retries_and_compaction(self):
        g = self.gateway()
        # Request origin labels cannot exempt any attempts from a shared budget.
        for origin in ["interview", "answerer", "compaction"]:
            g.handle(request(user=origin))
        with self.assertRaisesRegex(Blocked, "call_cap"):
            g.handle(request(user="native-retry"))
        self.assertEqual(len(self.sent), 3)

    def test_spend_reservation_never_refunds_even_low_reported_usage(self):
        g = self.gateway(spend_ceiling_usd="0.0045")
        g.handle(request())  # Full reservation: 1000 * $3/M + 100 * $15/M.
        self.assertEqual(g.budget.reserved, 4500)
        with self.assertRaisesRegex(Blocked, "spend_ceiling"):
            g.handle(request())
        self.assertEqual(len(self.sent), 1)

    def test_concurrency_cannot_overspend(self):
        g = self.gateway(max_model_calls=1)
        def call(_):
            try:
                g.handle(request())
                return True
            except Blocked:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(call, range(4))), 1)

    def test_no_proxy_retry_native_retry_keeps_separate_reservations(self):
        g = self.gateway()
        def failed(*_):
            self.sent.append("attempt")
            raise OSError("sensitive-upstream-detail")
        g.transport = failed
        self.assertEqual(g.handle(request())[0], 502)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(g.handle(request())[0], 502)
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(g.budget.calls, 2)
        self.assertGreater(g.budget.reserved, 0)
        self.assertTrue((self.root / "request-0001.json").exists())
        self.assertNotIn(b"sensitive-upstream-detail", b"".join(p.read_bytes() for p in self.root.iterdir()))

    def test_upstream_error_is_preserved_so_native_can_retry(self):
        g = self.gateway()
        raw = b'{"error":{"message":"temporarily unavailable"}}'
        g.transport = lambda *_: (503, "application/json", raw)
        self.assertEqual(g.handle(request()), (503, "application/json", raw))
        self.assertEqual(g.handle(request()), (503, "application/json", raw))
        self.assertEqual(g.budget.calls, 2)

    def test_secret_in_raw_refused_without_forwarding_or_mutation(self):
        self.artifacts = Artifacts(self.root, offline=True, secrets=["offline-sensitive-marker"])
        g = self.gateway()
        with self.assertRaisesRegex(Blocked, "forward_failed"):
            g.handle(request(messages=[{"role": "user", "content": "offline-sensitive-marker"}]))
        self.assertEqual(self.sent, [])
        self.assertNotIn(b"offline-sensitive-marker", b"".join(p.read_bytes() for p in self.root.iterdir()))

    def test_immutability_hash_and_restart_refusal(self):
        info = self.artifacts.write("raw.txt", b"unaltered")
        self.assertEqual(info["sha256"], hashlib.sha256(b"unaltered").hexdigest())
        with self.assertRaises(FileExistsError):
            self.artifacts.write("raw.txt", b"changed")
        g = self.gateway()
        with self.assertRaises(FileExistsError):
            Gateway(g.policy, self.artifacts, self.transport)

    def test_doubles_cannot_write_pilot_or_unmarked_paths(self):
        with self.assertRaises(Blocked):
            Artifacts("/workspace/pilot", offline=True)
        other = self.root / "unmarked"
        other.mkdir()
        with self.assertRaises(Blocked):
            Artifacts(other, offline=True)

    def test_unsupported_payloads_fail_before_dispatch(self):
        g = self.gateway()
        for raw in [b'{"model":"a","model":"b"}', request(n=2),
                    request(tools=[{"type": "web_search"}]),
                    request(messages=[{"role": "user", "content": [{"type": "image_url"}]}]),
                    request(max_tokens=1, max_completion_tokens=2), request(max_tokens=101)]:
            with self.assertRaises(Blocked):
                g.handle(raw)
        self.assertEqual(self.sent, [])

    def test_sse_raw_bytes_are_not_rewritten(self):
        g = self.gateway()
        raw = b'data: {"model":"offline-test-model","choices":[]}\n\ndata: [DONE]\n\n'
        g.transport = lambda *_: (200, "text/event-stream", raw)
        self.assertEqual(g.handle(request(stream=True))[2], raw)

    def test_missing_usage_keeps_full_reservation_and_records_length(self):
        g = self.gateway()
        raw = canonical({'model': 'offline-test-model', 'choices': [{'finish_reason': 'length'}]})
        g.transport = lambda *_: (200, 'application/json', raw)
        self.assertEqual(g.handle(request())[2], raw)
        record = json.loads((self.root / 'result-0001.json').read_text())
        self.assertFalse(record['usage_present'])
        self.assertTrue(record['length_truncated'])
        self.assertFalse(record['output_limit_intervention'])
        self.assertEqual(g.budget.reserved, 4500)

    def test_text_parts_supported_without_accepting_images(self):
        g = self.gateway()
        body = request(messages=[{'role': 'user', 'content': [{'type': 'text', 'text': 'offline'}]}])
        g.handle(body)
        self.assertEqual(self.sent[0][1], json.loads(body))

    def test_nonstream_missing_usage_over_loopback_http(self):
        g = self.gateway()
        raw = canonical({'model': 'offline-test-model', 'choices': [{'message': {'role': 'assistant', 'content': 'offline acknowledgement'}, 'finish_reason': 'stop'}]})
        g.transport = lambda *_: (200, 'application/json', raw)
        server = offline_server(g, self.artifacts)
        t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
        try:
            c = http.client.HTTPConnection(*server.server_address, timeout=2)
            c.request('POST', '/v1/chat/completions', request(stream=False))
            r = c.getresponse(); self.assertEqual(r.status, 200); self.assertEqual(r.read(), raw); c.close()
            self.assertEqual(g.budget.reserved, 4500)
            self.assertFalse(json.loads((self.root/'result-0001.json').read_text())['usage_present'])
        finally:
            server.shutdown(); server.server_close(); t.join(timeout=2)

    def test_stream_length_finish_recorded_without_rewriting_raw(self):
        g = self.gateway()
        raw = b'data: {"model":"offline-test-model","choices":[{"finish_reason":"length"}]}\n\ndata: [DONE]\n\n'
        g.transport = lambda *_: (200, 'text/event-stream', raw)
        self.assertEqual(g.handle(request(stream=True))[2], raw)
        self.assertTrue(json.loads((self.root/'result-0001.json').read_text())['length_truncated'])

    def test_loopback_forwarding_and_repeated_sdk_attempts(self):
        g = self.gateway(max_model_calls=1)
        server = offline_server(g, self.artifacts)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            for expected in [200, 403, 403]:
                c = http.client.HTTPConnection(*server.server_address, timeout=2)
                c.request("POST", "/v1/chat/completions", body=request(), headers={"Content-Type": "application/json"})
                r = c.getresponse()
                self.assertEqual(r.status, expected)
                r.read()
                c.close()
            self.assertEqual(len(self.sent), 1)
        finally:
            server.shutdown()
            server.server_close()
            t.join(timeout=2)

    def test_forwarder_exact_destination_and_bounded_single_read(self):
        policy = Policy.from_config(config())
        calls = []
        class Reply:
            status = 200
            headers = {"Content-Type": "application/json"}
            def geturl(self): return policy.upstream_url
            def read(self, limit):
                calls.append(limit)
                return response()
            def __enter__(self): return self
            def __exit__(self, *_): pass
        class Opener:
            def open(self, req, timeout):
                calls.append(req.full_url)
                self.assertion = timeout
                return Reply()
        f = HTTPSForwarder(policy, "Bearer offline-placeholder", opener=Opener())
        self.assertEqual(f(policy.upstream_url, request())[0], 200)
        self.assertEqual(calls, [policy.upstream_url, 8_000_001])
        with self.assertRaisesRegex(Blocked, "destination_mismatch"):
            f("https://other.invalid/v1/chat/completions", request())
        self.assertEqual(len(calls), 2)

    def test_no_fusion_execution_imports(self):
        tree = ast.parse(Path(__file__).with_name("gateway.py").read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(x.name for x in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertTrue(imports)
        self.assertTrue(all(x.split(".")[0] in {
            "__future__", "hashlib", "json", "threading", "time", "dataclasses", "decimal",
            "pathlib", "http", "urllib", "tempfile", "os"} for x in imports))

    def test_forwarder_preserves_http_error_status(self):
        import io
        from urllib.error import HTTPError
        p = Policy.from_config(config())
        class Opener:
            def open(self, *_args, **_kwargs):
                raise HTTPError(p.upstream_url, 503, "offline", {"Content-Type": "application/json"}, io.BytesIO(b'{}'))
        f = HTTPSForwarder(p, "Bearer offline-placeholder", opener=Opener())
        self.assertEqual(f(p.upstream_url, request()), (503, "application/json", b'{}'))


if __name__ == "__main__":
    unittest.main()
