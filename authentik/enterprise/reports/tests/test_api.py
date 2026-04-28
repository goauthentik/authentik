from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.reports.tests.utils import patch_license
from authentik.events.models import Event


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
