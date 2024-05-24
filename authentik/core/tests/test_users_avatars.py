"""Test Users Avatars"""

from json import loads

from django.urls.base import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.tenants.utils import get_current_tenant


class TestUsersAvatars(APITestCase):
    """Test Users avatars"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = User.objects.create(username="test-user")

    def set_avatar_mode(self, mode: str):
        """Set the avatar mode on the current tenant."""
        tenant = get_current_tenant()
        tenant.avatars = mode
        tenant.save()

    def test_avatars_none(self):
        """Test avatars none"""
        self.set_avatar_mode("none")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "/static/dist/assets/images/user_default.png")

    def test_avatars_gravatar(self):
        """Test avatars gravatar"""
        self.set_avatar_mode("gravatar")
        self.admin.email = "static@t.goauthentik.io"
        self.admin.save()
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                (
                    "https://www.gravatar.com/avatar/76eb3c74c8beb6faa037f1b6e2ecb3e252bdac"
                    "6cf71fb567ae36025a9d4ea86b?size=158&rating=g&default=404"
                ),
                text="foo",
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("gravatar", body["user"]["avatar"])

    def test_avatars_initials(self):
        """Test avatars initials"""
        self.set_avatar_mode("initials")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    def test_avatars_custom(self):
        """Test avatars custom"""
        self.set_avatar_mode("foo://%(username)s")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], f"foo://{self.admin.username}")

    def test_avatars_attributes(self):
        """Test avatars attributes"""
        self.set_avatar_mode("attributes.foo.avatar")
        self.admin.attributes = {"foo": {"avatar": "bar"}}
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "bar")

    def test_avatars_fallback(self):
        """Test fallback"""
        self.set_avatar_mode("attributes.foo.avatar,initials")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])
