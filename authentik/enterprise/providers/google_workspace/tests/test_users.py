"""Google Workspace User tests"""

from json import loads
from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.enterprise.providers.google_workspace.clients.test_http import MockHTTP
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderMapping,
    GoogleWorkspaceProviderUser,
)
from authentik.enterprise.providers.google_workspace.tasks import google_workspace_sync
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.lib.tests.utils import load_fixture
from authentik.tasks.models import Task, TaskStatus

domains_list_v1_mock = load_fixture("fixtures/domains_list_v1.json")


class GoogleWorkspaceUserTests(TestCase):
    """Google workspace User tests"""

    @apply_blueprint("system/providers-google-workspace.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        SystemSettings.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider: GoogleWorkspaceProvider = GoogleWorkspaceProvider.objects.create(
            name=generate_id(),
            credentials={},
            delegated_subject="",
            exclude_users_service_account=True,
            default_group_email_domain="goauthentik.io",
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
        self.api_key = generate_id()

    def test_user_create(self):
        """Test user creation"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 2)

    def _test_user_create_conflict(self, uid: str, remote_user: dict) -> User:
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"error": {"code": 409, "message": "Entity already exists."}},
            meta={"status": "409"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}&alt=json",
            body=remote_user,
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            return User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )

    def test_user_create_conflict(self):
        """A user that already exists in Google Workspace is linked"""
        uid = generate_id()
        remote_user = {"id": generate_id(), "primaryEmail": f"{uid}@goauthentik.io"}
        user = self._test_user_create_conflict(uid, remote_user)
        google_user = GoogleWorkspaceProviderUser.objects.get(provider=self.provider, user=user)
        self.assertEqual(google_user.google_id, f"{uid}@goauthentik.io")
        self.assertEqual(google_user.attributes, remote_user)
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())

    def test_user_create_conflict_alias(self):
        """A user whose email address is another user's alias is reported"""
        uid = generate_id()
        remote_user = {"id": generate_id(), "primaryEmail": f"{generate_id()}@goauthentik.io"}
        user = self._test_user_create_conflict(uid, remote_user)
        self.assertFalse(
            GoogleWorkspaceProviderUser.objects.filter(provider=self.provider, user=user).exists()
        )
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        log = Task.objects.get(
            _uid=f"{self.provider.name}:user:{user.pk}:direct",
        ).tasklogs.get(log_level=TaskStatus.WARNING)
        self.assertIn(f"Failed to sync {user}", log.event)
        self.assertIn("Entity already exists.", log.event)

    def test_user_create_bad_request(self):
        """A user that Google Workspace rejects is reported with Google's error"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"error": {"code": 400, "message": "Invalid Input: primary_user_email"}},
            meta={"status": "400"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
        self.assertFalse(
            GoogleWorkspaceProviderUser.objects.filter(provider=self.provider, user=user).exists()
        )
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        log = Task.objects.get(
            _uid=f"{self.provider.name}:user:{user.pk}:direct",
        ).tasklogs.get(log_level=TaskStatus.WARNING)
        self.assertIn(f"Failed to sync {user}", log.event)
        self.assertIn("Invalid Input: primary_user_email", log.event)

    def test_user_not_created(self):
        """Test without property mappings, no group is created"""
        self.provider.property_mappings.clear()
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            user = User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            google_user = GoogleWorkspaceProviderUser.objects.filter(
                provider=self.provider, user=user
            ).first()
            self.assertIsNone(google_user)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 1)

    def test_user_create_update(self):
        """Test user updating"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}&alt=json",
            method="PUT",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 4)

    def test_user_create_delete(self):
        """Test user deletion"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}",
            method="DELETE",
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 4)

    def test_user_create_delete_suspend(self):
        """Test user deletion (delete action = Suspend)"""
        self.provider.user_delete_action = OutgoingSyncDeleteAction.SUSPEND
        self.provider.save()
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}&alt=json",
            method="PUT",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 4)
            _, _, body, _ = http.requests()[3]
            self.assertEqual(
                loads(body),
                {
                    "suspended": True,
                },
            )
            self.assertFalse(
                GoogleWorkspaceProviderUser.objects.filter(
                    provider=self.provider, user__username=uid
                ).exists()
            )

    def test_user_create_delete_do_nothing(self):
        """Test user deletion (delete action = do nothing)"""
        self.provider.user_delete_action = OutgoingSyncDeleteAction.DO_NOTHING
        self.provider.save()
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?key={self.api_key}&alt=json",
            method="POST",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 3)
            self.assertFalse(
                GoogleWorkspaceProviderUser.objects.filter(
                    provider=self.provider, user__username=uid
                ).exists()
            )

    def test_sync_discover(self):
        """Test user discovery"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"users": [{"primaryEmail": f"{uid}@goauthentik.io"}]},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"groups": []},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}&alt=json",
            method="PUT",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        self.app.backchannel_providers.remove(self.provider)
        different_user = User.objects.create(
            username=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.app.backchannel_providers.add(self.provider)
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderUser.objects.filter(
                    user=different_user, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            # Full sync creates separate clients for user and group discovery.
            self.assertEqual(len(http.requests()), 9)

    def test_sync_discover_multiple(self):
        """Test user discovery, running multiple times"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"users": [{"primaryEmail": f"{uid}@goauthentik.io"}]},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"groups": []},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users/{uid}%40goauthentik.io?key={self.api_key}&alt=json",
            method="PUT",
            body={"primaryEmail": f"{uid}@goauthentik.io"},
        )
        self.app.backchannel_providers.remove(self.provider)
        different_user = User.objects.create(
            username=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.app.backchannel_providers.add(self.provider)
        # Sync once
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderUser.objects.filter(
                    user=different_user, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            # Full sync creates separate clients for user and group discovery.
            self.assertEqual(len(http.requests()), 9)
            # Change response, which will trigger a discovery update
            http.add_response(
                f"https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
                method="GET",
                body={
                    "users": [
                        {"primaryEmail": f"{uid}@goauthentik.io", "foo": "bar"},
                    ]
                },
            )
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderUser.objects.filter(
                    user=different_user, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
