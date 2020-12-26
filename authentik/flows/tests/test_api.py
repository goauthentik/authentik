"""API flow tests"""
from django.shortcuts import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.api import StageSerializer, StageViewSet
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding, Stage
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage

DIAGRAM_EXPECTED = """st=>start: Start
stage_0=>operation: Stage
dummy1
stage_1=>operation: Stage
dummy2
stage_1_policy_0=>condition: Policy
None
e=>end: End|future
st(right)->stage_0
stage_0(bottom)->stage_1
stage_1(bottom)->stage_1_policy_0
stage_1_policy_0(yes, right)->e
stage_1_policy_0(no, bottom)->e"""
DIAGRAM_SHORT_EXPECTED = """st=>start: Start
e=>end: End|future
st(right)->e"""


class TestFlowsAPI(APITestCase):
    """API tests"""

    def test_models(self):
        """Test that ui_user_settings returns none"""
        self.assertIsNone(Stage().ui_user_settings)

    def test_api_serializer(self):
        """Test that stage serializer returns the correct type"""
        obj = DummyStage()
        self.assertEqual(StageSerializer().get_type(obj), "dummy")
        self.assertEqual(StageSerializer().get_verbose_name(obj), "Dummy Stage")

    def test_api_viewset(self):
        """Test that stage serializer returns the correct type"""
        dummy = DummyStage.objects.create()
        self.assertIn(dummy, StageViewSet().get_queryset())

    def test_api_diagram(self):
        """Test flow diagram."""
        user = User.objects.get(username="akadmin")
        self.client.force_login(user)

        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
        false_policy = DummyPolicy.objects.create(result=False, wait_min=1, wait_max=2)

        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name="dummy2"),
            order=1,
            re_evaluate_policies=True,
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        response = self.client.get(
            reverse("authentik_api:flow-diagram", kwargs={"slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"diagram": DIAGRAM_EXPECTED})

    def test_api_diagram_no_stages(self):
        """Test flow diagram with no stages."""
        user = User.objects.get(username="akadmin")
        self.client.force_login(user)

        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
        response = self.client.get(
            reverse("authentik_api:flow-diagram", kwargs={"slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"diagram": DIAGRAM_SHORT_EXPECTED})
