"""password tests"""

from io import StringIO
from unittest.mock import MagicMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth.hashers import PBKDF2PasswordHasher, make_password
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.auth import InbuiltBackend, TokenBackend
from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_brand,
    create_test_flow,
    create_test_user,
)
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.authenticator import device_classes, devices_for_user
from authentik.stages.authenticator.models import Device
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordDevice, PasswordStage

MOCK_BACKEND_AUTHENTICATE = MagicMock(side_effect=PermissionDenied("test"))


class TestPasswordStage(FlowTestCase):
    """Password tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = PasswordStage.objects.create(name=generate_id(), backends=[BACKEND_INBUILT])
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_user(self):
        """Test without user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Still have to send the password so the form is valid
            {"password": self.user.username},
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Unknown error",
        )

    def test_recovery_flow_link(self):
        """Test link to the default recovery flow"""
        flow = create_test_flow(designation=FlowDesignation.RECOVERY)
        brand = create_test_brand()
        brand.flow_recovery = flow
        brand.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.slug, response.content.decode())

    def test_valid_password(self):
        """Test with a valid pending user and valid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.user.username},
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_valid_password_inactive(self):
        """Test with a valid pending user and valid password"""
        self.user.is_active = False
        self.user.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.user.username},
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={"password": [{"string": "Invalid password", "code": "invalid"}]},
        )

    def test_invalid_password(self):
        """Test with a valid pending user and invalid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.user.username + "test"},
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_password_lockout(self):
        """Test with a valid pending user and invalid password (trigger logout counter)"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        res = self.client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.flow.slug},
            ),
        )
        self.assertEqual(res.status_code, 200)
        for _ in range(self.stage.failed_attempts_before_cancel - 1):
            response = self.client.post(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                ),
                # Form data
                {"password": self.user.username + "test"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertStageResponse(
                response,
                flow=self.flow,
                response_errors={"password": [{"string": "Invalid password", "code": "invalid"}]},
            )

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.user.username + "test"},
        )
        self.assertEqual(response.status_code, 200)
        # To ensure the plan has been cancelled, check SESSION_KEY_PLAN
        self.assertNotIn(SESSION_KEY_PLAN, self.client.session)
        self.assertStageResponse(response, flow=self.flow, error_message="Invalid password")

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "authentik.core.auth.InbuiltBackend.authenticate",
        MOCK_BACKEND_AUTHENTICATE,
    )
    def test_permission_denied(self):
        """Test with a valid pending user and valid password.
        Backend is patched to return PermissionError"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.user.username + "test"},
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Unknown error",
        )


class TestPasswordDevice(TestCase):
    """Password device tests"""

    def test_not_offered_as_mfa(self):
        """Test password devices are not usable as a second factor"""
        user = create_test_admin_user()
        device = PasswordDevice.objects.get(user=user)

        self.assertNotIn(PasswordDevice, list(device_classes()))
        self.assertEqual(list(devices_for_user(user)), [])
        self.assertIsNone(Device.from_persistent_id(device.persistent_id))

    def test_set_password(self):
        """Test changing a password replaces it on the user's only device"""
        user = create_test_user()
        PasswordDevice.set_password(user, "changed")

        device = PasswordDevice.objects.get(user=user)
        self.assertTrue(device.check_password("changed"))
        self.assertFalse(device.check_password(user.username))
        self.assertEqual(user.password, device.password)

    def test_one_device_per_user(self):
        """Test the database refuses a second password device"""
        user = create_test_user()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PasswordDevice.objects.create(user=user, name="Password", password="second")

    def test_password_write_saves_user(self):
        """Test password writes save the user, so sync and policy caches see the change"""
        user = create_test_user()
        for write in (
            lambda: PasswordDevice.set_password(user, generate_id()),
            lambda: PasswordDevice.set_password_from_hash(user, make_password(generate_id())),
            lambda: PasswordDevice.set_unusable_password(user),
        ):
            with self.subTest(write=write), patch.object(post_save, "send") as send:
                write()
                self.assertIn(User, [call.kwargs["sender"] for call in send.call_args_list])

    def test_password_change_keeps_lock(self):
        """Test a new password clears failed attempts without unlocking"""
        user = create_test_user()
        locked_at = now()
        PasswordDevice.objects.filter(user=user).update(failed_attempts=2, locked_at=locked_at)

        PasswordDevice.set_password(user, generate_id())

        device = PasswordDevice.objects.get(user=user)
        self.assertEqual(device.failed_attempts, 0)
        self.assertEqual(device.locked_at, locked_at)

    def test_set_unusable_password(self):
        """Test revoking a password keeps its device state and creates no device"""
        user = create_test_user()
        changed_at = user.password_change_date
        PasswordDevice.objects.filter(user=user).update(failed_attempts=2)
        PasswordDevice.set_unusable_password(user)

        device = PasswordDevice.objects.get(user=user)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(device.failed_attempts, 2)
        self.assertEqual(device.password_change_date, changed_at)

        without_device = User.objects.create(username=generate_id())
        PasswordDevice.set_unusable_password(without_device)
        self.assertFalse(PasswordDevice.objects.filter(user=without_device).exists())

    def test_user_without_device(self):
        """Test a user without a password device has no usable password"""
        user = User.objects.create(username=generate_id())

        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.password_change_date, user.date_joined)
        self.assertIsNone(
            InbuiltBackend().authenticate(None, username=user.username, password=user.username)
        )

    def test_hash_upgrade(self):
        """Test rehashing keeps the change date, sends no signal and loses to a concurrent reset"""
        user = create_test_user()
        old_hash = PBKDF2PasswordHasher().encode("initial", "salt", iterations=1)
        PasswordDevice.objects.filter(user=user).update(password=old_hash)
        device = PasswordDevice.objects.get(user=user)
        changed_at = device.password_change_date

        with patch.object(password_changed, "send") as signal:
            self.assertTrue(device.check_password("initial"))
        signal.assert_not_called()
        upgraded = PasswordDevice.objects.get(user=user)
        self.assertNotEqual(upgraded.password, old_hash)
        self.assertEqual(upgraded.password_change_date, changed_at)

        PasswordDevice.objects.filter(user=user).update(password=old_hash)
        device = PasswordDevice.objects.get(user=user)
        reset_hash = make_password("reset")
        PasswordDevice.objects.filter(user=user).update(password=reset_hash)
        self.assertTrue(device.check_password("initial"))
        self.assertEqual(PasswordDevice.objects.get(user=user).password, reset_hash)

    def test_async_authenticate(self):
        """Test async authentication runs the backend's own check"""
        user = create_test_user()
        self.assertEqual(
            async_to_sync(InbuiltBackend().aauthenticate)(
                None, username=user.username, password=user.username
            ),
            user,
        )
        self.assertIsNone(
            async_to_sync(TokenBackend().aauthenticate)(
                None, username=user.username, password=user.username
            )
        )

    def test_changepassword(self):
        """Test `ak changepassword` stores the password on the device"""
        user = create_test_user()
        with patch(
            "authentik.admin.management.commands.changepassword.getpass", return_value="changed"
        ):
            call_command("changepassword", user.username, stdout=StringIO())
        self.assertTrue(PasswordDevice.objects.get(user=user).check_password("changed"))
