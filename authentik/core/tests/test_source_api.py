from django.apps import apps
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Source
from authentik.core.tests.utils import create_test_admin_user


class TestSourceAPI(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_builtin_source_used_by(self):
        """Test Providers's types endpoint"""
        apps.get_app_config("authentik_core").source_inbuilt()
        source = Source.objects.get(slug="authentik-built-in")
        response = self.client.get(
            reverse("authentik_api:core-used-by"),
            data={"model": "authentik_core.source", "pk": str(source.pk)},
        )
        self.assertEqual(response.status_code, 200)
