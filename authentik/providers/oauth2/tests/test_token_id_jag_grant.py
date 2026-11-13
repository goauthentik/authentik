"""ID-JAG redemption (RFC 7523 jwt-bearer) as a Resource Authorization Server,
draft-ietf-oauth-identity-assertion-authz-grant-06 §4.4"""

from base64 import b64encode
from json import loads
from time import time
from typing import Any
from unittest.mock import patch

from django.urls import reverse
from jwt import decode, encode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_PROFILE_ID_JAG,
    GRANT_TYPE_JWT_BEARER,
    JWT_TYPE_ID_JAG,
    TOKEN_TYPE,
)
from authentik.core.models import Application, UserTypes
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.token.id_jag import issuer_metadata_urls
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection

IDP_ISSUER = "https://idp.example.com/tenant-a"


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
            # RFC 8414 path insertion for IDP_ISSUER
            oidc_well_known_url=(
                "https://idp.example.com/.well-known/oauth-authorization-server/tenant-a"
            ),
            oidc_jwks_url="https://idp.example.com/jwks",
            oidc_jwks={"keys": [JWKSView().get_jwk_for_key(self.idp_cert, "sig")]},
        )
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

    def redeem(self, assertion: str, secret: str | None = None, **extra: str):
        secret = self.provider.client_secret if secret is None else secret
        basic = b64encode(f"{self.provider.client_id}:{secret}".encode()).decode()
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {"grant_type": GRANT_TYPE_JWT_BEARER, "assertion": assertion, **extra},
            HTTP_AUTHORIZATION=f"Basic {basic}",
        )

    def assert_error(self, response, error: str):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(loads(response.content)["error"], error)

    def assert_rejected(self, assertion: str, error: str, cause: str):
        """Rejected with `error`, for the reason `cause` (not by accident)"""
        causes = []
        with_cause = TokenError.with_cause

        def record(error: TokenError, cause: str):
            causes.append(cause)
            return with_cause(error, cause)

        with patch.object(TokenError, "with_cause", record):
            response = self.redeem(assertion)
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
                self.id_jag(resource="https://mcp.example.com/mcp"),
                "resource_not_governed",
            ),
            "cnf": (self.id_jag(cnf={"jkt": generate_id()}), "cnf_unsupported"),
            "aud_tenant": (self.id_jag(aud_tenant=generate_id()), "aud_tenant_unsupported"),
            "alg none": (
                encode(self.claims(), None, "none", {"typ": JWT_TYPE_ID_JAG}),
                "invalid_alg",
            ),
            "not a JWT": ("foo.bar", "malformed_assertion"),
        }
        for name, (assertion, cause) in cases.items():
            with self.subTest(name):
                self.assert_rejected(assertion, "invalid_grant", cause)

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

    def test_subject_not_provisioned(self):
        """A valid ID-JAG for a subject without a connection is access_denied (§4.4.3)"""
        self.assert_rejected(
            self.id_jag(sub=generate_id()), "access_denied", "subject_not_provisioned"
        )
        self.user.is_active = False
        self.user.save()
        self.assert_rejected(self.id_jag(), "access_denied", "subject_inactive")

    def email_user(self, email: str = "alex@corp.example", **kwargs: Any):
        """A user without a connection, and the source trusted for corp.example emails"""
        self.source.id_jag_email_domains = ["corp.example"]
        self.source.save()
        user = create_test_user(**kwargs)
        user.email = email
        user.save()
        return user

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
