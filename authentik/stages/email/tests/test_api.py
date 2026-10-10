"""email stage api tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.email.api import EmailStageSerializer
from authentik.stages.email.models import EmailTemplate


class TestEmailStageAPI(APITestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_validate(self):
        """Test EmailStage's validation"""

        template = EmailTemplate.objects.get(managed="goauthentik.io/email/account-confirmation")
        serializer = EmailStageSerializer(
            data={
                "name": generate_id(),
                "template": template.pk,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["template"], template)

        serializer = EmailStageSerializer(
            data={
                "name": generate_id(),
                "template": None,
            },
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("template", serializer.errors)


class TestEmailTemplateAPI(APITestCase):
    """Email template API tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_invalid_path(self):
        """Test paths outside the template tree are rejected"""
        response = self.client.post(
            reverse("authentik_api:emailtemplate-list"),
            data={"path": "../template.html", "body": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("path", response.json())

    def test_invalid_syntax(self):
        """Test bodies with invalid template syntax are rejected"""
        for field in ("body", "body_plaintext"):
            with self.subTest(field=field):
                response = self.client.post(
                    reverse("authentik_api:emailtemplate-list"),
                    data={"path": f"{generate_id()}.html", field: "{% if %}"},
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

    def test_path_unique_per_scope(self):
        """Test a custom template can share a built-in's path, but not another custom's"""
        builtin = EmailTemplate.objects.get(managed="goauthentik.io/email/password-reset")
        url = reverse("authentik_api:emailtemplate-list")

        response = self.client.post(url, data={"path": builtin.path, "body": "custom"})
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, data={"path": builtin.path, "body": "custom"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("path", response.json())

        response = self.client.patch(
            reverse("authentik_api:emailtemplate-detail", kwargs={"pk": builtin.pk}),
            data={"body": "updated"},
        )
        self.assertEqual(response.status_code, 200)
