"""Tests for OAuth2 Dynamic Client Registration (RFC 7591)"""

import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import SCOPE_AUTHENTIK_DCR
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    GrantType,
    OAuth2DynamicClientRegistration,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)


class TestDynamicClientRegistration(TestCase):
    """RFC 7591 Dynamic Client Registration tests"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self):
        self.flow = create_test_flow()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.dcr = OAuth2DynamicClientRegistration.objects.create(
            provider=self.provider,
            create_application=True,
            default_authorization_flow=self.flow,
        )
        self.register_url = reverse(
            "authentik_enterprise_providers_oauth2:dynamic-client-registration",
            kwargs={"application_slug": self.app.slug},
        )

    def _access_token(self, scope: str = SCOPE_AUTHENTIK_DCR, **kwargs) -> AccessToken:
        return AccessToken.objects.create(
            user=kwargs.pop("user", None) or create_test_user(),
            provider=kwargs.pop("provider", None) or self.provider,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope=scope,
            _id_token=json.dumps({}),
            **kwargs,
        )

    def _post(self, body: dict, token: str | None = None) -> object:
        headers = {"content_type": "application/json"}
        if token:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.client.post(self.register_url, json.dumps(body), **headers)

    def test_registration_success(self):
        """Basic registration creates a new OAuth2Provider and Application."""
        token = self._access_token()
        response = self._post(
            {"redirect_uris": ["https://example.com/callback"], "client_name": "Test Client"},
            token=token.token,
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        self.assertIn("client_id", body)
        self.assertIn("client_secret", body)
        self.assertEqual(body["redirect_uris"], ["https://example.com/callback"])
        self.assertEqual(body["client_name"], "Test Client")
        # Provider created
        self.assertTrue(OAuth2Provider.objects.filter(client_id=body["client_id"]).exists())
        # Application created
        provider = OAuth2Provider.objects.get(client_id=body["client_id"])
        self.assertIsNotNone(provider.application)

    def test_registration_no_application(self):
        """When create_application=False, no Application is created."""
        self.dcr.create_application = False
        self.dcr.save()
        token = self._access_token()
        response = self._post({"redirect_uris": ["https://example.com/cb"]}, token=token.token)
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        provider = OAuth2Provider.objects.get(client_id=body["client_id"])
        self.assertFalse(hasattr(provider, "application") and provider.application is not None)

    def test_requires_redirect_uris(self):
        """redirect_uris is required."""
        token = self._access_token()
        response = self._post({"client_name": "No URIs"}, token=token.token)
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_redirect_uri")

    def test_invalid_json(self):
        """Non-JSON body is rejected."""
        token = self._access_token()
        response = self.client.post(
            self.register_url,
            "not-json",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_client_metadata")

    def test_requires_access_token(self):
        """Requests without a bearer token are rejected."""
        response = self._post({"redirect_uris": ["https://example.com/cb"]})
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_token")

    def test_access_token_missing_scope_rejected(self):
        """An access token without the DCR scope is rejected."""
        token = self._access_token(scope="")
        response = self._post(
            {"redirect_uris": ["https://example.com/cb"]},
            token=token.token,
        )
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_token")

    def test_valid_access_token(self):
        """A valid access token with the DCR scope grants registration."""
        token = self._access_token()
        response = self._post(
            {"redirect_uris": ["https://example.com/cb"]},
            token=token.token,
        )
        self.assertEqual(response.status_code, 201)

    def test_expired_access_token_rejected(self):
        """An expired access token cannot be used to register clients."""
        token = self._access_token(expires=timezone.now() - timedelta(hours=1))
        response = self._post(
            {"redirect_uris": ["https://example.com/cb"]},
            token=token.token,
        )
        self.assertEqual(response.status_code, 401)

    def test_grant_type_restriction(self):
        """Grant types not in allowed_grant_types are filtered out."""
        self.dcr.allowed_grant_types = [GrantType.AUTHORIZATION_CODE]
        self.dcr.save()
        token = self._access_token()
        response = self._post(
            {
                "redirect_uris": ["https://example.com/cb"],
                "grant_types": [GrantType.AUTHORIZATION_CODE, GrantType.CLIENT_CREDENTIALS],
            },
            token=token.token,
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        self.assertNotIn(GrantType.CLIENT_CREDENTIALS, body["grant_types"])
        self.assertIn(GrantType.AUTHORIZATION_CODE, body["grant_types"])

    def test_public_client_no_secret(self):
        """Public client (auth_method=none) does not receive a client_secret."""
        token = self._access_token()
        response = self._post(
            {
                "redirect_uris": ["https://example.com/cb"],
                "token_endpoint_auth_method": "none",
            },
            token=token.token,
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        self.assertNotIn("client_secret", body)
        provider = OAuth2Provider.objects.get(client_id=body["client_id"])
        self.assertEqual(provider.client_type, ClientType.PUBLIC)

    def test_registration_endpoint_in_openid_config(self):
        """registration_endpoint is advertised in .well-known/openid-configuration."""
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": self.app.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        config = json.loads(response.content)
        self.assertIn("registration_endpoint", config)
        self.assertIn("/register/", config["registration_endpoint"])

    def test_no_registration_endpoint_when_dcr_disabled(self):
        """registration_endpoint is absent when DCR is not configured."""
        # Create a separate provider/app without DCR
        provider2 = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        app2 = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider2,
        )
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": app2.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        config = json.loads(response.content)
        self.assertNotIn("registration_endpoint", config)

    def test_register_endpoint_404_without_dcr(self):
        """Registration endpoint returns 404 when DCR is not configured on that provider."""
        provider2 = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        app2_slug = generate_id().lower()
        app2 = Application.objects.create(
            name=generate_id(),
            slug=app2_slug,
            provider=provider2,
        )
        response = self.client.post(
            reverse(
                "authentik_enterprise_providers_oauth2:dynamic-client-registration",
                kwargs={"application_slug": app2.slug},
            ),
            json.dumps({"redirect_uris": ["https://x.com/cb"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
