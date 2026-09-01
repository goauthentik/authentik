"""Tests for authentik_core template tags"""

from tempfile import NamedTemporaryFile
from unittest.mock import patch

from django.test import TestCase
from django.utils import translation

from authentik.core.templatetags.authentik_core import (
    locale_modulepreload,
    read_locale_manifest,
    resolve_catalog_tag,
)

MANIFEST = {
    "de-DE": "chunks/de.abc123.js",
    "fr-FR": "chunks/fr.def456.js",
    "zh-Hans": "chunks/zhs.789.js",
    "zh-Hant": "chunks/zht.012.js",
    "en-XA": "chunks/pseudo.345.js",
}

MANIFEST_LOADER = "authentik.core.templatetags.authentik_core.read_locale_manifest"
MANIFEST_FINDER = "authentik.core.templatetags.authentik_core.finders.find"


class TestResolveCatalogTag(TestCase):
    """The Django language code is mapped to a catalog tag present in the manifest."""

    def test_exact_tag_is_returned(self):
        self.assertEqual(resolve_catalog_tag(MANIFEST, "de-DE"), "de-DE")

    def test_match_is_case_insensitive(self):
        self.assertEqual(resolve_catalog_tag(MANIFEST, "de-de"), "de-DE")
        self.assertEqual(resolve_catalog_tag(MANIFEST, "zh-hans"), "zh-Hans")

    def test_base_language_matches_regional_catalog(self):
        self.assertEqual(resolve_catalog_tag(MANIFEST, "fr"), "fr-FR")

    def test_english_resolves_to_no_catalog(self):
        self.assertIsNone(resolve_catalog_tag(MANIFEST, "en"))

    def test_english_never_resolves_to_pseudo_locale(self):
        """`en` must not fall through to the `en-XA` pseudo catalog."""
        self.assertNotEqual(resolve_catalog_tag(MANIFEST, "en"), "en-XA")

    def test_unknown_language_resolves_to_no_catalog(self):
        self.assertIsNone(resolve_catalog_tag(MANIFEST, "xx"))

    def test_empty_language_resolves_to_no_catalog(self):
        self.assertIsNone(resolve_catalog_tag(MANIFEST, ""))


class TestReadLocaleManifest(TestCase):
    """A missing or malformed manifest is read as no catalogs being known, so a stale or
    half-written build directory cannot take the interface down."""

    def setUp(self):
        read_locale_manifest.cache_clear()
        self.addCleanup(read_locale_manifest.cache_clear)

    def test_missing_manifest(self):
        """A manifest the static finder cannot locate."""
        with patch(MANIFEST_FINDER, return_value=None):
            self.assertEqual(read_locale_manifest(), {})

    def test_malformed_manifest(self):
        """A manifest that is not valid JSON."""
        with NamedTemporaryFile(mode="w", suffix=".json") as manifest_file:
            manifest_file.write("{not json")
            manifest_file.flush()
            with patch(MANIFEST_FINDER, return_value=manifest_file.name):
                self.assertEqual(read_locale_manifest(), {})

    def test_unexpected_manifest_shape(self):
        """A manifest holding valid JSON that is not an object."""
        with NamedTemporaryFile(mode="w", suffix=".json") as manifest_file:
            manifest_file.write("[]")
            manifest_file.flush()
            with patch(MANIFEST_FINDER, return_value=manifest_file.name):
                self.assertEqual(read_locale_manifest(), {})


class TestLocaleModulePreload(TestCase):
    """The template tag emits a modulepreload for the active locale's catalog."""

    def test_emits_modulepreload_for_active_locale(self):
        with patch(MANIFEST_LOADER, return_value=MANIFEST), translation.override("de"):
            html = locale_modulepreload()
        self.assertIn('rel="modulepreload"', html)
        self.assertIn("/static/dist/chunks/de.abc123.js", html)

    def test_emits_nothing_for_english(self):
        with patch(MANIFEST_LOADER, return_value=MANIFEST), translation.override("en"):
            self.assertEqual(locale_modulepreload(), "")

    def test_emits_nothing_without_manifest(self):
        with patch(MANIFEST_LOADER, return_value={}), translation.override("de"):
            self.assertEqual(locale_modulepreload(), "")
