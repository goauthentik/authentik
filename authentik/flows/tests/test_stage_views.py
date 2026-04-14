"""stage view tests"""

from collections.abc import Callable

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import RequestFactory as AuthentikRequestFactory
from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.stage import StageView
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.utils.reflection import all_subclasses
from authentik.stages.dummy.models import DummyStage
from authentik.stages.dummy.stage import DummyStageView


class TestViews(TestCase):
    """Generic model properties tests"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.exec = FlowExecutorView(request=self.factory.get("/"))
        self.authentik_factory = AuthentikRequestFactory()

    def test_challenge_stage_flow_info_uses_relative_background(self):
        """Test challenge flow info keeps background URLs app-relative."""
        flow = create_test_flow()
        stage = DummyStage.objects.create(name="dummy")
        FlowStageBinding.objects.create(target=flow, stage=stage, order=0)
        request = self.authentik_factory.get("/")

        executor = FlowExecutorView(flow=flow, request=request)
        executor.current_stage = stage

        view = DummyStageView(executor)
        view.request = request

        challenge = view._get_challenge()

        self.assertEqual(
            challenge.initial_data["flow_info"]["background"],
            "/static/dist/assets/images/flow_background.jpg",
        )


def view_tester_factory(view_class: type[StageView]) -> Callable:
    """Test a form"""

    def tester(self: TestViews):
        model_class = view_class(self.exec)
        if not hasattr(model_class, "dispatch"):
            self.assertIsNotNone(model_class.post)
            self.assertIsNotNone(model_class.get)

    return tester


for view in all_subclasses(StageView):
    setattr(TestViews, f"test_view_{view.__name__}", view_tester_factory(view))
