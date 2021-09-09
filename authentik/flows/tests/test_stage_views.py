"""stage view tests"""
from typing import Callable, Type

from django.test import RequestFactory, TestCase

from authentik.flows.stage import StageView
from authentik.flows.views import FlowExecutorView
from authentik.lib.utils.reflection import all_subclasses


class TestViews(TestCase):
    """Generic model properties tests"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.exec = FlowExecutorView(self.factory.request("/"))


def view_tester_factory(view: Type[StageView]) -> Callable:
    """Test a form"""

    def tester(self: TestViews):
        model_class = view(self.exec)
        self.assertIsNotNone(model_class.post)
        self.assertIsNotNone(model_class.get)

    return tester


for view in all_subclasses(StageView):
    setattr(TestViews, f"test_view_{view.__name__}", view_tester_factory(view))
