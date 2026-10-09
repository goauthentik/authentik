"""Locale catalog tests"""

from django.urls import reverse
from django.utils.translation import gettext, ngettext, override, pgettext
from rest_framework.test import APITestCase

from authentik.admin.i18n.catalog import CATALOG_STORE, canonicalize_language
from authentik.admin.i18n.models import LocaleCatalog
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id


class TestLocaleCatalogs(APITestCase):
    """Locale catalog tests"""

    def setUp(self):
        super().setUp()
        self.admin = create_test_admin_user()

    def create(self, locale: str, messages: dict, **kwargs) -> LocaleCatalog:
        with self.captureOnCommitCallbacks(execute=True):
            return LocaleCatalog.objects.create(
                name=generate_id(), locale=locale, messages=messages, **kwargs
            )

    def test_canonicalize(self):
        """Language tags are compared in their canonical form"""
        self.assertEqual(canonicalize_language("de_de"), "de-DE")
        self.assertEqual(canonicalize_language("zh-hans"), "zh-Hans")
        self.assertEqual(canonicalize_language("ES-419"), "es-419")

    def test_gettext(self):
        """Custom messages are used by gettext, other locales are unaffected"""
        self.create("de", {"Username": "Kennung"})
        with override("de"):
            self.assertEqual(gettext("Username"), "Kennung")
        with override("fr"):
            self.assertNotEqual(gettext("Username"), "Kennung")

    def test_gettext_source_language(self):
        """The source language can be customized as well"""
        self.create("en", {"Username": "Employee ID"})
        with override("en"):
            self.assertEqual(gettext("Username"), "Employee ID")

    def test_pgettext(self):
        """Messages with context are keyed by context and message joined by \\x04"""
        self.create("de", {"greeting\x04Hello": "Servus"})
        with override("de"):
            self.assertEqual(pgettext("greeting", "Hello"), "Servus")

    def test_ngettext(self):
        """Plural forms"""
        self.create("de", {"%(n)s item": ["%(n)s Ding", "%(n)s Dinge"]})
        self.create("fr", {"%(n)s item": "%(n)s chose", "%(n)s items": "%(n)s choses"})
        with override("de"):
            self.assertEqual(ngettext("%(n)s item", "%(n)s items", 1), "%(n)s Ding")
            self.assertEqual(ngettext("%(n)s item", "%(n)s items", 2), "%(n)s Dinge")
        with override("fr"):
            self.assertEqual(ngettext("%(n)s item", "%(n)s items", 1), "%(n)s chose")
            self.assertEqual(ngettext("%(n)s item", "%(n)s items", 2), "%(n)s choses")

    def test_precedence(self):
        """More specific locales win, then higher order"""
        self.create("de", {"a": "de", "b": "de", "c": "de"})
        self.create("de-AT", {"b": "de-AT low", "c": "de-AT low"}, order=0)
        self.create("de-AT", {"c": "de-AT high"}, order=10)
        self.create("de", {"b": "de high"}, order=100)
        self.assertEqual(
            CATALOG_STORE.messages("de_at"),
            {"a": "de", "b": "de-AT low", "c": "de-AT high"},
        )

    def test_base_language_fallback(self):
        """Django activates `de`, which falls back to regional catalogs"""
        self.create("de-DE", {"a": "de-DE", "b": "de-DE"})
        self.create("de", {"b": "de"})
        self.assertEqual(CATALOG_STORE.messages("de"), {"a": "de-DE", "b": "de"})
        # But a different region doesn't
        self.assertEqual(CATALOG_STORE.messages("de-CH"), {"b": "de"})

    def test_disabled(self):
        """Disabled catalogs are ignored"""
        self.create("de", {"Username": "Kennung"}, enabled=False)
        self.assertEqual(CATALOG_STORE.messages("de"), {})

    def test_invalidation(self):
        """Changes are picked up"""
        catalog = self.create("de", {"Username": "Kennung"})
        self.assertEqual(CATALOG_STORE.lookup("de", "Username"), "Kennung")
        with self.captureOnCommitCallbacks(execute=True):
            catalog.messages = {"Username": "Benutzer-ID"}
            catalog.save()
        self.assertEqual(CATALOG_STORE.lookup("de", "Username"), "Benutzer-ID")
        with self.captureOnCommitCallbacks(execute=True):
            catalog.delete()
        self.assertIsNone(CATALOG_STORE.lookup("de", "Username"))

    def test_api_create(self):
        """Create a catalog, normalizing its locale"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:localecatalog-list"),
            data={"name": generate_id(), "locale": "de_de", "messages": {"Username": "Kennung"}},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(LocaleCatalog.objects.get().locale, "de-DE")

    def test_api_validation(self):
        """Invalid locales and messages are rejected"""
        self.client.force_login(self.admin)
        for locale, messages in (
            ("not a locale", {}),
            ("de", []),
            ("de", {"Username": ""}),
            ("de", {"Username": 1}),
            ("de", {"Username": ["one", 2]}),
            ("de", {"": "empty"}),
        ):
            response = self.client.post(
                reverse("authentik_api:localecatalog-list"),
                data={"name": generate_id(), "locale": locale, "messages": messages},
                format="json",
            )
            self.assertEqual(response.status_code, 400, (locale, messages))

    def test_api_resolve(self):
        """Unauthenticated users can get merged messages, without plural forms"""
        self.create("de", {"Username": "Kennung", "%(n)s item": ["a", "b"]})
        self.create("de-DE", {"Password": "Kennwort"})
        response = self.client.get(
            reverse("authentik_api:localecatalog-resolve"), {"locale": "de-de"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"locale": "de-DE", "messages": {"Username": "Kennung", "Password": "Kennwort"}},
        )
        response = self.client.get(
            reverse("authentik_api:localecatalog-resolve"), {"locale": "<script>"}
        )
        self.assertEqual(response.status_code, 400)

    def test_interface_embeds_catalog(self):
        """Interfaces embed the custom messages of the request's language"""
        self.create("de-DE", {"Username": "Kennung", "</script>": "<script>"})
        flow = create_test_flow()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}),
            HTTP_ACCEPT_LANGUAGE="de-DE",
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('<script id="ak-locale-catalog" type="application/json">', content)
        self.assertIn('"Username": "Kennung"', content)
        self.assertNotIn('"<script>"', content)
