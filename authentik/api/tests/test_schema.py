"""Schema generation tests"""

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import add_representer, safe_load


def represent_type(dumper, data):
    """Custom representer for type objects"""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


add_representer(type, represent_type)


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
