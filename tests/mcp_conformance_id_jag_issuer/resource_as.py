"""Independent ID-JAG Resource Authorization Server + protected MCP resource (TEST FIXTURE).

This module is test infrastructure for the `test-mcp-conformance (id-jag-issuer)` check. It
plays the two roles *downstream* of the authentik IdP in
draft-ietf-oauth-identity-assertion-authz-grant-06 (pinned, 31 October 2026):

* a Resource Authorization Server that redeems an ID-JAG via the RFC 7523 JWT bearer grant
  (draft-06 Section 4.4 / 4.4.1), and
* an MCP server (protected resource, RFC 9728 + MCP Streamable HTTP) that only accepts
  access tokens issued by that Resource Authorization Server.

Independence requirements (enforced by `selfcheck_resource_as.py`):

* stdlib + `cryptography` primitives only. It MUST NOT import `authentik`, PyJWT (`jwt`),
  `jwcrypto`, `authlib` or `joserfc`: JWS parsing, JWK conversion, signature verification and
  claim validation are implemented here, so authentik's own JOSE code is never used to
  validate authentik's output.
* The IdP signing keys are discovered from the IdP *issuer identifier* only (RFC 8414
  Section 3 path-insertion metadata, falling back to OpenID Connect Discovery Section 4 as
  allowed by draft-06 Section 7.1), with the issuer-equality check of RFC 8414 Section 3.3.

It can be run as a subprocess (`python resource_as.py --config cfg.json`) or started in-process
with `start_fixture()`. It never logs raw tokens or client secrets.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
import time
from base64 import urlsafe_b64decode
from binascii import Error as BinasciiError
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote_plus, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

GRANT_TYPE_JWT_BEARER = "urn:ietf:params:oauth:grant-type:jwt-bearer"
GRANT_PROFILE_ID_JAG = "urn:ietf:params:oauth:grant-profile:id-jag"
ID_JAG_TYP = "oauth-id-jag+jwt"
MAX_CLAIMS_LOG = 8192
MCP_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")

_HASHES = {"256": hashes.SHA256, "384": hashes.SHA384, "512": hashes.SHA512}
_EC_CURVES = {"ES256": ("P-256", 32), "ES384": ("P-384", 48), "ES512": ("P-521", 66)}
_CRV = {"P-256": ec.SECP256R1, "P-384": ec.SECP384R1, "P-521": ec.SECP521R1}
# RFC 7518 asymmetric algorithms. draft-06 Section 3: RS256 is mandatory to implement,
# ES256 SHOULD be supported. `none` and HMAC are never accepted (RFC 8725 Section 3.1/3.2).
DEFAULT_ALLOWED_ALGS = ("RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384")


class GrantError(Exception):
    """A rejected token request. `rule` names the validation rule that failed."""

    def __init__(self, error: str, rule: str, description: str, status: int = 400):
        super().__init__(description)
        self.error = error
        self.rule = rule
        self.description = description
        self.status = status


def b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or any(c in value for c in "=+/ \n"):
        raise ValueError("not base64url without padding")
    return urlsafe_b64decode(value + "=" * (-len(value) % 4))


def parse_compact_jws(token: str) -> tuple[dict, dict, bytes, bytes]:
    """Split a JWS compact serialization (RFC 7515 Section 7.1) into header, payload,
    signing input and signature. Raises GrantError(rule=jose.format)."""
    parts = token.split(".") if isinstance(token, str) else []
    if len(parts) != 3:  # noqa: PLR2004 - header.payload.signature
        raise GrantError("invalid_grant", "jose.format", "assertion is not a compact JWS")
    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        signature = b64url_decode(parts[2])
    except (ValueError, BinasciiError, UnicodeDecodeError) as exc:
        raise GrantError("invalid_grant", "jose.format", f"undecodable JWS: {exc}") from None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise GrantError("invalid_grant", "jose.format", "JWS header/payload is not an object")
    return header, payload, f"{parts[0]}.{parts[1]}".encode("ascii"), signature


def _b64_int(value: str) -> int:
    return int.from_bytes(b64url_decode(value), "big")


def jwk_to_public_key(jwk: dict):
    """RFC 7518 Section 6 public JWK -> cryptography public key (RSA and EC only)."""
    kty = jwk.get("kty")
    if kty == "RSA":
        return rsa.RSAPublicNumbers(_b64_int(jwk["e"]), _b64_int(jwk["n"])).public_key()
    if kty == "EC":
        curve = _CRV[jwk["crv"]]()
        return ec.EllipticCurvePublicNumbers(
            _b64_int(jwk["x"]), _b64_int(jwk["y"]), curve
        ).public_key()
    raise ValueError(f"unsupported kty {kty!r}")


def _key_matches_alg(key, alg: str) -> bool:
    if alg.startswith(("RS", "PS")):
        return isinstance(key, rsa.RSAPublicKey)
    if alg in _EC_CURVES:
        return (
            isinstance(key, ec.EllipticCurvePublicKey)
            and key.curve.name
            == {
                "P-256": "secp256r1",
                "P-384": "secp384r1",
                "P-521": "secp521r1",
            }[_EC_CURVES[alg][0]]
        )
    return False


def verify_signature(alg: str, key, signing_input: bytes, signature: bytes) -> bool:
    """Verify a JWS signature per RFC 7518 Section 3.3-3.5."""
    hash_cls = _HASHES[alg[2:]]
    try:
        if alg.startswith("RS"):
            key.verify(signature, signing_input, padding.PKCS1v15(), hash_cls())
        elif alg.startswith("PS"):
            key.verify(
                signature,
                signing_input,
                padding.PSS(mgf=padding.MGF1(hash_cls()), salt_length=hash_cls.digest_size),
                hash_cls(),
            )
        else:
            size = _EC_CURVES[alg][1]
            if len(signature) != 2 * size:
                return False
            r = int.from_bytes(signature[:size], "big")
            s = int.from_bytes(signature[size:], "big")
            key.verify(encode_dss_signature(r, s), signing_input, ec.ECDSA(hash_cls()))
    except InvalidSignature:
        return False
    return True


def _http_get_json(url: str, timeout: float = 10.0) -> dict:
    req = Request(url, headers={"Accept": "application/json"})  # noqa: S310 (test fixture)
    with urlopen(req, timeout=timeout) as resp:  # nosec B310 - test fixture, configured URL
        return json.loads(resp.read())


def metadata_urls(issuer: str) -> list[tuple[str, str]]:
    """Candidate metadata URLs derived from an issuer identifier only.

    1. RFC 8414 Section 3.1 (terminating "/" removed, well-known inserted before the path),
    2. the same with the issuer's trailing slash kept (common deployment variant),
    3. OpenID Connect Discovery 1.0 Section 4 (fallback allowed by draft-06 Section 7.1)."""
    parts = urlsplit(issuer)
    path = parts.path.rstrip("/")
    candidates = [
        (
            "rfc8414",
            urlunsplit(
                (
                    parts.scheme,
                    parts.netloc,
                    f"/.well-known/oauth-authorization-server{path}",
                    "",
                    "",
                )
            ),
        ),
    ]
    if parts.path.endswith("/") and path:
        candidates.append(
            (
                "rfc8414-trailing-slash",
                urlunsplit(
                    (
                        parts.scheme,
                        parts.netloc,
                        f"/.well-known/oauth-authorization-server{path}/",
                        "",
                        "",
                    )
                ),
            )
        )
    candidates.append(("oidc-discovery", issuer.rstrip("/") + "/.well-known/openid-configuration"))
    return candidates


class IssuerKeys:
    """Trusted IdP issuer -> metadata -> jwks_uri -> keys, with issuer equality check."""

    def __init__(self, issuer: str, fetch=_http_get_json):
        self.issuer = issuer
        self._fetch = fetch
        self._lock = threading.Lock()
        self.metadata: dict | None = None
        self.metadata_source: str | None = None
        self._jwks: list[dict] = []
        self.diagnostics: list[str] = []

    def _load_metadata(self) -> dict:
        for source, url in metadata_urls(self.issuer):
            try:
                doc = self._fetch(url)
            except (HTTPError, URLError, OSError, ValueError) as exc:
                if isinstance(exc, HTTPError):
                    exc.close()
                self.diagnostics.append(f"{source} {url}: {exc}")
                continue
            # RFC 8414 Section 3.3 / OIDC Discovery Section 4.3: issuer MUST be identical
            if doc.get("issuer") != self.issuer:
                self.diagnostics.append(f"{source} {url}: issuer mismatch {doc.get('issuer')!r}")
                continue
            if not isinstance(doc.get("jwks_uri"), str):
                self.diagnostics.append(f"{source} {url}: no jwks_uri")
                continue
            self.metadata_source = source
            return doc
        raise GrantError(
            "invalid_grant", "issuer.metadata", f"no valid metadata for issuer {self.issuer}"
        )

    def _refresh(self) -> None:
        if self.metadata is None:
            self.metadata = self._load_metadata()
        try:
            jwks = self._fetch(self.metadata["jwks_uri"])
        except (HTTPError, URLError, OSError, ValueError) as exc:
            raise GrantError("invalid_grant", "issuer.jwks", f"jwks fetch failed: {exc}") from None
        self._jwks = [k for k in jwks.get("keys", []) if isinstance(k, dict)]

    def key_for(self, header: dict):
        with self._lock:
            for attempt in range(2):
                if attempt or not self._jwks:
                    self._refresh()
                candidates = [
                    k
                    for k in self._jwks
                    if k.get("use") in (None, "sig")
                    and ("kid" not in header or k.get("kid") == header["kid"])
                ]
                usable = []
                for jwk in candidates:
                    try:
                        key = jwk_to_public_key(jwk)
                    except KeyError, ValueError, TypeError:
                        continue
                    if _key_matches_alg(key, header["alg"]) and jwk.get("alg") in (
                        None,
                        header["alg"],
                    ):
                        usable.append(key)
                if "kid" not in header and len(usable) > 1:
                    raise GrantError("invalid_grant", "jose.kid", "no kid and multiple keys")
                if usable:
                    return usable[0]
        raise GrantError("invalid_grant", "jose.kid", f"no IdP key for kid {header.get('kid')!r}")


@dataclass
class FixtureConfig:
    idp_issuer: str
    # client_id at THIS Resource AS -> client_secret (client_secret_basic)
    clients: dict[str, str]
    host: str = "127.0.0.1"
    resource_path: str = "/mcp"
    # resources governed by this AS, besides the MCP resource itself (draft-06 Section 4.4.1)
    extra_resources: list[str] = field(default_factory=list)
    scopes_supported: list[str] = field(default_factory=lambda: ["mcp:tools"])
    allowed_algs: tuple[str, ...] = DEFAULT_ALLOWED_ALGS
    leeway: int = 30
    access_token_lifetime: int = 300
    events_file: str | None = None


class IdJagValidator:
    """draft-06 Section 4.4.1 (+ RFC 7521 Section 5.2, RFC 7523 Section 3) processing."""

    def __init__(self, cfg: FixtureConfig, own_issuer: str, governed: list[str], keys: IssuerKeys):
        self.cfg = cfg
        self.own_issuer = own_issuer
        self.governed = governed
        self.keys = keys
        self._used_jti: set[str] = set()
        self._lock = threading.Lock()

    def validate(  # noqa: PLR0912, PLR0915 - one linear list of spec rules
        self, assertion: str, client_id: str, now: float | None = None
    ) -> dict:
        now = time.time() if now is None else now
        header, claims, signing_input, signature = parse_compact_jws(assertion)
        # draft-06 Section 3.1 / 4.4.1: typ MUST be oauth-id-jag+jwt (RFC 8725 Section 3.11).
        # RFC 7515 Section 4.1.9: the "application/" prefix may be omitted, compare case-insens.
        typ = str(header.get("typ", "")).lower()
        if typ.removeprefix("application/") != ID_JAG_TYP:
            raise GrantError("invalid_grant", "jose.typ", f"typ {header.get('typ')!r}")
        alg = header.get("alg")
        if alg not in self.cfg.allowed_algs:
            raise GrantError("invalid_grant", "jose.alg", f"alg {alg!r} not allowed")
        if "crit" in header:
            raise GrantError("invalid_grant", "jose.crit", "unsupported crit header")
        # RFC 7523 Section 3 item 1 / draft-06 Section 4.4.1: iss must be a trusted IdP
        if claims.get("iss") != self.keys.issuer:
            raise GrantError("invalid_grant", "claims.iss", f"untrusted iss {claims.get('iss')!r}")
        key = self.keys.key_for(header)
        if not verify_signature(alg, key, signing_input, signature):
            raise GrantError("invalid_grant", "jose.signature", "signature verification failed")
        # draft-06 Section 4.4.1: aud is this AS's issuer, string or single-element array
        aud = claims.get("aud")
        if isinstance(aud, list):
            if len(aud) != 1:
                raise GrantError("invalid_grant", "claims.aud", "aud array must have one element")
            aud = aud[0]
        if aud != self.own_issuer:
            raise GrantError("invalid_grant", "claims.aud", f"aud {claims.get('aud')!r}")
        # draft-06 Section 3.1 (REQUIRED) + 4.4.1 client continuity check
        if not isinstance(claims.get("client_id"), str) or not claims["client_id"]:
            raise GrantError("invalid_grant", "claims.client_id", "client_id claim missing")
        if claims["client_id"] != client_id:
            raise GrantError(
                "invalid_grant",
                "claims.client_id",
                "client_id claim does not identify the authenticated client",
            )
        if not isinstance(claims.get("sub"), str) or not claims["sub"]:
            raise GrantError("invalid_grant", "claims.sub", "sub missing")
        for name in ("exp", "iat"):
            if not isinstance(claims.get(name), int | float) or isinstance(claims.get(name), bool):
                raise GrantError("invalid_grant", f"claims.{name}", f"{name} missing/not numeric")
        if claims["exp"] <= now - self.cfg.leeway:
            raise GrantError("invalid_grant", "claims.exp", "assertion expired")
        if claims["iat"] > now + self.cfg.leeway:
            raise GrantError("invalid_grant", "claims.iat", "iat in the future")
        if "nbf" in claims and (
            not isinstance(claims["nbf"], int | float) or claims["nbf"] > now + self.cfg.leeway
        ):
            raise GrantError("invalid_grant", "claims.nbf", "not yet valid")
        if not isinstance(claims.get("jti"), str) or not claims["jti"]:
            raise GrantError("invalid_grant", "claims.jti", "jti missing")
        resources = claims.get("resource")
        if resources is None:
            # draft-06 Section 4.4.1 allows a default; this AS governs exactly one MCP resource
            resources = [self.governed[0]]
        else:
            if isinstance(resources, str):
                resources = [resources]
            if (
                not isinstance(resources, list)
                or not resources
                or not all(isinstance(r, str) for r in resources)
                or len(set(resources)) != len(resources)
            ):
                raise GrantError("invalid_grant", "claims.resource", "malformed resource claim")
            # draft-06 Section 4.4.1: every identifier MUST be governed (Simple String Comp.)
            ungoverned = [r for r in resources if r not in self.governed]
            if ungoverned:
                raise GrantError("invalid_grant", "claims.resource", f"not governed: {ungoverned}")
        # RFC 7523 Section 3 item 7 / draft-06 Section 4.4.4: accept each jti once
        with self._lock:
            if claims["jti"] in self._used_jti:
                raise GrantError("invalid_grant", "claims.jti-replay", "jti already used")
            self._used_jti.add(claims["jti"])
        return {"header": header, "claims": claims, "resources": resources}


def redact_claims(claims: Any) -> Any:
    """Claims are diagnostics; they hold no secrets. Keep them, but bound the size."""
    text = json.dumps(claims, default=str)
    return claims if len(text) < MAX_CLAIMS_LOG else {"_truncated": text[:MAX_CLAIMS_LOG]}


class FixtureHTTPServer(ThreadingHTTPServer):
    """Bind local test endpoints without depending on reverse DNS availability."""

    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


class Fixture:
    def __init__(self, cfg: FixtureConfig, fetch=_http_get_json):
        self.cfg = cfg
        self.events: list[dict] = []
        self._events_lock = threading.Lock()
        self.tokens: dict[str, dict] = {}
        self.as_server = FixtureHTTPServer((cfg.host, 0), _make_as_handler(self))
        self.rs_server = FixtureHTTPServer((cfg.host, 0), _make_rs_handler(self))
        self.as_issuer = f"http://{cfg.host}:{self.as_server.server_address[1]}"
        rs_base = f"http://{cfg.host}:{self.rs_server.server_address[1]}"
        self.resource = rs_base + cfg.resource_path
        self.prm_url = f"{rs_base}/.well-known/oauth-protected-resource{cfg.resource_path}"
        self.keys = IssuerKeys(cfg.idp_issuer, fetch=fetch)
        self.validator = IdJagValidator(
            cfg, self.as_issuer, [self.resource, *cfg.extra_resources], self.keys
        )
        self._threads: list[threading.Thread] = []

    # -- lifecycle
    def start(self) -> Fixture:
        for server in (self.as_server, self.rs_server):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self._threads.append(thread)
        return self

    def stop(self) -> None:
        for server in (self.as_server, self.rs_server):
            server.shutdown()
            server.server_close()

    def describe(self) -> dict:
        return {
            "as_issuer": self.as_issuer,
            "as_metadata_url": f"{self.as_issuer}/.well-known/oauth-authorization-server",
            "token_endpoint": f"{self.as_issuer}/token",
            "resource": self.resource,
            "prm_url": self.prm_url,
            "events_url": f"{self.as_issuer}/_fixture/events",
        }

    def record(self, event: dict) -> None:
        event = {"ts": time.time(), **event}
        with self._events_lock:
            self.events.append(event)
            if self.cfg.events_file:
                with open(self.cfg.events_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, default=str) + "\n")

    # -- Resource AS token endpoint
    def authenticate_client(self, headers, form: dict[str, list[str]]) -> str:
        auth = headers.get("Authorization", "")
        if "client_secret" in form or "client_assertion" in form:
            raise GrantError(
                "invalid_client", "client.auth-method", "only client_secret_basic is supported", 401
            )
        if not auth.startswith("Basic "):
            raise GrantError("invalid_client", "client.auth", "client authentication required", 401)
        try:
            raw = urlsafe_b64decode_std(auth[6:].strip())
            cid, sep, secret = raw.partition(":")
        except ValueError:
            raise GrantError("invalid_client", "client.auth", "malformed Basic auth", 401) from None
        # RFC 6749 Section 2.3.1: credentials are form-urlencoded before Basic encoding
        cid, secret = unquote_plus(cid), unquote_plus(secret)
        expected = self.cfg.clients.get(cid)
        if not sep or expected is None or not secrets.compare_digest(expected, secret):
            raise GrantError("invalid_client", "client.auth", "invalid client credentials", 401)
        return cid

    def token_request(self, headers, form: dict[str, list[str]]) -> tuple[int, dict]:
        event: dict[str, Any] = {"endpoint": "token"}
        try:
            client_id = self.authenticate_client(headers, form)
            event["client_id"] = client_id
            grant_type = form.get("grant_type", [""])
            if grant_type != [GRANT_TYPE_JWT_BEARER]:
                raise GrantError(
                    "unsupported_grant_type", "request.grant_type", f"grant_type {grant_type!r}"
                )
            assertion = form.get("assertion", [])
            if len(assertion) != 1:
                raise GrantError("invalid_request", "request.assertion", "exactly one assertion")
            try:
                header, claims, _, _ = parse_compact_jws(assertion[0])
                event["id_jag"] = {"header": header, "claims": redact_claims(claims)}
            except GrantError:
                pass
            result = self.validator.validate(assertion[0], client_id)
            claims = result["claims"]
            requested = set(str(claims.get("scope", "")).split())
            granted = sorted(requested & set(self.cfg.scopes_supported))
            token = secrets.token_urlsafe(32)
            self.tokens[token] = {
                "iss": claims["iss"],
                "sub": claims["sub"],
                "client_id": client_id,
                "resources": result["resources"],
                "scope": granted,
                "act": claims.get("act"),
                "id_jag_jti": claims["jti"],
                "exp": time.time() + self.cfg.access_token_lifetime,
            }
            body = {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": self.cfg.access_token_lifetime,
            }
            if granted:
                body["scope"] = " ".join(granted)
            event.update(
                outcome="issued",
                granted_scope=granted,
                resources=result["resources"],
                metadata_source=self.keys.metadata_source,
            )
            self.record(event)
            return 200, body
        except GrantError as err:
            event.update(
                outcome="rejected",
                error=err.error,
                rule=err.rule,
                description=err.description,
                key_diagnostics=self.keys.diagnostics[-5:],
            )
            self.record(event)
            return err.status, {"error": err.error, "error_description": err.description}

    def as_metadata(self) -> dict:
        # RFC 8414 + draft-06 Section 7.2
        return {
            "issuer": self.as_issuer,
            "token_endpoint": f"{self.as_issuer}/token",
            "grant_types_supported": [GRANT_TYPE_JWT_BEARER],
            "token_endpoint_auth_methods_supported": ["client_secret_basic"],
            "authorization_grant_profiles_supported": [GRANT_PROFILE_ID_JAG],
            "scopes_supported": self.cfg.scopes_supported,
        }

    # -- MCP protected resource
    def prm(self) -> dict:
        # RFC 9728 Section 2
        return {
            "resource": self.resource,
            "authorization_servers": [self.as_issuer],
            "bearer_methods_supported": ["header"],
            "scopes_supported": self.cfg.scopes_supported,
        }

    def check_bearer(self, headers) -> dict | None:
        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        record = self.tokens.get(auth[7:].strip())
        if not record or record["exp"] < time.time():
            return None
        # MCP EMA profile: access token MUST be audience-restricted to the MCP server
        if self.resource not in record["resources"]:
            return None
        return record

    def mcp_request(self, headers, body: bytes) -> tuple[int, dict | None, dict]:
        extra_headers: dict[str, str] = {}
        record = self.check_bearer(headers)
        if record is None:
            challenge = f'Bearer resource_metadata="{self.prm_url}"'
            if headers.get("Authorization"):
                challenge = f'Bearer error="invalid_token", resource_metadata="{self.prm_url}"'
            self.record(
                {
                    "endpoint": "mcp",
                    "outcome": "unauthorized",
                    "had_token": bool(headers.get("Authorization")),
                }
            )
            return 401, {"error": "invalid_token"}, {"WWW-Authenticate": challenge}
        try:
            msg = json.loads(body)
        except ValueError:
            return 400, _rpc_error(None, -32700, "parse error"), extra_headers
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "method" not in msg:
            return 400, _rpc_error(None, -32600, "invalid request"), extra_headers
        method = msg["method"]
        self.record(
            {
                "endpoint": "mcp",
                "outcome": "authorized",
                "method": method,
                "sub": record["sub"],
                "client_id": record["client_id"],
            }
        )
        if "id" not in msg:  # notification
            return 202, None, extra_headers
        if method == "initialize":
            requested = (msg.get("params") or {}).get("protocolVersion")
            version = requested if requested in MCP_PROTOCOL_VERSIONS else MCP_PROTOCOL_VERSIONS[0]
            result = {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "authentik-id-jag-test-resource", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "whoami",
                        "description": "Return the identity bound to the presented access token",
                        "inputSchema": {"type": "object", "properties": {}},
                    }
                ]
            }
        elif method == "tools/call" and (msg.get("params") or {}).get("name") == "whoami":
            identity = {k: record[k] for k in ("iss", "sub", "client_id", "scope", "act")}
            result = {
                "content": [{"type": "text", "text": json.dumps(identity)}],
                "structuredContent": identity,
                "isError": False,
            }
        else:
            return 200, _rpc_error(msg["id"], -32601, f"method {method!r} not found"), extra_headers
        return 200, {"jsonrpc": "2.0", "id": msg["id"], "result": result}, extra_headers


def urlsafe_b64decode_std(value: str) -> str:
    from base64 import b64decode

    return b64decode(value, validate=True).decode("utf-8")


def _rpc_error(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


class _Handler(BaseHTTPRequestHandler):
    fixture: Fixture
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002 - silence default stderr logging
        return

    def _send(self, status: int, body: dict | None, headers: dict | None = None):
        data = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> bytes:
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))


def _make_as_handler(fixture: Fixture):
    class AsHandler(_Handler):
        def do_GET(self):
            if self.path == "/.well-known/oauth-authorization-server":
                return self._send(200, fixture.as_metadata())
            if self.path == "/_fixture/events":
                return self._send(200, {"events": list(fixture.events)})
            return self._send(404, {"error": "not_found"})

        def do_POST(self):
            if self.path != "/token":
                return self._send(404, {"error": "not_found"})
            if not self.headers.get("Content-Type", "").startswith(
                "application/x-www-form-urlencoded"
            ):
                return self._send(
                    400, {"error": "invalid_request", "error_description": "form encoding required"}
                )
            form = parse_qs(self._body().decode("utf-8"), keep_blank_values=True)
            status, body = fixture.token_request(self.headers, form)
            headers = (
                {"WWW-Authenticate": 'Basic realm="id-jag-test-as"'}
                if status == HTTPStatus.UNAUTHORIZED
                else None
            )
            return self._send(status, body, headers)

    return AsHandler


def _make_rs_handler(fixture: Fixture):
    class RsHandler(_Handler):
        def do_GET(self):
            if self.path == urlsplit(fixture.prm_url).path:
                return self._send(200, fixture.prm())
            if self.path == fixture.cfg.resource_path:
                # No server-initiated SSE stream on this test resource
                return self._send(405, None, {"Allow": "POST"})
            return self._send(404, {"error": "not_found"})

        def do_POST(self):
            if self.path != fixture.cfg.resource_path:
                return self._send(404, {"error": "not_found"})
            status, body, headers = fixture.mcp_request(self.headers, self._body())
            return self._send(status, body, headers)

    return RsHandler


def start_fixture(cfg: FixtureConfig, fetch=_http_get_json) -> Fixture:
    return Fixture(cfg, fetch=fetch).start()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, help="JSON file with FixtureConfig fields")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        raw = json.load(f)
    raw["allowed_algs"] = tuple(raw.get("allowed_algs", DEFAULT_ALLOWED_ALGS))
    fixture = start_fixture(FixtureConfig(**raw))
    # Readiness line, parsed by the acceptance harness. Contains no secrets.
    print(json.dumps({"ready": True, **fixture.describe()}), flush=True)
    try:
        # Exit when the parent closes our stdin (harness teardown) or on SIGTERM
        sys.stdin.read()
    except KeyboardInterrupt:
        pass
    fixture.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
