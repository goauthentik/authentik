from json import loads

from django.apps import apps
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import (
    GroupOAuthSourceConnection,
    OAuthSource,
    UserOAuthSourceConnection,
)

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


class TestSourceConnectionAPI(APITestCase):
    """Creating and updating user and group source connections"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)
        self.source = OAuthSource.objects.create(name=generate_id(), slug=generate_id())
        self.user = create_test_user()

    def test_create_user_connection(self):
        """An admin links an existing user to their subject at a source"""
        identifier = generate_id()
        response = self.client.post(
            "/api/v3/sources/user_connections/oauth/",
            {"user": self.user.pk, "source": self.source.pk, "identifier": identifier},
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            UserOAuthSourceConnection.objects.filter(
                user=self.user, source=self.source, identifier=identifier
            ).exists()
        )

    def test_create_user_connection_requires_user(self):
        """A connection without a user is refused, not a server error"""
        response = self.client.post(
            "/api/v3/sources/user_connections/oauth/",
            {"source": self.source.pk, "identifier": generate_id()},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.json())

    def test_create_user_connection_duplicate(self):
        """A user has one connection per source"""
        UserOAuthSourceConnection.objects.create(
            user=self.user, source=self.source, identifier=generate_id()
        )
        response = self.client.post(
            "/api/v3/sources/user_connections/oauth/",
            {"user": self.user.pk, "source": self.source.pk, "identifier": generate_id()},
        )
        self.assertEqual(response.status_code, 400)

    def test_update_keeps_user(self):
        """A connection can't be moved to another user"""
        connection = UserOAuthSourceConnection.objects.create(
            user=self.user, source=self.source, identifier=generate_id()
        )
        response = self.client.patch(
            f"/api/v3/sources/user_connections/oauth/{connection.pk}/",
            {"user": self.admin.pk, "identifier": "changed"},
        )
        self.assertEqual(response.status_code, 200, response.content)
        connection.refresh_from_db()
        self.assertEqual(connection.user, self.user)
        self.assertEqual(connection.identifier, "changed")

    def test_create_group_connection(self):
        """An admin links an existing group to its identifier at a source"""
        group = Group.objects.create(name=generate_id())
        response = self.client.post(
            "/api/v3/sources/group_connections/oauth/",
            {"group": str(group.pk), "source": self.source.pk, "identifier": generate_id()},
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            GroupOAuthSourceConnection.objects.filter(group=group, source=self.source).exists()
        )
