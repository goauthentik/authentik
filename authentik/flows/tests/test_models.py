"""flow model tests"""
from typing import Callable, Type

from django.forms import ModelForm
from django.test import TestCase

from authentik.flows.models import Stage
from authentik.flows.stage import StageView


class TestStageProperties(TestCase):
    """Generic model properties tests"""


def stage_tester_factory(model: Type[Stage]) -> Callable:
    """Test a form"""

    def tester(self: TestStageProperties):
        model_inst = model()
        self.assertTrue(issubclass(model_inst.form, ModelForm))
        self.assertTrue(issubclass(model_inst.type, StageView))

    return tester


for stage_type in Stage.__subclasses__():
    setattr(
        TestStageProperties,
        f"test_stage_{stage_type.__name__}",
        stage_tester_factory(stage_type),
    )
