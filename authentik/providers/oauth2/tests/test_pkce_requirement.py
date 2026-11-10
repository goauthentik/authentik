"""Test requiring PKCE and restricting PKCE methods on OAuth2 providers"""

import json
from base64 import b64encode
from datetime import timedelta
from importlib import import_module
from itertools import product
from urllib.parse import parse_qs, urlparse

from django.db.migrations import AddField, AlterField
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    PKCE_METHOD_PLAIN,
    PKCE_METHOD_S256,
    SCOPE_AUTHENTIK_DCR,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import AuthorizeError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2DynamicClientRegistration,
    OAuth2Provider,
    PKCEMode,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams

REDIRECT_URI = "http://local.invalid/callback"
VERIFIER = generate_id(64)
NO_CHALLENGE = None


def challenge_params(method: str | None) -> dict[str, str]:
    """Authorization request parameters for a challenge with the given method"""
    if method == PKCE_METHOD_S256:
        return {"code_challenge": pkce_s256_challenge(VERIFIER), "code_challenge_method": method}
    if method == PKCE_METHOD_PLAIN:
        return {"code_challenge": VERIFIER, "code_challenge_method": method}
    return {}


def is_required(mode: PKCEMode, client_type: ClientType) -> bool:
    return mode == PKCEMode.REQUIRED or (
        mode == PKCEMode.REQUIRED_PUBLIC and client_type == ClientType.PUBLIC
    )


class TestPKCERequirement(OAuthTestCase):
    """Test the PKCE requirement at the authorization and token endpoints"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.IMPLICIT, GrantType.HYBRID],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            signing_key=self.keypair,
            access_code_validity="seconds=100",
        )
        self.provider.property_mappings.set(ScopeMapping.objects.filter(scope_name="openid"))
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def configure(self, mode: PKCEMode, allow_plain: bool, client_type: ClientType):
        self.provider.pkce_mode = mode
        self.provider.pkce_allow_plain = allow_plain
        self.provider.client_type = client_type
        self.provider.save()

    def authorize(self, response_type: str = "code", **params) -> OAuthAuthorizationParams:
        request = self.factory.get(
            "/",
            data={
                "response_type": response_type,
                "client_id": self.provider.client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "openid",
                "nonce": generate_id(),
                "state": generate_id(),
                **params,
            },
        )
        return OAuthAuthorizationParams.from_request(request)

    def redeem(self, code: AuthorizationCode, verifier: str | None):
        data = {
            "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
            "code": code.code,
            "redirect_uri": REDIRECT_URI,
        }
        if verifier:
            data["code_verifier"] = verifier
        headers = {}
        if self.provider.client_type == ClientType.CONFIDENTIAL:
            credentials = f"{self.provider.client_id}:{self.provider.client_secret}"
            headers["HTTP_AUTHORIZATION"] = f"Basic {b64encode(credentials.encode()).decode()}"
        else:
            data["client_id"] = self.provider.client_id
        return self.client.post(reverse("authentik_providers_oauth2:token"), data=data, **headers)

    def create_code(self, method: str | None) -> AuthorizationCode:
        code = AuthorizationCode(
            code=generate_id(),
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=1),
        )
        params = challenge_params(method)
        code.code_challenge = params.get("code_challenge")
        code.code_challenge_method = params.get("code_challenge_method")
        code.save()
        return code

    def test_authorize_matrix(self):
        """Every mode, client type and challenge method at the authorization endpoint"""
        for mode, allow_plain, client_type, method in product(
            PKCEMode,
            [True, False],
            ClientType,
            [NO_CHALLENGE, PKCE_METHOD_PLAIN, PKCE_METHOD_S256],
        ):
            with self.subTest(
                mode=mode, allow_plain=allow_plain, client_type=client_type, method=method
            ):
                self.configure(mode, allow_plain, client_type)
                if method == NO_CHALLENGE:
                    rejected = is_required(mode, client_type)
                    cause = "pkce_challenge_missing"
                else:
                    rejected = method == PKCE_METHOD_PLAIN and not allow_plain
                    cause = "pkce_method_not_allowed"
                if not rejected:
                    params = self.authorize(**challenge_params(method))
                    self.assertEqual(
                        params.code_challenge, challenge_params(method).get("code_challenge")
                    )
                    continue
                with self.assertRaises(AuthorizeError) as cm:
                    self.authorize(**challenge_params(method))
                self.assertEqual(cm.exception.error, "invalid_request")
                self.assertEqual(cm.exception.cause, cause)
                # Errors are returned to the client, not shown to the user
                self.assertEqual(cm.exception.redirect_uri, REDIRECT_URI)

    def test_authorize_hybrid_requires_pkce(self):
        """The hybrid flow issues an authorization code, so it requires PKCE"""
        self.configure(PKCEMode.REQUIRED, False, ClientType.PUBLIC)
        with self.assertRaises(AuthorizeError) as cm:
            self.authorize(response_type="code id_token")
        self.assertEqual(cm.exception.cause, "pkce_challenge_missing")
        self.authorize(response_type="code id_token", **challenge_params(PKCE_METHOD_S256))

    def test_authorize_implicit_not_affected(self):
        """The implicit flow issues no authorization code, so PKCE is not required"""
        self.configure(PKCEMode.REQUIRED, False, ClientType.PUBLIC)
        self.authorize(response_type="id_token")

    def test_authorize_default_method_is_plain(self):
        """A challenge without a method uses plain (RFC 7636 section 4.3)"""
        self.configure(PKCEMode.REQUIRED, False, ClientType.PUBLIC)
        with self.assertRaises(AuthorizeError) as cm:
            self.authorize(code_challenge=VERIFIER)
        self.assertEqual(cm.exception.cause, "pkce_method_not_allowed")
        self.assertEqual(
            cm.exception.description, "Challenge method plain is not allowed, use S256"
        )

    def test_authorize_unsupported_method(self):
        """Unknown methods are rejected regardless of the provider's settings"""
        self.configure(PKCEMode.OPTIONAL, True, ClientType.CONFIDENTIAL)
        with self.assertRaises(AuthorizeError) as cm:
            self.authorize(code_challenge=VERIFIER, code_challenge_method="S512")
        self.assertEqual(cm.exception.cause, "pkce_method_unsupported")

    def test_authorize_view_error_redirect(self):
        """A missing challenge is returned to the client as invalid_request"""
        self.configure(PKCEMode.REQUIRED_PUBLIC, False, ClientType.PUBLIC)
        state = generate_id()
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": self.provider.client_id,
                "redirect_uri": REDIRECT_URI,
                "state": state,
            },
        )
        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.url)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", REDIRECT_URI)
        query = parse_qs(parsed.query)
        self.assertEqual(query["error"], ["invalid_request"])
        self.assertEqual(query["error_description"], ["code_challenge is required"])
        self.assertEqual(query["state"], [state])

    def test_token_matrix(self):
        """Codes are only redeemed when they satisfy the provider's current settings, even
        when they were issued without doing so"""
        for mode, allow_plain, client_type, method in product(
            PKCEMode,
            [True, False],
            ClientType,
            [NO_CHALLENGE, PKCE_METHOD_PLAIN, PKCE_METHOD_S256],
        ):
            with self.subTest(
                mode=mode, allow_plain=allow_plain, client_type=client_type, method=method
            ):
                self.configure(mode, allow_plain, client_type)
                code = self.create_code(method)
                if method == NO_CHALLENGE:
                    rejected = is_required(mode, client_type)
                else:
                    rejected = method == PKCE_METHOD_PLAIN and not allow_plain
                response = self.redeem(code, VERIFIER if method else None)
                if rejected:
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()["error"], "invalid_grant")
                else:
                    self.assertEqual(response.status_code, 200, response.content)
                    self.assertIn("access_token", response.json())

    def test_token_still_verifies(self):
        """Required PKCE still needs a matching verifier"""
        self.configure(PKCEMode.REQUIRED, False, ClientType.PUBLIC)
        response = self.redeem(self.create_code(PKCE_METHOD_S256), generate_id(64))
        self.assertEqual(response.status_code, 400)
        response = self.redeem(self.create_code(PKCE_METHOD_S256), None)
        self.assertEqual(response.status_code, 400)

    def test_full_flow(self):
        """A public client using S256 completes the flow with the new defaults"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.PUBLIC,
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            signing_key=self.keypair,
            access_code_validity="seconds=100",
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        self.provider = provider
        self.client.force_login(self.user)
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": provider.client_id,
                "redirect_uri": REDIRECT_URI,
                **challenge_params(PKCE_METHOD_S256),
            },
        )
        code = AuthorizationCode.objects.get(user=self.user, provider=provider)
        self.assertEqual(code.code_challenge_method, PKCE_METHOD_S256)
        response = self.redeem(code, VERIFIER)
        self.assertEqual(response.status_code, 200, response.content)


class TestPKCESettings(OAuthTestCase):
    """Test PKCE settings defaults, discovery, API and dynamic client registration"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            signing_key=self.keypair,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def test_new_provider_defaults(self):
        """New providers require S256 PKCE from public clients"""
        self.assertEqual(self.provider.pkce_mode, PKCEMode.REQUIRED_PUBLIC)
        self.assertFalse(self.provider.pkce_allow_plain)
        self.assertFalse(self.provider.pkce_required)
        self.provider.client_type = ClientType.PUBLIC
        self.assertTrue(self.provider.pkce_required)

    def test_migration_defaults(self):
        """Existing providers keep their behavior, new providers get the strict defaults"""
        migration = import_module(
            "authentik.providers.oauth2.migrations.0039_oauth2provider_pkce"
        ).Migration
        added = {op.name: op.field for op in migration.operations if isinstance(op, AddField)}
        altered = {op.name: op.field for op in migration.operations if isinstance(op, AlterField)}
        # Applied to rows that exist when migrating
        self.assertEqual(added["pkce_mode"].default, PKCEMode.OPTIONAL)
        self.assertTrue(added["pkce_allow_plain"].default)
        # Default for rows created afterwards, matching the model
        self.assertEqual(altered["pkce_mode"].default, PKCEMode.REQUIRED_PUBLIC)
        self.assertFalse(altered["pkce_allow_plain"].default)
        for name in ["pkce_mode", "pkce_allow_plain"]:
            self.assertEqual(altered[name].default, OAuth2Provider._meta.get_field(name).default)
        # Adding the field with the legacy default must come first
        names = [(type(op), op.name) for op in migration.operations]
        for name in ["pkce_mode", "pkce_allow_plain"]:
            self.assertLess(names.index((AddField, name)), names.index((AlterField, name)))

    def test_migrated_provider_unchanged(self):
        """A provider with the migrated settings accepts requests without PKCE"""
        self.provider.pkce_mode = PKCEMode.OPTIONAL
        self.provider.pkce_allow_plain = True
        self.provider.client_type = ClientType.PUBLIC
        self.assertFalse(self.provider.pkce_required)
        self.assertEqual(self.provider.pkce_methods, [PKCE_METHOD_PLAIN, PKCE_METHOD_S256])

    def get_info(self) -> dict:
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": self.app.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_discovery(self):
        """Discovery only advertises plain when the provider allows it"""
        self.assertEqual(self.get_info()["code_challenge_methods_supported"], [PKCE_METHOD_S256])
        self.provider.pkce_allow_plain = True
        self.provider.save()
        self.assertEqual(
            self.get_info()["code_challenge_methods_supported"],
            [PKCE_METHOD_PLAIN, PKCE_METHOD_S256],
        )

    def test_api(self):
        """Settings default when creating providers and are kept when omitted on update"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["pkce_mode"], PKCEMode.REQUIRED_PUBLIC)
        self.assertFalse(response.json()["pkce_allow_plain"])
        pk = response.json()["pk"]
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": pk}),
            data={"pkce_mode": PKCEMode.OPTIONAL, "pkce_allow_plain": True},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": pk}),
            data={"name": generate_id()},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        provider = OAuth2Provider.objects.get(pk=pk)
        self.assertEqual(provider.pkce_mode, PKCEMode.OPTIONAL)
        self.assertTrue(provider.pkce_allow_plain)

    def test_dcr_inherits(self):
        """Dynamically registered clients copy the registration provider's settings"""
        self.provider.pkce_mode = PKCEMode.REQUIRED
        self.provider.pkce_allow_plain = True
        self.provider.save()
        OAuth2DynamicClientRegistration.objects.create(provider=self.provider)
        token = AccessToken.objects.create(
            user=self.user,
            provider=self.provider,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope=SCOPE_AUTHENTIK_DCR,
            _id_token=json.dumps({}),
        )
        response = self.client.post(
            reverse(
                "authentik_providers_oauth2:dynamic-client-registration",
                kwargs={"application_slug": self.app.slug},
            ),
            json.dumps({"redirect_uris": [REDIRECT_URI], "token_endpoint_auth_method": "none"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        registered = OAuth2Provider.objects.get(client_id=response.json()["client_id"])
        self.assertEqual(registered.pkce_mode, PKCEMode.REQUIRED)
        self.assertTrue(registered.pkce_allow_plain)
