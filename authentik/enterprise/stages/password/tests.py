"""Password lock API permissions."""

from unittest.mock import patch

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_204_NO_CONTENT
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
                if status == HTTP_204_NO_CONTENT:
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


class TestPasswordLockActions(APITestCase):
    """Lock transitions preserve credentials and emit one event."""

    def setUp(self):
        self.actor = create_test_user()
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.reset_user_password")
        self.client.force_login(self.actor)
        self.target = create_test_user()
        license_summary = self.enterContext(
            patch("authentik.enterprise.license.LicenseKey.cached_summary")
        )
        license_summary.return_value.status.is_valid = True

    def test_repeated_transitions_preserve_credentials(self):
        device = PasswordDevice.objects.get(user=self.target)
        password, changed_at = device.password, device.password_change_date
        for action in ("lock", "unlock"):
            PasswordDevice.objects.filter(pk=device.pk).update(failed_attempts=3)
            url = reverse(f"authentik_api:user-{action}-password", kwargs={"pk": self.target.pk})
            for _ in range(2):
                self.assertEqual(self.client.post(url).status_code, 204)
            device.refresh_from_db()
            self.assertEqual(device.locked, action == "lock")
            self.assertEqual(device.failed_attempts, 0)
            self.assertEqual(device.password, password)
            self.assertEqual(device.password_change_date, changed_at)
            self.assertEqual(
                Event.objects.filter(
                    action=f"password_{action}ed", context__affected_user__pk=self.target.pk
                ).count(),
                1,
            )

    def test_lock_before_setting_first_password(self):
        """Locking a passwordless user also prevents a later password from logging in."""
        PasswordDevice.objects.filter(user=self.target).delete()
        url = reverse("authentik_api:user-lock-password", kwargs={"pk": self.target.pk})
        self.assertEqual(self.client.post(url).status_code, 204)
        self.target.refresh_from_db()
        self.assertFalse(self.target.has_usable_password())
        self.assertEqual(self.target.password_change_date, self.target.date_joined)
        self.target.set_password("new password")
        self.target.save()
        self.assertTrue(PasswordDevice.objects.get(user=self.target).locked)

    def test_unlock_missing_password_is_noop(self):
        PasswordDevice.objects.filter(user=self.target).delete()
        url = reverse("authentik_api:user-unlock-password", kwargs={"pk": self.target.pk})
        self.assertEqual(self.client.post(url).status_code, 204)
        self.assertFalse(PasswordDevice.objects.filter(user=self.target).exists())
        self.assertFalse(
            Event.objects.filter(
                action__in=[EventAction.PASSWORD_LOCKED, EventAction.PASSWORD_UNLOCKED],
                context__affected_user__pk=self.target.pk,
            ).exists()
        )

    def test_unlock_without_license(self):
        PasswordDevice.objects.filter(user=self.target).update(locked_at=now())
        with patch("authentik.enterprise.license.LicenseKey.cached_summary") as summary:
            summary.return_value.status.is_valid = False
            url = reverse("authentik_api:user-unlock-password", kwargs={"pk": self.target.pk})
            self.assertEqual(self.client.post(url).status_code, 204)
        self.assertFalse(PasswordDevice.objects.get(user=self.target).locked)
