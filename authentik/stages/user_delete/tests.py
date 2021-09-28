"""delete tests"""
from unittest.mock import patch

from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.user_delete.models import UserDeleteStage


class TestUserDeleteStage(APITestCase):
    """Delete tests"""

    def setUp(self):
        super().setUp()
        self.username = "qerqwerqrwqwerwq"
        self.user = User.objects.create(username=self.username, email="test@beryju.org")

        self.flow = Flow.objects.create(
            name="test-delete",
            slug="test-delete",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserDeleteStage.objects.create(name="delete")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_no_user(self):
        """Test without user set"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
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

    def test_user_delete_get(self):
        """Test Form render"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
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

        self.assertFalse(User.objects.filter(username=self.username).exists())
