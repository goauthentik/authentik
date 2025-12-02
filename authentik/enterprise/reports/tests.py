import csv
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test.testcases import TestCase
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APITestCase

from authentik.admin.files.tests.utils import FileTestFileBackendMixin
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.reports.models import DataExport
from authentik.events.models import Event


def _add_perm(user, codename: str, app_label: str):
    permission = Permission.objects.get(codename=codename, content_type__app_label=app_label)
    user.user_permissions.add(permission)
    user.save()


def _drop_perm(user, codename: str, app_label: str):
    permission = Permission.objects.get(codename=codename, content_type__app_label=app_label)
    user.user_permissions.remove(permission)
    user.save()


patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)


@patch_license
class TestExportAPI(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_create_user_export(self):
        """Test User export endpoint"""
        response = self.client.post(
            reverse("authentik_api:user-export"),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers["Location"],
            reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]}),
        )
        self.assertEqual(response.data["requested_by"]["pk"], self.user.pk)
        self.assertEqual(response.data["completed"], False)
        self.assertEqual(response.data["file_url"], "")
        self.assertEqual(response.data["query_params"], {})
        self.assertEqual(
            response.data["content_type"]["id"],
            ContentType.objects.get_for_model(User).id,
        )

    def test_create_event_export(self):
        """Test Event export endpoint"""
        response = self.client.post(
            reverse("authentik_api:event-export"),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers["Location"],
            reverse("authentik_api:dataexport-detail", kwargs={"pk": response.data["id"]}),
        )
        self.assertEqual(response.data["requested_by"]["pk"], self.user.pk)
        self.assertEqual(response.data["completed"], False)
        self.assertEqual(response.data["file_url"], "")
        self.assertEqual(response.data["query_params"], {})
        self.assertEqual(
            response.data["content_type"]["id"],
            ContentType.objects.get_for_model(Event).id,
        )


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


@patch_license
class TestSchemaMatch(TestCase):
    def setUp(self) -> None:
        generator = SchemaGenerator()
        self.schema = generator.get_schema(request=None, public=True)

    def _index_params_by_name(self, parameters):
        result = {}
        for p in parameters or []:
            if p.get("in") != "query":
                continue
            schema = p.get("schema", {})
            result[p["name"]] = {
                "required": p.get("required", False),
                "type": schema.get("type"),
                "format": schema.get("format"),
                "enum": tuple(schema.get("enum", [])),
            }
        return result

    def _find_operation_by_operation_id(self, operation_id):
        for path_item in self.schema.get("paths", {}).values():
            for operation in path_item.values():
                if isinstance(operation, dict) and operation.get("operationId") == operation_id:
                    return operation
        raise AssertionError(f"operationId '{operation_id}' not found in schema")

    def _get_op_params(self, operation_id):
        operation = self._find_operation_by_operation_id(operation_id)
        return self._index_params_by_name(operation.get("parameters", []))

    def test_user_export_action_query_params_match_list(self):
        list_params = self._get_op_params("core_users_list")
        del list_params["include_groups"]  # Not applicable for export
        export_params = self._get_op_params("core_users_export_create")
        self.assertDictEqual(list_params, export_params)

    def test_event_export_action_query_params_match_list(self):
        list_params = self._get_op_params("events_events_list")
        export_params = self._get_op_params("events_events_export_create")
        self.assertDictEqual(list_params, export_params)


@patch_license
class TestUserExport(FileTestFileBackendMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.u1 = create_test_user(username="a")
        _add_perm(self.u1, "view_user", "authentik_core")
        self.u2 = create_test_user(username="b", path="abcd")
        _add_perm(self.u1, "view_user", "authentik_core")

    def _read_export(self, filename):
        with open(f"{self.reports_backend_path}/reports/public/{filename}") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def test_generate_user_export(self):
        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            requested_by=self.u1,
            query_params={"email": str(self.u1.email)},
        )
        export.generate()

        self.assertEqual(export.completed, True)
        data = self._read_export(export.file)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["Username"], self.u1.username)

    def test_path_filter(self):
        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            requested_by=self.u1,
            query_params={"path": str(self.u2.path)},
        )
        records = list(export.get_queryset())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.u2)

    def test_search_filter(self):
        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            requested_by=self.u1,
            query_params={"search": f'username = "{self.u2.username}"'},
        )
        records = list(export.get_queryset())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.u2)

    def test_ordering(self):
        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            requested_by=self.u1,
            query_params={"ordering": "-username"},
        )
        records = list(export.get_queryset())
        self.assertGreaterEqual(records[0].username, records[-1].username)
        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            requested_by=self.u1,
            query_params={"ordering": "username"},
        )
        records = list(export.get_queryset())
        self.assertLess(records[0].username, records[-1].username)


@patch_license
class TestEventExport(TestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        _add_perm(self.user, "view_event", "authentik_events")
        from authentik.events.models import Event, EventAction

        self.e1 = Event.new(EventAction.LOGIN, user=self.user)
        self.e1.save()
        self.e2 = Event.new(EventAction.LOGIN_FAILED, user=self.user)
        self.e2.save()

    def test_type_filter(self):
        from authentik.events.models import Event, EventAction

        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(Event),
            requested_by=self.user,
            query_params={"actions": [EventAction.LOGIN]},
        )
        records = list(export.get_queryset())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.e1)
