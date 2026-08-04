"""Schema generation tests"""

from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from django.core.management import call_command
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy, override
from drf_spectacular.openapi import AutoSchema
from rest_framework.fields import ChoiceField
from rest_framework.test import APITestCase
from yaml import safe_load

from authentik.api.fields import GeneratedEnumChoiceField
from authentik.api.v3.schema.enum import ChoiceFieldEnumExtension
from authentik.lib.config import CONFIG


class TestChoiceFieldEnumExtension(SimpleTestCase):
    """Choice field enum schema tests."""

    def test_generated_enum_choice_field_emits_labels(self):
        field = GeneratedEnumChoiceField(
            choices=[
                ("default", gettext_lazy("Default")),
                ("aws", "AWS"),
                ("sfdc", "Salesforce"),
            ],
            allow_blank=True,
            allow_null=True,
        )

        with override("de_DE"):
            schema = ChoiceFieldEnumExtension(field).map_serializer_field(
                AutoSchema(),
                "response",
            )

        self.assertEqual(schema["enum"], ["default", "aws", "sfdc", "", None])
        self.assertEqual(schema["x-enum-labels"], ["Default", "AWS", "Salesforce"])
        self.assertEqual(schema["x-enum-varnames"], ["Default", "AWS", "Salesforce"])

    def test_plain_choice_field_is_not_targeted(self):
        self.assertIs(ChoiceFieldEnumExtension.target_class, GeneratedEnumChoiceField)
        self.assertFalse(issubclass(ChoiceField, GeneratedEnumChoiceField))

    def test_redundant_choice_labels_do_not_become_enum_names(self):
        field = GeneratedEnumChoiceField(choices=[("foo", "Foo"), ("bar", "Bar")])

        schema = ChoiceFieldEnumExtension(field).map_serializer_field(
            AutoSchema(),
            "response",
        )

        self.assertEqual(schema["x-enum-labels"], ["Foo", "Bar"])
        self.assertNotIn("x-enum-varnames", schema)

    def test_identical_choice_labels_are_not_repeated(self):
        field = GeneratedEnumChoiceField(choices=[("foo", "foo"), ("bar", "bar")])

        schema = ChoiceFieldEnumExtension(field).map_serializer_field(
            AutoSchema(),
            "response",
        )

        self.assertNotIn("x-enum-labels", schema)
        self.assertNotIn("x-enum-varnames", schema)

    def test_prose_choice_labels_do_not_become_enum_names(self):
        field = GeneratedEnumChoiceField(
            choices=[
                ("command", "authentik.commands"),
                ("six", "6 digits, widely compatible"),
                ("oauth", "OAuth (Silent)"),
            ]
        )

        schema = ChoiceFieldEnumExtension(field).map_serializer_field(
            AutoSchema(),
            "response",
        )

        self.assertEqual(
            schema["x-enum-labels"],
            ["authentik.commands", "6 digits, widely compatible", "OAuth (Silent)"],
        )
        self.assertNotIn("x-enum-varnames", schema)


class TestSchemaGeneration(APITestCase):
    """Generic admin tests"""

    def test_schema(self):
        """Test generation"""
        response = self.client.get(
            reverse("authentik_api:schema"),
        )
        schema = safe_load(response.content.decode())
        self.assertTrue(schema)
        components = schema["components"]["schemas"]
        self.assertEqual(
            components["CompatibilityModeEnum"]["x-enum-varnames"],
            ["Default", "AWS", "Slack", "Salesforce", "GitLab", "Webex", "vCenter"],
        )
        self.assertEqual(
            components["CompatibilityModeEnum"]["x-enum-labels"],
            ["Default", "AWS", "Slack", "Salesforce", "GitLab", "Webex", "vCenter"],
        )
        self.assertEqual(
            components["DigestAlgorithmEnum"]["x-enum-labels"],
            ["SHA1", "SHA256", "SHA384", "SHA512"],
        )
        self.assertEqual(
            components["SignatureAlgorithmEnum"]["x-enum-labels"],
            [
                "RSA-SHA1",
                "RSA-SHA256",
                "RSA-SHA384",
                "RSA-SHA512",
                "ECDSA-SHA1",
                "ECDSA-SHA256",
                "ECDSA-SHA384",
                "ECDSA-SHA512",
                "DSA-SHA1",
            ],
        )
        self.assertNotIn("x-enum-labels", components["DeniedActionEnum"])
        self.assertNotIn("x-enum-labels", components["CountryCodeEnum"])

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
