"""Test SCIM Schema"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.crypto.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMSchemas(APITestCase):
    """Test SCIM Schema view"""

    def setUp(self) -> None:
        self.source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())

    def test_schema(self):
        """Test full schema view"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
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
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
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
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 404)
