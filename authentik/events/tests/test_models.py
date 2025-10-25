"""authentik event models tests"""

from collections.abc import Callable

from django.db.models import Model
from django.test import TestCase

from authentik.core.models import default_token_key
from authentik.events.models import default_event_duration
from authentik.lib.utils.reflection import get_apps


class TestModels(TestCase):
    """Test Models"""


def model_tester_factory(test_model: type[Model]) -> Callable:
    """Test models' __str__ and __repr__"""

    def tester(self: TestModels):
        allowed = 0
        # Token-like objects need to lookup the current tenant to get the default token length
        for field in test_model._meta.fields:
            if field.default in [default_token_key, default_event_duration]:
                allowed += 1
        with self.assertNumQueries(allowed):
            str(test_model())
        with self.assertNumQueries(allowed):
            repr(test_model())

    return tester


for app in get_apps():
    for model in app.get_models():
        setattr(TestModels, f"test_{app.label}_{model.__name__}", model_tester_factory(model))
