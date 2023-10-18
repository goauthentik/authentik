"""deny tests"""
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.deny.models import DenyStage


class TestUserDenyStage(FlowTestCase):
    """Deny tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = DenyStage.objects.create(name="logout")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_get(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")

    def test_valid_post(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")

    def test_message_static(self):
        """Test with a static error message"""
        self.stage.deny_message = "foo"
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response, self.flow, component="ak-stage-access-denied", error_message="foo"
        )

    def test_message_overwrite(self):
        """Test with an overwritten error message"""
        self.stage.deny_message = "foo"
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context["deny_message"] = "bar"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response, self.flow, component="ak-stage-access-denied", error_message="bar"
        )
