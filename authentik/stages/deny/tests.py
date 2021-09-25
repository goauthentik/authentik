"""deny tests"""
from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.deny.models import DenyStage


class TestUserDenyStage(APITestCase):
    """Deny tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")

        self.flow = Flow.objects.create(
            name="test-logout",
            slug="test-logout",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = DenyStage.objects.create(name="logout")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
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
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
                "type": ChallengeTypes.NATIVE.value,
            },
        )
