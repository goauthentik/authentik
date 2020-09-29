"""flow model tests"""
from typing import Callable, Type

from django.forms import ModelForm
from django.test import TestCase

from passbook.lib.utils.reflection import all_subclasses
from passbook.policies.models import Policy


class TestPolicyProperties(TestCase):
    """Generic model properties tests"""


def policy_tester_factory(model: Type[Policy]) -> Callable:
    """Test a form"""

    def tester(self: TestPolicyProperties):
        model_inst = model()
        self.assertTrue(issubclass(model_inst.form, ModelForm))

    return tester


for policy_type in all_subclasses(Policy):
    setattr(
        TestPolicyProperties,
        f"test_policy_{policy_type.__name__}",
        policy_tester_factory(policy_type),
    )
