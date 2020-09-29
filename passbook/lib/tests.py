"""base model tests"""
from typing import Callable, Type

from django.test import TestCase
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Stage
from passbook.lib.models import SerializerModel
from passbook.lib.utils.reflection import all_subclasses


class TestModels(TestCase):
    """Generic model properties tests"""


def model_tester_factory(test_model: Type[Stage]) -> Callable:
    """Test a form"""

    def tester(self: TestModels):
        model_inst = test_model()
        try:
            self.assertTrue(issubclass(model_inst.serializer, BaseSerializer))
        except NotImplementedError:
            pass

    return tester


for model in all_subclasses(SerializerModel):
    setattr(TestModels, f"test_model_{model.__name__}", model_tester_factory(model))
