from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.reports.tests.utils import _add_perm, _drop_perm, patch_license


@patch_license
class TestExportPermissions(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.client.force_login(self.user)

    def _add_perm(self, codename: str, app_label: str, user=None):
        if user is None:
            user = self.user
        _add_perm(user, codename, app_label)

    def _drop_perm(self, codename: str, app_label: str, user=None):
        if user is None:
            user = self.user
        _drop_perm(user, codename, app_label)

    def test_export_without_permission(self):
        """Test User export endpoint without permission"""
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 403)

    def test_export_only_user_permission(self):
        """Test User export endpoint with only view_user permission"""
        self._add_perm("view_user", "authentik_core")
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 403)

    def test_export_with_permission(self):
        """Test User export endpoint with view_user and add_dataexport permission"""
        self._add_perm("view_user", "authentik_core")
        self._add_perm("add_dataexport", "authentik_reports")
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 201)

    def test_export_access(self):
        """Test that data export access is restricted to the user who created it"""
        self._add_perm("view_user", "authentik_core")
        self._add_perm("add_dataexport", "authentik_reports")
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)
        other_user = create_test_user()
        self._add_perm("view_user", "authentik_core", other_user)
        self._add_perm("add_dataexport", "authentik_reports", other_user)
        self.client.logout()
        self.client.force_login(other_user)
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)

    def test_export_access_no_datatype_permission(self):
        """Test that data export access requires view permission on the data type"""
        self._add_perm("view_user", "authentik_core")
        self._add_perm("add_dataexport", "authentik_reports")
        self._add_perm("view_dataexport", "authentik_reports")
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})

        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)

        self._drop_perm("view_user", "authentik_core")
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("authentik_api:dataexport-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_export_access_owner(self):
        self._add_perm("view_user", "authentik_core")
        self._add_perm("add_dataexport", "authentik_reports")
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)

        self._drop_perm("view_user", "authentik_core")
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)
