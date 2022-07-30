"""delete tests"""
from unittest.mock import patch

from django.urls import reverse

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.user_delete.models import UserDeleteStage


class TestUserDeleteStage(FlowTestCase):
    """Delete tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
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
        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")

    def test_user_delete_get(self):
        """Test Form render"""
        self.client.force_login(self.user)
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        self.assertFalse(User.objects.filter(username=self.user.username).exists())

    def test_user_delete_post(self):
        """Test Form render"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        self.assertFalse(User.objects.filter(username=self.user.username).exists())
