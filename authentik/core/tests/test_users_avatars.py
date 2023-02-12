"""Test Users Avatars"""
from json import loads

from django.urls.base import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.config import CONFIG


class TestUsersAvatars(APITestCase):
    """Test Users avatars"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = User.objects.create(username="test-user")

    @CONFIG.patch("avatars", "none")
    def test_avatars_none(self):
        """Test avatars none"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "/static/dist/assets/images/user_default.png")

    @CONFIG.patch("avatars", "gravatar")
    def test_avatars_gravatar(self):
        """Test avatars gravatar"""
        self.admin.email = "static@t.goauthentik.io"
        self.admin.save()
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                (
                    "https://secure.gravatar.com/avatar/84730f9c1851d1ea03f1a"
                    "a9ed85bd1ea?size=158&rating=g&default=404"
                ),
                text="foo",
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("gravatar", body["user"]["avatar"])

    @CONFIG.patch("avatars", "initials")
    def test_avatars_initials(self):
        """Test avatars initials"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    @CONFIG.patch("avatars", "foo://%(username)s")
    def test_avatars_custom(self):
        """Test avatars custom"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], f"foo://{self.admin.username}")

    @CONFIG.patch("avatars", "attributes.foo.avatar")
    def test_avatars_attributes(self):
        """Test avatars attributes"""
        self.admin.attributes = {"foo": {"avatar": "bar"}}
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "bar")

    @CONFIG.patch("avatars", "attributes.foo.avatar,initials")
    def test_avatars_fallback(self):
        """Test fallback"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])
