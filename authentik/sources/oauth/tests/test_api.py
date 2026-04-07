from django.urls import reverse
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
