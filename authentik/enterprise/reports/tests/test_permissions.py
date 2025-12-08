from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.reports.tests.utils import patch_license


@patch_license
class TestExportPermissions(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.client.force_login(self.user)

    def test_export_without_permission(self):
        """Test User export endpoint without permission"""
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 403)

    def test_export_only_user_permission(self):
        """Test User export endpoint with only view_user permission"""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 403)

    def test_export_with_permission(self):
        """Test User export endpoint with view_user and add_dataexport permission"""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_reports.add_dataexport")
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 201)

    def test_export_access(self):
        """Test that data export access is restricted to the user who created it"""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_reports.add_dataexport")
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)
        other_user = create_test_user()
        other_user.assign_perms_to_managed_role("authentik_core.view_user")
        other_user.assign_perms_to_managed_role("authentik_reports.add_dataexport")
        self.client.logout()
        self.client.force_login(other_user)
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)

    def test_export_access_no_datatype_permission(self):
        """Test that data export access requires view permission on the data type"""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_reports.add_dataexport")
        self.user.assign_perms_to_managed_role("authentik_reports.view_dataexport")
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})

        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)

        self.user.remove_perms_from_managed_role("authentik_core.view_user")
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("authentik_api:dataexport-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_export_access_owner(self):
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_reports.add_dataexport")
        response = self.client.post(reverse("authentik_api:user-export"))
        self.assertEqual(response.status_code, 201)
        export_url = reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]})
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)

        self.user.remove_perms_from_managed_role("authentik_core.view_user")
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 404)
