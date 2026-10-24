"""authentik event models tests"""

from collections.abc import Callable

from django.db.models import Model
from django.test import TestCase

from authentik.admin.utils import get_system_settings
from authentik.lib.utils.reflection import get_apps


class TestModels(TestCase):
    """Test Models"""


def model_tester_factory(test_model: type[Model]) -> Callable:
    """Test models' __str__ and __repr__"""

    def tester(self: TestModels):
        # Token-like defaults read the system settings, which are cached in memory
        get_system_settings()
        with self.assertNumQueries(0):
            str(test_model())
        with self.assertNumQueries(0):
            repr(test_model())

    return tester


for app in get_apps():
    for model in app.get_models():
        setattr(TestModels, f"test_{app.label}_{model.__name__}", model_tester_factory(model))
