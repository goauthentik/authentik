"""Test blueprints v1 api"""

from json import dumps, loads
from tempfile import NamedTemporaryFile, mkdtemp

from django.urls import reverse
from rest_framework.test import APITestCase
from yaml import dump

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.stages.invitation.models import InvitationStage
from authentik.stages.user_write.models import UserWriteStage

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
            {"content": ["Failed to validate blueprint", "- Invalid blueprint version"]},
        )

    def test_api_import_with_context(self):
        """Test that the import endpoint applies the supplied context to the real blueprint"""
        slug = f"invitation-enrollment-{generate_id()}"
        flow_name = f"Invitation Enrollment {generate_id()}"
        stage_name = f"invitation-stage-{generate_id()}"
        user_type = "internal"
        continue_without_invitation = True

        res = self.client.post(
            reverse("authentik_api:blueprintinstance-import-"),
            data={
                "path": "example/flows-invitation-enrollment-minimal.yaml",
                "context": dumps(
                    {
                        "flow_slug": slug,
                        "flow_name": flow_name,
                        "stage_name": stage_name,
                        "continue_flow_without_invitation": continue_without_invitation,
                        "user_type": user_type,
                    }
                ),
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        flow = Flow.objects.get(slug=slug)
        self.assertEqual(flow.name, flow_name)
        self.assertEqual(flow.title, flow_name)

        invitation_stage = InvitationStage.objects.get(name=stage_name)
        self.assertEqual(
            invitation_stage.continue_flow_without_invitation,
            continue_without_invitation,
        )

        user_write_stage = UserWriteStage.objects.get(
            name=f"invitation-enrollment-user-write-{slug}"
        )
        self.assertEqual(user_write_stage.user_type, user_type)
        self.assertEqual(user_write_stage.user_path_template, f"users/{user_type}")

    def test_api_import_blank_path(self):
        """Validator returns empty path unchanged (covers api.py:53)."""
        with NamedTemporaryFile(mode="w+", suffix=".yaml") as file:
            file.write(dump({"version": 1, "entries": []}))
            file.flush()
            file.seek(0)
            res = self.client.post(
                reverse("authentik_api:blueprintinstance-import-"),
                data={"path": "", "file": file},
                format="multipart",
            )
        self.assertEqual(res.status_code, 200)

    def test_api_import_unknown_path(self):
        """Path not in available blueprints is rejected (covers api.py:56)."""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-import-"),
            data={"path": "does/not/exist.yaml"},
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Blueprint file does not exist", res.content.decode())

    def test_api_import_blank_context(self):
        """Blank context is normalized to empty dict (covers api.py:62)."""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-import-"),
            data={
                "path": "example/flows-invitation-enrollment-minimal.yaml",
                "context": "",
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 200)

    def test_api_import_invalid_json_context(self):
        """Malformed JSON context raises ValidationError (covers api.py:65-66)."""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-import-"),
            data={
                "path": "example/flows-invitation-enrollment-minimal.yaml",
                "context": "{not json",
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Context must be valid JSON", res.content.decode())

    def test_api_import_non_object_context(self):
        """JSON context that isn't an object is rejected (covers api.py:68)."""
        res = self.client.post(
            reverse("authentik_api:blueprintinstance-import-"),
            data={
                "path": "example/flows-invitation-enrollment-minimal.yaml",
                "context": "[1, 2, 3]",
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Context must be a JSON object", res.content.decode())
