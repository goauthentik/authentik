"""API flow tests"""
from django.test import RequestFactory, TestCase

from authentik.core.models import User
from authentik.flows.api import FlowViewSet, StageSerializer, StageViewSet
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding, Stage
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage


class TestFlowsAPI(TestCase):
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
        """Test flow diagram. This only tests that the code works,
        the result is not validated."""
        factory = RequestFactory()
        request = factory.get("/")
        request.user = User.objects.get(username="akadmin")

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

        FlowViewSet().diagram(request, slug=flow.slug)
