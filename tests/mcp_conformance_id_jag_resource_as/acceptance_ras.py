"""Live acceptance check: authentik as ID-JAG Resource Authorization Server.
Pinned spec: draft-ietf-oauth-identity-assertion-authz-grant-06 §4.4 (see README.md).

Flow exercised against a live authentik (Django live server, real HTTP, production views):
  admin API: trust a stub IdP Authorization Server (OIDC source from its metadata URL)
  -> stub IdP (stdlib + cryptography, separate code from authentik) signs ID-JAGs
  -> authentik token endpoint: RFC 7523 jwt-bearer with client_secret_basic
  -> the access token is verified with an independent JOSE verifier and used at userinfo.
Plus authentik-to-authentik (authentik issues the ID-JAG via token exchange, then redeems
it), and §4.4.1 negatives. Every check in catalog.CATALOG must PASS.

Not named test_*.py, so it only runs when invoked explicitly:
  uv run manage.py test tests/mcp_conformance_id_jag_resource_as/acceptance_ras.py
"""

from __future__ import annotations

import os
import time
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
    ID_JAG_TYP,
    TT_ID_JAG,
    CheckFailed,
    json_or_empty,
    require,
    response_summary,
)
from tests.mcp_conformance_id_jag_issuer.resource_as import (
    GRANT_PROFILE_ID_JAG,
    GRANT_TYPE_JWT_BEARER,
    GrantError,
    IssuerKeys,
    parse_compact_jws,
    verify_signature,
)
from tests.mcp_conformance_id_jag_issuer.selfcheck_resource_as import StubIdP
from tests.mcp_conformance_id_jag_resource_as.catalog import CATALOG, SUITE

HERE = Path(__file__).resolve().parent
RESULTS_DIR = Path(os.environ.get("MCP_CONFORMANCE_RESULTS_DIR", HERE / "results"))
FEATURE_REFERENCE = "providers/oauth2/id-jag-resource-as (not merged)"
# A protected resource the RAS provider would govern, once providers can declare them
MCP_RESOURCE_PATH = "/mcp"
IDP_SCOPE = "openid profile"


class IdJagResourceASAcceptance(StaticLiveServerTestCase):
    """test-mcp-conformance (id-jag-resource-as)"""

    # Live-server plumbing shared with the issuer suite (none of these use super()). The
    # issuer test class is reached through its module, so this module doesn't collect it.
    url_for = issuer_suite.IdJagIssuerAcceptance.url_for
    run_check = issuer_suite.IdJagIssuerAcceptance.run_check
    sso = issuer_suite.IdJagIssuerAcceptance.sso
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
        self.idp = StubIdP(issuer_path="/tenant-a/")
        self.user = create_test_user()
        self.password = self.user.username  # create_test_user sets password = username
        self.subject = f"idp-user-{generate_id(8)}"
        self.auth_flow = self._login_flow()
        self.ras = self._oauth_client("idjag-ras")
        self.ras_issuer = self.url_for(
            "authentik_providers_oauth2:provider-root", application_slug=self.ras["app"].slug
        )
        admin = create_test_admin_user()
        self.api_token = Token.objects.create(
            identifier=generate_id(), user=admin, intent=TokenIntents.INTENT_API, expiring=False
        ).key
        self.report = checks.Report(
            {
                "authentik_commit": os.environ.get("GITHUB_SHA") or self._git_sha(),
                "authentik_issuer": self.ras_issuer,
                "idp_issuer": self.idp.issuer,
                "feature_reference": FEATURE_REFERENCE,
            },
            catalog=CATALOG,
            suite=SUITE,
        )
        self.state: dict[str, Any] = {}

    def tearDown(self):
        self.idp.stop()
        super().tearDown()

    # ------------------------------------------------------------------ helpers
    def api(self, method: str, path: str, **kwargs) -> requests.Response:
        return requests.request(
            method,
            f"{self.live_server_url}/api/v3/{path}",
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=HTTP_TIMEOUT,
            **kwargs,
        )

    def claims(self, **overrides: Any) -> dict[str, Any]:
        now = int(time.time())
        claims = {
            "iss": self.idp.issuer,
            "sub": self.subject,
            "aud": self.ras_issuer,
            "client_id": self.ras["client_id"],
            "jti": generate_id(),
            "iat": now,
            "exp": now + 300,
            "scope": IDP_SCOPE,
        }
        claims.update(overrides)
        return {k: v for k, v in claims.items() if v is not None}

    def id_jag(self, header: dict | None = None, key: str = "rsa1", **overrides: Any) -> str:
        return self.idp.sign(self.claims(**overrides), header=header, key=key)

    def redeem(self, assertion: str, auth: bool = True, **extra: str) -> requests.Response:
        data = {"grant_type": GRANT_TYPE_JWT_BEARER, "assertion": assertion, **extra}
        kwargs: dict[str, Any] = {"timeout": HTTP_TIMEOUT}
        if auth:
            kwargs["auth"] = (self.ras["client_id"], self.ras["client_secret"])
        else:
            data["client_id"] = self.ras["client_id"]
        return requests.post(self.url_for("authentik_providers_oauth2:token"), data=data, **kwargs)

    def expect_issued(self, resp: requests.Response) -> dict:
        body = json_or_empty(resp)
        require(
            resp.status_code == HTTPStatus.OK and isinstance(body.get("access_token"), str),
            f"expected an access token, got HTTP {resp.status_code} "
            f"error={body.get('error')!r}",
            response=response_summary(resp),
        )
        return body

    def verify_access_token(self, token: str) -> tuple[dict, dict]:
        """Verify an authentik access token with the independent verifier + discovered JWKS"""
        header, claims, signing_input, signature = parse_compact_jws(token)
        keys = self.state.setdefault("ras_keys", IssuerKeys(self.ras_issuer))
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
            "access token signature does not verify against authentik JWKS",
            header=header,
        )
        return header, claims

    def rejects(
        self,
        assertion: Any,
        errors: tuple[str, ...] = ("invalid_grant",),
        statuses: tuple[int, ...] = (HTTPStatus.BAD_REQUEST,),
        **redeem_kwargs,
    ):
        def probe():
            value = assertion() if callable(assertion) else assertion
            resp = self.redeem(value, **redeem_kwargs)
            body = json_or_empty(resp)
            observed = response_summary(resp)
            require(
                "access_token" not in body,
                "authentik ISSUED an access token for an invalid ID-JAG",
                response=observed,
            )
            require(
                resp.status_code in statuses and body.get("error") in errors,
                f"expected HTTP {'/'.join(map(str, statuses))} error in {list(errors)}, got "
                f"HTTP {resp.status_code} error={body.get('error')!r}",
                response=observed,
            )
            return {
                "summary": f"rejected: HTTP {resp.status_code} {body.get('error')}",
                "details": {"response": observed},
            }

        return probe

    # ------------------------------------------------------------------ checks
    def check_trust_idp(self):
        metadata_url = (
            f"{self.idp.base}/.well-known/oauth-authorization-server"
            f"{self.idp.issuer.removeprefix(self.idp.base).rstrip('/')}"
        )
        resp = self.api(
            "POST",
            "sources/oauth/",
            json={
                "name": "Stub IdP Authorization Server",
                "slug": f"stub-idp-{generate_id(6).lower()}",
                "provider_type": "openidconnect",
                "consumer_key": generate_id(),
                "consumer_secret": generate_id(),
                "oidc_well_known_url": metadata_url,
                # The stub publishes no browser endpoints; SSO through it isn't exercised
                "authorization_url": f"{self.idp.base}/authorize",
                "access_token_url": f"{self.idp.base}/token",
                "profile_url": f"{self.idp.base}/userinfo",
            },
        )
        require(
            resp.status_code == HTTPStatus.CREATED,
            f"creating the IdP source failed: HTTP {resp.status_code}",
            response=response_summary(resp),
        )
        source = OAuthSource.objects.get(pk=resp.json()["pk"])
        kids = sorted(k.get("kid") for k in source.oidc_jwks.get("keys", []))
        require("rsa1" in kids, "authentik did not load the IdP's JWKS", kids=kids)
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
            f"enabling jwt-bearer on the provider failed: HTTP {resp.status_code}",
            response=response_summary(resp),
        )
        # The user has previously signed in through this IdP (as an SSO would record it)
        UserOAuthSourceConnection.objects.create(
            user=self.user, source=source, identifier=self.subject
        )
        self.state["source"] = source
        return {
            "summary": "IdP trusted through the admin API from its metadata URL",
            "details": {"metadata_url": metadata_url, "jwks_kids": kids},
            "notes": [
                "The source API checks the metadata has an issuer, but doesn't compare it with "
                "the issuer the URL is derived from (draft-06 §9.5); redemption binds iss to "
                "the URL instead."
            ],
        }

    def check_discovery(self):
        keys = IssuerKeys(self.ras_issuer)
        try:
            keys._refresh()
        except GrantError as err:
            raise CheckFailed(
                f"metadata not found from issuer: {err.description}", tried=keys.diagnostics
            ) from None
        doc = keys.metadata
        require(
            GRANT_TYPE_JWT_BEARER in doc.get("grant_types_supported", []),
            "grant_types_supported lacks jwt-bearer",
            grant_types_supported=doc.get("grant_types_supported"),
        )
        require(
            GRANT_PROFILE_ID_JAG in doc.get("authorization_grant_profiles_supported", []),
            "authorization_grant_profiles_supported lacks the ID-JAG profile",
            authorization_grant_profiles_supported=doc.get(
                "authorization_grant_profiles_supported"
            ),
        )
        return {"summary": f"metadata via {keys.metadata_source}"}

    def check_redeem(self):
        resp = self.redeem(self.id_jag())
        body = self.expect_issued(resp)
        require(
            str(body.get("token_type", "")).lower() == "bearer",
            "token_type is not Bearer",
            token_type=body.get("token_type"),
        )
        require(
            "no-store" in resp.headers.get("Cache-Control", ""),
            "response lacks Cache-Control: no-store (RFC 6749 §5.1)",
            cache_control=resp.headers.get("Cache-Control"),
        )
        require("scope" in body, "granted scope not reported (draft-06 §4.4.1 MUST)")
        notes = []
        if "refresh_token" in body:
            notes.append("refresh_token returned; draft-06 §4.4.4 SHOULD NOT")
        if "expires_in" not in body:
            notes.append("expires_in absent (RFC 6749 §5.1 RECOMMENDED)")
        self.state["redeemed"] = body
        return {
            "summary": "ID-JAG redeemed for a Bearer access token",
            "details": {"response": response_summary(resp)},
            "notes": notes,
        }

    def check_access_token(self):
        token = self.state["redeemed"]["access_token"]
        _header, claims = self.verify_access_token(token)
        provider = self.ras["provider"]
        expected_sub = IDToken()._resolve_sub(provider, self.user)
        require(claims.get("iss") == self.ras_issuer, "iss is not authentik", iss=claims.get("iss"))
        require(
            claims.get("sub") == expected_sub,
            "sub doesn't identify the user connected to the ID-JAG subject",
            sub=claims.get("sub"),
        )
        require(
            claims.get("azp") == self.ras["client_id"],
            "token isn't issued to the redeeming client",
            azp=claims.get("azp"),
        )
        resp = requests.get(
            self.url_for("authentik_providers_oauth2:userinfo"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=HTTP_TIMEOUT,
        )
        userinfo = json_or_empty(resp)
        require(
            resp.ok and userinfo.get("sub") == expected_sub,
            "userinfo didn't accept the access token for the user",
            response=response_summary(resp),
        )
        return {"summary": "verified; userinfo accepts it for the connected user"}

    def check_subject_email_link(self):
        """An administrator trusts the IdP for an email domain; an ID-JAG for a subject with no
        connection yet, whose email names an existing user in it, connects that user"""
        source = self.state["source"]
        domain = f"corp-{generate_id(6).lower()}.example"
        resp = self.api(
            "PATCH",
            f"sources/oauth/{source.slug}/",
            json={
                # Partial updates of an OpenID Connect source still have to name its URLs
                "authorization_url": source.authorization_url,
                "access_token_url": source.access_token_url,
                "profile_url": source.profile_url,
                "id_jag_email_domains": [domain.upper()],
            },
        )
        require(
            resp.ok and resp.json().get("id_jag_email_domains") == [domain],
            f"trusting the IdP for {domain} failed: HTTP {resp.status_code}",
            response=response_summary(resp),
        )
        user = create_test_user()
        user.email = f"{user.username}@{domain}"
        user.save()
        subject = f"idp-user-{generate_id(8)}"
        # Emails compare without case (Claude-issued ID-JAGs lowercase them, IdPs needn't)
        email = f"{user.username.upper()}@{domain}"
        body = self.expect_issued(self.redeem(self.id_jag(sub=subject, email=email)))
        _header, claims = self.verify_access_token(body["access_token"])
        expected_sub = IDToken()._resolve_sub(self.ras["provider"], user)
        require(
            claims.get("sub") == expected_sub,
            "the access token doesn't name the user with the ID-JAG's email",
            sub=claims.get("sub"),
        )
        connection = UserOAuthSourceConnection.objects.filter(source=source, user=user).first()
        require(
            connection is not None and connection.identifier == subject,
            "the user wasn't connected to the ID-JAG subject",
        )
        # From now on the subject resolves by `sub`, whatever email the IdP sends
        self.expect_issued(self.redeem(self.id_jag(sub=subject, email="moved@else.example")))
        self.state["email_domain"] = domain
        return {
            "summary": "user found by email in a trusted domain, then by sub",
            "details": {"trusted_domain": domain},
        }

    def neg_email_domain_not_trusted(self):
        """An email naming an existing user, in a domain the IdP isn't trusted for"""
        user = create_test_user()
        user.email = f"{user.username}@untrusted-{generate_id(6).lower()}.example"
        user.save()
        result = self.rejects(
            lambda: self.id_jag(sub=f"idp-user-{generate_id(8)}", email=user.email),
            ("access_denied",),
        )()
        require(
            not UserOAuthSourceConnection.objects.filter(user=user).exists(),
            "the user was connected although the email domain isn't trusted",
        )
        return result

    def check_scope_semantics(self):
        claimed = f"{IDP_SCOPE} fixture:unknown"
        body = self.expect_issued(self.redeem(self.id_jag(scope=claimed)))
        require("scope" in body, "granted scope not reported (draft-06 §4.4.1 MUST)")
        granted = set(str(body["scope"]).split())
        require(
            granted <= set(claimed.split()),
            "granted scopes exceed the ID-JAG scope claim",
            granted=sorted(granted),
        )
        return {"summary": f"granted {sorted(granted)} of {sorted(claimed.split())}"}

    def check_resource_bound(self):
        resource = f"{self.live_server_url}{MCP_RESOURCE_PATH}"
        resp = self.redeem(self.id_jag(resource=resource))
        if resp.status_code != HTTPStatus.OK:
            raise CheckFailed(
                "authentik refused an ID-JAG for a resource it should govern: providers can't "
                "declare governed resources yet (RFC 8707 support)",
                resource=resource,
                response=response_summary(resp),
            )
        _header, claims = self.verify_access_token(resp.json()["access_token"])
        aud = claims.get("aud")
        auds = aud if isinstance(aud, list) else [aud]
        require(auds == [resource], "access token isn't audience-restricted", aud=aud)
        return {"summary": f"access token restricted to {resource}"}

    def check_e2e_authentik_issuer(self):
        from authentik.enterprise.agents.models import Agent

        issuer_client = self._oauth_client("idjag-idp")
        idp_issuer = self.url_for(
            "authentik_providers_oauth2:provider-root", application_slug=issuer_client["app"].slug
        )
        # authentik, as Resource AS, trusts authentik as IdP Authorization Server
        source = OAuthSource.objects.create(
            name="authentik IdP Authorization Server",
            slug=f"authentik-idp-{generate_id(6).lower()}",
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url=self.url_for("authentik_providers_oauth2:authorize"),
            access_token_url=self.url_for("authentik_providers_oauth2:token"),
            profile_url=self.url_for("authentik_providers_oauth2:userinfo"),
            oidc_well_known_url=f"{idp_issuer}.well-known/openid-configuration",
            oidc_jwks=requests.get(
                self.url_for(
                    "authentik_providers_oauth2:jwks", application_slug=issuer_client["app"].slug
                ),
                timeout=HTTP_TIMEOUT,
            ).json(),
        )
        self.ras["provider"].jwt_federation_sources.add(source)
        # The IdP's ID-JAG trust configuration for this Resource AS
        agent = Agent.create_for_user(None)
        agent.id_jag_audience = self.ras_issuer
        agent.id_jag_client_id = self.ras["client_id"]
        agent.save()
        agent.applications.add(issuer_client["app"])
        UserOAuthSourceConnection.objects.create(
            user=self.user,
            source=source,
            identifier=IDToken()._resolve_sub(issuer_client["provider"], self.user),
        )
        id_token = self.sso(issuer_client)["id_token"]
        resp = requests.post(
            self.url_for("authentik_providers_oauth2:token"),
            auth=(issuer_client["client_id"], issuer_client["client_secret"]),
            timeout=HTTP_TIMEOUT,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "requested_token_type": TT_ID_JAG,
                "subject_token": id_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
                "audience": self.ras_issuer,
            },
        )
        body = json_or_empty(resp)
        require(
            resp.ok and body.get("issued_token_type") == TT_ID_JAG,
            "authentik didn't issue an ID-JAG for itself as Resource AS",
            response=response_summary(resp),
        )
        header, _claims, _si, _sig = parse_compact_jws(body["access_token"])
        require(header.get("typ") == ID_JAG_TYP, "issued assertion isn't an ID-JAG", header=header)
        redeemed = self.expect_issued(self.redeem(body["access_token"]))
        _header, claims = self.verify_access_token(redeemed["access_token"])
        expected_sub = IDToken()._resolve_sub(self.ras["provider"], self.user)
        require(
            claims.get("sub") == expected_sub,
            "redeemed token doesn't name the user who signed in at the IdP",
            sub=claims.get("sub"),
        )
        return {"summary": "authentik-issued ID-JAG redeemed by authentik for the same user"}

    def test_id_jag_resource_as(self):
        self.run_check("ras.config.trust-idp", self.check_trust_idp)
        self.run_check(
            "ras.discovery.metadata", self.check_discovery, requires=("ras.config.trust-idp",)
        )
        self.run_check("ras.redeem", self.check_redeem, requires=("ras.config.trust-idp",))
        positive = ("ras.redeem",)
        self.run_check("ras.access-token", self.check_access_token, requires=positive)
        self.run_check("ras.scope-semantics", self.check_scope_semantics, requires=positive)
        self.run_check("ras.resource-bound", self.check_resource_bound, requires=positive)
        self.run_check(
            "ras.e2e.authentik-issuer", self.check_e2e_authentik_issuer, requires=positive
        )
        other_issuer = f"{self.idp.base}/tenant-b/"
        negatives = {
            "ras.neg.typ": self.rejects(lambda: self.id_jag(header={"typ": "JWT"})),
            "ras.neg.alg-none": self.rejects(
                lambda: self.id_jag(header={"alg": "none", "kid": None})
            ),
            "ras.neg.signature": self.rejects(
                lambda: self.id_jag(header={"kid": "rsa1"}, key="rogue")
            ),
            "ras.neg.untrusted-issuer": self.rejects(lambda: self.id_jag(iss=other_issuer)),
            "ras.neg.audience": self.rejects(
                lambda: self.id_jag(aud=f"{self.live_server_url}/application/o/other/")
            ),
            "ras.neg.audience-array": self.rejects(
                lambda: self.id_jag(aud=[self.ras_issuer, f"{self.idp.base}/other-as/"])
            ),
            "ras.neg.client-binding": self.rejects(lambda: self.id_jag(client_id=generate_id())),
            "ras.neg.expired": self.rejects(
                lambda: self.id_jag(iat=int(time.time()) - 900, exp=int(time.time()) - 600)
            ),
            "ras.neg.missing-claim": self.rejects(lambda: self.id_jag(jti=None)),
            "ras.neg.resource-not-governed": self.rejects(
                lambda: self.id_jag(resource=f"{self.idp.base}/not-governed")
            ),
            "ras.neg.no-client-auth": self.rejects(
                self.id_jag,
                ("invalid_client",),
                (HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED),
                auth=False,
            ),
            "ras.neg.subject-not-provisioned": self.rejects(
                lambda: self.id_jag(sub=f"unknown-{generate_id(8)}"), ("access_denied",)
            ),
        }
        for check_id, probe in negatives.items():
            self.run_check(check_id, probe, requires=positive)
        self.run_check("ras.neg.replay", self.neg_replay, requires=positive)
        self.run_check("ras.subject-email-link", self.check_subject_email_link, requires=positive)
        self.run_check(
            "ras.neg.email-domain-not-trusted",
            self.neg_email_domain_not_trusted,
            requires=("ras.subject-email-link",),
        )

        self.report.write(RESULTS_DIR)
        ok, problems = self.report.verdict()
        self.assertTrue(
            ok,
            "ID-JAG Resource AS acceptance failed:\n  "
            + "\n  ".join(problems)
            + f"\nFull report: {RESULTS_DIR / 'report.json'}",
        )

    def neg_replay(self):
        assertion = self.id_jag()
        self.expect_issued(self.redeem(assertion))
        return self.rejects(assertion)()
