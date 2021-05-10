"""Swagger generation tests"""
from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import safe_load


class TestSwaggerGeneration(APITestCase):
    """Generic admin tests"""

    def test_yaml(self):
        """Test YAML generation"""
        response = self.client.get(
            reverse("authentik_api:schema-json", kwargs={"format": ".yaml"}),
        )
        self.assertTrue(safe_load(response.content.decode()))

    def test_json(self):
        """Test JSON generation"""
        response = self.client.get(
            reverse("authentik_api:schema-json", kwargs={"format": ".json"}),
        )
        self.assertTrue(loads(response.content.decode()))

    def test_browser(self):
        """Test API Browser"""
        response = self.client.get(
            reverse("authentik_api:swagger"),
        )
        self.assertEqual(response.status_code, 200)
