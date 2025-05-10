"""base model tests"""

from collections.abc import Callable

from django.test import TestCase
from rest_framework.serializers import BaseSerializer

from authentik.common.models import SerializerModel
from authentik.common.utils.reflection import all_subclasses
from authentik.flows.models import Stage


class TestModels(TestCase):
    """Generic model properties tests"""


def model_tester_factory(test_model: type[Stage]) -> Callable:
    """Test a form"""

    def tester(self: TestModels):
        try:
            model_class = None
            if test_model._meta.abstract:  # pragma: no cover
                return
            model_class = test_model()
            self.assertTrue(issubclass(model_class.serializer, BaseSerializer))
        except NotImplementedError:
            pass

    return tester


for model in all_subclasses(SerializerModel):
    setattr(TestModels, f"test_model_{model.__name__}", model_tester_factory(model))
