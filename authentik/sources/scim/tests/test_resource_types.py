"""Test SCIM ResourceTypes"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMResourceTypes(APITestCase):
    """Test SCIM ResourceTypes view"""

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

    def test_resource_type(self):
        """Test full resource type view"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-resource-types",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_resource_type_single(self):
        """Test single resource type"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-resource-types",
                kwargs={
                    "source_slug": self.source.slug,
                    "resource_type": "ServiceProviderConfig",
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_resource_type_single_404(self):
        """Test single resource type (404"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-resource-types",
                kwargs={
                    "source_slug": self.source.slug,
                    "resource_type": "foo",
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 404)
