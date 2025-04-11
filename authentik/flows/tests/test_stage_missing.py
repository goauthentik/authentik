"""Test FlowPlanner handling of missing stages"""

from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase
from django.urls import reverse
from guardian.shortcuts import get_anonymous_user

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import FlowPlanner
from authentik.stages.dummy.models import DummyStage


class TestFlowPlannerStageMissing(TestCase):
    """Test planner's handling of missing stages"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.flow = create_test_flow()
        # Create a stage to use in our test
        self.stage = DummyStage.objects.create(name="dummy-stage")

    def test_missing_stage_handled_gracefully(self):
        """Test that a missing stage is handled gracefully by the planner"""
        # Create a binding with a valid stage initially
        binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

        # Make a valid request for the initial test
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        request.user = get_anonymous_user()

        # First verify the planner works with a valid binding
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True

        # Mock the Stage.objects.filter to return a stage list that doesn't include
        # a stage for one of the bindings
        mock_binding = Mock()
        mock_binding.pk = "missing-stage-binding"
        mock_binding.stage_id = "non-existent-stage-id"

        with patch("authentik.flows.planner.FlowStageBinding.objects.filter") as mock_filter:
            # Create a mock logger that we can inspect later
            mock_logger = Mock()

            # Replace the planner's logger with our mock
            original_logger = planner._logger
            planner._logger = mock_logger

            # Make filter return both a real binding and our mock binding with missing stage
            mock_filter.return_value.order_by.return_value = [binding, mock_binding]

            # Stage.objects.filter should return only the real stage
            with patch("authentik.flows.planner.Stage.objects.filter") as mock_stage_filter:
                mock_stage_filter.return_value = [self.stage]

                # Run the planner - this should trigger our missing stage handling
                plan = planner._build_plan(request.user, request, None)

                # Verify warning was logged about the missing stage
                mock_logger.warning.assert_called_once_with(
                    "Could not find stage for binding",
                    binding_id=mock_binding.pk,
                    stage_id=mock_binding.stage_id,
                )

                # Restore the original logger
                planner._logger = original_logger

                # Plan should only contain the valid binding
                self.assertEqual(len(plan.bindings), 1)
                self.assertEqual(plan.bindings[0].pk, binding.pk)
