"""test decorators api"""

from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.crypto.generators import generate_id


class TestAPIDecorators(APITestCase):
    """test decorators api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_user()

    def test_obj_perm_denied(self):
        """Test object perm denied"""
        self.client.force_login(self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_obj_perm_global(self):
        """Test object perm successful (global)"""
        assign_perm("authentik_core.view_application", self.user)
        assign_perm("authentik_events.view_event", self.user)
        self.client.force_login(self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_obj_perm_scoped(self):
        """Test object perm successful (scoped)"""
        assign_perm("authentik_events.view_event", self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        assign_perm("authentik_core.view_application", self.user, app)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_perm_denied(self):
        """Test other perm denied"""
        self.client.force_login(self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        assign_perm("authentik_core.view_application", self.user, app)
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 403)
