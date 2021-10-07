"""logout tests"""
from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_logout.models import UserLogoutStage


class TestUserLogoutStage(APITestCase):
    """Logout tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")

        self.flow = Flow.objects.create(
            name="test-logout",
            slug="test-logout",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserLogoutStage.objects.create(name="logout")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        # pylint: disable=no-member
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            # pylint: disable=no-member
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
