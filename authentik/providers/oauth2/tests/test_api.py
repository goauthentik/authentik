"""Test OAuth2 API"""

from json import loads
from sys import version_info
from unittest import skipUnless

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)


class TestAPI(APITestCase):
    """Test api view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_preview(self):
        """Test Preview API Endpoint"""
        response = self.client.get(
            reverse("authentik_api:oauth2provider-preview-user", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())["preview"]
        self.assertEqual(body["iss"], "http://testserver/application/o/test/")

    def test_setup_urls(self):
        """Test Setup URLs API Endpoint"""
        response = self.client.get(
            reverse("authentik_api:oauth2provider-setup-urls", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["issuer"], "http://testserver/application/o/test/")

    def test_global_token_view_permission(self):
        """Test that global view permissions are honored for all grant APIs"""
        service_account = create_test_user()
        token_owner = create_test_user()
        self.client.force_login(service_account)

        grants = [
            (
                AuthorizationCode,
                "authorization_codes",
                "authorizationcode",
                {"code": generate_id()},
            ),
            (
                RefreshToken,
                "refresh_tokens",
                "refreshtoken",
                {"token": generate_id(), "_id_token": "{}"},
            ),
            (
                AccessToken,
                "access_tokens",
                "accesstoken",
                {"token": generate_id(), "_id_token": "{}"},
            ),
        ]
        for model, endpoint, model_name, fields in grants:
            for action in ("view", "delete"):
                service_account.assign_perms_to_managed_role(
                    f"authentik_providers_oauth2.{action}_{model_name}"
                )
            grant = model.objects.create(
                provider=self.provider,
                user=token_owner,
                auth_time=timezone.now(),
                expiring=False,
                **fields,
            )

            response = self.client.get(f"/api/v3/oauth2/{endpoint}/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["results"][0]["user"]["pk"], token_owner.pk)

            response = self.client.delete(f"/api/v3/oauth2/{endpoint}/{grant.pk}/")

            self.assertEqual(response.status_code, 204)

    # https://github.com/goauthentik/authentik/pull/5918
    @skipUnless(version_info >= (3, 11, 4), "This behaviour is only Python 3.11.4 and up")
    def test_launch_url(self):
        """Test launch_url"""
        self.provider.redirect_uris = [
            RedirectURI(
                RedirectURIMatchingMode.REGEX,
                "https://[\\d\\w]+.pr.test.goauthentik.io/source/oauth/callback/authentik/",
            ),
        ]
        self.provider.save()
        self.provider.refresh_from_db()
        self.assertIsNone(self.provider.launch_url)

    def test_validate_client_id(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_id": "ú",
                "redirect_uris": [],
            },
        )
        self.assertJSONEqual(
            response.content,
            {"client_id": ["Client ID must consist of only ASCII characters."]},
        )

    def test_validate_client_secret(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_secret": "ú",
                "redirect_uris": [],
            },
        )
        self.assertJSONEqual(
            response.content,
            {"client_secret": ["Client secret must consist of only ASCII characters."]},
        )

    def test_validate_redirect_uris(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                    {"matching_mode": "regex", "url": "**"},
                ],
            },
        )
        self.assertJSONEqual(response.content, {"redirect_uris": ["Invalid Regex Pattern: **"]})

    def test_logout_uri_validation(self):
        """Test logout_uri API validation"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                ],
                "logout_uri": "invalid-url",
                "logout_method": "backchannel",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_logout_uri_create_and_retrieve(self):
        """Test creating and retrieving logout URI with method"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                ],
                "logout_uri": "http://goauthentik.io/logout",
                "logout_method": "backchannel",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider_data = response.json()
        self.assertEqual(provider_data["logout_uri"], "http://goauthentik.io/logout")
        self.assertEqual(provider_data["logout_method"], "backchannel")

        # Test retrieving the provider
        provider_pk = provider_data["pk"]
        response = self.client.get(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider_pk})
        )
        self.assertEqual(response.status_code, 200)
        retrieved_data = response.json()
        self.assertEqual(retrieved_data["logout_uri"], "http://goauthentik.io/logout")
        self.assertEqual(retrieved_data["logout_method"], "backchannel")
