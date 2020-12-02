"""impersonation tests"""
from django.shortcuts import reverse
from django.test.testcases import TestCase

from authentik.core.models import User


class TestImpersonation(TestCase):
    """impersonation tests"""

    def setUp(self) -> None:
        super().setUp()
        self.other_user = User.objects.create(username="to-impersonate")
        self.pbadmin = User.objects.get(username="pbadmin")

    def test_impersonate_simple(self):
        """test simple impersonation and un-impersonation"""
        self.client.force_login(self.pbadmin)

        self.client.get(
            reverse(
                "authentik_core:impersonate-init",
                kwargs={"user_id": self.other_user.pk},
            )
        )

        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertIn(self.other_user.username, response.content.decode())
        self.assertNotIn(self.pbadmin.username, response.content.decode())

        self.client.get(reverse("authentik_core:impersonate-end"))

        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertNotIn(self.other_user.username, response.content.decode())
        self.assertIn(self.pbadmin.username, response.content.decode())

    def test_impersonate_denied(self):
        """test impersonation without permissions"""
        self.client.force_login(self.other_user)

        self.client.get(
            reverse(
                "authentik_core:impersonate-init", kwargs={"user_id": self.pbadmin.pk}
            )
        )

        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertIn(self.other_user.username, response.content.decode())
        self.assertNotIn(self.pbadmin.username, response.content.decode())

    def test_un_impersonate_empty(self):
        """test un-impersonation without impersonating first"""
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("authentik_core:impersonate-end"))
        self.assertRedirects(response, reverse("authentik_core:shell"))
