"""Google Workspace Group tests"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils.text import slugify

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.providers.google_workspace.clients.test_http import MockHTTP
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderGroup,
    GoogleWorkspaceProviderMapping,
)
from authentik.enterprise.providers.google_workspace.tasks import google_workspace_sync
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction
from authentik.lib.tests.utils import load_fixture
from authentik.tasks.models import Task, TaskStatus

domains_list_v1_mock = load_fixture("fixtures/domains_list_v1.json")


class GoogleWorkspaceGroupTests(TestCase):
    """Google workspace Group tests"""

    @apply_blueprint("system/providers-google-workspace.yaml")
    def setUp(self) -> None:
        # Delete all groups and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple groups
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

    def test_group_create(self):
        """Test group creation"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": generate_id()},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 2)

    def _create_conflicting_group(
        self, uid: str, lookup_body: dict, lookup_meta: dict | None = None
    ) -> Group:
        """Create a group whose email address is already in use in Google Workspace"""
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"error": {"code": 409, "message": "Entity already exists."}},
            meta={"status": "409"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{slugify(uid)}%40goauthentik.io?key={self.api_key}&alt=json",
            body=lookup_body,
            meta=lookup_meta,
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            return Group.objects.create(name=uid)

    def _assert_group_conflict(self, group: Group):
        self.assertFalse(
            GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).exists()
        )
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        log = Task.objects.get(
            _uid=f"{self.provider.name}:group:{group.pk}:direct",
        ).tasklogs.get(log_level=TaskStatus.WARNING)
        self.assertIn(f"Failed to sync {group}", log.event)
        self.assertIn("Entity already exists.", log.event)
        self.assertIn("Delete or rename the conflicting object", log.event)

    def test_group_create_conflict(self):
        """A group that already exists in Google Workspace is linked"""
        uid = generate_id()
        remote_group = {"id": generate_id(), "email": f"{slugify(uid)}@goauthentik.io"}
        group = self._create_conflicting_group(uid, remote_group)
        google_group = GoogleWorkspaceProviderGroup.objects.get(provider=self.provider, group=group)
        self.assertEqual(google_group.google_id, remote_group["id"])
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())

    def test_group_create_conflict_user(self):
        """A group whose email address a user already has is reported"""
        group = self._create_conflicting_group(
            generate_id(),
            {"error": {"code": 404, "message": "Resource Not Found: groupKey"}},
            {"status": "404"},
        )
        self._assert_group_conflict(group)

    def test_group_create_conflict_alias(self):
        """A group whose email address is another group's alias is reported"""
        group = self._create_conflicting_group(
            generate_id(), {"id": generate_id(), "email": f"{generate_id()}@goauthentik.io"}
        )
        self._assert_group_conflict(group)

    def test_group_not_created(self):
        """Test without group property mappings, no group is created"""
        self.provider.property_mappings_group.clear()
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
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNone(google_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 1)

    def test_group_create_update(self):
        """Test group updating"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}?key={self.api_key}&alt=json",
            method="PUT",
            body={"id": ext_id},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)

            group.name = "new name"
            group.save()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 4)

    def test_group_create_delete(self):
        """Test group deletion"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}?key={self.api_key}",
            method="DELETE",
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)

            group.delete()
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 4)

    def test_group_create_member_add(self):
        """Test group creation"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
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
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members?key={self.api_key}&alt=json",
            method="POST",
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            self.assertEqual(len(http.requests()), 8)

    def test_group_member_add_bad_request(self):
        """A membership change that Google Workspace rejects is reported with the group"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
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
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members?key={self.api_key}&alt=json",
            method="POST",
            body={"error": {"code": 400, "message": "Invalid Input: memberKey"}},
            meta={"status": "400"},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
        self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_TASK_EXCEPTION).exists())
        log = Task.objects.get(
            _uid=f"{self.provider.name}:group:{group.pk}:m2m",
        ).tasklogs.get(log_level=TaskStatus.WARNING)
        self.assertIn(f"Failed to sync {group}", log.event)
        self.assertIn("Invalid Input: memberKey", log.event)

    def test_group_create_member_remove(self):
        """Test group creation"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
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
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members/{uid}%40goauthentik.io?key={self.api_key}",
            method="DELETE",
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members?key={self.api_key}&alt=json",
            method="POST",
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
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
            self.assertEqual(len(http.requests()), 10)

    def test_group_member_remove_not_member(self):
        """Removing a user who isn't a member in Google Workspace anymore succeeds"""
        uid = generate_id()
        ext_id = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": ext_id},
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
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members/{uid}%40goauthentik.io?key={self.api_key}",
            method="DELETE",
            body={"error": {"code": 404, "message": "Resource Not Found: memberKey"}},
            meta={"status": "404"},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{ext_id}/members?key={self.api_key}&alt=json",
            method="POST",
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            user = create_test_user(uid)
            group = Group.objects.create(name=uid)
            group.users.add(user)
            group.users.remove(user)
        self.assertEqual(http.requests()[-1][1], "DELETE")
        self.assertFalse(
            Task.objects.filter(
                _uid=f"{self.provider.name}:group:{group.pk}:m2m",
                tasklogs__log_level__in=[TaskStatus.WARNING, TaskStatus.ERROR],
            ).exists()
        )

    def test_group_create_delete_do_nothing(self):
        """Test group deletion (delete action = do nothing)"""
        self.provider.group_delete_action = OutgoingSyncDeleteAction.DO_NOTHING
        self.provider.save()
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?key={self.api_key}&alt=json",
            method="POST",
            body={"id": uid},
        )
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            group = Group.objects.create(name=uid)
            google_group = GoogleWorkspaceProviderGroup.objects.filter(
                provider=self.provider, group=group
            ).first()
            self.assertIsNotNone(google_group)

            group.delete()
            self.assertEqual(len(http.requests()), 3)
            self.assertFalse(
                GoogleWorkspaceProviderGroup.objects.filter(
                    provider=self.provider, group__name=uid
                ).exists()
            )

    def test_sync_discover(self):
        """Test group discovery"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"users": []},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"groups": [{"id": uid, "name": uid}]},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{uid}?key={self.api_key}&alt=json",
            method="PUT",
            body={"id": uid},
        )
        self.app.backchannel_providers.remove(self.provider)
        different_group = Group.objects.create(
            name=uid,
        )
        self.app.backchannel_providers.add(self.provider)
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderGroup.objects.filter(
                    group=different_group, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            # Full sync creates separate clients for user and group discovery.
            self.assertEqual(len(http.requests()), 9)

    def test_sync_discover_multiple(self):
        """Test group discovery"""
        uid = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains?key={self.api_key}&alt=json",
            domains_list_v1_mock,
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"users": []},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
            method="GET",
            body={"groups": [{"id": uid, "name": uid}]},
        )
        http.add_response(
            f"https://admin.googleapis.com/admin/directory/v1/groups/{uid}?key={self.api_key}&alt=json",
            method="PUT",
            body={"id": uid},
        )
        self.app.backchannel_providers.remove(self.provider)
        different_group = Group.objects.create(
            name=uid,
        )
        self.app.backchannel_providers.add(self.provider)
        with patch(
            "authentik.enterprise.providers.google_workspace.models.GoogleWorkspaceProvider.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderGroup.objects.filter(
                    group=different_group, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
            # Full sync creates separate clients for user and group discovery.
            self.assertEqual(len(http.requests()), 9)
            # Change response to trigger update
            http.add_response(
                f"https://admin.googleapis.com/admin/directory/v1/groups?customer=my_customer&maxResults=500&orderBy=email&key={self.api_key}&alt=json",
                method="GET",
                body={"groups": [{"id": uid, "name": uid, "bar": "baz"}]},
            )
            google_workspace_sync.send(self.provider.pk).get_result()
            self.assertTrue(
                GoogleWorkspaceProviderGroup.objects.filter(
                    group=different_group, provider=self.provider
                ).exists()
            )
            self.assertFalse(Event.objects.filter(action=EventAction.SYSTEM_EXCEPTION).exists())
