import csv

from django.contrib.contenttypes.models import ContentType
from django.test.testcases import TestCase

from authentik.admin.files.tests.utils import FileTestFileBackendMixin
from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.reports.models import DataExport
from authentik.enterprise.reports.tests.utils import _add_perm, patch_license


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
