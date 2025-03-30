"""Test SCIM User"""

from json import dumps
from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.common.scim.schema import User as SCIMUserSchema
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.sources.scim.models import SCIMSource, SCIMSourcePropertyMapping, SCIMSourceUser
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE


class TestSCIMUsers(APITestCase):
    """Test SCIM User view"""

    def setUp(self) -> None:
        self.source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())

    def test_user_list(self):
        """Test full user list"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_user_list_single(self):
        """Test full user list (single user)"""
        user = create_test_user()
        SCIMSourceUser.objects.create(
            source=self.source,
            user=user,
            id=str(uuid4()),
        )
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                    "user_id": str(user.uuid),
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        SCIMUserSchema.model_validate_json(response.content, strict=True)

    def test_user_create(self):
        """Test user create"""
        user = create_test_user()
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
                            "value": user.email,
                        }
                    ],
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SCIMSourceUser.objects.filter(source=self.source, id=ext_id).exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED, user__username=self.source.token.user.username
            ).exists()
        )

    def test_user_create_duplicate_by_username(self):
        """Test user create"""
        user = create_test_user()
        username = generate_id()
        obj1 = {
            "userName": username,
            "externalId": generate_id(),
            "emails": [
                {
                    "primary": True,
                    "value": user.email,
                }
            ],
        }
        obj2 = obj1.copy()
        obj2.update({"externalId": generate_id()})
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps(obj1),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SCIMSourceUser.objects.filter(source=self.source, user__username=username).exists()
        )
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED, user__username=self.source.token.user.username
            ).exists()
        )
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps(obj2),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 409)

    def test_user_property_mappings(self):
        """Test user property_mappings"""
        self.source.user_property_mappings.set(
            [
                SCIMSourcePropertyMapping.objects.create(
                    name=generate_id(),
                    expression='return {"attributes": {"phone": data.get("phoneNumber")}}',
                )
            ]
        )
        user = create_test_user()
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
                            "value": user.email,
                        }
                    ],
                    "phoneNumber": "0123456789",
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            SCIMSourceUser.objects.get(source=self.source, id=ext_id).user.attributes["phone"],
            "0123456789",
        )
