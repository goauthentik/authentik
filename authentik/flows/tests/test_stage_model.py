"""base model tests"""

from collections.abc import Callable

from django.test import TestCase

from authentik.common.utils.reflection import all_subclasses
from authentik.flows.models import Stage
from authentik.flows.stage import StageView


class TestModels(TestCase):
    """Generic model properties tests"""


def model_tester_factory(test_model: type[Stage]) -> Callable:
    """Test a form"""

    def tester(self: TestModels):
        model_class = None
        if test_model._meta.abstract:  # pragma: no cover
            model_class = test_model.__bases__[0]()
        else:
            model_class = test_model()
        self.assertTrue(issubclass(model_class.view, StageView))
        self.assertIsNotNone(test_model.component)
        _ = model_class.ui_user_settings()

    return tester


for model in all_subclasses(Stage):
    setattr(TestModels, f"test_model_{model.__name__}", model_tester_factory(model))
