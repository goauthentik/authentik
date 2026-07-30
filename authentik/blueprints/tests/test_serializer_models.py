"""authentik managed models tests"""

from collections.abc import Callable

from django.apps import apps
from django.test import TestCase

from authentik.lib.models import SerializerModel
from authentik.providers.oauth2.models import RefreshToken


class TestModels(TestCase):
    """Test Models"""


def serializer_tester_factory(test_model: type[SerializerModel]) -> Callable:
    """Test serializer"""

    def tester(self: TestModels):
        if test_model._meta.abstract:  # pragma: no cover
            return
        model_class = test_model()
        self.assertTrue(isinstance(model_class, SerializerModel))
        # Models that have subclasses don't have to have a serializer
        if len(test_model.__subclasses__()) > 0:
            return
        self.assertIsNotNone(model_class.serializer)
        if model_class.serializer.Meta().model == RefreshToken:
            return
        self.assertTrue(issubclass(test_model, model_class.serializer.Meta().model))

    return tester


for app in apps.get_app_configs():
    if not app.label.startswith("authentik"):
        continue
    for model in app.get_models():
        if not issubclass(model, SerializerModel):
            continue
        setattr(TestModels, f"test_{app.label}_{model.__name__}", serializer_tester_factory(model))
