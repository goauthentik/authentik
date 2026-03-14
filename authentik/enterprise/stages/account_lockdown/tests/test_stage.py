"""Account lockdown stage tests"""

from unittest.mock import patch

from django.urls import reverse

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.enterprise.stages.account_lockdown.models import (
    PLAN_CONTEXT_LOCKDOWN_REASON,
    PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE,
    PLAN_CONTEXT_LOCKDOWN_TARGETS,
    AccountLockdownStage,
)
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class TestAccountLockdownStage(FlowTestCase):
    """Account lockdown stage tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.target_user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.stage = AccountLockdownStage.objects.create(name="lockdown")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)

    def test_lockdown_no_target(self):
        """Test lockdown stage with no target user fails"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="No target user specified for account lockdown",
        )

    def test_lockdown_with_pending_user(self):
        """Test lockdown stage with pending user"""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.target_user
        plan.context[PLAN_CONTEXT_LOCKDOWN_REASON] = "Security incident"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertFalse(self.target_user.has_usable_password())

        # Check event was created
        event = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "Security incident")
        self.assertEqual(event.context["affected_user"], self.target_user.username)

    def test_lockdown_with_target_user(self):
        """Test lockdown stage with explicit target user"""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        plan.context[PLAN_CONTEXT_LOCKDOWN_REASON] = "Compromised account"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_lockdown_with_authenticated_request_user(self):
        """Test direct self-service execution falls back to the authenticated request user."""
        self.target_user.is_active = True
        self.target_user.save()
        self.client.force_login(self.target_user)

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_lockdown_reason_from_prompt(self):
        """Test lockdown stage reads reason from prompt data"""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        plan.context[PLAN_CONTEXT_PROMPT] = {"reason": "User requested lockdown"}
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        event = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "User requested lockdown")

    def test_lockdown_event_failure_does_not_fail_self_service(self):
        """Test lockdown still succeeds when event emission fails."""
        self.stage.delete_sessions = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        plan.context[PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE] = True
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        original_event_new = Event.new

        def _event_new_side_effect(action, *args, **kwargs):
            if action == EventAction.ACCOUNT_LOCKDOWN_TRIGGERED:
                raise RuntimeError("simulated event failure")
            return original_event_new(action, *args, **kwargs)

        with patch(
            "authentik.enterprise.stages.account_lockdown.stage.Event.new",
            side_effect=_event_new_side_effect,
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_lockdown_self_service_redirects_to_completion_flow(self):
        """Test self-service lockdown redirects to completion flow when sessions are deleted."""
        completion_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.stage.self_service_completion_flow = completion_flow
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        plan.context[PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE] = True
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(
            response,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": completion_flow.slug}),
        )

    def test_lockdown_revokes_tokens(self):
        """Test lockdown stage revokes tokens"""
        Token.objects.create(
            user=self.target_user,
            identifier="test-token",
            intent=TokenIntents.INTENT_API,
        )
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 1)

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 0)

    def test_lockdown_selective_actions(self):
        """Test lockdown stage with selective actions"""
        self.stage.deactivate_user = True
        self.stage.set_unusable_password = False
        self.stage.delete_sessions = False
        self.stage.revoke_tokens = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.set_password("testpassword")
        self.target_user.save()

        Token.objects.create(
            user=self.target_user,
            identifier="test-token",
            intent=TokenIntents.INTENT_API,
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.target_user.refresh_from_db()
        # User should be deactivated
        self.assertFalse(self.target_user.is_active)
        # Password should still be usable
        self.assertTrue(self.target_user.has_usable_password())
        # Token should still exist
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 1)

    def test_lockdown_no_actions(self):
        """Test lockdown stage with all actions disabled"""
        self.stage.deactivate_user = False
        self.stage.set_unusable_password = False
        self.stage.delete_sessions = False
        self.stage.revoke_tokens = False
        self.stage.save()

        self.target_user.is_active = True
        self.target_user.set_password("testpassword")
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS] = [self.target_user]
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.target_user.refresh_from_db()
        # User should still be active
        self.assertTrue(self.target_user.is_active)
        # Password should still be usable
        self.assertTrue(self.target_user.has_usable_password())
        # Event should still be created
        event = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
