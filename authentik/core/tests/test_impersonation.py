"""impersonation tests"""
from json import loads

from django.test.testcases import TestCase
from django.urls import reverse

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user


class TestImpersonation(TestCase):
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

        self.client.get(
            reverse(
                "authentik_core:impersonate-init",
                kwargs={"user_id": self.other_user.pk},
            )
        )

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)
        self.assertEqual(response_body["original"]["username"], self.user.username)

        self.client.get(reverse("authentik_core:impersonate-end"))

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)
        self.assertNotIn("original", response_body)

    def test_impersonate_denied(self):
        """test impersonation without permissions"""
        self.client.force_login(self.other_user)

        self.client.get(
            reverse("authentik_core:impersonate-init", kwargs={"user_id": self.user.pk})
        )

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)

    def test_un_impersonate_empty(self):
        """test un-impersonation without impersonating first"""
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("authentik_core:impersonate-end"))
        self.assertRedirects(
            response, reverse("authentik_interfaces:if", kwargs={"if_name": "user"})
        )
