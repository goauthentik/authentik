"""ID-JAG redemption (RFC 7523 jwt-bearer) as a Resource Authorization Server,
draft-ietf-oauth-identity-assertion-authz-grant-06 §4.4"""

from base64 import b64encode
from json import loads
from time import time
from typing import Any
from unittest.mock import patch

from django.core.cache import cache
from django.db import DatabaseError
from django.urls import reverse
from jwt import decode, encode
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.brands.models import Brand
from authentik.common.oauth.constants import (
    CLIENT_ASSERTION_TYPE_JWT,
    GRANT_PROFILE_ID_JAG,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_JWT_BEARER,
    GRANT_TYPE_TOKEN_EXCHANGE,
    JWT_TYPE_ID_JAG,
    TOKEN_TYPE,
    TOKEN_TYPE_URI_ACCESS_TOKEN,
    TOKEN_TYPE_URI_JWT,
)
from authentik.core.models import (
    Application,
    Group,
    Source,
    User,
    UserSourceConnection,
    UserTypes,
)
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.issuer import CONFIG_TRUSTED_ISSUER_ORIGINS
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.token.id_jag import (
    CACHE_KEY_ID_JAG_FETCH,
    CACHE_KEY_ID_JAG_ISSUER,
    ID_JAG_ISSUER_MIN_CACHE_SECONDS,
    issuer_metadata_urls,
)
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.oidc import OpenIDConnectType

IDP_ISSUER = "https://idp.example.com/tenant-a"
# RFC 8414 path insertion for IDP_ISSUER
IDP_METADATA_URL = "https://idp.example.com/.well-known/oauth-authorization-server/tenant-a"
IDP_JWKS_URL = "https://idp.example.com/jwks"
MCP_RESOURCE = "https://mcp.example.com/mcp"
OTHER_RESOURCE = "https://api.example.com/"


class TestTokenIdJagGrant(OAuthTestCase):
    """Redeeming ID-JAGs issued by a trusted IdP Authorization Server"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.idp_cert = create_test_cert()
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="https://idp.example.com/authorize",
            access_token_url="https://idp.example.com/token",
            profile_url="https://idp.example.com/userinfo",
            oidc_well_known_url=IDP_METADATA_URL,
            oidc_jwks_url=IDP_JWKS_URL,
            oidc_jwks={"keys": [JWKSView().get_jwk_for_key(self.idp_cert, "sig")]},
        )
        # The issuer's discovery document holds only what an issuer that only signs
        # assertions publishes, as Claude's issuers do
        self.requests = Mocker()
        self.requests.start()
        self.addCleanup(self.requests.stop)
        self.metadata = self.requests.get(
            IDP_METADATA_URL, json={"issuer": IDP_ISSUER, "jwks_uri": IDP_JWKS_URL}
        )
        self.jwks = self.requests.get(IDP_JWKS_URL, json=self.source.oidc_jwks)
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=create_test_cert(),
            grant_types=[GrantType.JWT_BEARER],
            client_type=ClientType.CONFIDENTIAL,
        )
        self.provider.jwt_federation_sources.add(self.source)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        # `aud` is checked against the issuer at a host the administrator configured
        Brand.objects.create(domain="testserver")
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.issuer = f"http://testserver/application/o/{self.app.slug}/"
        self.user = create_test_user()
        self.subject = generate_id()
        UserOAuthSourceConnection.objects.create(
            user=self.user, source=self.source, identifier=self.subject
        )

    def claims(self, **overrides: Any) -> dict[str, Any]:
        now = int(time())
        claims = {
            "iss": IDP_ISSUER,
            "sub": self.subject,
            "aud": self.issuer,
            "client_id": self.provider.client_id,
            "jti": generate_id(),
            "iat": now,
            "exp": now + 300,
            "scope": "openid profile",
        }
        claims.update(overrides)
        return {key: value for key, value in claims.items() if value is not None}

    def id_jag(self, typ: str = JWT_TYPE_ID_JAG, key=None, **overrides: Any) -> str:
        return encode(
            self.claims(**overrides),
            key or self.idp_cert.private_key,
            algorithm="RS256",
            headers={"kid": self.idp_cert.kid, "typ": typ},
        )

    def redeem(
        self, assertion: str, secret: str | None = None, host: str = "testserver", **extra: str
    ):
        secret = self.provider.client_secret if secret is None else secret
        basic = b64encode(f"{self.provider.client_id}:{secret}".encode()).decode()
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {"grant_type": GRANT_TYPE_JWT_BEARER, "assertion": assertion, **extra},
            HTTP_AUTHORIZATION=f"Basic {basic}",
            HTTP_HOST=host,
        )

    def assert_error(self, response, error: str):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(loads(response.content)["error"], error)

    def assert_rejected(self, assertion: str, error: str, cause: str, host: str = "testserver"):
        """Rejected with `error`, for the reason `cause` (not by accident)"""
        causes = []
        with_cause = TokenError.with_cause

        def record(error: TokenError, cause: str):
            causes.append(cause)
            return with_cause(error, cause)

        with patch.object(TokenError, "with_cause", record):
            response = self.redeem(assertion, host=host)
        self.assert_error(response, error)
        self.assertEqual(causes[-1:], [cause])

    def test_redeem(self):
        """A valid ID-JAG yields a Bearer access token for the connected user"""
        response = self.redeem(self.id_jag(scope="openid profile not-a-scope"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response["Cache-Control"], "no-store")
        body = loads(response.content)
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        # Unknown scopes are dropped, and the granted ones reported (draft-06 §4.4.1)
        self.assertEqual(set(body["scope"].split()), {"openid", "profile"})
        # §4.4.4: no refresh token
        self.assertNotIn("refresh_token", body)
        token = decode(
            body["access_token"],
            self.provider.signing_key.private_key.public_key(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        self.assertEqual(token["iss"], self.issuer)
        self.assertEqual(token["sub"], self.user.uid)
        self.assertEqual(token["azp"], self.provider.client_id)

    def test_redeem_array_aud(self):
        """aud may be an array with exactly one element"""
        response = self.redeem(self.id_jag(aud=[self.issuer]))
        self.assertEqual(response.status_code, 200, response.content)

    def test_redeem_typ_variants(self):
        """typ is case-insensitive, and may carry the application/ prefix"""
        for typ in ("OAUTH-ID-JAG+JWT", f"application/{JWT_TYPE_ID_JAG}"):
            with self.subTest(typ=typ):
                self.assertEqual(self.redeem(self.id_jag(typ=typ)).status_code, 200)

    def test_scope_parameter_without_claim(self):
        """Without a scope claim, the request's scope parameter applies"""
        response = self.redeem(self.id_jag(scope=None), scope="openid email")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(loads(response.content)["scope"].split()), {"openid", "email"})

    def access_token_claims(self, response) -> dict[str, Any]:
        self.assertEqual(response.status_code, 200, response.content)
        return decode(
            loads(response.content)["access_token"],
            self.provider.signing_key.private_key.public_key(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

    def test_redeem_resource(self):
        """An ID-JAG restricted to a governed resource yields a token for that resource,
        bound to the authenticated client"""
        self.provider.allowed_resources = [MCP_RESOURCE, OTHER_RESOURCE]
        self.provider.save()
        token = self.access_token_claims(self.redeem(self.id_jag(resource=MCP_RESOURCE)))
        self.assertEqual(token["aud"], MCP_RESOURCE)
        self.assertEqual(token["azp"], self.provider.client_id)
        access_token = AccessToken.objects.get(provider=self.provider, user=self.user)
        self.assertEqual(access_token.resources, (MCP_RESOURCE,))
        self.assertEqual(access_token.client_id, self.provider.client_id)

    def test_redeem_resources_narrowed(self):
        """A `resource` parameter narrows the ID-JAG's resources, and can't widen them"""
        self.provider.allowed_resources = [MCP_RESOURCE, OTHER_RESOURCE]
        self.provider.save()
        both = [MCP_RESOURCE, OTHER_RESOURCE]
        token = self.access_token_claims(self.redeem(self.id_jag(resource=both)))
        self.assertEqual(token["aud"], both)
        token = self.access_token_claims(
            self.redeem(self.id_jag(resource=both), resource=OTHER_RESOURCE)
        )
        self.assertEqual(token["aud"], OTHER_RESOURCE)
        response = self.redeem(self.id_jag(resource=MCP_RESOURCE), resource=OTHER_RESOURCE)
        self.assert_error(response, "invalid_target")

    def test_redeem_resource_parameter_without_claim(self):
        """Without a resource claim, the request's `resource` parameter applies"""
        self.provider.allowed_resources = [MCP_RESOURCE]
        self.provider.save()
        token = self.access_token_claims(self.redeem(self.id_jag(), resource=MCP_RESOURCE))
        self.assertEqual(token["aud"], MCP_RESOURCE)
        response = self.redeem(self.id_jag(), resource=OTHER_RESOURCE)
        self.assert_error(response, "invalid_target")

    def test_resource_not_governed(self):
        """Resources the provider doesn't allow are refused, as are malformed claims"""
        self.provider.allowed_resources = [OTHER_RESOURCE]
        self.provider.save()
        cases = {
            "not allowed": (self.id_jag(resource=MCP_RESOURCE), "resource_not_governed"),
            "one of several not allowed": (
                self.id_jag(resource=[OTHER_RESOURCE, MCP_RESOURCE]),
                "resource_not_governed",
            ),
            "not a string": (self.id_jag(resource=1), "invalid_resource_claim"),
            "empty list": (self.id_jag(resource=[]), "invalid_resource_claim"),
            "not a URI": (self.id_jag(resource="mcp"), "invalid_resource_claim"),
            "fragment": (
                self.id_jag(resource=f"{OTHER_RESOURCE}#frag"),
                "invalid_resource_claim",
            ),
        }
        for name, (assertion, cause) in cases.items():
            with self.subTest(name):
                self.assert_rejected(assertion, "invalid_grant", cause)

    def test_invalid_grant(self):
        """Every §4.4.1 validation failure is invalid_grant"""
        other_key = create_test_cert().private_key
        cases = {
            "wrong typ": (self.id_jag(typ="JWT"), "invalid_typ"),
            "missing typ": (
                encode(
                    self.claims(), self.idp_cert.private_key, "RS256", {"kid": self.idp_cert.kid}
                ),
                "invalid_typ",
            ),
            "untrusted issuer": (
                self.id_jag(iss="https://evil.example.com/tenant-a"),
                "untrusted_issuer",
            ),
            "issuer of another tenant": (
                self.id_jag(iss="https://idp.example.com/tenant-b"),
                "untrusted_issuer",
            ),
            "wrong key": (self.id_jag(key=other_key), "invalid_signature"),
            "wrong aud": (self.id_jag(aud="https://other.example.com/"), "invalid_aud"),
            "two auds": (
                self.id_jag(aud=[self.issuer, "https://other.example.com/"]),
                "invalid_aud",
            ),
            "client_id of another client": (
                self.id_jag(client_id=generate_id()),
                "client_id_mismatch",
            ),
            "expired": (
                self.id_jag(iat=int(time()) - 600, exp=int(time()) - 300),
                "invalid_signature",
            ),
            "issued in the future": (
                self.id_jag(iat=int(time()) + 600, exp=int(time()) + 900),
                "invalid_signature",
            ),
            "missing jti": (self.id_jag(jti=None), "invalid_signature"),
            "missing client_id": (self.id_jag(client_id=None), "invalid_signature"),
            "missing exp": (self.id_jag(exp=None), "invalid_signature"),
            "resource not governed": (
                self.id_jag(resource=MCP_RESOURCE),
                "resource_not_governed",
            ),
            "cnf": (self.id_jag(cnf={"jkt": generate_id()}), "cnf_unsupported"),
            "alg none": (
                encode(self.claims(), None, "none", {"typ": JWT_TYPE_ID_JAG}),
                "invalid_alg",
            ),
            "not a JWT": ("foo.bar", "malformed_assertion"),
        }
        for name, (assertion, cause) in cases.items():
            with self.subTest(name):
                self.assert_rejected(assertion, "invalid_grant", cause)

    def test_spoofed_host(self):
        """An ID-JAG minted for an authorization server at another host, with this
        provider's path, can't be replayed here by sending that host: only hosts of a
        brand's domain (or configured origins) are trusted for `aud`"""
        aud = f"http://evil.example/application/o/{self.app.slug}/"
        self.assert_rejected(
            self.id_jag(aud=aud), "invalid_grant", "host_not_trusted", host="evil.example"
        )
        # The host is refused before anything is fetched from the issuer
        self.assertEqual(self.metadata.call_count, 0)
        self.assert_rejected(self.id_jag(aud=aud), "invalid_grant", "invalid_aud")
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)

    def test_trusted_issuer_origins(self):
        """Configured origins replace brand domains as the trusted hosts"""
        with CONFIG.patch(CONFIG_TRUSTED_ISSUER_ORIGINS, ["https://idp-rs.example"]):
            self.assert_rejected(self.id_jag(), "invalid_grant", "origin_not_trusted")
            response = self.client.post(
                reverse("authentik_providers_oauth2:token"),
                {
                    "grant_type": GRANT_TYPE_JWT_BEARER,
                    "assertion": self.id_jag(
                        aud=f"https://idp-rs.example/application/o/{self.app.slug}/"
                    ),
                    "client_id": self.provider.client_id,
                    "client_secret": self.provider.client_secret,
                },
                HTTP_HOST="idp-rs.example",
                secure=True,
            )
            self.assertEqual(response.status_code, 200, response.content)

    def test_aud_tenant_ignored(self):
        """aud_tenant only selects a tenant; a provider is one, so the claim is ignored"""
        response = self.redeem(self.id_jag(aud_tenant=generate_id()))
        self.assertEqual(response.status_code, 200, response.content)

    def test_issuer_confirmed_once(self):
        """The issuer's discovery document and keys are fetched once, then reused"""
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)
        self.assertEqual(self.metadata.call_count, 1)
        self.assertEqual(self.jwks.call_count, 1)

    def test_issuer_mismatch(self):
        """The discovery document must name the ID-JAG's issuer"""
        self.requests.get(
            IDP_METADATA_URL,
            json={"issuer": "https://idp.example.com/tenant-b", "jwks_uri": IDP_JWKS_URL},
        )
        self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_mismatch")
        self.assertEqual(self.jwks.call_count, 0)

    def test_issuer_metadata_unavailable(self):
        """Without the discovery document, the issuer can't be confirmed"""
        self.requests.get(IDP_METADATA_URL, status_code=500)
        self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_metadata_unavailable")
        # Fetched again only once the fetch interval has passed
        self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_unconfirmed")

    def test_issuer_jwks_unavailable(self):
        """Without keys at the document's jwks_uri, nothing is accepted"""
        for metadata, jwks in (
            ({"issuer": IDP_ISSUER}, {}),
            ({"issuer": IDP_ISSUER, "jwks_uri": IDP_JWKS_URL}, {"status_code": 404}),
            ({"issuer": IDP_ISSUER, "jwks_uri": IDP_JWKS_URL}, {"json": {"keys": "foo"}}),
        ):
            with self.subTest(metadata=metadata, jwks=jwks):
                cache.delete(CACHE_KEY_ID_JAG_FETCH % self.source.pk)
                self.requests.get(IDP_METADATA_URL, json=metadata)
                if jwks:
                    self.requests.get(IDP_JWKS_URL, **jwks)
                self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_jwks_unavailable")

    def test_key_rotation(self):
        """An assertion signed with a key the cached keys don't have fetches them again"""
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)
        new_cert = create_test_cert()
        new_jwks = {"keys": [JWKSView().get_jwk_for_key(new_cert, "sig")]}
        self.requests.get(IDP_JWKS_URL, json=new_jwks)
        assertion = encode(
            self.claims(),
            new_cert.private_key,
            algorithm="RS256",
            headers={"kid": new_cert.kid, "typ": JWT_TYPE_ID_JAG},
        )
        # Keys are fetched at most once per interval, so the new key isn't known yet
        self.assert_rejected(assertion, "invalid_grant", "invalid_signature")
        cache.delete(CACHE_KEY_ID_JAG_FETCH % self.source.pk)
        assertion = encode(
            self.claims(),
            new_cert.private_key,
            algorithm="RS256",
            headers={"kid": new_cert.kid, "typ": JWT_TYPE_ID_JAG},
        )
        self.assertEqual(self.redeem(assertion).status_code, 200)
        self.source.refresh_from_db()
        self.assertEqual(self.source.oidc_jwks, new_jwks)
        self.assertEqual(self.metadata.call_count, 2)

    def test_header_key_ignored(self):
        """Keys carried in the assertion's header are never used"""
        attacker = create_test_cert()
        assertion = encode(
            self.claims(),
            attacker.private_key,
            algorithm="RS256",
            headers={
                "kid": attacker.kid,
                "typ": JWT_TYPE_ID_JAG,
                "jwk": JWKSView().get_jwk_for_key(attacker, "sig"),
                "jku": "https://evil.example.com/jwks",
            },
        )
        self.assert_rejected(assertion, "invalid_grant", "invalid_signature")

    def test_hmac_with_public_key(self):
        """A trusted issuer's public key can't be used as an HMAC secret"""
        jwk = JWKSView().get_jwk_for_key(self.idp_cert, "sig")
        assertion = encode(
            self.claims(), jwk["n"].encode(), "HS256", {"typ": JWT_TYPE_ID_JAG, "kid": jwk["kid"]}
        )
        self.assert_rejected(assertion, "invalid_grant", "invalid_alg")

    def test_replay(self):
        """Each ID-JAG is accepted once"""
        assertion = self.id_jag()
        self.assertEqual(self.redeem(assertion).status_code, 200)
        self.assert_rejected(assertion, "invalid_grant", "jti_replayed")

    def test_lifetime_too_long(self):
        """An ID-JAG valid for longer than an hour is refused, so a jti is never remembered
        for longer"""
        now = int(time())
        self.assert_rejected(
            self.id_jag(iat=now, exp=now + 2 * 60 * 60), "invalid_grant", "lifetime_too_long"
        )

    def test_cache_unavailable(self):
        """Without the cache, replays and issuers can't be checked, so nothing is accepted"""
        with patch.object(cache, "add", side_effect=DatabaseError):
            self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_unconfirmed")
        # Confirmed issuer, but the jti can't be recorded
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)
        with patch.object(cache, "add", side_effect=DatabaseError):
            self.assert_rejected(self.id_jag(), "invalid_grant", "jti_replayed")

    def test_issuer_cache_max_age(self):
        """A confirmed issuer is reused for the shorter max-age of its discovery document
        and keys, and an hour without one"""
        timeouts = []
        cache_set = cache.set

        def record(key, value, timeout=None, **kwargs):
            if key.startswith(CACHE_KEY_ID_JAG_ISSUER % ""):
                timeouts.append(timeout)
            return cache_set(key, value, timeout=timeout, **kwargs)

        cases = (
            ({}, {}, 60 * 60),
            ({"Cache-Control": "public, max-age=600"}, {"Cache-Control": "max-age=300"}, 300),
            ({"Cache-Control": "no-cache"}, {"Cache-Control": "max-age=0"}, 60),
            ({}, {"Cache-Control": "max-age=99999"}, 60 * 60),
            ({"Cache-Control": "max-age=99999"}, {"Cache-Control": "max-age=99999"}, 24 * 60 * 60),
        )
        for metadata_headers, jwks_headers, expected in cases:
            with self.subTest(expected=expected):
                cache.clear()
                self.requests.get(
                    IDP_METADATA_URL,
                    json={"issuer": IDP_ISSUER, "jwks_uri": IDP_JWKS_URL},
                    headers=metadata_headers,
                )
                self.requests.get(IDP_JWKS_URL, json=self.source.oidc_jwks, headers=jwks_headers)
                with patch.object(cache, "set", record):
                    self.assertEqual(self.redeem(self.id_jag()).status_code, 200)
                self.assertEqual(timeouts[-1], max(expected, ID_JAG_ISSUER_MIN_CACHE_SECONDS))

    def test_auth_time(self):
        """The access token keeps the ID-JAG's auth_time"""
        auth_time = int(time()) - 120
        token = self.access_token_claims(self.redeem(self.id_jag(auth_time=auth_time)))
        self.assertEqual(token["auth_time"], auth_time)
        for value in ("yesterday", True, int(time()) + 600):
            with self.subTest(auth_time=value):
                self.assert_rejected(
                    self.id_jag(auth_time=value), "invalid_grant", "invalid_auth_time"
                )

    def test_issuer_ambiguous(self):
        """Two sources the provider trusts for one issuer could resolve users differently,
        so the issuer isn't trusted"""
        other = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="https://idp.example.com/authorize",
            access_token_url="https://idp.example.com/token",
            profile_url="https://idp.example.com/userinfo",
            # Another metadata URL derived from the same issuer
            oidc_well_known_url=f"{IDP_ISSUER}/.well-known/openid-configuration",
        )
        self.provider.jwt_federation_sources.add(other)
        self.assert_rejected(self.id_jag(), "invalid_grant", "issuer_ambiguous")
        # A disabled one doesn't count
        other.enabled = False
        other.save()
        self.assertEqual(self.redeem(self.id_jag()).status_code, 200)

    def test_missing_assertion(self):
        self.assert_error(self.redeem(""), "invalid_request")

    def test_client_authentication(self):
        """The client must authenticate as the client named by client_id"""
        self.assert_error(self.redeem(self.id_jag(), secret=generate_id()), "invalid_client")
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        self.assert_error(self.redeem(self.id_jag()), "invalid_client")

    def test_grant_not_enabled(self):
        self.provider.grant_types = [GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        self.assert_error(self.redeem(self.id_jag()), "invalid_grant")

    def test_disabled_source(self):
        self.source.enabled = False
        self.source.save()
        self.assert_rejected(self.id_jag(), "invalid_grant", "untrusted_issuer")

    def post_token(self, **data: str):
        """POST to the token endpoint, recording the causes of TokenErrors"""
        causes: list[str] = []
        with_cause = TokenError.with_cause

        def record(error: TokenError, cause: str):
            causes.append(cause)
            return with_cause(error, cause)

        with patch.object(TokenError, "with_cause", record):
            response = self.client.post(reverse("authentik_providers_oauth2:token"), data)
        return response, causes

    def client_assertion(self, assertion: str):
        return self.post_token(
            grant_type=GRANT_TYPE_CLIENT_CREDENTIALS,
            client_id=self.provider.client_id,
            client_assertion_type=CLIENT_ASSERTION_TYPE_JWT,
            client_assertion=assertion,
        )

    def test_not_a_client_assertion(self):
        """An ID-JAG is redeemed only by the jwt-bearer grant: as a client_credentials
        client assertion it's refused, and creates no service account, although the source
        trusted for its issuer has the key that signed it"""
        self.provider.grant_types = [GrantType.JWT_BEARER, GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        users = User.objects.count()
        for typ in (JWT_TYPE_ID_JAG, "Application/OAuth-ID-JAG+JWT"):
            with self.subTest(typ=typ):
                response, causes = self.client_assertion(self.id_jag(typ=typ))
                self.assert_error(response, "invalid_grant")
                self.assertIn("id_jag_not_accepted", causes)
        self.assertEqual(User.objects.count(), users)
        self.assertFalse(User.objects.filter(type=UserTypes.SERVICE_ACCOUNT).exists())
        # Other JWTs the source signed are still accepted
        response, _ = self.client_assertion(self.id_jag(typ="JWT"))
        self.assertEqual(response.status_code, 200, response.content)

    def test_not_a_subject_token(self):
        """An ID-JAG is redeemed only by the jwt-bearer grant: as a token exchange subject
        token it's refused, and creates no service account"""
        self.provider.grant_types = [GrantType.JWT_BEARER, GrantType.TOKEN_EXCHANGE]
        self.provider.save()
        users = User.objects.count()
        for subject_token_type in (TOKEN_TYPE_URI_JWT, TOKEN_TYPE_URI_ACCESS_TOKEN):
            with self.subTest(subject_token_type=subject_token_type):
                response, causes = self.post_token(
                    grant_type=GRANT_TYPE_TOKEN_EXCHANGE,
                    client_id=self.provider.client_id,
                    client_secret=self.provider.client_secret,
                    subject_token=self.id_jag(),
                    subject_token_type=subject_token_type,
                )
                self.assert_error(response, "invalid_grant")
                self.assertIn("id_jag_not_accepted", causes)
        self.assertEqual(User.objects.count(), users)

    def test_federation_disabled_source(self):
        """A disabled source's keys don't validate client assertions either"""
        self.provider.grant_types = [GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        self.source.enabled = False
        self.source.save()
        response, _ = self.client_assertion(self.id_jag(typ="JWT"))
        self.assert_error(response, "invalid_grant")
        self.assertFalse(User.objects.filter(type=UserTypes.SERVICE_ACCOUNT).exists())

    def test_federation_assertion_only_source(self):
        """A source type that only issues assertions never validates client assertions"""
        self.provider.grant_types = [GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        with patch.object(OpenIDConnectType, "assertion_only", True, create=True):
            response, _ = self.client_assertion(self.id_jag(typ="JWT"))
        self.assert_error(response, "invalid_grant")
        self.assertFalse(User.objects.filter(type=UserTypes.SERVICE_ACCOUNT).exists())

    def test_subject_not_provisioned(self):
        """A valid ID-JAG for a subject without a connection is access_denied (§4.4.3)"""
        self.assert_rejected(
            self.id_jag(sub=generate_id()), "access_denied", "subject_not_provisioned"
        )
        self.user.is_active = False
        self.user.save()
        self.assert_rejected(self.id_jag(), "access_denied", "subject_inactive")

    def email_user(self, email: str = "alex@corp.example", linked: bool = True, **kwargs: Any):
        """A user without a connection to the ID-JAG's source, and that source trusted for
        corp.example emails. A `linked` user is connected to a directory, so their address
        may identify them."""
        self.source.id_jag_email_domains = ["corp.example"]
        self.source.save()
        user = create_test_user(**kwargs)
        user.email = email
        user.save()
        if linked:
            UserSourceConnection.objects.create(
                user=user, source=self.directory(), identifier=generate_id()
            )
        return user

    def directory(self) -> Source:
        """A source users are connected to, which isn't trusted for ID-JAGs"""
        if not hasattr(self, "_directory"):
            self._directory = Source.objects.create(name=generate_id(), slug=generate_id())
        return self._directory

    def test_email_eligibility(self):
        """Only users connected to an enabled source, or members of the source's ID-JAG email
        group, are found by email: a user who registered themselves never is"""
        user = self.email_user(linked=False)
        self.assert_rejected(
            self.id_jag(sub=generate_id(), email=user.email),
            "access_denied",
            "subject_not_provisioned",
        )
        # A member of a subgroup of the source's ID-JAG email group
        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)
        child.users.add(user)
        self.source.id_jag_email_group = parent
        self.source.save()
        self.assertEqual(
            self.redeem(self.id_jag(sub=generate_id(), email=user.email)).status_code, 200
        )

    def test_email_eligibility_disabled_directory(self):
        """A connection to a disabled source doesn't make an address trusted, and an
        ineligible user with the same address doesn't make it ambiguous"""
        user = self.email_user()
        directory = self.directory()
        directory.enabled = False
        directory.save()
        self.assert_rejected(
            self.id_jag(sub=generate_id(), email=user.email),
            "access_denied",
            "subject_not_provisioned",
        )
        directory.enabled = True
        directory.save()
        self.email_user(email=user.email.upper(), linked=False)
        self.assertEqual(
            self.redeem(self.id_jag(sub=generate_id(), email=user.email)).status_code, 200
        )

    def test_email_link(self):
        """§9.8: without a connection, a verified email in a trusted domain connects the one
        active user with that address, once; later ID-JAGs resolve by `sub`"""
        user = self.email_user()
        subject = generate_id()
        response = self.redeem(self.id_jag(sub=subject, email="Alex@CORP.example"))
        self.assertEqual(response.status_code, 200, response.content)
        connection = UserOAuthSourceConnection.objects.get(source=self.source, user=user)
        self.assertEqual(connection.identifier, subject)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.SOURCE_LINKED, user__pk=user.pk, context__identifier=subject
            ).exists()
        )
        # Resolved by `sub` from now on, whatever the email
        user.email = "renamed@corp.example"
        user.save()
        response = self.redeem(self.id_jag(sub=subject, email="someone@else.example"))
        self.assertEqual(response.status_code, 200, response.content)

    def test_email_link_refused(self):
        """Email linking needs a trusted domain, a verified address naming exactly one
        active person, and that person not connected to another subject"""
        user = self.email_user()
        sub = generate_id()
        # The source isn't trusted for any domain
        self.source.id_jag_email_domains = []
        self.source.save()
        self.assert_rejected(
            self.id_jag(sub=sub, email=user.email), "access_denied", "subject_not_provisioned"
        )
        self.source.id_jag_email_domains = ["corp.example"]
        self.source.save()
        for email, error, cause in (
            (None, "access_denied", "subject_not_provisioned"),
            ("alex@sub.corp.example", "access_denied", "email_domain_not_trusted"),
            ("alex@corp.example.evil", "access_denied", "email_domain_not_trusted"),
            ("corp.example", "access_denied", "email_domain_not_trusted"),
            ("@corp.example", "access_denied", "email_domain_not_trusted"),
            ("nobody@corp.example", "access_denied", "subject_not_provisioned"),
            (["alex@corp.example"], "invalid_grant", "invalid_email_claim"),
        ):
            with self.subTest(email=email):
                self.assert_rejected(self.id_jag(sub=sub, email=email), error, cause)
        for verified in (False, "true"):
            with self.subTest(email_verified=verified):
                self.assert_rejected(
                    self.id_jag(sub=sub, email=user.email, email_verified=verified),
                    "access_denied",
                    "email_not_verified",
                )
        # The user already has a connection to this source, for another subject
        UserOAuthSourceConnection.objects.create(
            user=user, source=self.source, identifier=generate_id()
        )
        self.assert_rejected(
            self.id_jag(sub=sub, email=user.email), "access_denied", "subject_conflict"
        )
        self.assertFalse(
            UserOAuthSourceConnection.objects.filter(source=self.source, identifier=sub).exists()
        )

    def test_email_link_not_unique(self):
        """Two active users with the address: nobody is connected"""
        self.email_user()
        self.email_user(email="ALEX@corp.example")
        self.assert_rejected(
            self.id_jag(sub=generate_id(), email="alex@corp.example"),
            "access_denied",
            "email_not_unique",
        )

    def test_email_link_skips_inactive_and_service_accounts(self):
        """Inactive users and service accounts are never found by email"""
        self.email_user(is_active=False)
        self.email_user(type=UserTypes.SERVICE_ACCOUNT)
        self.assert_rejected(
            self.id_jag(sub=generate_id(), email="alex@corp.example"),
            "access_denied",
            "subject_not_provisioned",
        )

    def test_email_link_policy_denied(self):
        """A user the application denies isn't connected"""
        user = self.email_user()
        PolicyBinding.objects.create(target=self.app, user=create_test_user(), order=0)
        sub = generate_id()
        self.assert_rejected(
            self.id_jag(sub=sub, email=user.email), "access_denied", "policy_denied"
        )
        self.assertFalse(UserOAuthSourceConnection.objects.filter(user=user).exists())

    def test_email_domains_api(self):
        """Domains are normalized; invalid ones are refused"""
        self.client.force_login(create_test_admin_user())
        url = reverse("authentik_api:oauthsource-detail", kwargs={"slug": self.source.slug})
        # Partial updates of an OpenID Connect source still have to name its URLs
        urls = {
            "enabled": False,
            "authorization_url": self.source.authorization_url,
            "access_token_url": self.source.access_token_url,
            "profile_url": self.source.profile_url,
        }
        response = self.client.patch(
            url,
            {**urls, "id_jag_email_domains": ["Corp.Example.", "corp.example"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.source.refresh_from_db()
        self.assertEqual(self.source.id_jag_email_domains, ["corp.example"])
        for domain in ("*.corp.example", "alex@corp.example", "localhost", "", "corp .example"):
            with self.subTest(domain=domain):
                response = self.client.patch(
                    url,
                    {**urls, "id_jag_email_domains": [domain]},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400, response.content)
        group = Group.objects.create(name=generate_id())
        response = self.client.patch(
            url, {**urls, "id_jag_email_group": str(group.pk)}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(loads(response.content)["id_jag_email_group"], str(group.pk))
        self.source.refresh_from_db()
        self.assertEqual(self.source.id_jag_email_group, group)

    def test_policy_denied(self):
        """A valid ID-JAG for a user the application denies is access_denied (§4.4.3)"""
        PolicyBinding.objects.create(target=self.app, user=create_test_user(), order=0)
        self.assert_rejected(self.id_jag(), "access_denied", "policy_denied")

    def test_metadata(self):
        """§7.2: the profile is advertised only by providers that redeem ID-JAGs"""
        url = reverse(
            "authentik_providers_oauth2:provider-info",
            kwargs={"application_slug": self.app.slug},
        )
        body = loads(self.client.get(url).content)
        self.assertEqual(body["authorization_grant_profiles_supported"], [GRANT_PROFILE_ID_JAG])
        self.assertIn(GRANT_TYPE_JWT_BEARER, body["grant_types_supported"])
        self.provider.grant_types = [GrantType.AUTHORIZATION_CODE]
        self.provider.save()
        body = loads(self.client.get(url).content)
        self.assertNotIn("authorization_grant_profiles_supported", body)

    def test_issuer_metadata_urls(self):
        self.assertEqual(
            issuer_metadata_urls("https://idp.example.com/"),
            {
                "https://idp.example.com/.well-known/oauth-authorization-server",
                "https://idp.example.com/.well-known/openid-configuration",
            },
        )
        self.assertIn(
            "https://idp.example.com/application/o/app/.well-known/openid-configuration",
            issuer_metadata_urls("https://idp.example.com/application/o/app/"),
        )
        self.assertEqual(issuer_metadata_urls("not a url"), set())
        self.assertEqual(issuer_metadata_urls("https://idp.example.com/?tenant=a"), set())
