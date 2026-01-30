"""Account lockdown stage tests"""

from django.urls import reverse

from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.enterprise.stages.account_lockdown.models import (
    PLAN_CONTEXT_LOCKDOWN_REASON,
    PLAN_CONTEXT_LOCKDOWN_TARGET,
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
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET] = self.target_user
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

    def test_lockdown_reason_from_prompt(self):
        """Test lockdown stage reads reason from prompt data"""
        self.target_user.is_active = True
        self.target_user.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET] = self.target_user
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

    def test_lockdown_revokes_tokens(self):
        """Test lockdown stage revokes tokens"""
        Token.objects.create(
            user=self.target_user,
            identifier="test-token",
            intent=TokenIntents.INTENT_API,
        )
        self.assertEqual(Token.objects.filter(user=self.target_user).count(), 1)

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET] = self.target_user
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
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET] = self.target_user
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
        plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET] = self.target_user
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
