"""Schema generation tests"""

from hashlib import sha512

from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import safe_load

from authentik.lib.config import CONFIG


def file_hash(path: str) -> str:
    with open(path) as _f:
        return sha512(_f.read().encode()).hexdigest()


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

    def test_build_schema(self):
        """Test schema build command"""
        blueprint_file = "blueprints/schema.json"
        api_file = "schema.yml"
        before_blueprint = file_hash(blueprint_file)
        before_api = file_hash(api_file)
        with (
            CONFIG.patch("debug", True),
            CONFIG.patch("tenants.enabled", True),
            CONFIG.patch("outposts.disable_embedded_outpost", True),
        ):
            call_command("build_schema")
        after_blueprint = file_hash(blueprint_file)
        after_api = file_hash(api_file)

        self.assertEqual(before_blueprint, after_blueprint, "Blueprint schema changed")
        self.assertEqual(before_api, after_api, "API schema changed")
