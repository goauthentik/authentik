"""Test SCIM User"""

from json import dumps
from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.schema import User as SCIMUserSchema
from authentik.sources.scim.models import SCIMSource, SCIMSourceUser
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE


class TestSCIMUsers(APITestCase):
    """Test SCIM User view"""

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

    def test_user_list(self):
        """Test full user list"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_user_list_single(self):
        """Test full user list (single user)"""
        SCIMSourceUser.objects.create(
            source=self.source,
            user=self.user,
            id=str(uuid4()),
        )
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                    "user_id": str(self.user.uuid),
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        SCIMUserSchema.model_validate_json(response.content, strict=True)

    def test_user_create(self):
        """Test user create"""
        ext_id = generate_id()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps(
                {
                    "userName": generate_id(),
                    "externalId": ext_id,
                    "emails": [
                        {
                            "primary": True,
                            "value": self.user.email,
                        }
                    ],
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SCIMSourceUser.objects.filter(source=self.source, id=ext_id).exists())
