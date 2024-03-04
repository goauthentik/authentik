"""Schema generation tests"""

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import safe_load


class TestSchemaGeneration(APITestCase):
    """Generic admin tests"""

    def test_schema(self):
        """Test generation"""
        response = self.client.get(
            reverse("authentik_api:schema"),
        )
        self.assertTrue(safe_load(response.content.decode()))

    def test_browser(self):
        """Test API Browser"""
        response = self.client.get(
            reverse("authentik_api:schema-browser"),
        )
        self.assertEqual(response.status_code, 200)
