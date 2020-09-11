"""invitation tests"""
from unittest.mock import MagicMock, patch

from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_str
from guardian.shortcuts import get_anonymous_user

from passbook.core.models import User
from passbook.flows.markers import StageMarker
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.invitation.forms import InvitationStageForm
from passbook.stages.invitation.models import Invitation, InvitationStage
from passbook.stages.invitation.stage import INVITATION_TOKEN_KEY, PLAN_CONTEXT_PROMPT
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND


class TestUserLoginStage(TestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-invitation",
            slug="test-invitation",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = InvitationStage.objects.create(name="invitation")
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(InvitationStageForm(data).is_valid(), True)

    def test_without_invitation_fail(self):
        """Test without any invitation, continue_flow_without_invitation not set."""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[
            PLAN_CONTEXT_AUTHENTICATION_BACKEND
        ] = "django.contrib.auth.backends.ModelBackend"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_flows:denied")},
        )

    def test_without_invitation_continue(self):
        """Test without any invitation, continue_flow_without_invitation is set."""
        self.stage.continue_flow_without_invitation = True
        self.stage.save()
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[
            PLAN_CONTEXT_AUTHENTICATION_BACKEND
        ] = "django.contrib.auth.backends.ModelBackend"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )

        self.stage.continue_flow_without_invitation = False
        self.stage.save()

    def test_with_invitation(self):
        """Test with invitation, check data in session"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[
            PLAN_CONTEXT_AUTHENTICATION_BACKEND
        ] = "django.contrib.auth.backends.ModelBackend"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        data = {"foo": "bar"}
        invite = Invitation.objects.create(
            created_by=get_anonymous_user(), fixed_data=data
        )

        with patch("passbook.flows.views.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
            response = self.client.get(
                base_url + f"?{INVITATION_TOKEN_KEY}={invite.pk.hex}"
            )

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PROMPT], data)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )
