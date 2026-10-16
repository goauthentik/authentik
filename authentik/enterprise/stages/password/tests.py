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
                    action__in=[
                        EventAction.AUTHENTICATOR_LOCKED,
                        EventAction.AUTHENTICATOR_UNLOCKED,
                    ]
                )
                count = events.count()
                response = self.client.post(
                    reverse(
                        f"authentik_api:passworddevice-{action}",
                        kwargs={"pk": target.password_device.pk},
                    )
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
            url = reverse(
                f"authentik_api:passworddevice-{action}",
                kwargs={"pk": self.target.password_device.pk},
            )
            for _ in range(2):
                self.assertEqual(self.client.post(url).status_code, 204)
            device.refresh_from_db()
            self.assertEqual(device.locked, action == "lock")
            self.assertEqual(device.failed_attempts, 0)
            self.assertEqual(device.password, password)
            self.assertEqual(device.password_change_date, changed_at)
            self.assertEqual(
                Event.objects.filter(
                    action=f"authenticator_{action}ed",
                    context__affected_user__pk=self.target.pk,
                    context__authenticator__pk=device.pk,
                    context__authenticator__model_name="passworddevice",
                ).count(),
                1,
            )

    def test_unlock_without_license(self):
        PasswordDevice.objects.filter(user=self.target).update(locked_at=now())
        with patch("authentik.enterprise.license.LicenseKey.cached_summary") as summary:
            summary.return_value.status.is_valid = False
            url = reverse(
                "authentik_api:passworddevice-unlock", kwargs={"pk": self.target.password_device.pk}
            )
            self.assertEqual(self.client.post(url).status_code, 204)
        self.assertFalse(PasswordDevice.objects.get(user=self.target).locked)

    def test_audit_failure_rolls_back_lock_transition(self):
        for action, locked_at in (("lock", None), ("unlock", now())):
            with self.subTest(action=action):
                device = self.target.password_device
                PasswordDevice.objects.filter(pk=device.pk).update(locked_at=locked_at)
                url = reverse(f"authentik_api:passworddevice-{action}", kwargs={"pk": device.pk})
                with (
                    patch.object(Event, "from_http", side_effect=RuntimeError("audit failed")),
                    self.assertRaisesMessage(RuntimeError, "audit failed"),
                ):
                    self.client.post(url)
                device.refresh_from_db()
                self.assertEqual(device.locked_at, locked_at)

    def test_deleted_device(self):
        device = self.target.password_device
        pk = device.pk
        device.delete()
        for action in ("lock", "unlock"):
            url = reverse(f"authentik_api:passworddevice-{action}", kwargs={"pk": pk})
            self.assertEqual(self.client.post(url).status_code, 404)
        self.assertFalse(PasswordDevice.objects.filter(user=self.target).exists())
        response = self.client.get(
            reverse("authentik_api:user-detail", kwargs={"pk": self.target.pk})
        )
        self.assertIsNone(response.json()["password_device"])
        self.assertFalse(response.json()["password_locked"])

    def test_lock_requires_license_and_reports_status(self):
        self.target.is_active = False
        self.target.save(update_fields=["is_active"])
        device = self.target.password_device
        url = reverse("authentik_api:passworddevice-lock", kwargs={"pk": device.pk})
        with patch("authentik.enterprise.license.LicenseKey.cached_summary") as summary:
            summary.return_value.status.is_valid = False
            self.assertEqual(self.client.post(url).status_code, 400)
        device.refresh_from_db()
        self.assertFalse(device.locked)
        self.assertEqual(self.client.post(url).status_code, 204)
        response = self.client.get(
            reverse("authentik_api:user-detail", kwargs={"pk": self.target.pk})
        )
        self.assertTrue(response.json()["password_locked"])
        self.assertEqual(response.json()["password_device"], device.pk)

    def test_self_lock_with_reset_permission(self):
        url = reverse(
            "authentik_api:passworddevice-lock", kwargs={"pk": self.actor.password_device.pk}
        )
        self.assertEqual(self.client.post(url).status_code, 204)
        self.assertTrue(PasswordDevice.objects.get(user=self.actor).locked)
