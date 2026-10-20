"""FlowExecution tests"""

from django.http import QueryDict
from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.storage import FlowExecution
from authentik.lib.generators import generate_id
from authentik.stages.dummy.models import DummyStage


class TestFlowExecution(TestCase):
    """FlowExecution tests"""

    def setUp(self):
        self.flow = create_test_flow()
        self.request = RequestFactory().get("/")
        self.request.session = {}

    def _plan(self, stages: int = 2) -> FlowPlan:
        bindings = [
            FlowStageBinding.objects.create(
                target=self.flow, stage=DummyStage.objects.create(name=generate_id()), order=i
            )
            for i in range(stages)
        ]
        return FlowPlan(self.flow.pk.hex, bindings=bindings, markers=[StageMarker()] * stages)

    def test_lifecycle(self):
        """Start, reload, advance, cancel"""
        self.request.session = {"authentik/flows/post": QueryDict("x=y")}
        self.assertIsNone(FlowExecution(self.request).plan)
        FlowExecution.start(self.request, self._plan(), query=QueryDict("next=/foo"))

        execution = FlowExecution(self.request)
        self.assertEqual(len(execution.plan.bindings), 2)
        self.assertEqual(execution.query["next"], "/foo")

        execution.advance()
        execution = FlowExecution(self.request)
        self.assertEqual(len(execution.plan.bindings), 1)
        self.assertEqual(len(execution.history), 1)
        self.assertEqual(len(execution.history[0].bindings), 2)

        execution.cancel()
        execution = FlowExecution(self.request)
        self.assertIsNone(execution.plan)
        self.assertEqual(execution.query, QueryDict())
        # History and POST body survive a cancel
        self.assertEqual(len(execution.history), 1)
        self.assertEqual(execution.pop_post(), QueryDict("x=y"))
        self.assertIsNone(FlowExecution(self.request).post)

    def test_start_drops_history(self):
        """Starting a fresh execution drops the previous history"""
        FlowExecution.start(self.request, self._plan()).advance()
        execution = FlowExecution.start(self.request, self._plan(1))
        self.assertEqual(FlowExecution(self.request).history, [])
        self.assertEqual(len(execution.plan.bindings), 1)
