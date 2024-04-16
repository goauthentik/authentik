"""Test SCIM Schema"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMSchemas(APITestCase):
    """Test SCIM Schema view"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.token = Token.objects.create(
            user=self.user,
            identifier=generate_id(),
            intent=TokenIntents.INTENT_API,
        )
        self.source = SCIMSource.objects.create(
            name=generate_id(), slug=generate_id(), token=self.token
        )

    def test_schema(self):
        """Test full schema view"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_schema_single(self):
        """Test single schema"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                    "schema_uri": "urn:ietf:params:scim:schemas:core:2.0:Meta",
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_schema_single_404(self):
        """Test single schema (404"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                    "schema_uri": "foo",
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 404)
