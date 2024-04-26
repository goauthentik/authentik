"""authentik event models tests"""

from collections.abc import Callable

from django.db.models import Model
from django.test import TestCase

from authentik.lib.utils.reflection import get_apps


class TestModels(TestCase):
    """Test Models"""


def model_tester_factory(test_model: type[Model]) -> Callable:
    """Test source"""

    def tester(self: TestModels):
        with self.assertNumQueries(0):
            _ = str(test_model())
            _ = repr(test_model())

    return tester


for app in get_apps():
    for model in app.get_models():
        setattr(TestModels, f"test_{app.label}_{model.__name__}", model_tester_factory(model))
