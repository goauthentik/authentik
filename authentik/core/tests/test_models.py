"""authentik core models tests"""
from time import sleep
from typing import Callable

from django.test import RequestFactory, TestCase
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Provider, Source, Token
from authentik.flows.models import Stage
from authentik.lib.utils.reflection import all_subclasses


class TestModels(TestCase):
    """Test Models"""

    def test_token_expire(self):
        """Test token expiring"""
        token = Token.objects.create(expires=now(), user=get_anonymous_user())
        sleep(0.5)
        self.assertTrue(token.is_expired)

    def test_token_expire_no_expire(self):
        """Test token expiring with "expiring" set"""
        token = Token.objects.create(expires=now(), user=get_anonymous_user(), expiring=False)
        sleep(0.5)
        self.assertFalse(token.is_expired)


def source_tester_factory(test_model: type[Stage]) -> Callable:
    """Test source"""

    factory = RequestFactory()
    request = factory.get("/")

    def tester(self: TestModels):
        model_class = None
        if test_model._meta.abstract:  # pragma: no cover
            model_class = test_model.__bases__[0]()
        else:
            model_class = test_model()
        model_class.slug = "test"
        self.assertIsNotNone(model_class.component)
        _ = model_class.ui_login_button(request)
        _ = model_class.ui_user_settings()

    return tester


def provider_tester_factory(test_model: type[Stage]) -> Callable:
    """Test provider"""

    def tester(self: TestModels):
        model_class = None
        if test_model._meta.abstract:  # pragma: no cover
            return
        model_class = test_model()
        self.assertIsNotNone(model_class.component)

    return tester


for model in all_subclasses(Source):
    setattr(TestModels, f"test_source_{model.__name__}", source_tester_factory(model))
for model in all_subclasses(Provider):
    setattr(TestModels, f"test_provider_{model.__name__}", provider_tester_factory(model))
