"""password tests"""

from threading import Thread
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import User, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.enterprise.license import LicenseSummary
from authentik.enterprise.models import LicenseUsageStatus
from authentik.enterprise.stages.password.lockout import PasswordLockout, PasswordLockoutResult
from authentik.events.models import Event, EventAction
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


class TestPasswordLockout(FlowTestCase):
    """Password lockout tests"""

    def setUp(self):
        super().setUp()
        self.licensed(True).start()
        self.addCleanup(patch.stopall)

        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = PasswordStage.objects.create(
            name=generate_id(),
            backends=[BACKEND_INBUILT],
            failed_attempts_before_lockout=2,
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def licensed(self, valid: bool):
        """Patch the license summary this stage reads to decide whether it may lock"""
        summary = LicenseSummary(
            internal_users=100,
            external_users=100,
            status=LicenseUsageStatus.VALID if valid else LicenseUsageStatus.UNLICENSED,
            latest_valid=now(),
            license_flags=[],
        )
        return patch(
            "authentik.enterprise.stages.password.lockout.LicenseKey.cached_summary",
            return_value=summary,
        )

    def start_flow(self):
        """Put a plan with the test user pending into the session"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

    def submit(self, password: str):
        return self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"password": password},
        )

    @property
    def device(self) -> PasswordDevice:
        return PasswordDevice.objects.get(user=self.user)

    def test_locks_after_limit(self):
        """Test the password is locked once the stage's limit is reached"""
        self.start_flow()
        response = self.submit("wrong")
        self.assertEqual(self.device.failed_attempts, 1)
        self.assertFalse(self.device.locked)
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={"password": [{"string": "Invalid password", "code": "invalid"}]},
        )

        response = self.submit("wrong")
        self.assertEqual(self.device.failed_attempts, 0)
        self.assertTrue(self.device.locked)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Invalid password",
        )
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.PASSWORD_LOCKED,
                context__affected_user__pk=self.user.pk,
            ).exists()
        )

    def test_locked_refuses_correct_password(self):
        """Test a locked password is refused even when the submitted password is correct"""
        device = self.device
        device.locked_at = now()
        device.save()

        self.start_flow()
        response = self.submit(self.user.username)
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={"password": [{"string": "Invalid password", "code": "invalid"}]},
        )

        response = self.submit(self.user.username)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Invalid password",
        )

    def test_success_resets_failures(self):
        """Test authenticating successfully forgets earlier failures"""
        self.start_flow()
        self.submit("wrong")
        self.assertEqual(self.device.failed_attempts, 1)

        self.submit(self.user.username)
        self.assertEqual(self.device.failed_attempts, 0)

    def test_new_password_preserves_lock(self):
        """Test setting a password clears failures but preserves the lock"""
        device = self.device
        device.failed_attempts = 5
        device.locked_at = now()
        device.save()

        self.user.set_password(generate_id())
        self.user.save()

        self.assertEqual(self.device.failed_attempts, 0)
        self.assertTrue(self.device.locked)

    def test_unlicensed_never_locks(self):
        """Test passwords are not locked without an enterprise license"""
        with self.licensed(False):
            self.start_flow()
            self.submit("wrong")
            self.submit("wrong")
        self.assertFalse(self.device.locked)

    def test_custom_messages(self):
        """Test custom warning and lockout messages are returned"""
        self.stage.last_attempt_warning_message = "One attempt remains."
        self.stage.lockout_message = "Contact support."
        self.stage.save()
        self.start_flow()

        response = self.submit("wrong")
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={"password": [{"string": "One attempt remains.", "code": "invalid"}]},
        )

        response = self.submit("wrong")
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Contact support.",
        )

    def test_flow_cancel_preserves_last_attempt_warning(self):
        """Test flow cancellation keeps a warning returned on the same attempt"""
        self.stage.failed_attempts_before_cancel = 1
        self.stage.last_attempt_warning_message = "One attempt remains."
        self.stage.save(
            update_fields=("failed_attempts_before_cancel", "last_attempt_warning_message")
        )
        self.start_flow()
        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        response = self.submit("wrong")

        self.assertNotIn(SESSION_KEY_PLAN, self.client.session)
        self.assertStageResponse(
            response,
            self.flow,
            error_message="One attempt remains.",
        )

    def test_api_unlock(self):
        """Test an administrator can unlock a locked password"""
        device = self.device
        device.failed_attempts = 5
        device.locked_at = now()
        device.save()

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:user-unlock-password", kwargs={"pk": self.user.pk})
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.device.locked)
        self.assertEqual(self.device.failed_attempts, 0)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.PASSWORD_UNLOCKED,
                context__affected_user__pk=self.user.pk,
            ).exists()
        )

    def test_api_lock(self):
        """Test an administrator can lock another user's password, even a deactivated one"""
        target = create_test_admin_user()
        target.is_active = False
        target.save()
        self.client.force_login(self.user)
        url = reverse("authentik_api:user-lock-password", kwargs={"pk": target.pk})

        with self.licensed(False):
            response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertTrue(PasswordDevice.objects.get(user=target).locked)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.PASSWORD_LOCKED,
                user__pk=self.user.pk,
                context__affected_user__pk=target.pk,
            ).exists()
        )
        response = self.client.get(reverse("authentik_api:user-detail", kwargs={"pk": target.pk}))
        self.assertTrue(response.json()["password_locked"])

    def test_api_allows_self_lock(self):
        """Test users can lock their own password, e.g. to only sign in with passkeys"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:user-lock-password", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(self.device.locked)

    def test_api_rejects_service_account_lock(self):
        """Test service account passwords cannot be locked"""
        service_account = User.objects.create(
            username=generate_id(), type=UserTypes.SERVICE_ACCOUNT
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:user-lock-password", kwargs={"pk": service_account.pk})
        )
        self.assertEqual(response.status_code, 400)


class TestPasswordLockoutConcurrency(TransactionTestCase):
    """Password lockout concurrency tests"""

    def test_concurrent_failures(self):
        """Concurrent failures update one serialized counter"""
        user = create_test_admin_user()
        request = RequestFactory().post("/")
        stage = PasswordStage.objects.create(
            name=generate_id(), backends=[BACKEND_INBUILT], failed_attempts_before_lockout=3
        )

        class FailureThread(Thread):
            __test__ = False
            result = PasswordLockoutResult()

            def run(self):
                try:
                    self.result = PasswordLockout(stage, request).apply(user, None, {})
                finally:
                    connection.close()

        connection.close()
        with patch.object(PasswordLockout, "is_available", return_value=True):
            threads = [FailureThread() for _ in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        device = PasswordDevice.objects.get(user=user)
        self.assertTrue(device.locked)
        self.assertCountEqual(
            [thread.result for thread in threads],
            [
                PasswordLockoutResult(),
                PasswordLockoutResult(last_attempt=True),
                PasswordLockoutResult(lockout_reached=True),
            ],
        )
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.PASSWORD_LOCKED,
                context__affected_user__pk=user.pk,
            ).count(),
            1,
        )
