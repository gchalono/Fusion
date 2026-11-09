"""Evaluation-only HTTP budget boundary; no Fusion/runtime imports or credentials.

FNXC:PlanningEvaluation 2026-11-04-09:54:
Preserve native retries/compaction and authorize each HTTP attempt externally.
This module deliberately has no live credential loader or live launch command.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

RATE_LIMIT_IDENTIFIER = "fusion-phase2a-pilot"
MAX_BODY_BYTES = 1_000_000
MAX_RESPONSE_BYTES = 8_000_000


class Blocked(Exception):
    """Only stable, non-sensitive codes may leave the boundary."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def positive_int(value):
    if type(value) is not int or value <= 0:
        raise Blocked("invalid_integer")
    return value


def dollars(value):
    try:
        if isinstance(value, bool):
            raise ValueError()
        result = Decimal(str(value))
        if not result.is_finite() or result <= 0:
            raise ValueError()
        return int((result * 1_000_000).to_integral_value(rounding=ROUND_CEILING))
    except (InvalidOperation, ValueError, TypeError):
        raise Blocked("invalid_price") from None


@dataclass(frozen=True)
class Policy:
    provider: str
    model: str
    upstream_url: str
    approved_hosts: tuple[str, ...]
    max_model_calls: int
    ceiling_micro_usd: int
    input_price_micro_per_million: int
    output_price_micro_per_million: int
    input_token_bound: int
    output_token_bound: int
    output_ceiling: int | None

    @classmethod
    def from_config(cls, c):
        # Caller must supply verified model-specific bounds, not tokenizer guesses.
        for key in ("provider", "model", "upstream_url", "token_bound_evidence_sha256"):
            if not isinstance(c.get(key), str) or not c[key].strip() or "<" in c[key]:
                raise Blocked("missing_" + key)
        evidence = c["token_bound_evidence_sha256"]
        if len(evidence) != 64 or any(x not in "0123456789abcdef" for x in evidence):
            raise Blocked("invalid_bound_evidence_hash")
        u = urlsplit(c["upstream_url"])
        hosts = c.get("approved_hosts")
        if (u.scheme != "https" or u.username or u.password or u.query or u.fragment
                or u.port not in (None, 443) or u.path != "/v1/chat/completions"
                or not isinstance(hosts, list) or hosts != [u.hostname]):
            raise Blocked("unapproved_destination")
        # Virtual/router/CLI providers are not covered by this dialect contract.
        if c.get("api_type") != "openai-chat-completions" or c.get("physical_model_verified") is not True:
            raise Blocked("unsupported_model_contract")
        ceiling = c.get("output_ceiling")
        if ceiling is not None:
            positive_int(ceiling)
        output_bound = positive_int(c.get("output_token_bound"))
        if ceiling is not None and ceiling > output_bound:
            raise Blocked("invalid_output_ceiling")
        return cls(c["provider"], c["model"], c["upstream_url"], tuple(hosts),
                   positive_int(c.get("max_model_calls")), dollars(c.get("spend_ceiling_usd")),
                   dollars(c.get("input_price_per_million")), dollars(c.get("output_price_per_million")),
                   positive_int(c.get("input_token_bound")), output_bound, ceiling)


class Artifacts:
    """Write-once raw bytes with hashes; tests are confined to marked temp roots."""
    def __init__(self, root, *, offline=False, secrets=()):
        self.root = Path(root)
        self.secrets = tuple(x.encode() for x in secrets if x)
        if offline:
            import tempfile
            temp = Path(tempfile.gettempdir()).resolve()
            resolved = self.root.resolve()
            if temp not in resolved.parents or not (self.root / ".offline-test").is_file():
                raise Blocked("test_output_not_isolated")
        if not self.root.is_dir() or self.root.is_symlink():
            raise Blocked("invalid_artifact_root")

    def write(self, name, data):
        if not name or Path(name).name != name or name.startswith("."):
            raise Blocked("invalid_artifact_name")
        if any(secret in data for secret in self.secrets):
            # Never mutate purported raw bytes. Refuse to persist sensitive content.
            raise Blocked("sensitive_raw_artifact")
        with (self.root / name).open("xb") as f:
            f.write(data)
            f.flush()
            import os
            os.fsync(f.fileno())
        directory = os.open(self.root, os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
        return {"file": name, "sha256": digest(data), "bytes": len(data)}


class Budget:
    def __init__(self, policy, artifacts):
        self.policy, self.artifacts = policy, artifacts
        self.calls = self.reserved = 0
        self.failed = False
        self.lock = threading.Lock()
        # Existing reservations cannot be silently reset by reopening a run.
        self.artifacts.write("run-open.json", canonical({"rate_limit_identifier": RATE_LIMIT_IDENTIFIER}))

    def reserve(self, request):
        with self.lock:
            if self.failed:
                raise Blocked("run_terminal")
            if request.get("model") != self.policy.model:
                raise Blocked("model_mismatch")
            if self.calls >= self.policy.max_model_calls:
                raise Blocked("call_cap")
            # No byte-to-token assumption: reserve the entire verified input bound.
            cap = self.policy.output_ceiling or self.policy.output_token_bound
            worst = (self.policy.input_token_bound * self.policy.input_price_micro_per_million
                     + cap * self.policy.output_price_micro_per_million + 999_999) // 1_000_000
            if self.reserved + worst > self.policy.ceiling_micro_usd:
                raise Blocked("spend_ceiling")
            n = self.calls + 1
            self.artifacts.write(f"reservation-{n:04}.json", canonical({
                "attempt": n, "reserved_micro_usd": worst, "accounting": "estimated_upper_bound",
                "request_sha256": digest(canonical(request)), "upstream_host": self.policy.approved_hosts[0],
            }))
            self.calls, self.reserved = n, self.reserved + worst
            return n


def prepare_request(raw, policy):
    if len(raw) > MAX_BODY_BYTES:
        raise Blocked("request_too_large")
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Blocked("duplicate_json_key")
            result[key] = value
        return result
    try:
        body = json.loads(raw, object_pairs_hook=no_duplicates,
                          parse_constant=lambda _: (_ for _ in ()).throw(Blocked("invalid_json")))
    except (ValueError, UnicodeError):
        raise Blocked("invalid_json") from None
    if not isinstance(body, dict) or not isinstance(body.get("messages"), list) or not body["messages"]:
        raise Blocked("invalid_messages")
    # Fail closed on modalities and provider-specific billable extensions.
    allowed = {"model", "messages", "tools", "tool_choice", "parallel_tool_calls", "stream",
               "stream_options", "max_tokens", "max_completion_tokens", "temperature", "top_p",
               "reasoning_effort", "seed", "store", "user"}
    if set(body) - allowed or body.get("n", 1) != 1:
        raise Blocked("unsupported_request_shape")
    if "tools" in body and (not isinstance(body["tools"], list) or any(
            not isinstance(tool, dict) or tool.get("type") != "function"
            or set(tool) != {"type", "function"} or not isinstance(tool["function"], dict)
            for tool in body["tools"])):
        raise Blocked("unsupported_billable_tool")
    for message in body["messages"]:
        if not isinstance(message, dict) or message.get("role") not in ("system", "developer", "user", "assistant", "tool"):
            raise Blocked("unsupported_message")
        content = message.get("content")
        if content is not None and not isinstance(content, str):
            if not isinstance(content, list) or any(
                    not isinstance(part, dict) or set(part) != {"type", "text"}
                    or part["type"] != "text" or not isinstance(part["text"], str)
                    for part in content):
                raise Blocked("unsupported_modality")
    fields = [k for k in ("max_tokens", "max_completion_tokens") if k in body]
    if len(fields) > 1:
        raise Blocked("ambiguous_output_limit")
    if fields:
        positive_int(body[fields[0]])
    if policy.output_ceiling is not None:
        # Evaluation must not lower Fusion's native token allowance. A tighter
        # budget rejects the request instead of silently degrading the output.
        if not fields or body[fields[0]] > policy.output_ceiling:
            raise Blocked("output_limit_intervention_forbidden")
    elif fields and body[fields[0]] > policy.output_token_bound:
        raise Blocked("output_bound_exceeded")
    return body


def validate_response(raw, content_type, model):
    if len(raw) > MAX_RESPONSE_BYTES:
        raise Blocked("response_too_large")
    try:
        if "text/event-stream" in content_type:
            payloads = [json.loads(line[5:].strip()) for line in raw.decode().splitlines()
                        if line.startswith("data:") and line[5:].strip() != "[DONE]"]
        else:
            payloads = [json.loads(raw)]
        if not payloads or any(not isinstance(x, dict) or x.get("model") != model for x in payloads):
            raise Blocked("response_model_mismatch")
        return [x["usage"] for x in payloads if x.get("usage") is not None]
    except (ValueError, UnicodeError, KeyError):
        raise Blocked("unsupported_response") from None


def length_truncated(raw, content_type):
    if 'text/event-stream' in content_type:
        payloads = [json.loads(line[5:].strip()) for line in raw.decode().splitlines()
                    if line.startswith('data:') and line[5:].strip() != '[DONE]']
    else:
        payloads = [json.loads(raw)]
    return any(choice.get('finish_reason') == 'length' for p in payloads for choice in p.get('choices', []))


class Gateway:
    """Transport injected by a supervisor; this gateway itself never retries.

    The transport must enforce exact HTTPS destination, no redirects, bounded reads,
    inherited proxy/CA trust, and sole-egress routing. Live supervisor is withheld.
    Response model checks happen AFTER upstream dispatch, not before billing.
    """
    def __init__(self, policy, artifacts, transport):
        self.policy, self.artifacts, self.transport = policy, artifacts, transport
        self.budget = Budget(policy, artifacts)
        self.serial = threading.Lock()
        self.blocked_attempts = []

    def handle(self, raw):
        with self.serial:
            body = prepare_request(raw, self.policy)
            attempt = self.budget.reserve(body)
            start = time.monotonic()
            try:
                request_artifact = self.artifacts.write(f"request-{attempt:04}.json", raw)
                try:
                    status, content_type, response = self.transport(self.policy.upstream_url, canonical(body))
                except OSError:
                    # Native retry policy stays enabled. This boundary does not
                    # retry; a later native attempt needs another reservation.
                    status, content_type, response = 502, "application/json", b'{"error":"upstream_transport_failed"}'
                if type(status) is not int or not 100 <= status <= 599 or len(response) > MAX_RESPONSE_BYTES:
                    raise Blocked("invalid_transport_response")
                usage = validate_response(response, content_type, self.policy.model) if status == 200 else []
                response_artifact = self.artifacts.write(f"response-{attempt:04}.raw", response)
                self.artifacts.write(f"result-{attempt:04}.json", canonical({
                    "request": request_artifact, "response": response_artifact,
                    "provider_reported_usage_unverified": usage,
                    "latency_ms": round((time.monotonic() - start) * 1000),
                    "reserved_micro_usd": self.budget.reserved,
                    "usage_present": bool(usage), "cost_accounting": "estimated_upper_bound",
                    "output_limit_intervention": False,
                    "length_truncated": length_truncated(response, content_type) if status == 200 else None,
                }))
                return status, content_type, response
            except Exception:
                self.budget.failed = True
                # No exception text, upstream body, headers, or credentials in logs.
                self.artifacts.write(f"failure-{attempt:04}.json", canonical({"code": "forward_failed"}))
                raise Blocked("forward_failed") from None


class HTTPSForwarder:
    """Bounded, single-attempt HTTPS forwarding with normal proxy and TLS trust.

    Credentials are supplied in memory by a future authorized supervisor. This
    class does not discover/read credentials, enable inference, or change egress.
    """
    def __init__(self, policy, authorization_header, *, opener=None):
        from urllib.request import build_opener, HTTPRedirectHandler
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *_args, **_kwargs):
                raise Blocked("redirect_forbidden")
        if not isinstance(authorization_header, str) or not authorization_header.startswith("Bearer "):
            raise Blocked("missing_authorization")
        self.policy = policy
        self.authorization_header = authorization_header
        # Default opener preserves environment proxy routing and normal TLS checks.
        self.opener = opener or build_opener(NoRedirect())

    def __call__(self, url, raw):
        from urllib.request import Request
        from urllib.error import HTTPError
        if url != self.policy.upstream_url:
            raise Blocked("destination_mismatch")
        req = Request(url, data=raw, method="POST", headers={
            "Authorization": self.authorization_header, "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        try:
            reply = self.opener.open(req, timeout=180)
        except HTTPError as error:
            reply = error
        with reply as r:
            if r.geturl() != url:
                raise Blocked("redirect_forbidden")
            data = r.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise Blocked("response_too_large")
            return r.status, r.headers.get("Content-Type", ""), data


def offline_server(gateway, artifacts):
    """Loopback HTTP integration harness, available only for marked test artifacts."""
    if not (artifacts.root / ".offline-test").is_file():
        raise Blocked("offline_server_only")
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                if self.path != "/v1/chat/completions" or self.headers.get("Transfer-Encoding"):
                    raise Blocked("unsupported_path_or_transfer")
                lengths = self.headers.get_all("Content-Length", [])
                if len(lengths) != 1 or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= MAX_BODY_BYTES:
                    raise Blocked("invalid_content_length")
                raw = self.rfile.read(int(lengths[0]))
                status, content_type, response = gateway.handle(raw)
            except (Blocked, ValueError) as error:
                gateway.blocked_attempts.append(str(error) if isinstance(error, Blocked) else 'invalid_value')
                # Offline diagnostics contain body only, never HTTP auth headers.
                if 'raw' in locals():
                    artifacts.write(f"blocked-{len(gateway.blocked_attempts):04}.json", raw)
                status, content_type, response = 403, "application/json", b'{"error":"evaluation_request_blocked"}'
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


if __name__ == "__main__":
    print("PILOT_BLOCKED: no live supervisor; inference authorization and routing proof required")
    raise SystemExit(2)
