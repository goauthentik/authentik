"""Live acceptance check: authentik as ID-JAG issuer (IdP Authorization Server).

Pinned spec: draft-ietf-oauth-identity-assertion-authz-grant-06 (see README.md).

Flow exercised against a live authentik (Django live server, real HTTP, production views):

  MCP client discovery (401 -> RFC 9728 PRM -> Resource AS RFC 8414 metadata)
  -> real authentik login (flow executor API) + authorization code/PKCE -> ID Token
  -> authentik token endpoint: RFC 8693 token exchange, requested_token_type=id-jag
  -> independent Resource AS fixture (resource_as.py, separate process, own JOSE code,
     keys discovered from authentik's issuer) redeems the ID-JAG via RFC 7523 jwt-bearer
  -> the Resource AS access token is used at the protected test MCP resource.

Plus negative scenarios at authentik's token endpoint and a client-binding negative at the
Resource AS. Every check in checks.CATALOG must PASS; see checks.Report.verdict().

This module is deliberately NOT named test_*.py: it is an acceptance check that fails until
the ID-JAG issuer feature exists, and must only run when invoked explicitly:

  uv run manage.py test tests/mcp_conformance_id_jag_issuer/acceptance_id_jag.py
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - launches the local test fixture only
import sys
import tempfile
import threading
import time
import traceback
from base64 import urlsafe_b64encode
from collections.abc import Callable
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from secrets import token_urlsafe
from typing import Any
from urllib.parse import parse_qs, urlsplit

import requests
from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse
from dramatiq import get_broker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.apps import Setup
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage
from authentik.tasks.test import use_test_broker
from tests.mcp_conformance_id_jag_issuer import checks
from tests.mcp_conformance_id_jag_issuer.checks import BLOCKED, ERROR, FAIL, PASS, CheckResult
from tests.mcp_conformance_id_jag_issuer.resource_as import (
    GRANT_PROFILE_ID_JAG,
    GRANT_TYPE_JWT_BEARER,
    GrantError,
    IssuerKeys,
    parse_compact_jws,
    verify_signature,
)

HERE = Path(__file__).resolve().parent
RESULTS_DIR = Path(os.environ.get("MCP_CONFORMANCE_RESULTS_DIR", HERE / "results"))

GRANT_TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
TT_ID_JAG = "urn:ietf:params:oauth:token-type:id-jag"
TT_ID_TOKEN = "urn:ietf:params:oauth:token-type:id_token"
ID_JAG_TYP = "oauth-id-jag+jwt"
# Fields PR goauthentik/authentik#26973 (dce0a00534cb) adds to the enterprise Agent model
AGENT_ID_JAG_FIELDS = ("applications", "id_jag_audience", "id_jag_client_id", "id_jag_resources")
UPSTREAM_CONFORMANCE = "modelcontextprotocol/conformance@c37eec888e1c6ff140af79987a40008548b7cc5f"
HTTP_TIMEOUT = 20
FEATURE_REFERENCE = (
    "goauthentik/authentik#26973 @ dce0a00534cb51ebe24d6a8f96ef3bc868006200 (not merged)"
)


class CheckFailed(Exception):
    def __init__(self, summary: str, **details):
        super().__init__(summary)
        self.summary = summary
        self.details = details


def require(condition: bool, summary: str, **details) -> None:
    if not condition:
        raise CheckFailed(summary, **details)


def redact(body: Any) -> Any:
    """Never persist tokens/secrets in artifacts: keep shape and length only."""
    if isinstance(body, dict):
        return {
            k: (
                f"<redacted len={len(v)}>"
                if k
                in {
                    "access_token",
                    "refresh_token",
                    "id_token",
                    "client_secret",
                    "assertion",
                    "subject_token",
                }
                and isinstance(v, str)
                else redact(v)
            )
            for k, v in body.items()
        }
    if isinstance(body, list):
        return [redact(v) for v in body]
    return body


def response_summary(resp: requests.Response) -> dict:
    try:
        body = resp.json()
    except ValueError:
        body = resp.text[:500]
    return {
        "status": resp.status_code,
        "body": redact(body),
        "cache_control": resp.headers.get("Cache-Control"),
        "content_type": resp.headers.get("Content-Type"),
    }


def json_or_empty(resp: requests.Response) -> dict:
    try:
        body = resp.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def aud_values(claims: dict) -> list:
    aud = claims.get("aud")
    return aud if isinstance(aud, list) else [aud]


class FixtureProcess:
    """The independent Resource AS + MCP resource, as a separate Python process."""

    def __init__(self, idp_issuer: str, clients: dict[str, str], events_file: Path):
        self.events_file = events_file
        events_file.parent.mkdir(parents=True, exist_ok=True)
        events_file.write_text("")
        cfg = {"idp_issuer": idp_issuer, "clients": clients, "events_file": str(events_file)}
        fd, self._cfg_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(cfg, f)
        self.stderr_path = events_file.with_name("resource_as.stderr.log")
        self._stderr = open(self.stderr_path, "w")  # noqa: SIM115
        self.proc = subprocess.Popen(  # nosec B603 - fixed argv, local fixture
            [sys.executable, str(HERE / "resource_as.py"), "--config", self._cfg_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._stderr,
            text=True,
        )
        self.info = self._wait_ready()
        # The config file holds client secrets; it is not needed after startup.
        os.unlink(self._cfg_path)

    def _wait_ready(self, timeout: float = 30) -> dict:
        result: dict = {}

        def read():
            line = self.proc.stdout.readline()
            if line:
                result.update(json.loads(line))

        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        reader.join(timeout)
        if not result.get("ready"):
            self.stop()
            raise RuntimeError(
                f"resource AS fixture did not start: rc={self.proc.poll()} "
                f"stderr={self.stderr_path.read_text()[-2000:]}"
            )
        return result

    def events(self) -> list[dict]:
        return [json.loads(line) for line in self.events_file.read_text().splitlines() if line]

    def stop(self) -> None:
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired, OSError:
                self.proc.kill()
                self.proc.wait(timeout=10)
        self._stderr.close()
        if os.path.exists(self._cfg_path):
            os.unlink(self._cfg_path)


class IdJagIssuerAcceptance(StaticLiveServerTestCase):
    """test-mcp-conformance (id-jag-issuer)"""

    RAS_CLIENT_ID = "mcp-client-at-resource-as"
    RAS_OTHER_CLIENT_ID = "another-client-at-resource-as"

    @classmethod
    def _pre_setup(cls):
        use_test_broker()
        return super()._pre_setup()

    def _post_teardown(self):
        broker = get_broker()
        broker.flush_all()
        broker.close()
        return super()._post_teardown()

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self):
        super().setUp()
        apps.get_app_config("authentik_admin").ready()
        Setup.set(True)
        self.ras_secrets = {
            self.RAS_CLIENT_ID: generate_id(),
            self.RAS_OTHER_CLIENT_ID: generate_id(),
        }
        self.user = create_test_user()
        self.password = self.user.username  # create_test_user sets password = username
        self.auth_flow = self._login_flow()
        self.client_a = self._oauth_client("idjag-client-a")
        self.client_b = self._oauth_client("idjag-client-b")
        self.issuer = self.url_for(
            "authentik_providers_oauth2:provider-root", application_slug=self.client_a["app"].slug
        )
        self.fixture = FixtureProcess(
            self.issuer, self.ras_secrets, RESULTS_DIR / "resource_as.events.jsonl"
        )
        self.report = checks.Report(
            {
                "authentik_commit": os.environ.get("GITHUB_SHA") or self._git_sha(),
                "authentik_issuer": self.issuer,
                "fixture": {k: v for k, v in self.fixture.info.items() if k != "ready"},
                "upstream_reference": UPSTREAM_CONFORMANCE,
                "feature_reference": FEATURE_REFERENCE,
            }
        )
        self.state: dict[str, Any] = {}

    def tearDown(self):
        self.fixture.stop()
        super().tearDown()

    # ------------------------------------------------------------------ provisioning helpers
    @staticmethod
    def _git_sha() -> str | None:
        try:
            return subprocess.check_output(  # nosec B603 B607
                ["git", "rev-parse", "HEAD"], cwd=HERE, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except OSError, subprocess.CalledProcessError:
            return None

    def url_for(self, view: str, **kwargs) -> str:
        return self.live_server_url + reverse(view, kwargs=kwargs)

    def _login_flow(self):
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        password = PasswordStage.objects.create(name=generate_id(), backends=[BACKEND_INBUILT])
        ident = IdentificationStage.objects.create(
            name=generate_id(), user_fields=[UserFields.USERNAME], password_stage=password
        )
        login = UserLoginStage.objects.create(name=generate_id())
        FlowStageBinding.objects.create(target=flow, stage=ident, order=0)
        FlowStageBinding.objects.create(target=flow, stage=login, order=1)
        return flow

    def _oauth_client(self, slug_prefix: str) -> dict:
        redirect = f"http://localhost/{slug_prefix}/callback"
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.CONFIDENTIAL,
            client_id=generate_id(),
            client_secret=generate_id(),
            authorization_flow=create_test_flow(FlowDesignation.AUTHORIZATION),
            invalidation_flow=create_test_flow(FlowDesignation.INVALIDATION),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, redirect)],
            signing_key=create_test_cert(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.TOKEN_EXCHANGE],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        app = Application.objects.create(
            name=slug_prefix, slug=f"{slug_prefix}-{generate_id(6).lower()}", provider=provider
        )
        return {
            "provider": provider,
            "app": app,
            "redirect_uri": redirect,
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        }

    # ------------------------------------------------------------------ check plumbing
    def run_check(self, check_id: str, fn: Callable[[], Any], requires: tuple[str, ...] = ()):
        """Run one check. If a prerequisite did not pass, the outcome is BLOCKED even when the
        probe itself 'succeeds' (a negative is vacuous without its positive control), but the
        observed behavior is still recorded."""
        start = time.monotonic()
        missing = [r for r in requires if not self.report.passed(r)]
        try:
            out = fn() or {}
            status, summary = PASS, out.pop("summary", "ok")
            details, notes = out.pop("details", {}), out.pop("notes", [])
        except CheckFailed as exc:
            status, summary, details, notes = FAIL, exc.summary, exc.details, []
        except Exception as exc:  # noqa: BLE001 - harness must record, not crash
            status, summary = ERROR, f"{type(exc).__name__}: {exc}"
            details, notes = {"traceback": traceback.format_exc()[-4000:]}, []
        if missing:
            # Root cause is upstream; keep what this probe observed for diagnostics.
            details = {**details, "observed_status": status}
            status = BLOCKED
            summary = f"prerequisite(s) not passed: {', '.join(missing)} (observed: {summary})"
        self.report.add(
            CheckResult(
                check_id, status, summary, details, notes, round(time.monotonic() - start, 3)
            )
        )

    # ------------------------------------------------------------------ protocol helpers
    def sso(self, client: dict) -> dict:
        """Real login via the flow executor API, then authorization code + PKCE."""
        s = requests.Session()
        executor = self.url_for("authentik_api:flow-executor", flow_slug=self.auth_flow.slug)
        r = s.get(executor, params={"query": ""}, timeout=HTTP_TIMEOUT)
        require(
            r.ok and r.json().get("component") == "ak-stage-identification",
            "login flow did not present identification",
            response=response_summary(r),
        )
        r = s.post(
            executor,
            params={"query": ""},
            timeout=HTTP_TIMEOUT,
            json={
                "component": "ak-stage-identification",
                "uid_field": self.user.username,
                "password": self.password,
            },
        )
        require(
            r.ok and r.json().get("component") == "xak-flow-redirect",
            "login did not complete",
            response=response_summary(r),
        )
        verifier = token_urlsafe(48)
        challenge = urlsafe_b64encode(sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state, nonce = token_urlsafe(16), token_urlsafe(16)
        r = s.get(
            self.url_for("authentik_providers_oauth2:authorize"),
            allow_redirects=False,
            timeout=HTTP_TIMEOUT,
            params={
                "client_id": client["client_id"],
                "redirect_uri": client["redirect_uri"],
                "response_type": "code",
                "scope": "openid profile email",
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        location = r.headers.get("Location", "")
        require(
            r.status_code == HTTPStatus.FOUND and location.startswith(client["redirect_uri"]),
            "authorize did not redirect to the client",
            status=r.status_code,
            location=location.split("?")[0],
        )
        query = parse_qs(urlsplit(location).query)
        require(query.get("state") == [state] and "code" in query, "bad authorization response")
        r = requests.post(
            self.url_for("authentik_providers_oauth2:token"),
            timeout=HTTP_TIMEOUT,
            auth=(client["client_id"], client["client_secret"]),
            data={
                "grant_type": "authorization_code",
                "code": query["code"][0],
                "redirect_uri": client["redirect_uri"],
                "code_verifier": verifier,
            },
        )
        body = json_or_empty(r)
        require(
            r.ok and "id_token" in body,
            "token endpoint returned no id_token",
            response=response_summary(r),
        )
        return {
            "id_token": body["id_token"],
            "access_token": body["access_token"],
            "nonce": nonce,
            "session": s,
        }

    def verify_authentik_jwt(self, token: str) -> tuple[dict, dict]:
        """Verify an authentik-signed JWT with the independent verifier + discovered JWKS."""
        header, claims, signing_input, signature = parse_compact_jws(token)
        keys = self.state.setdefault("idp_keys", IssuerKeys(self.issuer))
        try:
            key = keys.key_for(header)
        except GrantError as err:
            raise CheckFailed(
                f"no authentik JWKS key for header: {err.description}",
                header=header,
                discovery=keys.diagnostics,
            ) from None
        require(
            verify_signature(header.get("alg"), key, signing_input, signature),
            "signature does not verify against authentik JWKS",
            header=header,
        )
        return header, claims

    def exchange(
        self,
        client: dict | None = None,
        *,
        subject_token: str | None = None,
        subject_token_type: str = TT_ID_TOKEN,
        audience: str | list | None = "default",
        resource: str | None = "default",
        scope: str | None = None,
        auth: bool = True,
    ) -> requests.Response:
        client = client or self.client_a
        data: dict[str, Any] = {
            "grant_type": GRANT_TOKEN_EXCHANGE,
            "requested_token_type": TT_ID_JAG,
            "subject_token": subject_token or self.state["sso_a"]["id_token"],
            "subject_token_type": subject_token_type,
        }
        if audience == "default":
            audience = self.state["ras_issuer"]
        if resource == "default":
            resource = self.state["mcp_resource"]
        if audience is not None:
            data["audience"] = audience
        if resource is not None:
            data["resource"] = resource
        if scope is not None:
            data["scope"] = scope
        kwargs: dict[str, Any] = {"timeout": HTTP_TIMEOUT}
        if auth:
            kwargs["auth"] = (client["client_id"], client["client_secret"])
        else:
            data["client_id"] = client["client_id"]
        return requests.post(self.url_for("authentik_providers_oauth2:token"), data=data, **kwargs)

    def expect_rejected(
        self,
        resp: requests.Response,
        errors: tuple[str, ...],
        statuses: tuple[int, ...] = (HTTPStatus.BAD_REQUEST,),
        profile_error: str | None = None,
    ):
        body = json_or_empty(resp)
        observed = response_summary(resp)
        require(
            "access_token" not in body,
            "authentik ISSUED a token for an invalid request",
            response=observed,
        )
        require(
            resp.status_code in statuses and body.get("error") in errors,
            f"expected HTTP {'/'.join(map(str, statuses))} error in {list(errors)}, got "
            f"HTTP {resp.status_code} error={body.get('error')!r}",
            response=observed,
        )
        notes = []
        if profile_error and body.get("error") != profile_error:
            notes.append(
                f"draft-06 §4.3.4.3 profiles '{profile_error}' for this case; authentik "
                f"returned '{body.get('error')}' (allowed by RFC 8693 §2.2.2)"
            )
        return {
            "summary": f"rejected: HTTP {resp.status_code} {body.get('error')}",
            "details": {"response": observed},
            "notes": notes,
        }

    # ------------------------------------------------------------------ checks
    def check_capability(self):
        from authentik.enterprise.agents.models import Agent

        missing = []
        for name in AGENT_ID_JAG_FIELDS:
            try:
                Agent._meta.get_field(name)
            except FieldDoesNotExist:
                missing.append(name)
        require(
            not missing,
            "authentik capability missing: enterprise Agent has no ID-JAG trust "
            f"configuration (missing fields: {', '.join(missing)}); a Resource AS trust "
            "relationship cannot be provisioned",
            missing_fields=missing,
        )
        ras, resource = self.state["ras_issuer"], self.state["mcp_resource"]
        agent = Agent.create_for_user(None)
        agent.id_jag_audience = ras
        agent.id_jag_client_id = self.RAS_CLIENT_ID
        agent.id_jag_resources = [resource]
        agent.save()
        agent.applications.add(self.client_a["app"])
        # A second trusted Resource AS, configured only for client B's application
        other = Agent.create_for_user(None)
        other.id_jag_audience = self.state["other_trusted_audience"]
        other.id_jag_client_id = self.RAS_CLIENT_ID
        other.id_jag_resources = [resource]
        other.save()
        other.applications.add(self.client_b["app"])
        self.state["agent_uid"] = agent.uid
        return {
            "summary": "system agents provisioned for the Resource AS trust relationship",
            "details": {
                "audience": ras,
                "resource": resource,
                "client_id_at_ras": self.RAS_CLIENT_ID,
            },
        }

    def check_mcp_discovery(self):
        mcp = self.fixture.info["resource"]
        r = requests.post(
            mcp, timeout=HTTP_TIMEOUT, json={"jsonrpc": "2.0", "id": 0, "method": "tools/list"}
        )
        challenge = r.headers.get("WWW-Authenticate", "")
        require(
            r.status_code == HTTPStatus.UNAUTHORIZED and "resource_metadata=" in challenge,
            "MCP resource did not challenge",
            status=r.status_code,
        )
        prm_url = challenge.split('resource_metadata="', 1)[1].split('"', 1)[0]
        prm = requests.get(prm_url, timeout=HTTP_TIMEOUT).json()
        # RFC 9728 §3.3 / draft-06 §9.6: resource identical to the URL that was requested
        require(prm.get("resource") == mcp, "PRM resource mismatch", prm=prm)
        ras = prm["authorization_servers"][0]
        meta = requests.get(
            f"{ras}/.well-known/oauth-authorization-server", timeout=HTTP_TIMEOUT
        ).json()
        require(meta.get("issuer") == ras, "Resource AS metadata issuer mismatch", meta=meta)
        require(
            GRANT_PROFILE_ID_JAG in meta.get("authorization_grant_profiles_supported", [])
            and GRANT_TYPE_JWT_BEARER in meta.get("grant_types_supported", []),
            "Resource AS does not advertise the ID-JAG profile",
            meta=meta,
        )
        self.state.update(ras_issuer=ras, mcp_resource=prm["resource"])
        return {
            "summary": "audience/resource taken from validated discovery",
            "details": {"prm": prm, "ras_metadata": meta},
        }

    def check_idp_metadata(self):
        keys = IssuerKeys(self.issuer)
        try:
            meta = keys._load_metadata()
        except GrantError as err:
            raise CheckFailed(err.description, diagnostics=keys.diagnostics) from None
        require(isinstance(meta.get("token_endpoint"), str), "no token_endpoint", meta=meta)
        notes = []
        if GRANT_TOKEN_EXCHANGE not in meta.get("grant_types_supported", []):
            notes.append("grant_types_supported does not list token-exchange (RFC 8414: OPTIONAL)")
        if TT_ID_JAG not in meta.get("identity_chaining_requested_token_types_supported", []):
            notes.append(
                "identity_chaining_requested_token_types_supported lacks id-jag "
                "(draft-06 §7.1 SHOULD)"
            )
        algs = meta.get("id_jag_signing_alg_values_supported")
        require(
            algs is None or "RS256" in algs,
            "id_jag_signing_alg_values_supported present without RS256 (draft-06 §7.1 MUST)",
        )
        self.state["token_endpoint"] = meta["token_endpoint"]
        return {
            "summary": f"metadata via {keys.metadata_source}",
            "details": {
                "metadata_source": keys.metadata_source,
                "token_endpoint": meta["token_endpoint"],
                "jwks_uri": meta["jwks_uri"],
                "lookup_diagnostics": keys.diagnostics,
            },
            "notes": notes,
        }

    def check_sso(self):
        sso = self.sso(self.client_a)
        self.state["sso_a"] = sso
        _, claims = self.verify_authentik_jwt(sso["id_token"])
        require(claims.get("iss") == self.issuer, "ID token iss mismatch", iss=claims.get("iss"))
        require(self.client_a["client_id"] in aud_values(claims), "ID token aud mismatch")
        require(claims.get("nonce") == sso["nonce"], "ID token nonce mismatch")
        self.state["sso_sub"] = claims.get("sub")
        try:
            self.state["sso_b"] = self.sso(self.client_b)
        except CheckFailed as exc:
            self.state["sso_b_error"] = exc.summary
        return {
            "summary": "ID token obtained via real login and verified",
            "details": {
                "id_token_claims": {
                    k: claims.get(k) for k in ("iss", "aud", "sub", "exp", "iat", "jti")
                }
            },
        }

    def check_exchange(self):
        r = self.exchange()
        body = json_or_empty(r)
        observed = response_summary(r)
        self.state["exchange_response"] = observed
        require(
            r.status_code == HTTPStatus.OK,
            f"authentik refused ID-JAG token exchange: HTTP {r.status_code} "
            f"error={body.get('error')!r} {body.get('error_description', '')}".strip(),
            response=observed,
        )
        require(
            body.get("issued_token_type") == TT_ID_JAG,
            f"issued_token_type={body.get('issued_token_type')!r}",
            response=observed,
        )
        require(
            body.get("token_type") == "N_A",
            f"token_type={body.get('token_type')!r}",
            response=observed,
        )
        require(
            isinstance(body.get("access_token"), str) and body["access_token"],
            "no access_token (ID-JAG) in response",
            response=observed,
        )
        require(
            "no-store" in (r.headers.get("Cache-Control") or ""),
            "token response lacks Cache-Control: no-store (RFC 6749 §5.1)",
            response=observed,
        )
        notes = []
        if "refresh_token" in body:
            notes.append("refresh_token returned (draft-06 §4.3.4: SHOULD NOT)")
        if "expires_in" not in body:
            notes.append("expires_in absent (draft-06 §4.3.4: RECOMMENDED)")
        self.state["id_jag"] = body["access_token"]
        return {"summary": "ID-JAG issued", "details": {"response": observed}, "notes": notes}

    def check_assertion_jose(self):
        header, _, _, _ = parse_compact_jws(self.state["id_jag"])
        require(
            str(header.get("typ", "")).lower().removeprefix("application/") == ID_JAG_TYP,
            f"typ={header.get('typ')!r}",
            header=header,
        )
        require(
            header.get("alg") not in (None, "none") and not str(header["alg"]).startswith("HS"),
            f"alg={header.get('alg')!r}",
            header=header,
        )
        header, claims = self.verify_authentik_jwt(self.state["id_jag"])
        self.state["id_jag_claims"] = claims
        return {
            "summary": f"typ={header['typ']} alg={header['alg']} signature verified",
            "details": {"header": header},
        }

    def check_assertion_claims(self):
        claims = self.state["id_jag_claims"]
        now = time.time()
        problems = []
        for name in ("iss", "sub", "aud", "client_id", "jti", "exp", "iat"):
            if name not in claims:
                problems.append(f"missing REQUIRED claim {name}")
        if claims.get("iss") != self.issuer:
            problems.append(f"iss {claims.get('iss')!r} != authentik issuer {self.issuer!r}")
        auds = aud_values(claims)
        if auds != [self.state["ras_issuer"]]:
            problems.append(f"aud {claims.get('aud')!r} != Resource AS issuer")
        if claims.get("client_id") != self.RAS_CLIENT_ID:
            problems.append(
                f"client_id {claims.get('client_id')!r} is not the client's id at "
                f"the Resource AS ({self.RAS_CLIENT_ID!r}) (draft-06 §3.1, §5.1)"
            )
        if claims.get("sub") != self.state.get("sso_sub"):
            problems.append("sub does not identify the SSO user (ID token sub)")
        if not (
            isinstance(claims.get("exp"), int | float)
            and claims["exp"] > now
            and isinstance(claims.get("iat"), int | float)
            and claims["iat"] <= now + 30
            and claims["exp"] > claims["iat"]
        ):
            problems.append(f"exp/iat invalid: exp={claims.get('exp')} iat={claims.get('iat')}")
        res = claims.get("resource")
        res = [res] if isinstance(res, str) else res
        # draft-06 §4.3.3: a granted resource MUST appear exactly as sent
        if not isinstance(res, list) or self.state["mcp_resource"] not in res:
            problems.append(
                f"resource claim {claims.get('resource')!r} does not contain the "
                "requested resource exactly as sent"
            )
        if "act" in claims and not isinstance(claims["act"], dict):
            problems.append("act claim is not a JSON object (RFC 8693 §4.1)")
        notes = []
        if "act" in claims:
            notes.append(f"act present: {claims['act']} (OPTIONAL, draft-06 §3.1)")
        if not ({"email", "aud_sub"} & claims.keys()):
            notes.append("neither email nor aud_sub present (draft-06 §3.1 RECOMMENDED)")
        require(not problems, "; ".join(problems), claims=claims)
        return {
            "summary": "required claims present and bound",
            "details": {"claims": claims},
            "notes": notes,
        }

    def check_not_bearer(self):
        r = requests.get(
            self.url_for("authentik_providers_oauth2:userinfo"),
            timeout=HTTP_TIMEOUT,
            headers={"Authorization": f"Bearer {self.state['id_jag']}"},
        )
        require(
            r.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN),
            f"authentik userinfo accepted the ID-JAG as a bearer token (HTTP {r.status_code})",
        )
        return {"summary": f"userinfo refused ID-JAG (HTTP {r.status_code})"}

    def redeem(self, client_id: str) -> requests.Response:
        return requests.post(
            self.fixture.info["token_endpoint"],
            timeout=HTTP_TIMEOUT,
            auth=(client_id, self.ras_secrets[client_id]),
            data={"grant_type": GRANT_TYPE_JWT_BEARER, "assertion": self.state["id_jag"]},
        )

    def last_fixture_event(self) -> dict:
        events = [e for e in self.fixture.events() if e["endpoint"] == "token"]
        return events[-1] if events else {}

    def check_ras_client_binding(self):
        r = self.redeem(self.RAS_OTHER_CLIENT_ID)
        event = self.last_fixture_event()
        require(
            r.status_code == HTTPStatus.BAD_REQUEST
            and json_or_empty(r).get("error") == "invalid_grant"
            and event.get("rule") == "claims.client_id",
            "Resource AS did not reject the ID-JAG for a different client on client_id",
            response=response_summary(r),
            fixture_event=event,
        )
        return {
            "summary": "rejected for the other client (rule claims.client_id)",
            "details": {"fixture_event": event},
        }

    def check_ras_redeem(self):
        r = self.redeem(self.RAS_CLIENT_ID)
        event = self.last_fixture_event()
        body = json_or_empty(r)
        require(
            r.status_code == HTTPStatus.OK and body.get("token_type") == "Bearer",
            f"Resource AS rejected the authentik ID-JAG: {event.get('rule')} "
            f"{event.get('description')}",
            response=response_summary(r),
            fixture_event=event,
        )
        self.state["ras_token"] = body["access_token"]
        return {
            "summary": "Resource AS issued an access token",
            "details": {"fixture_event": event, "response": response_summary(r)},
        }

    def check_mcp_access(self):
        mcp, token = self.state["mcp_resource"], self.state["ras_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/event-stream",
        }

        def rpc(payload):
            return requests.post(mcp, json=payload, headers=headers, timeout=HTTP_TIMEOUT)

        init = rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "authentik-id-jag-acceptance", "version": "1"},
                },
            }
        )
        require(
            init.status_code == HTTPStatus.OK and "result" in json_or_empty(init),
            "MCP initialize failed",
            response=response_summary(init),
        )
        headers["MCP-Protocol-Version"] = init.json()["result"]["protocolVersion"]
        rpc({"jsonrpc": "2.0", "method": "notifications/initialized"})
        call = rpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "whoami", "arguments": {}},
            }
        )
        identity = json_or_empty(call).get("result", {}).get("structuredContent", {})
        require(
            call.status_code == HTTPStatus.OK
            and identity.get("sub") == self.state["id_jag_claims"]["sub"]
            and identity.get("iss") == self.issuer
            and identity.get("client_id") == self.RAS_CLIENT_ID,
            "MCP tool call did not run as the ID-JAG subject",
            identity=identity,
            response=response_summary(call),
        )
        return {
            "summary": "MCP tools/call succeeded as the SSO user",
            "details": {"identity": identity},
        }

    def check_scope_semantics(self):
        requested = {"mcp:tools"}
        r = self.exchange(scope="mcp:tools")
        body = json_or_empty(r)
        if r.status_code == HTTPStatus.BAD_REQUEST and body.get("error") == "invalid_scope":
            return {"summary": "scope refused with invalid_scope (allowed)"}
        require(
            r.status_code == HTTPStatus.OK,
            f"exchange with scope failed: HTTP {r.status_code} " f"{body.get('error')}",
            response=response_summary(r),
        )
        _, claims = self.verify_authentik_jwt(body["access_token"])
        claim = set(str(claims.get("scope", "")).split())
        response_scope = body.get("scope")
        granted = set(response_scope.split()) if isinstance(response_scope, str) else requested
        require(
            claim == granted,
            f"scope silently changed: requested {sorted(requested)}, ID-JAG scope claim "
            f"{sorted(claim)}, response scope {response_scope!r} (draft-06 §4.3.3 MUST "
            "include granted values; §4.3.4 scope REQUIRED when it differs)",
            claims=claims,
            response=response_summary(r),
        )
        return {"summary": f"granted {sorted(granted)} consistently"}

    def negative(
        self,
        request: Callable[[], dict[str, Any]],
        errors: tuple[str, ...],
        statuses: tuple[int, ...] = (HTTPStatus.BAD_REQUEST,),
        profile_error: str | None = None,
    ) -> Callable[[], dict]:
        """A negative probe. `request` is evaluated lazily so missing state from a failed
        earlier step is recorded by run_check instead of crashing the harness."""

        def run():
            return self.expect_rejected(self.exchange(**request()), errors, statuses, profile_error)

        return run

    def neg_wrong_client(self):
        require(
            "sso_b" in self.state,
            f"could not obtain client B ID token: " f"{self.state.get('sso_b_error')}",
        )
        return self.negative(
            lambda: {"subject_token": self.state["sso_b"]["id_token"]}, ("invalid_request",)
        )()

    def neg_tampered(self):
        header, payload, sig = self.state["sso_a"]["id_token"].split(".")
        claims = json.loads(urlsafe_b64decode_padded(payload))
        claims["sub"] = "attacker"
        forged = urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        return self.negative(
            lambda: {"subject_token": f"{header}.{forged}.{sig}"}, ("invalid_request",)
        )()

    # ------------------------------------------------------------------ the test
    def test_id_jag_issuer(self):
        positive = ("exchange.id-jag-issued",)
        self.state["other_trusted_audience"] = f"{self.fixture.info['as_issuer']}/other-trusted-as"
        self.run_check("discovery.mcp-prm", self.check_mcp_discovery)
        self.run_check(
            "capability.agent-id-jag-config", self.check_capability, requires=("discovery.mcp-prm",)
        )
        self.run_check("discovery.idp-metadata", self.check_idp_metadata)
        self.run_check("sso.id-token", self.check_sso)
        base = ("sso.id-token", "discovery.mcp-prm")
        # Not gated on provisioning: when the capability is absent the exchange is still sent,
        # so the report shows authentik's own protocol response as the failure.
        self.run_check("exchange.id-jag-issued", self.check_exchange, requires=base)
        self.run_check("assertion.jose", self.check_assertion_jose, requires=positive)
        self.run_check(
            "assertion.claims", self.check_assertion_claims, requires=("assertion.jose",)
        )
        self.run_check("assertion.not-a-bearer-token", self.check_not_bearer, requires=positive)
        self.run_check(
            "ras.client-binding", self.check_ras_client_binding, requires=("assertion.jose",)
        )
        self.run_check("ras.redeem", self.check_ras_redeem, requires=("assertion.jose",))
        self.run_check("mcp.access", self.check_mcp_access, requires=("ras.redeem",))
        self.run_check("exchange.scope-semantics", self.check_scope_semantics, requires=positive)
        # Negatives: each is only meaningful once the positive control has passed.
        self.run_check("negative.wrong-client-id-token", self.neg_wrong_client, requires=positive)
        self.run_check("negative.tampered-id-token", self.neg_tampered, requires=positive)
        self.run_check(
            "negative.access-token-as-subject",
            self.negative(
                lambda: {"subject_token": self.state["sso_a"]["access_token"]},
                ("invalid_request",),
            ),
            requires=positive,
        )
        self.run_check(
            "negative.id-jag-as-subject",
            self.negative(lambda: {"subject_token": self.state["id_jag"]}, ("invalid_request",)),
            requires=positive,
        )
        self.run_check(
            "negative.unknown-audience",
            self.negative(
                lambda: {"audience": f"{self.fixture.info['as_issuer']}/unknown-as"},
                ("invalid_target",),
            ),
            requires=positive,
        )
        self.run_check(
            "negative.multiple-audiences",
            self.negative(
                lambda: {
                    "audience": [self.state["ras_issuer"], self.state["other_trusted_audience"]]
                },
                ("invalid_request",),
            ),
            requires=positive,
        )
        self.run_check(
            "negative.resource-not-governed",
            self.negative(
                lambda: {"resource": f"{self.state['mcp_resource']}-not-governed"},
                ("invalid_target",),
            ),
            requires=positive,
        )
        self.run_check(
            "negative.client-not-authorized-for-audience",
            self.negative(
                lambda: {"audience": self.state["other_trusted_audience"]},
                ("access_denied", "invalid_target"),
                profile_error="access_denied",
            ),
            requires=(*positive, "capability.agent-id-jag-config"),
        )
        self.run_check(
            "negative.no-client-auth",
            self.negative(
                lambda: {"auth": False},
                ("invalid_client",),
                (HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED),
            ),
            requires=positive,
        )

        self.report.write(RESULTS_DIR)
        ok, problems = self.report.verdict()
        self.assertTrue(
            ok,
            "ID-JAG issuer acceptance failed:\n  "
            + "\n  ".join(problems)
            + f"\nFull report: {RESULTS_DIR / 'report.json'}",
        )


def urlsafe_b64decode_padded(value: str) -> bytes:
    from base64 import urlsafe_b64decode

    return urlsafe_b64decode(value + "=" * (-len(value) % 4))
