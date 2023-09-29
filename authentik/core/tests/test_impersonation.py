"""impersonation tests"""
from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.config import CONFIG


class TestImpersonation(APITestCase):
    """impersonation tests"""

    def setUp(self) -> None:
        super().setUp()
        self.other_user = User.objects.create(username="to-impersonate")
        self.user = create_test_admin_user()

    def test_impersonate_simple(self):
        """test simple impersonation and un-impersonation"""
        # test with an inactive user to ensure that still works
        self.other_user.is_active = False
        self.other_user.save()
        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "authentik_api:user-impersonate",
                kwargs={"pk": self.other_user.pk},
            )
        )

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)
        self.assertEqual(response_body["original"]["username"], self.user.username)

        self.client.get(reverse("authentik_api:user-impersonate-end"))

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)
        self.assertNotIn("original", response_body)

    def test_impersonate_denied(self):
        """test impersonation without permissions"""
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)

    @CONFIG.patch("impersonation", False)
    def test_impersonate_disabled(self):
        """test impersonation that is disabled"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.other_user.pk})
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)

    def test_impersonate_self(self):
        """test impersonation that user can't impersonate themselves"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)

    def test_un_impersonate_empty(self):
        """test un-impersonation without impersonating first"""
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("authentik_api:user-impersonate-end"))
        self.assertEqual(response.status_code, 204)
