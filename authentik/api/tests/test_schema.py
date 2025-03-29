"""Schema generation tests"""

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import add_multi_representer, add_representer, safe_load
from yaml.representer import SafeRepresenter


def represent_type(dumper, data):
    """Custom representer for type objects"""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def represent_str_class(dumper, data):
    """Custom representer for str class object (not string instances)"""
    if data is str:
        return dumper.represent_scalar("tag:yaml.org,2002:str", "string")
    if isinstance(data, type):
        return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


add_representer(type, represent_type)
# Specifically handle the str class
SafeRepresenter.add_representer(str, represent_str_class)
# Special case for <class 'str'>
add_multi_representer(type, represent_type)


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
