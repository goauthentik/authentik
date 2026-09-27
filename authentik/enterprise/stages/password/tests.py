"""Password lock API permissions."""

from unittest.mock import patch

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.stages.password.models import PasswordDevice


class TestPasswordLockPermissions(APITestCase):
    """Lock and unlock require permission to reset the target's password."""

    def setUp(self):
        self.actor = create_test_user()
        self.target = create_test_user()
        license_summary = self.enterContext(
            patch("authentik.enterprise.license.LicenseKey.cached_summary")
        )
        license_summary.return_value.status.is_valid = True

    def assert_actions(self, target, status):
        for action, locked_at in (("lock", None), ("unlock", now())):
            with self.subTest(action=action, target=target.pk):
                PasswordDevice.objects.filter(user=target).update(locked_at=locked_at)
                events = Event.objects.filter(
                    action__in=[EventAction.PASSWORD_LOCKED, EventAction.PASSWORD_UNLOCKED]
                )
                count = events.count()
                response = self.client.post(
                    reverse(f"authentik_api:user-{action}-password", kwargs={"pk": target.pk})
                )
                self.assertEqual(response.status_code, status, response.content)
                device = PasswordDevice.objects.get(user=target)
                if status == 204:
                    self.assertEqual(device.locked, action == "lock")
                    self.assertEqual(events.count(), count + 1)
                else:
                    self.assertEqual(device.locked_at, locked_at)
                    self.assertEqual(events.count(), count)

    def test_anonymous_denied(self):
        self.assert_actions(self.target, 403)

    def test_view_only_denied(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        self.assert_actions(self.target, 403)

    def test_change_user_denied(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.change_user")
        self.client.force_login(self.actor)
        self.assert_actions(self.target, 403)

    def test_self_requires_reset_permission(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        self.assert_actions(self.actor, 403)

    def test_global_reset_permission(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.reset_user_password")
        self.client.force_login(self.actor)
        self.assert_actions(self.target, 204)

    def test_object_reset_permission(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.reset_user_password", self.target)
        self.client.force_login(self.actor)
        self.assert_actions(self.target, 204)
        self.assert_actions(create_test_user(), 403)

    def test_object_visibility(self):
        self.actor.assign_perms_to_managed_role("authentik_core.view_user", self.target)
        self.actor.assign_perms_to_managed_role("authentik_core.reset_user_password", self.target)
        self.client.force_login(self.actor)
        self.assert_actions(self.target, 204)
        self.assert_actions(create_test_user(), 404)
