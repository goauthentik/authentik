"""Live acceptance check: MCP Enterprise-Managed Authorization end to end, with the official
MCP TypeScript SDK as an independent client and authentik in both ID-JAG roles.
Pinned spec: draft-ietf-oauth-identity-assertion-authz-grant-06 (see README.md).

  authentik (live server)                       Node harness (harness/, own lockfile)
  -----------------------                       -------------------------------------
  IdP provider  <-- 1. OIDC code + PKCE ------- openid-client
                <-- 2. token exchange --------- SDK discoverAndRequestJwtAuthGrant
  RAS provider  <-- 3. jwt-bearer ------------- SDK CrossAppAccessProvider / exchangeJwtAuthGrant
                                                4. SDK Client + StreamableHTTPClientTransport
                                                   -> minimal MCP server (server SDK), whose
                                                      RFC 9728 metadata names the RAS provider

This module configures authentik (admin API where it exposes the setting), runs the harness
once, and turns its observations into the checks in catalog.CATALOG, gating negatives on
their positive controls. Every check must PASS; see checks.Report.verdict().

Not named test_*.py, so it only runs when invoked explicitly:
  uv run manage.py test tests/mcp_conformance_id_jag_mcp_client/acceptance_mcp_client.py
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess  # nosec B404 - launches the local Node harness only
from http import HTTPStatus
from pathlib import Path
from typing import Any

import requests
from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from dramatiq import get_broker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.apps import Setup
from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import GrantType
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.tasks.test import use_test_broker
from tests.mcp_conformance_id_jag_issuer import acceptance_id_jag as issuer_suite
from tests.mcp_conformance_id_jag_issuer import checks
from tests.mcp_conformance_id_jag_issuer.acceptance_id_jag import (
    HTTP_TIMEOUT,
    CheckFailed,
    require,
    response_summary,
)
from tests.mcp_conformance_id_jag_mcp_client.catalog import CATALOG, SUITE

HERE = Path(__file__).resolve().parent
RESULTS_DIR = Path(os.environ.get("MCP_CONFORMANCE_RESULTS_DIR", HERE / "results"))
HARNESS = HERE / "harness" / "run.mjs"
HARNESS_TIMEOUT = 300
FEATURE_REFERENCE = "providers/oauth2/id-jag-resource-as (not merged)"
MCP_STRICT_PATH = "/mcp"


class HarnessError(Exception):
    """The harness raised instead of observing a protocol outcome (reported as ERROR)"""


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def package_version(name: str) -> str | None:
    path = HERE / "node_modules" / name / "package.json"
    try:
        return json.loads(path.read_text())["version"]
    except OSError, ValueError, KeyError:
        return None


class IdJagMcpClientAcceptance(StaticLiveServerTestCase):
    """test-mcp-conformance (id-jag-mcp-client)"""

    # Live-server plumbing shared with the issuer suite (none of these use super()). The
    # issuer test class is reached through its module, so this module doesn't collect it.
    url_for = issuer_suite.IdJagIssuerAcceptance.url_for
    run_check = issuer_suite.IdJagIssuerAcceptance.run_check
    _git_sha = staticmethod(issuer_suite.IdJagIssuerAcceptance._git_sha)
    _login_flow = issuer_suite.IdJagIssuerAcceptance._login_flow
    _oauth_client = issuer_suite.IdJagIssuerAcceptance._oauth_client

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
        self.user = create_test_user()
        self.password = self.user.username  # create_test_user sets password = username
        self.auth_flow = self._login_flow()
        # IdP side: the MCP client's application, and one the agent isn't linked to
        self.idp = self._oauth_client("idjag-mcp-client")
        self.idp_unlinked = self._oauth_client("idjag-unlinked")
        # Resource AS side: the MCP server's authorization server
        self.ras = self._oauth_client("idjag-mcp-server-as")
        self.idp_issuer = self.issuer_of(self.idp)
        self.ras_issuer = self.issuer_of(self.ras)
        self.mcp_port = free_port()
        self.mcp_resource = f"http://localhost:{self.mcp_port}{MCP_STRICT_PATH}"
        admin = create_test_admin_user()
        self.api_token = Token.objects.create(
            identifier=generate_id(), user=admin, intent=TokenIntents.INTENT_API, expiring=False
        ).key
        self.versions = {
            "client": package_version("@modelcontextprotocol/client"),
            "server": package_version("@modelcontextprotocol/server"),
            "openid-client": package_version("openid-client"),
            "jose": package_version("jose"),
        }
        self.report = checks.Report(
            {
                "authentik_commit": os.environ.get("GITHUB_SHA") or self._git_sha(),
                "idp_issuer": self.idp_issuer,
                "resource_as_issuer": self.ras_issuer,
                "mcp_resource": self.mcp_resource,
                "harness_packages": self.versions,
                "feature_reference": FEATURE_REFERENCE,
            },
            catalog=CATALOG,
            suite=SUITE,
        )
        self.harness: dict[str, Any] = {}

    def issuer_of(self, client: dict) -> str:
        return self.url_for(
            "authentik_providers_oauth2:provider-root", application_slug=client["app"].slug
        )

    def api(self, method: str, path: str, **kwargs) -> requests.Response:
        return requests.request(
            method,
            f"{self.live_server_url}/api/v3/{path}",
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=HTTP_TIMEOUT,
            **kwargs,
        )

    # ------------------------------------------------------------------ configuration
    def check_config(self):
        from authentik.enterprise.agents.models import Agent

        metadata_url = f"{self.idp_issuer}.well-known/openid-configuration"
        resp = self.api(
            "POST",
            "sources/oauth/",
            json={
                "name": "authentik IdP Authorization Server",
                "slug": f"authentik-idp-{generate_id(6).lower()}",
                "provider_type": "openidconnect",
                "consumer_key": generate_id(),
                "consumer_secret": generate_id(),
                "oidc_well_known_url": metadata_url,
                "authorization_url": self.url_for("authentik_providers_oauth2:authorize"),
                "access_token_url": self.url_for("authentik_providers_oauth2:token"),
                "profile_url": self.url_for("authentik_providers_oauth2:userinfo"),
            },
        )
        require(
            resp.status_code == HTTPStatus.CREATED,
            f"creating the IdP source failed: HTTP {resp.status_code}",
            response=response_summary(resp),
        )
        source = OAuthSource.objects.get(pk=resp.json()["pk"])
        require(source.oidc_jwks.get("keys"), "authentik did not load the IdP's JWKS")
        provider = self.ras["provider"]
        resp = self.api(
            "PATCH",
            f"providers/oauth2/{provider.pk}/",
            json={
                "grant_types": [*provider.grant_types, GrantType.JWT_BEARER],
                "jwt_federation_sources": [str(source.pk)],
            },
        )
        require(
            resp.ok,
            f"enabling jwt-bearer on the Resource AS provider failed: HTTP {resp.status_code}",
            response=response_summary(resp),
        )
        # The IdP's trust relationship for the Resource AS (system agent; same as the other
        # ID-JAG suites)
        agent = Agent.create_for_user(None)
        agent.id_jag_audience = self.ras_issuer
        agent.id_jag_client_id = self.ras["client_id"]
        agent.id_jag_resources = [self.mcp_resource]
        agent.save()
        agent.applications.add(self.idp["app"])
        # The user has signed in through the IdP before, as an SSO would record it
        UserOAuthSourceConnection.objects.create(
            user=self.user,
            source=source,
            identifier=IDToken()._resolve_sub(self.idp["provider"], self.user),
        )
        return {
            "summary": "IdP trusted by the Resource AS; agent links the MCP client to it",
            "details": {
                "source_metadata_url": metadata_url,
                "agent": {
                    "id_jag_audience": self.ras_issuer,
                    "id_jag_resources": [self.mcp_resource],
                },
            },
        }

    # ------------------------------------------------------------------ the harness
    def run_harness(self) -> dict:
        node = os.environ.get("MCP_CLIENT_NODE") or shutil.which("node")
        if not node:
            raise HarnessError("node not found (set MCP_CLIENT_NODE or put Node 24 on PATH)")
        if not (HERE / "node_modules" / "@modelcontextprotocol" / "client").exists():
            raise HarnessError(f"harness dependencies missing: run `pnpm install` in {HERE}")
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        results_file = RESULTS_DIR / "harness.json"
        login = {
            "flow_slug": self.auth_flow.slug,
            "username": self.user.username,
            "password": self.password,
        }
        config = {
            "authentik": self.live_server_url,
            "idp": self.client_config(self.idp, self.idp_issuer),
            "idp_unlinked": self.client_config(
                self.idp_unlinked, self.issuer_of(self.idp_unlinked)
            ),
            "ras": self.client_config(self.ras, self.ras_issuer),
            "login": login,
            "mcp_port": self.mcp_port,
            "untrusted_audience": f"{self.live_server_url}/application/o/not-a-trusted-as/",
            "results_file": str(results_file),
            "versions": self.versions,
        }
        stderr_path = RESULTS_DIR / "harness.stderr.log"
        with open(stderr_path, "w") as stderr:
            # Secrets go over stdin, never argv or the environment
            proc = subprocess.run(  # nosec B603 - fixed argv, local harness
                [node, str(HARNESS)],
                input=json.dumps(config),
                cwd=HERE,
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                text=True,
                timeout=HARNESS_TIMEOUT,
                check=False,
            )
        if proc.returncode != 0 or not results_file.exists():
            tail = stderr_path.read_text()[-2000:]
            for secret in self.secrets():
                tail = tail.replace(secret, "<redacted>")
            stderr_path.write_text(tail)
            raise HarnessError(f"harness exited with {proc.returncode}: {tail}")
        return json.loads(results_file.read_text())

    def client_config(self, client: dict, issuer: str) -> dict:
        return {
            "issuer": issuer,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uri"],
        }

    def secrets(self) -> list[str]:
        clients = (self.idp, self.idp_unlinked, self.ras)
        return [c["client_secret"] for c in clients] + [self.password, self.api_token]

    def observed(self, check_id: str, verify=None):
        """A check backed by a harness observation, with optional authentik-side checks"""

        def run():
            if "error" in self.harness:
                raise HarnessError(self.harness["error"])
            result = self.harness.get("results", {}).get(check_id)
            if result is None:
                raise HarnessError("the harness produced no observation for this check")
            details = {**result.get("details", {}), "http": result.get("http", [])}
            if result["status"] == checks.FAIL:
                raise CheckFailed(result["summary"], **details)
            if result["status"] != checks.PASS:
                raise HarnessError(f"{result['summary']} {json.dumps(details)[:2000]}")
            if verify:
                verify(result)
            return {"summary": result["summary"], "details": details, "notes": result["notes"]}

        return run

    def verify_exchange(self, result: dict):
        expected = IDToken()._resolve_sub(self.idp["provider"], self.user)
        claims = result["details"].get("claims", {})
        require(claims.get("sub") == expected, "ID-JAG sub isn't the user's subject at the IdP")

    def verify_identity(self, result: dict):
        identity = result["details"].get("identity", {})
        expected = IDToken()._resolve_sub(self.ras["provider"], self.user)
        require(
            identity.get("sub") == expected,
            "the MCP server didn't see the user connected to the ID-JAG subject",
            identity=identity,
        )

    def test_id_jag_mcp_client(self):
        self.run_check("config.authentik-both-roles", self.check_config)
        if self.report.passed("config.authentik-both-roles"):
            try:
                self.harness = self.run_harness()
            except (HarnessError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
                self.harness = {"error": f"{type(exc).__name__}: {exc}"}
        else:
            self.harness = {"error": "authentik was not configured; the harness did not run"}

        config = ("config.authentik-both-roles",)
        steps: list[tuple[str, tuple[str, ...], Any]] = [
            ("mcp.discovery", config, None),
            ("sso.id-token", config, None),
            ("exchange.id-jag", ("sso.id-token", "mcp.discovery"), self.verify_exchange),
            ("exchange.scope-forwarding", ("exchange.id-jag",), None),
            ("redeem.resource-bound", ("exchange.id-jag",), None),
            ("redeem.id-jag", ("sso.id-token", "mcp.discovery"), None),
            ("redeem.client-auth-methods", ("redeem.id-jag",), None),
            ("mcp.tool-call", ("redeem.id-jag",), self.verify_identity),
            ("mcp.audience-bound", ("mcp.tool-call",), self.verify_identity),
            ("e2e.sdk-default", ("exchange.id-jag", "mcp.tool-call"), self.verify_identity),
            # Negatives are vacuous without their positive control
            ("neg.exchange.wrong-audience", ("exchange.id-jag",), None),
            ("neg.exchange.unregistered-resource", ("exchange.id-jag",), None),
            ("neg.exchange.unlinked-app", ("exchange.id-jag",), None),
            ("neg.redeem.replay", ("redeem.id-jag",), None),
        ]
        for check_id, requires, verify in steps:
            self.run_check(check_id, self.observed(check_id, verify), requires=requires)

        self.report.meta["sdk_warnings"] = self.harness.get("sdk_warnings", [])
        self.report.write(RESULTS_DIR)
        ok, problems = self.report.verdict()
        self.assertTrue(
            ok,
            "ID-JAG MCP client acceptance failed:\n  "
            + "\n  ".join(problems)
            + f"\nFull report: {RESULTS_DIR / 'report.json'}",
        )
