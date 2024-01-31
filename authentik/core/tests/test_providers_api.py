"""Test providers API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user


class TestProvidersAPI(APITestCase):
    """Test providers API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_types(self):
        """Test Providers's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:provider-types"),
        )
        self.assertEqual(response.status_code, 200)
