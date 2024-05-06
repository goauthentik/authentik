"""Google Workspace Group tests"""

from json import dumps
from unittest.mock import MagicMock, patch

from django.test import TestCase
from googleapiclient.http import HttpMockSequence

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderGroup,
    GoogleWorkspaceProviderMapping,
)
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.tenants.models import Tenant

domains_list_v1_mock = load_fixture("fixtures/domains_list_v1.json")


class GoogleWorkspaceGroupTests(TestCase):
    """Google workspace Group tests"""

    @apply_blueprint("system/providers-google-workspace.yaml")
    def setUp(self) -> None:
        # Delete all groups and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple groups
        Tenant.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider: GoogleWorkspaceProvider = GoogleWorkspaceProvider.objects.create(
            name=generate_id(),
            credentials={},
            delegated_subject="",
            exclude_users_service_account=True,
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            GoogleWorkspaceProviderMapping.objects.get(
                managed="goauthentik.io/providers/google_workspace/user"
            )
        )
        self.provider.property_mappings_group.add(
            GoogleWorkspaceProviderMapping.objects.get(
                managed="goauthentik.io/providers/google_workspace/group"
            )
        )

    def test_group_create(self):
        """Test group creation"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": generate_id()})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_group_create_update(self):
        """Test group updating"""
        uid = generate_id()
        ext_id = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": ext_id})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": ext_id})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)

            group.name = "new name"
            group.save()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_group_create_delete(self):
        """Test group deletion"""
        uid = generate_id()
        ext_id = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": ext_id})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": ext_id})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)

            group.delete()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_group_create_member_add(self):
        """Test group creation"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": generate_id()})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_group_create_member_remove(self):
        """Test group creation"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"id": generate_id()})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)
            group.users.remove(user)

        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
