from json import loads

from django.apps import apps
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource

GITHUB_ICON_THEMED_URLS = {
    "light": "/static/authentik/sources/github/light.svg",
    "dark": "/static/authentik/sources/github/dark.svg",
}


class TestSourceAPI(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_builtin_source_used_by(self):
        """Test Providers's types endpoint"""
        apps.get_app_config("authentik_core").source_inbuilt()
        response = self.client.get(
            reverse("authentik_api:source-used-by", kwargs={"slug": "authentik-built-in"}),
        )
        self.assertEqual(response.status_code, 200)

    def test_user_settings_icon_themed_urls(self):
        """Test themed icon URLs of user settings"""
        github = OAuthSource.objects.create(
            name=generate_id(), slug=generate_id(), provider_type="github"
        )
        custom = OAuthSource.objects.create(
            name=generate_id(), slug=generate_id(), icon="https://example.com/logo.png"
        )

        response = self.client.get(reverse("authentik_api:source-user-settings"))

        self.assertEqual(response.status_code, 200)
        settings = {setting["object_uid"]: setting for setting in loads(response.content)}
        self.assertEqual(settings[github.slug]["icon_themed_urls"], GITHUB_ICON_THEMED_URLS)
        self.assertIsNone(settings[custom.slug]["icon_themed_urls"])

    def test_types_icon_themed_urls(self):
        """Test themed icon URLs of source types"""
        response = self.client.get(reverse("authentik_api:source-types"))

        self.assertEqual(response.status_code, 200)
        types = {source_type["model_name"]: source_type for source_type in loads(response.content)}
        self.assertEqual(types["githuboauthsource"]["icon_themed_urls"], GITHUB_ICON_THEMED_URLS)
