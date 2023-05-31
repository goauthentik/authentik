"""Test blueprints v1 api"""
from json import loads
from tempfile import NamedTemporaryFile, mkdtemp

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import dump

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.config import CONFIG

TMP = mkdtemp("authentik-blueprints")


class TestBlueprintsV1API(APITestCase):
    """Test Blueprints API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    @CONFIG.patch("blueprints_dir", TMP)
    def test_api_available(self):
        """Test valid file"""
        with NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP) as file:
            file.write(
                dump(
                    {
                        "version": 1,
                        "entries": [],
                    }
                )
            )
            file.flush()
            res = self.client.get(reverse("authentik_api:blueprintinstance-available"))
            self.assertEqual(res.status_code, 200)
            response = loads(res.content.decode())
            self.assertEqual(len(response), 1)
            self.assertEqual(
                response[0]["hash"],
                (
                    "e52bb445b03cd36057258dc9f0ce0fbed8278498ee1470e45315293e5f026d1bd1f9b352"
                    "6871c0003f5c07be5c3316d9d4a08444bd8fed1b3f03294e51e44522"
                ),
            )

    def test_api_oci(self):
        """Test validation with OCI path"""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-list"),
            data={"name": "foo", "path": "oci://foo/bar"},
        )
        self.assertEqual(res.status_code, 201)

    def test_api_blank(self):
        """Test blank"""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-list"),
            data={
                "name": "foo",
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content.decode(), {"non_field_errors": ["Either path or content must be set."]}
        )

    def test_api_content(self):
        """Test blank"""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-list"),
            data={
                "name": "foo",
                "content": '{"version": 3}',
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content.decode(),
            {"content": ["Failed to validate blueprint: Invalid blueprint version"]},
        )
