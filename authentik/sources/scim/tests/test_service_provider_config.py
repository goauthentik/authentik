"""Test SCIM ServiceProviderConfig"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.crypto.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMServiceProviderConfig(APITestCase):
    """Test SCIM ServiceProviderConfig view"""

    def setUp(self) -> None:
        self.source = SCIMSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )

    def test_config(self):
        """Test full config view"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-service-provider-config",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200)
