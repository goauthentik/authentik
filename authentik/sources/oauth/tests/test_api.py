from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource


class TestOAuthSourceAPI(APITestCase):
    def setUp(self):
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key=generate_id(),
        )
        self.user = create_test_admin_user()

    def test_patch_no_type(self):
        self.client.force_login(self.user)
        res = self.client.patch(
            reverse("authentik_api:oauthsource-detail", kwargs={"slug": self.source.slug}),
            {
                "authorization_url": f"https://{generate_id()}",
                "profile_url": f"https://{generate_id()}",
                "access_token_url": f"https://{generate_id()}",
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_patch_long_url(self):
        """URL fields are TextField, so URLs longer than 255 chars (e.g. an
        authorization URL carrying many static query parameters) must save."""
        self.client.force_login(self.user)
        long_url = "https://cilogon.org/authorize?idphint=" + ",".join(
            f"https://idp{i}.institution.example.org/idp/shibboleth" for i in range(10)
        )
        self.assertGreater(len(long_url), 255)
        res = self.client.patch(
            reverse("authentik_api:oauthsource-detail", kwargs={"slug": self.source.slug}),
            {"authorization_url": long_url},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.source.refresh_from_db()
        self.assertEqual(self.source.authorization_url, long_url)

    @Mocker()
    def test_disable_source_invalid_well_known_url(self, mock: Mocker):
        """Saving a disabled source should not make a request to the well-known url"""
        self.client.force_login(self.user)

        well_known_url = f"https://{generate_id()}/.well-known/openid-configuration"
        mock.get(well_known_url, json={})

        res = self.client.patch(
            reverse("authentik_api:oauthsource-detail", kwargs={"slug": self.source.slug}),
            {
                "enabled": False,
                "oidc_well_known_url": well_known_url,
                "authorization_url": f"https://{generate_id()}",
                "profile_url": f"https://{generate_id()}",
                "access_token_url": f"https://{generate_id()}",
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(mock.call_count, 0)
