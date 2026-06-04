"""Tests for SCIM source managed-objects-only mode."""

from json import dumps
from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.sources.scim.models import SCIMSource, SCIMSourceGroup, SCIMSourceUser
from authentik.sources.scim.views.v2.base import SCIM_CONTENT_TYPE


class TestSCIMManagedObjectsOnly(APITestCase):
    """Test SCIM source managed_objects_only behavior."""

    def setUp(self) -> None:
        self.source = SCIMSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            managed_objects_only=True,
        )

    def test_user_create_conflict_existing_username(self):
        """Cannot correlate to an existing user when managed_objects_only is enabled."""
        existing = create_test_user()
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps({"userName": existing.username, "name": {"formatted": "Test"}}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 409)

    def test_group_create_conflict_existing_name(self):
        """Cannot correlate to an existing group when managed_objects_only is enabled."""
        admin_group = Group.objects.create(name="authentik Admins", is_superuser=True)
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps({"displayName": admin_group.name, "externalId": generate_id()}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(SCIMSourceGroup.objects.filter(source=self.source, group=admin_group).exists())

    def test_group_members_require_managed_users(self):
        """Group membership is limited to users managed by this SCIM source."""
        unmanaged = create_test_user()
        scim_user = create_test_user()
        SCIMSourceUser.objects.create(
            source=self.source,
            user=scim_user,
            external_id=str(uuid4()),
        )
        response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps(
                {
                    "displayName": generate_id(),
                    "externalId": generate_id(),
                    "members": [{"value": str(unmanaged.uuid)}],
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(response.status_code, 400)

    def test_escalation_to_admin_group_blocked(self):
        """Full escalation path is blocked when managed_objects_only is enabled."""
        admin_group = Group.objects.create(name="authentik Admins", is_superuser=True)
        attacker_username = generate_id()
        create_response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps(
                {
                    "userName": attacker_username,
                    "name": {"formatted": "Attacker"},
                    "active": True,
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(create_response.status_code, 201)
        attacker_uuid = create_response.json()["id"]

        group_response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps(
                {
                    "displayName": admin_group.name,
                    "externalId": generate_id(),
                    "members": [{"value": attacker_uuid}],
                }
            ),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(group_response.status_code, 409)
        attacker = User.objects.get(uuid=attacker_uuid)
        self.assertFalse(attacker.is_superuser)
        self.assertEqual(admin_group.users.count(), 0)

    def test_delete_user_unlinks_only(self):
        """DELETE removes the SCIM link but keeps the user when managed_objects_only is enabled."""
        username = generate_id()
        create_response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps({"userName": username, "name": {"formatted": "Test"}}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(create_response.status_code, 201)
        user_id = create_response.json()["id"]
        delete_response = self.client.delete(
            reverse(
                "authentik_sources_scim:v2-users",
                kwargs={"source_slug": self.source.slug, "user_id": user_id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertFalse(SCIMSourceUser.objects.filter(source=self.source, user__uuid=user_id).exists())

    def test_delete_group_unlinks_only(self):
        """DELETE removes the SCIM link but keeps the group when managed_objects_only is enabled."""
        name = generate_id()
        create_response = self.client.post(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug},
            ),
            data=dumps({"displayName": name, "externalId": generate_id()}),
            content_type=SCIM_CONTENT_TYPE,
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(create_response.status_code, 201)
        group_id = create_response.json()["id"]
        delete_response = self.client.delete(
            reverse(
                "authentik_sources_scim:v2-groups",
                kwargs={"source_slug": self.source.slug, "group_id": group_id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.source.token.key}",
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(Group.objects.filter(name=name).exists())
        self.assertFalse(
            SCIMSourceGroup.objects.filter(source=self.source, group__group_uuid=group_id).exists()
        )
