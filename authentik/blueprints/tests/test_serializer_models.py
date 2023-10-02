"""authentik managed models tests"""
from typing import Callable, Type

from django.apps import apps
from django.test import TestCase

from authentik.blueprints.v1.importer import is_model_allowed
from authentik.lib.models import SerializerModel
from authentik.providers.oauth2.models import RefreshToken


class TestModels(TestCase):
    """Test Models"""


def serializer_tester_factory(test_model: Type[SerializerModel]) -> Callable:
    """Test serializer"""

    def tester(self: TestModels):
        if test_model._meta.abstract:  # pragma: no cover
            return
        model_class = test_model()
        self.assertTrue(isinstance(model_class, SerializerModel))
        self.assertIsNotNone(model_class.serializer)
        if model_class.serializer.Meta().model == RefreshToken:
            return
        self.assertEqual(model_class.serializer.Meta().model, test_model)

    return tester


for app in apps.get_app_configs():
    if not app.label.startswith("authentik"):
        continue
    for model in app.get_models():
        if not is_model_allowed(model):
            continue
        setattr(TestModels, f"test_{app.label}_{model.__name__}", serializer_tester_factory(model))
