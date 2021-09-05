"""authentik managed models tests"""
from typing import Callable, Type

from django.apps import apps
from django.test import TestCase

from authentik.lib.models import SerializerModel
from authentik.managed.transport.importer import EXCLUDED_MODELS


class TestModels(TestCase):
    """Test Models"""


def serializer_tester_factory(test_model: Type[SerializerModel]) -> Callable:
    """Test serializer"""

    def tester(self: TestModels):
        if test_model._meta.abstract:
            return
        model_class = test_model()
        self.assertTrue(isinstance(model_class, SerializerModel))
        self.assertIsNotNone(model_class.serializer)

    return tester


for app in apps.get_app_configs():
    if not app.label.startswith("authentik"):
        continue
    for model in app.get_models():
        if model in EXCLUDED_MODELS:
            continue
        setattr(TestModels, f"test_{app.label}_{model.__name__}", serializer_tester_factory(model))
