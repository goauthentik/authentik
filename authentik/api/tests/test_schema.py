"""Schema generation tests"""

from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import safe_load

from authentik.lib.config import CONFIG


class TestSchemaGeneration(APITestCase):
    """Generic admin tests"""

    def test_schema(self):
        """Test generation"""
        response = self.client.get(
            reverse("authentik_api:schema"),
        )
        components = safe_load(response.content.decode())["components"]["schemas"]
        self.assertEqual(
            components["KeyTypeEnum"]["x-enum-varnames"],
            ["RSA", "EC", "DSA", "Ed25519", "Ed448"],
        )
        self.assertNotIn("CertificateKeyPairKeyTypeEnum", components)
        self.assertNotIn("x-enum-varnames", components["SignatureAlgorithmEnum"])

    def test_browser(self):
        """Test API Browser"""
        response = self.client.get(
            reverse("authentik_api:schema-browser"),
        )
        self.assertEqual(response.status_code, 200)

    def test_build_schema(self):
        """Test schema build command"""
        tmp = Path(gettempdir())
        blueprint_file = tmp / f"{str(uuid4())}.json"
        api_file = tmp / f"{str(uuid4())}.yml"
        with (
            CONFIG.patch("debug", True),
            CONFIG.patch("tenants.enabled", True),
            CONFIG.patch("outposts.disable_embedded_outpost", True),
        ):
            call_command("build_schema", blueprint_file=blueprint_file, api_file=api_file)
        self.assertTrue(blueprint_file.exists())
        self.assertTrue(api_file.exists())
