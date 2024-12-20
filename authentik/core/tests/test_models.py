"""authentik core models tests"""

from collections.abc import Callable
from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils.timezone import now
from freezegun import freeze_time
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Provider, Source, Token
from authentik.lib.utils.reflection import all_subclasses


class TestModels(TestCase):
    """Test Models"""

    def test_token_expire(self):
        """Test token expiring"""
        with freeze_time() as freeze:
            token = Token.objects.create(expires=now(), user=get_anonymous_user())
            freeze.tick(timedelta(seconds=1))
            self.assertTrue(token.is_expired)

    def test_token_expire_no_expire(self):
        """Test token expiring with "expiring" set"""
        with freeze_time() as freeze:
            token = Token.objects.create(expires=now(), user=get_anonymous_user(), expiring=False)
            freeze.tick(timedelta(seconds=1))
            self.assertFalse(token.is_expired)


def source_tester_factory(test_model: type[Source]) -> Callable:
    """Test source"""

    factory = RequestFactory()
    request = factory.get("/")

    def tester(self: TestModels):
        model_class = None
        if test_model._meta.abstract:
            model_class = [x for x in test_model.__bases__ if issubclass(x, Source)][0]()
        else:
            model_class = test_model()
        model_class.slug = "test"
        self.assertIsNotNone(model_class.component)
        model_class.ui_login_button(request)
        model_class.ui_user_settings()

    return tester


def provider_tester_factory(test_model: type[Provider]) -> Callable:
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
