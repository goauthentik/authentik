"""Self-check for the independent Resource AS / MCP fixture (no authentik, no database).

Run: uv run python tests/mcp_conformance_id_jag_issuer/selfcheck_resource_as.py

Demonstrates, independently of whether authentik implements ID-JAG issuance, that the fixture
(1) accepts a correctly formed and signed ID-JAG end to end (positive control: Resource AS
token + MCP call), and (2) rejects each invalid assertion with the expected OAuth error and
the expected validation rule. A stub IdP served over HTTP publishes metadata + JWKS; it signs
with `cryptography` directly (separate code path from the fixture's verifier).

Deliberately not named test_*.py so it is not picked up by general pytest discovery.
"""

from __future__ import annotations

import ast
import json
import sys
import threading
import time
import unittest
from base64 import b64encode, urlsafe_b64encode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import resource_as  # noqa: E402

FORBIDDEN_IMPORTS = {"authentik", "jwt", "jwcrypto", "authlib", "joserfc", "jose", "django"}


def b64u(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def int_b64u(value: int) -> str:
    return b64u(value.to_bytes((value.bit_length() + 7) // 8, "big"))


class StubIdP:
    """Minimal IdP: RFC 8414 metadata + JWKS, and a signer for test ID-JAGs."""

    def __init__(self, issuer_path="/application/o/stub/", metadata_issuer: str | None = None):
        self.rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.ec_key = ec.generate_private_key(ec.SECP256R1())
        self.rogue_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        stub = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                return

            def do_GET(self):
                if self.path == f"/.well-known/oauth-authorization-server{issuer_path.rstrip('/')}":
                    body = {
                        "issuer": metadata_issuer or stub.issuer,
                        "jwks_uri": f"{stub.base}/jwks",
                    }
                elif self.path == "/jwks":
                    body = stub.jwks()
                else:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                data = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.issuer = self.base + issuer_path
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def jwks(self) -> dict:
        rn = self.rsa_key.public_key().public_numbers()
        en = self.ec_key.public_key().public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "rsa1",
                    "use": "sig",
                    "alg": "RS256",
                    "n": int_b64u(rn.n),
                    "e": int_b64u(rn.e),
                },
                {
                    "kty": "EC",
                    "kid": "ec1",
                    "use": "sig",
                    "crv": "P-256",
                    "x": b64u(en.x.to_bytes(32, "big")),
                    "y": b64u(en.y.to_bytes(32, "big")),
                },
            ]
        }

    def sign(self, claims: dict, header: dict | None = None, key: str = "rsa1") -> str:
        hdr = {"typ": "oauth-id-jag+jwt", "alg": "RS256" if key != "ec1" else "ES256", "kid": key}
        hdr.update(header or {})
        hdr = {k: v for k, v in hdr.items() if v is not None}
        signing_input = f"{b64u(json.dumps(hdr).encode())}.{b64u(json.dumps(claims).encode())}"
        if hdr["alg"] == "none":
            return signing_input + "."
        if key == "ec1":
            der = self.ec_key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
            r, s = decode_dss_signature(der)
            sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        else:
            priv = self.rogue_key if key == "rogue" else self.rsa_key
            sig = priv.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
        return f"{signing_input}.{b64u(sig)}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def post_form(url, data, basic=None):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if basic:
        headers["Authorization"] = "Basic " + b64encode(f"{basic[0]}:{basic[1]}".encode()).decode()
    return _do(Request(url, data=urlencode(data, doseq=True).encode(), headers=headers))


def post_json(url, body, token=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _do(Request(url, data=json.dumps(body).encode(), headers=headers))


def _do(req):
    try:
        with urlopen(req, timeout=10) as resp:  # nosec B310 - local test servers
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None), dict(resp.headers)
    except HTTPError as err:
        with err:
            raw = err.read()
        return err.code, (json.loads(raw) if raw else None), dict(err.headers)


class ResourceASSelfCheck(unittest.TestCase):
    CLIENT = ("mcp-client-at-ras", "s3cret-for-selfcheck")
    OTHER = ("other-client-at-ras", "other-secret")

    @classmethod
    def setUpClass(cls):
        cls.idp = StubIdP()
        cls.fx = resource_as.start_fixture(
            resource_as.FixtureConfig(
                idp_issuer=cls.idp.issuer, clients=dict([cls.CLIENT, cls.OTHER])
            )
        )
        cls.desc = cls.fx.describe()

    @classmethod
    def tearDownClass(cls):
        cls.fx.stop()
        cls.idp.stop()

    def test_fixture_startup_does_not_require_reverse_dns(self):
        with patch("socket.getfqdn", side_effect=AssertionError("Reverse DNS unavailable")):
            fixture = resource_as.start_fixture(
                resource_as.FixtureConfig(idp_issuer=self.idp.issuer, clients={})
            )
            try:
                status, body, _ = _do(Request(fixture.describe()["as_metadata_url"]))
                self.assertEqual(status, 200)
                self.assertEqual(body["issuer"], fixture.as_issuer)
            finally:
                fixture.stop()

    def claims(self, **overrides):
        now = int(time.time())
        base = {
            "iss": self.idp.issuer,
            "sub": "user-123",
            "aud": self.desc["as_issuer"],
            "client_id": self.CLIENT[0],
            "jti": f"jti-{time.time_ns()}",
            "iat": now,
            "exp": now + 300,
            "resource": self.desc["resource"],
            "scope": "mcp:tools",
        }
        base.update(overrides)
        return {k: v for k, v in base.items() if v is not None}

    def redeem(self, assertion, client=CLIENT, grant_type=resource_as.GRANT_TYPE_JWT_BEARER):
        return post_form(
            self.desc["token_endpoint"],
            {"grant_type": grant_type, "assertion": assertion},
            basic=client,
        )

    def assertRejected(self, assertion, rule, error="invalid_grant", client=CLIENT):
        before = len(self.fx.events)
        status, body, _ = self.redeem(assertion, client=client)
        self.assertEqual(status, 400 if error != "invalid_client" else 401, body)
        self.assertEqual(body["error"], error, body)
        ev = [e for e in self.fx.events[before:] if e["endpoint"] == "token"][-1]
        self.assertEqual(ev["outcome"], "rejected")
        self.assertEqual(ev["rule"], rule, ev)
        self.assertNotIn("access_token", body)

    # --- positive controls
    def test_positive_rs256_end_to_end(self):
        status, body, headers = self.redeem(self.idp.sign(self.claims()))
        self.assertEqual(status, 200, body)
        self.assertEqual(body["token_type"], "Bearer")
        self.assertEqual(body["scope"], "mcp:tools")
        self.assertNotIn("refresh_token", body)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        token = body["access_token"]
        status, init, _ = post_json(
            self.desc["resource"],
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "selfcheck", "version": "0"},
                },
            },
            token,
        )
        self.assertEqual(status, 200, init)
        self.assertEqual(init["result"]["protocolVersion"], "2025-11-25")
        status, _, _ = post_json(
            self.desc["resource"], {"jsonrpc": "2.0", "method": "notifications/initialized"}, token
        )
        self.assertEqual(status, 202)
        status, call, _ = post_json(
            self.desc["resource"],
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "whoami", "arguments": {}},
            },
            token,
        )
        self.assertEqual(status, 200, call)
        self.assertEqual(call["result"]["structuredContent"]["sub"], "user-123")
        self.assertEqual(self.fx.keys.metadata_source, "rfc8414")

    def test_positive_es256_and_aud_array(self):
        status, body, _ = self.redeem(
            self.idp.sign(self.claims(aud=[self.desc["as_issuer"]]), key="ec1")
        )
        self.assertEqual(status, 200, body)

    def test_mcp_requires_token(self):
        status, _, headers = post_json(
            self.desc["resource"], {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )
        self.assertEqual(status, 401)
        self.assertIn(f'resource_metadata="{self.desc["prm_url"]}"', headers["WWW-Authenticate"])
        status, _, headers = post_json(
            self.desc["resource"], {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, "bogus"
        )
        self.assertEqual(status, 401)
        self.assertIn('error="invalid_token"', headers["WWW-Authenticate"])

    # --- rejection matrix (draft-06 §4.4.1, RFC 7523 §3, RFC 8725)
    def test_reject_typ(self):
        self.assertRejected(self.idp.sign(self.claims(), {"typ": "JWT"}), "jose.typ")
        self.assertRejected(self.idp.sign(self.claims(), {"typ": None}), "jose.typ")

    def test_reject_alg_none_and_hmac(self):
        self.assertRejected(self.idp.sign(self.claims(), {"alg": "none"}), "jose.alg")
        self.assertRejected(self.idp.sign(self.claims(), {"alg": "HS256"}), "jose.alg")

    def test_reject_signature(self):
        # signed by a key that is not in the IdP JWKS, but claiming the IdP's kid
        self.assertRejected(
            self.idp.sign(self.claims(), {"kid": "rsa1"}, key="rogue"), "jose.signature"
        )
        tampered = self.idp.sign(self.claims()).split(".")
        tampered[1] = b64u(json.dumps(self.claims(sub="attacker")).encode())
        self.assertRejected(".".join(tampered), "jose.signature")

    def test_reject_unknown_kid(self):
        self.assertRejected(self.idp.sign(self.claims(), {"kid": "nope"}), "jose.kid")

    def test_reject_issuer(self):
        self.assertRejected(self.idp.sign(self.claims(iss="https://evil.example/")), "claims.iss")

    def test_reject_audience(self):
        self.assertRejected(
            self.idp.sign(self.claims(aud="https://other-as.example/")), "claims.aud"
        )
        self.assertRejected(
            self.idp.sign(self.claims(aud=[self.desc["as_issuer"], "https://other-as.example/"])),
            "claims.aud",
        )

    def test_reject_client_binding(self):
        self.assertRejected(self.idp.sign(self.claims()), "claims.client_id", client=self.OTHER)
        self.assertRejected(self.idp.sign(self.claims(client_id=None)), "claims.client_id")

    def test_reject_required_claims(self):
        self.assertRejected(self.idp.sign(self.claims(sub=None)), "claims.sub")
        self.assertRejected(self.idp.sign(self.claims(jti=None)), "claims.jti")
        self.assertRejected(self.idp.sign(self.claims(exp=None)), "claims.exp")
        self.assertRejected(self.idp.sign(self.claims(iat=None)), "claims.iat")
        self.assertRejected(self.idp.sign(self.claims(exp=int(time.time()) - 120)), "claims.exp")
        self.assertRejected(self.idp.sign(self.claims(iat=int(time.time()) + 600)), "claims.iat")

    def test_reject_resource(self):
        self.assertRejected(
            self.idp.sign(self.claims(resource="http://127.0.0.1:1/other")), "claims.resource"
        )

    def test_reject_replay(self):
        assertion = self.idp.sign(self.claims())
        self.assertEqual(self.redeem(assertion)[0], 200)
        self.assertRejected(assertion, "claims.jti-replay")

    def test_reject_client_auth_and_grant_type(self):
        self.assertRejected(
            self.idp.sign(self.claims()),
            "client.auth",
            "invalid_client",
            client=(self.CLIENT[0], "wrong"),
        )
        status, body, headers = post_form(
            self.desc["token_endpoint"],
            {
                "grant_type": resource_as.GRANT_TYPE_JWT_BEARER,
                "assertion": self.idp.sign(self.claims()),
            },
        )
        self.assertEqual((status, body["error"]), (401, "invalid_client"))
        status, body, _ = self.redeem(self.idp.sign(self.claims()), grant_type="password")
        self.assertEqual(body["error"], "unsupported_grant_type")

    def test_reject_metadata_issuer_mismatch(self):
        rogue = StubIdP(metadata_issuer="https://not-the-issuer.example/")
        fx = resource_as.start_fixture(
            resource_as.FixtureConfig(idp_issuer=rogue.issuer, clients=dict([self.CLIENT]))
        )
        try:
            claims = self.claims(iss=rogue.issuer, aud=fx.as_issuer)
            claims.pop("resource")
            status, body, _ = post_form(
                fx.describe()["token_endpoint"],
                {"grant_type": resource_as.GRANT_TYPE_JWT_BEARER, "assertion": rogue.sign(claims)},
                basic=self.CLIENT,
            )
            self.assertEqual((status, body["error"]), (400, "invalid_grant"))
            self.assertEqual(fx.events[-1]["rule"], "issuer.metadata")
        finally:
            fx.stop()
            rogue.stop()

    # --- independence guard
    def test_fixture_does_not_import_authentik_or_jwt_libraries(self):
        for name in ("resource_as.py", "checks.py", "selfcheck_resource_as.py"):
            tree = ast.parse((HERE / name).read_text())
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(
                imported & FORBIDDEN_IMPORTS, f"{name}: {imported & FORBIDDEN_IMPORTS}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
