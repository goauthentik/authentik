"""Google Workspace User tests"""

from json import dumps
from unittest.mock import MagicMock, patch

from django.test import TestCase
from googleapiclient.http import HttpMockSequence

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderMapping,
    GoogleWorkspaceProviderUser,
)
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.tenants.models import Tenant

domains_list_v1_mock = load_fixture("fixtures/domains_list_v1.json")


class GoogleWorkspaceUserTests(TestCase):
    """Google workspace User tests"""

    @apply_blueprint("system/providers-google-workspace.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
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

    def test_user_create(self):
        """Test user creation"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            google_user = GoogleWorkspaceProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(google_user)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_user_create_update(self):
        """Test user updating"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            google_user = GoogleWorkspaceProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(google_user)

            user.name = "new name"
            user.save()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())

    def test_user_create_delete(self):
        """Test user deletion"""
        uid = generate_id()
        http = HttpMockSequence(
            [
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
                ({"status": "200"}, domains_list_v1_mock),
                ({"status": "200"}, dumps({"primaryEmail": f"{uid}@goauthentik.io"})),
            ]
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": generate_id(), "http": http}),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            google_user = GoogleWorkspaceProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNotNone(google_user)

            user.delete()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
