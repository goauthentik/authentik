"""Test SCIM Group"""

from json import dumps
from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.schema import Group as SCIMGroupSchema
from authentik.sources.scim.models import (
    SCIMSource,
    SCIMSourceGroup,
)
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE


class TestSCIMGroups(APITestCase):
    """Test SCIM Group view"""

    def setUp(self) -> None:
        self.source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())

    def test_group_list(self):
        """Test full group list"""
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_group_list_single(self):
        """Test full group list (single group)"""
        group = Group.objects.create(name=generate_id())
        user = create_test_user()
        group.users.add(user)
        SCIMSourceGroup.objects.create(
            source=self.source,
            group=group,
            id=str(uuid4()),
        )
        response = self.client.get(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                    "group_id": str(group.pk),
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, second=200)
        SCIMGroupSchema.model_validate_json(response.content, strict=True)

    def test_group_create(self):
        """Test group create"""
        ext_id = generate_id()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps({"displayName": generate_id(), "externalId": ext_id}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SCIMSourceGroup.objects.filter(source=self.source, external_id=ext_id).exists()
        )
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED, user__username=self.source.token.user.username
            ).exists()
        )

    def test_group_create_members(self):
        """Test group create"""
        user = create_test_user()
        ext_id = generate_id()
        name = generate_id()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps(
                {
                    "displayName": name,
                    "externalId": ext_id,
                    "members": [{"value": str(user.uuid)}],
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        connection = SCIMSourceGroup.objects.filter(source=self.source, external_id=ext_id).first()
        self.assertIsNotNone(connection)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED, user__username=self.source.token.user.username
            ).exists()
        )
        connection.refresh_from_db()
        self.assertEqual(
            connection.attributes,
            {
                "displayName": name,
                "externalId": ext_id,
                "members": [{"value": str(user.uuid)}],
            },
        )

    def test_group_create_members_empty(self):
        """Test group create"""
        ext_id = generate_id()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps({"displayName": generate_id(), "externalId": ext_id, "members": []}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SCIMSourceGroup.objects.filter(source=self.source, external_id=ext_id).exists()
        )
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED, user__username=self.source.token.user.username
            ).exists()
        )

    def test_group_create_duplicate(self):
        """Test group create (duplicate)"""
        group = Group.objects.create(name=generate_id())
        existing = SCIMSourceGroup.objects.create(
            source=self.source, group=group, external_id=uuid4()
        )
        ext_id = generate_id()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data=dumps(
                {"displayName": generate_id(), "externalId": ext_id, "id": str(existing.group.pk)}
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 409)
        self.assertJSONEqual(
            response.content,
            {
                "detail": "Group with ID exists already.",
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "scimType": "uniqueness",
                "status": 409,
            },
        )

    def test_group_update(self):
        """Test group update"""
        group = Group.objects.create(name=generate_id())
        existing = SCIMSourceGroup.objects.create(
            source=self.source, group=group, external_id=uuid4()
        )
        ext_id = generate_id()
        response = self.client.put(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group.pk},
            ),
            data=dumps(
                {"displayName": generate_id(), "externalId": ext_id, "id": str(existing.pk)}
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, second=200)

    def test_group_update_non_existent(self):
        """Test group update"""
        ext_id = generate_id()
        response = self.client.put(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={
                    "source_slug": self.source.slug,
                    "group_id": str(uuid4()),
                },
            ),
            data=dumps({"displayName": generate_id(), "externalId": ext_id, "id": ""}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, second=404)
        self.assertJSONEqual(
            response.content,
            {
                "detail": "Group not found.",
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "status": 404,
            },
        )

    def test_group_patch_modify(self):
        """Test group patch"""
        group = Group.objects.create(name=generate_id())
        connection = SCIMSourceGroup.objects.create(
            source=self.source,
            group=group,
            external_id=uuid4(),
            attributes={"displayName": group.name, "members": []},
        )
        response = self.client.patch(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group.pk},
            ),
            data=dumps(
                {
                    "Operations": [
                        {
                            "op": "Add",
                            "value": {"externalId": "d85051cb-0557-4aa1-98ca-51eabcee4d40"},
                        }
                    ]
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200, response.content)
        connection = SCIMSourceGroup.objects.filter(id="d85051cb-0557-4aa1-98ca-51eabcee4d40")
        self.assertIsNotNone(connection)

    def test_group_patch_member_add(self):
        """Test group patch"""
        user = create_test_user()
        other_user = create_test_user()
        group = Group.objects.create(name=generate_id())
        group.users.add(other_user)
        connection = SCIMSourceGroup.objects.create(
            source=self.source,
            group=group,
            external_id=uuid4(),
            attributes={"displayName": group.name, "members": [{"value": str(other_user.uuid)}]},
        )
        response = self.client.patch(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group.pk},
            ),
            data=dumps(
                {
                    "Operations": [
                        {
                            "op": "Add",
                            "path": "members",
                            "value": [{"value": str(user.uuid)}],
                        }
                    ]
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(group.users.filter(pk=user.pk).exists())
        self.assertTrue(group.users.filter(pk=other_user.pk).exists())
        connection.refresh_from_db()
        self.assertEqual(
            connection.attributes,
            {
                "displayName": group.name,
                "members": sorted(
                    [{"value": str(other_user.uuid)}, {"value": str(user.uuid)}],
                    key=lambda u: u["value"],
                ),
            },
        )

    def test_group_patch_member_remove(self):
        """Test group patch"""
        user = create_test_user()

        group = Group.objects.create(name=generate_id())
        group.users.add(user)
        connection = SCIMSourceGroup.objects.create(
            source=self.source,
            group=group,
            external_id=uuid4(),
            attributes={"displayName": group.name, "members": []},
        )
        response = self.client.patch(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group.pk},
            ),
            data=dumps(
                {
                    "Operations": [
                        {
                            "op": "remove",
                            "path": "members",
                            "value": [{"value": str(user.uuid)}],
                        }
                    ]
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(group.users.filter(pk=user.pk).exists())
        connection.refresh_from_db()
        self.assertEqual(
            connection.attributes,
            {
                "displayName": group.name,
                "members": [],
            },
        )

    def test_group_delete(self):
        """Test group delete"""
        group = Group.objects.create(name=generate_id())
        SCIMSourceGroup.objects.create(source=self.source, group=group, external_id=uuid4())
        response = self.client.delete(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group.pk},
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, second=204)
