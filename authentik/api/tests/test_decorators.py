"""test decorators api"""
from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Application, User


class TestAPIDecorators(APITestCase):
    """test decorators api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="test-user")

    def test_obj_perm_denied(self):
        """Test object perm denied"""
        self.client.force_login(self.user)
        app = Application.objects.create(name="denied", slug="denied")
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_other_perm_denied(self):
        """Test other perm denied"""
        self.client.force_login(self.user)
        app = Application.objects.create(name="denied", slug="denied")
        assign_perm("authentik_core.view_application", self.user, app)
        response = self.client.get(
            reverse("authentik_api:application-metrics", kwargs={"slug": app.slug})
        )
        self.assertEqual(response.status_code, 403)
