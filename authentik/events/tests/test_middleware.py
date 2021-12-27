"""Event Middleware tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction


class TestEventsMiddleware(APITestCase):
    """Test Event Middleware"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_create(self):
        """Test model creation event"""
        self.client.post(
            reverse("authentik_api:application-list"),
            data={"name": "test-create", "slug": "test-create"},
        )
        self.assertTrue(Application.objects.filter(name="test-create").exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED,
                context__model__model_name="application",
                context__model__app="authentik_core",
                context__model__name="test-create",
            ).exists()
        )

    def test_delete(self):
        """Test model creation event"""
        Application.objects.create(name="test-delete", slug="test-delete")
        self.client.delete(
            reverse("authentik_api:application-detail", kwargs={"slug": "test-delete"})
        )
        self.assertFalse(Application.objects.filter(name="test").exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_DELETED,
                context__model__model_name="application",
                context__model__app="authentik_core",
                context__model__name="test-delete",
            ).exists()
        )
