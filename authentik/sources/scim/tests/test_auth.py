"""Test SCIM Auth"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMAuth(APITestCase):
    """Test SCIM Auth view"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.token3 = Token.objects.create(
            user=self.user,
            identifier=generate_id(),
            intent=TokenIntents.INTENT_API,
        )
        self.source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())
        self.source2 = SCIMSource.objects.create(name=generate_id(), slug=generate_id())

    def test_auth_ok(self):
        """Test successful auth"""
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

    def test_auth_missing(self):
        """Test without header"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_auth_wrong_token(self):
        """Test with wrong token"""
        # Token for wrong source
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source2.token.key}",
        )
        self.assertEqual(response.status_code, 403)
        # Token for no source
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-schema",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token3.key}",
        )
        self.assertEqual(response.status_code, 403)
