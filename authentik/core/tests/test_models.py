"""authentik core models tests"""

from collections.abc import Callable
from datetime import timedelta
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.utils.timezone import now
from freezegun import freeze_time
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Provider, Source, Token
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
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

    def test_filter_not_expired_warning(self):
        """Test filter_not_expired's deprecation message"""
        id = generate_id()
        Token.objects.create(
            expires=now() - timedelta(hours=1),
            expiring=True,
            user=get_anonymous_user(),
            identifier=id,
        )
        self.assertFalse(Token.filter_not_expired(identifier=id).exists())
        event = Event.objects.filter(action=EventAction.CONFIGURATION_WARNING).first()
        self.assertIsNotNone(event)
        self.assertEqual(
            event.context["deprecation"], "authentik.core.models.Token.filter_not_expired"
        )

    @patch("authentik.core.models.get_file_manager")
    def test_source_icon_url_can_bypass_cache(self, get_file_manager):
        request = RequestFactory().get("/")
        manager = get_file_manager.return_value
        manager.file_url.return_value = "/files/media/public/source-icons/icon.svg?token=fresh"

        source = Source(icon="source-icons/icon.svg")

        self.assertEqual(
            source.get_icon_url(request, use_cache=False),
            "/files/media/public/source-icons/icon.svg?token=fresh",
        )
        manager.file_url.assert_called_once_with(
            "source-icons/icon.svg",
            request,
            use_cache=False,
        )

    @patch("authentik.flows.models.get_file_manager")
    def test_flow_background_urls_can_bypass_cache(self, get_file_manager):
        request = RequestFactory().get("/")
        manager = get_file_manager.return_value
        manager.file_url.return_value = "/files/media/public/background.svg?token=fresh"
        manager.themed_urls.return_value = {
            "light": "/files/media/public/background-light.svg?token=fresh",
            "dark": "/files/media/public/background-dark.svg?token=fresh",
        }

        flow = Flow(background="background-%(theme)s.svg")

        self.assertEqual(
            flow.background_url(request, use_cache=False),
            "/files/media/public/background.svg?token=fresh",
        )
        self.assertEqual(
            flow.background_themed_urls(request, use_cache=False),
            {
                "light": "/files/media/public/background-light.svg?token=fresh",
                "dark": "/files/media/public/background-dark.svg?token=fresh",
            },
        )
        manager.file_url.assert_called_once_with(
            "background-%(theme)s.svg",
            request,
            use_cache=False,
        )
        manager.themed_urls.assert_called_once_with(
            "background-%(theme)s.svg",
            request,
            use_cache=False,
        )


def source_tester_factory(test_model: type[Source]) -> Callable:
    """Test source"""

    factory = RequestFactory()
    request = factory.get("/")

    def tester(self: TestModels):
        model_class = None
        if test_model._meta.abstract:
            return
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
