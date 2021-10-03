"""invitation tests"""
from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlencode
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.invitation.models import Invitation, InvitationStage
from authentik.stages.invitation.stage import (
    INVITATION_TOKEN_KEY,
    INVITATION_TOKEN_KEY_CONTEXT,
    PLAN_CONTEXT_PROMPT,
)
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND


class TestUserLoginStage(APITestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")

        self.flow = Flow.objects.create(
            name="test-invitation",
            slug="test-invitation",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = InvitationStage.objects.create(name="invitation")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_invitation_fail(self):
        """Test without any invitation, continue_flow_without_invitation not set."""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "ak-stage-access-denied",
                "error_message": None,
                "type": ChallengeTypes.NATIVE.value,
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
            },
        )

    def test_without_invitation_continue(self):
        """Test without any invitation, continue_flow_without_invitation is set."""
        self.stage.continue_flow_without_invitation = True
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )

        self.stage.continue_flow_without_invitation = False
        self.stage.save()

    def test_with_invitation_get(self):
        """Test with invitation, check data in session"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        data = {"foo": "bar"}
        invite = Invitation.objects.create(created_by=get_anonymous_user(), fixed_data=data)

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            args = urlencode({INVITATION_TOKEN_KEY: invite.pk.hex})
            response = self.client.get(base_url + f"?query={args}")

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PROMPT], data)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )

    def test_with_invitation_prompt_data(self):
        """Test with invitation, check data in session"""
        data = {"foo": "bar"}
        invite = Invitation.objects.create(
            created_by=get_anonymous_user(), fixed_data=data, single_use=True
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {INVITATION_TOKEN_KEY_CONTEXT: invite.pk.hex}
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            response = self.client.get(base_url, follow=True)

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(
            plan.context[PLAN_CONTEXT_PROMPT], data | plan.context[PLAN_CONTEXT_PROMPT]
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
        self.assertFalse(Invitation.objects.filter(pk=invite.pk))


class TestInvitationsAPI(APITestCase):
    """Test Invitations API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_invite_create(self):
        """Test Invitations creation endpoint"""
        response = self.client.post(
            reverse("authentik_api:invitation-list"),
            {"identifier": "test-token", "fixed_data": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Invitation.objects.first().created_by, self.user)
