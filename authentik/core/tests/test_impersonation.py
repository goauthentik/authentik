"""impersonation tests"""

from json import loads

from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.tenants.utils import get_current_tenant


class TestImpersonation(APITestCase):
    """impersonation tests"""

    def setUp(self) -> None:
        super().setUp()
        self.other_user = create_test_user()
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
            ),
            data={"reason": "some reason"},
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

    def test_impersonate_global(self):
        """Test impersonation with global permissions"""
        new_user = create_test_user()
        assign_perm("authentik_core.impersonate", new_user)
        assign_perm("authentik_core.view_user", new_user)
        self.client.force_login(new_user)

        response = self.client.post(
            reverse(
                "authentik_api:user-impersonate",
                kwargs={"pk": self.other_user.pk},
            ),
            data={"reason": "some reason"},
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)
        self.assertEqual(response_body["original"]["username"], new_user.username)

    def test_impersonate_scoped(self):
        """Test impersonation with scoped permissions"""
        new_user = create_test_user()
        assign_perm("authentik_core.impersonate", new_user, self.other_user)
        assign_perm("authentik_core.view_user", new_user, self.other_user)
        self.client.force_login(new_user)

        response = self.client.post(
            reverse(
                "authentik_api:user-impersonate",
                kwargs={"pk": self.other_user.pk},
            ),
            data={"reason": "some reason"},
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)
        self.assertEqual(response_body["original"]["username"], new_user.username)

    def test_impersonate_denied(self):
        """test impersonation without permissions"""
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk}),
            data={"reason": "some reason"},
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.other_user.username)

    def test_impersonate_disabled(self):
        """test impersonation that is disabled"""
        tenant = get_current_tenant()
        tenant.impersonation = False
        tenant.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.other_user.pk}),
            data={"reason": "some reason"},
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)

    def test_impersonate_self(self):
        """test impersonation that user can't impersonate themselves"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk}),
            data={"reason": "some reason"},
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.get(reverse("authentik_api:user-me"))
        response_body = loads(response.content.decode())
        self.assertEqual(response_body["user"]["username"], self.user.username)

    def test_impersonate_reason_required(self):
        """test impersonation that user must provide reason"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk}),
            data={"reason": ""},
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
