"""password tests"""

from threading import Thread
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from authentik.core.models import User, UserPasswordLoginState, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.lockout import (
    PasswordAuthenticationStatus,
    lock_password_login,
    record_failed_password_attempt,
)
from authentik.stages.password.models import PasswordStage

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
        UserPasswordLoginState.objects.create(user=self.user, failed_attempts=1)
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
        self.assertFalse(UserPasswordLoginState.objects.filter(user=self.user).exists())

    def test_valid_password_inactive(self):
        """Test with a valid pending user and valid password"""
        lock_password_login(self.user)
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
        self.assertIsNotNone(UserPasswordLoginState.objects.get(user=self.user).locked_at)

    def test_valid_password_locked(self):
        """A correct password cannot authenticate while password login is locked."""
        lock_password_login(self.user)
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"password": self.user.username},
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Invalid password",
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
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(UserPasswordLoginState.objects.filter(user=self.user).exists())

    def test_invalid_password_account_lockout(self):
        """Test that consecutive invalid passwords lock password login."""
        self.stage.failed_attempts_before_lockout = 2
        self.stage.show_last_attempt_warning = True
        self.stage.show_lockout_message = True
        self.stage.save(
            update_fields=(
                "failed_attempts_before_lockout",
                "show_last_attempt_warning",
                "show_lockout_message",
            )
        )
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        self.client.get(url)
        response = self.client.post(url, {"password": self.user.username + "test"})
        state = UserPasswordLoginState.objects.get(user=self.user)
        self.assertEqual(state.failed_attempts, 1)
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={
                "password": [
                    {
                        "string": (
                            "You have one password attempt remaining before your account is "
                            "locked out. If you have forgotten your password, please contact "
                            "your administrator."
                        ),
                        "code": "invalid",
                    }
                ]
            },
        )

        response = self.client.post(url, {"password": self.user.username + "test"})
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_login_locked_at)
        self.assertEqual(
            UserPasswordLoginState.objects.get(user=self.user).failed_attempts,
            0,
        )
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.PASSWORD_LOGIN_LOCKED,
                user__pk=self.user.pk,
            ).exists()
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message=(
                "Your account has been locked out due to too many failed attempts. "
                "Please contact your administrator."
            ),
        )

    def test_lockout_message_customization(self):
        """Configured messages override the default warning and lockout messages."""
        self.assertEqual(self.stage.get_last_attempt_message("generic"), "generic")
        self.stage.show_last_attempt_warning = True
        self.assertIn("one password attempt", self.stage.get_last_attempt_message("generic"))
        self.stage.last_attempt_warning_message = "This is your final attempt."
        self.assertEqual(
            self.stage.get_last_attempt_message("generic"), "This is your final attempt."
        )
        self.stage.show_lockout_message = True
        self.assertIn("contact your administrator", self.stage.get_lockout_message("generic"))
        self.stage.lockout_message = "Contact the help desk."
        self.assertEqual(self.stage.get_lockout_message("generic"), "Contact the help desk.")

    def test_internal_service_account_not_locked_out(self):
        """Failed attempts do not lock authentik's internal service accounts."""
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save(update_fields=("type",))
        self.stage.failed_attempts_before_lockout = 1

        result = record_failed_password_attempt(
            self.user,
            self.stage.failed_attempts_before_lockout,
        )

        self.assertIs(result, PasswordAuthenticationStatus.INVALID)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.password_login_locked_at)
        self.assertFalse(UserPasswordLoginState.objects.filter(user=self.user).exists())

    def test_invalid_password_cancels_flow(self):
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


class TestPasswordLockoutConcurrency(TransactionTestCase):
    """Password lockout concurrency tests."""

    def test_user_save_does_not_overwrite_lockout_state(self):
        """Saving a stale user cannot erase failures or a password-login lock."""
        user = create_test_admin_user()
        stale_user = User.objects.get(pk=user.pk)

        self.assertIs(
            record_failed_password_attempt(user, 2),
            PasswordAuthenticationStatus.LAST_ATTEMPT,
        )
        stale_user.name = generate_id()
        stale_user.save()
        self.assertEqual(
            UserPasswordLoginState.objects.get(user=user).failed_attempts,
            1,
        )

        self.assertIs(
            record_failed_password_attempt(user, 2),
            PasswordAuthenticationStatus.LOCKED,
        )
        stale_user.email = "updated@example.com"
        stale_user.save()
        self.assertIsNotNone(UserPasswordLoginState.objects.get(user=user).locked_at)

    def test_concurrent_failures(self):
        """Concurrent failures update one serialized counter."""
        user = create_test_admin_user()
        stage = PasswordStage.objects.create(
            name=generate_id(), backends=[BACKEND_INBUILT], failed_attempts_before_lockout=3
        )

        class FailureThread(Thread):
            __test__ = False
            result = PasswordAuthenticationStatus.INVALID

            def run(self):
                try:
                    self.result = record_failed_password_attempt(
                        user,
                        stage.failed_attempts_before_lockout,
                    )
                finally:
                    connection.close()

        connection.close()
        threads = [FailureThread() for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        user.refresh_from_db()
        self.assertIsNotNone(user.password_login_locked_at)
        self.assertCountEqual(
            [thread.result for thread in threads],
            [
                PasswordAuthenticationStatus.INVALID,
                PasswordAuthenticationStatus.LAST_ATTEMPT,
                PasswordAuthenticationStatus.LOCKED,
            ],
        )
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.PASSWORD_LOGIN_LOCKED,
                user__pk=user.pk,
            ).count(),
            1,
        )
