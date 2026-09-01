"""Test core middleware"""

from django.test import TestCase
from django.urls import reverse

from authentik.core.apps import Setup
from authentik.core.models import UserTypes
from authentik.core.tests.utils import create_test_brand, create_test_user


class TestLocaleOverrideMiddleware(TestCase):
    """The `?locale=` override is honored (and validated) server-side, so the
    server-rendered shell and the web UI agree on the active locale."""

    def setUp(self):
        Setup.set(True)
        self.user = create_test_user(type=UserTypes.INTERNAL)
        create_test_brand()
        self.client.force_login(self.user)

    def test_valid_locale_query_param_applied(self):
        """A supported `?locale=` is applied to the server-rendered shell."""
        response = self.client.get(reverse("authentik_core:if-user") + "?locale=fr")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'locale: "fr"', response.content)
        self.assertIn(b'lang="fr"', response.content)

    def test_invalid_locale_query_param_ignored(self):
        """An unsupported `?locale=` is ignored rather than applied blindly."""
        response = self.client.get(reverse("authentik_core:if-user") + "?locale=not-a-language")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'locale: "not-a-language"', response.content)

    def test_query_param_wins_over_user_locale(self):
        """An explicit `?locale=` takes precedence over the user's saved locale."""
        self.user.attributes["settings"] = {"locale": "de"}
        self.user.save()
        response = self.client.get(reverse("authentik_core:if-user") + "?locale=fr")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lang="fr"', response.content)
