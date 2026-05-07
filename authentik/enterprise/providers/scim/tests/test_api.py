"""SCIM OAuth tests"""

from unittest.mock import MagicMock, PropertyMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.enterprise.tests.test_license import expiry_valid
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource


class TestSCIMOAuthAPI(APITestCase):
    """SCIM User tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            access_token_url="http://localhost/token",  # nosec
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            provider_type="openidconnect",
        )

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_api_create(self):
        License.objects.create(key=generate_id())
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:scimprovider-list"),
            {
                "name": generate_id(),
                "url": "http://localhost",
                "auth_mode": "oauth_silent",
                "auth_oauth": str(self.source.pk),
            },
        )
        self.assertEqual(res.status_code, 201)

    @patch(
        "authentik.enterprise.models.LicenseUsageStatus.is_valid",
        PropertyMock(return_value=False),
    )
    def test_api_create_no_license(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:scimprovider-list"),
            {
                "name": generate_id(),
                "url": "http://localhost",
                "auth_mode": "oauth_silent",
                "auth_oauth": str(self.source.pk),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"auth_mode": ["Enterprise is required to use the OAuth mode."]}
        )
