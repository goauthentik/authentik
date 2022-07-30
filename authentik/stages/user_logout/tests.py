"""logout tests"""
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_logout.models import UserLogoutStage


class TestUserLogoutStage(FlowTestCase):
    """Logout tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = UserLogoutStage.objects.create(name="logout")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_get(self):
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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_valid_post(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        # pylint: disable=no-member
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
