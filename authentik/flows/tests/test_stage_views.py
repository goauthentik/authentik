"""stage view tests"""
from typing import Callable

from django.test import RequestFactory, TestCase

from authentik.flows.stage import StageView
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.utils.reflection import all_subclasses


class TestViews(TestCase):
    """Generic model properties tests"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.exec = FlowExecutorView(request=self.factory.get("/"))


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
