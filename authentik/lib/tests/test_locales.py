"""Tests for the canonical locale registry."""

from gettext import GNUTranslations
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import TestCase
from django.utils import translation
from django.utils.translation import to_locale

from authentik.lib.locales import (
    REGISTRY_PATH,
    Locale,
    RegistryError,
    catalog_locales,
    known_catalog_names,
    known_xliff_names,
    language_mapping,
    load_registry,
    shipped_locales,
    target_locales,
)


def write_registry(directory: str, body: str) -> Path:
    path = Path(directory) / "locales.yaml"
    path.write_text(body, encoding="utf-8")
    return path


class TestLocaleRegistry(TestCase):
    """The registry file itself."""

    def test_loads(self):
        """The shipped registry parses and validates."""
        self.assertGreater(len(load_registry()), 0)

    def test_catalog_matches_django_resolution(self):
        """Every catalog directory is one Django can actually resolve.

        This is the invariant that makes a `locale/zh-Hans` style directory —
        which Django silently ignores — impossible to reintroduce.
        """
        for locale in catalog_locales():
            with self.subTest(tag=locale.tag):
                self.assertEqual(locale.django, to_locale(locale.tag))

    def test_source_locale_ships(self):
        """English is present and shipped."""
        tags = target_locales()
        self.assertIn("en", tags)

    def test_pseudo_locale_has_no_backend(self):
        """en-XA is frontend-only and not translated upstream."""
        (pseudo,) = [locale for locale in load_registry() if locale.tag == "en-XA"]
        self.assertIsNone(pseudo.django)
        self.assertIsNone(pseudo.transifex)
        self.assertIsNone(pseudo.catalog_path)
        self.assertTrue(pseudo.ship)

    def test_language_mapping_covers_unshipped(self):
        """Unshipped locales still get a mapping, so they land on canonical paths."""
        mapping = language_mapping()
        unshipped = [
            locale for locale in load_registry() if not locale.ship and locale.transifex is not None
        ]
        self.assertGreater(len(unshipped), 0)
        for locale in unshipped:
            with self.subTest(tag=locale.tag):
                self.assertEqual(mapping[locale.transifex], locale.tag)

    def test_language_mapping_excludes_locally_generated(self):
        """A locale with no upstream code contributes no mapping entry."""
        self.assertNotIn(None, language_mapping())
        self.assertNotIn("en-XA", language_mapping().values())

    def test_shipped_is_a_subset(self):
        shipped = {locale.tag for locale in shipped_locales()}
        everything = {locale.tag for locale in load_registry()}
        self.assertTrue(shipped.issubset(everything))
        self.assertLess(len(shipped), len(everything))

    def test_known_names(self):
        self.assertIn("pt-BR.xlf", known_xliff_names())
        self.assertIn("pt_BR", known_catalog_names())
        self.assertNotIn("pt_BR.xlf", known_xliff_names())
        self.assertNotIn("pt-BR", known_catalog_names())

    def test_paths(self):
        (locale,) = [row for row in load_registry() if row.tag == "pt-BR"]
        self.assertEqual(locale.xliff_path, Path("web/xliff/pt-BR.xlf"))
        self.assertEqual(locale.catalog_path, Path("locale/pt_BR"))

    def test_registry_file_exists(self):
        self.assertTrue(REGISTRY_PATH.is_file())


class TestCatalogsLoad(TestCase):
    """Every shipping catalog is one Django can actually find and read.

    `locale/zh-Hans` sat in the tree for months looking correct while Django
    resolved the tag to `zh_Hans`, found nothing, and silently served English.
    Nothing failed, so nobody noticed. Comparing directory names would not have
    caught it — only asking Django for a translation does.
    """

    def catalog_root(self) -> Path:
        (root,) = settings.LOCALE_PATHS
        return Path(root)

    def test_shipping_catalogs_resolve(self):
        checked = 0

        for locale in shipped_locales():
            if locale.django is None:
                continue

            # A catalog sitting at the tag rather than the Django locale name is
            # exactly the failure this test exists for. Assert it before the
            # lookup below, which would otherwise just skip the missing file.
            if locale.tag != locale.django:
                with self.subTest(tag=locale.tag, stray=locale.tag):
                    self.assertFalse(
                        (self.catalog_root() / locale.tag).exists(),
                        f"locale/{locale.tag} is named for the language tag, but "
                        f"Django looks for locale/{locale.django}. Run "
                        "`make locales-normalize`.",
                    )

            compiled = self.catalog_root() / locale.django / "LC_MESSAGES/django.mo"
            if not compiled.is_file():
                continue

            with compiled.open("rb") as handle:
                catalog = GNUTranslations(handle)

            translated = [
                (msgid, msgstr)
                for msgid, msgstr in catalog._catalog.items()
                if isinstance(msgid, str) and msgid and msgstr and msgid != msgstr
            ]
            if not translated:
                # A registered language nobody has translated yet is fine.
                continue

            msgid, expected = translated[0]
            with self.subTest(tag=locale.tag, catalog=locale.django):
                with translation.override(locale.tag):
                    self.assertEqual(
                        translation.gettext(msgid),
                        expected,
                        f"locale/{locale.django} exists and has translations, but "
                        f"Django serves English for {locale.tag}. The catalog "
                        f"directory must be named {to_locale(locale.tag)}.",
                    )
            checked += 1

        self.assertGreater(checked, 0, "no compiled catalogs were checked")

    def test_chinese_specifically(self):
        """The regression that motivated this test."""
        for tag, catalog in (("zh-Hans", "zh_Hans"), ("zh-Hant", "zh_Hant")):
            with self.subTest(tag=tag):
                self.assertTrue((self.catalog_root() / catalog).is_dir())
                self.assertFalse((self.catalog_root() / tag).exists())


class TestRegistryValidation(TestCase):
    """The invariants the loader refuses to load without."""

    def load(self, body: str) -> tuple[Locale, ...]:
        with TemporaryDirectory() as directory:
            return load_registry(write_registry(directory, body))

    def test_rejects_unresolvable_catalog(self):
        """A hyphenated catalog directory is refused outright."""
        with self.assertRaises(RegistryError) as caught:
            self.load(
                "locales:\n"
                "  - tag: zh-Hans\n"
                "    django: zh-Hans\n"
                "    transifex: zh-Hans\n"
                "    ship: true\n"
            )
        self.assertIn("zh_Hans", str(caught.exception))

    def test_rejects_duplicate_tag(self):
        with self.assertRaises(RegistryError) as caught:
            self.load(
                "locales:\n"
                "  - tag: de-DE\n"
                "    django: de_DE\n"
                "    transifex: de_DE\n"
                "    ship: true\n"
                "  - tag: de-DE\n"
                "    django: de_DE\n"
                "    transifex: de_AT\n"
                "    ship: true\n"
            )
        self.assertIn("duplicate tag", str(caught.exception))

    def test_rejects_colliding_upstream_code(self):
        """Two tags cannot claim one upstream code; language_mapping is a dict."""
        with self.assertRaises(RegistryError) as caught:
            self.load(
                "locales:\n"
                "  - tag: ar\n"
                "    django: ar\n"
                "    transifex: ar_AA\n"
                "    ship: true\n"
                "  - tag: ar-AA\n"
                "    django: ar_AA\n"
                "    transifex: ar_AA\n"
                "    ship: false\n"
            )
        self.assertIn("more than one tag", str(caught.exception))

    def test_rejects_empty(self):
        with self.assertRaises(RegistryError):
            self.load("locales: []\n")

    def test_rejects_missing_key(self):
        with self.assertRaises(RegistryError):
            self.load("languages: []\n")

    def test_accepts_null_catalog(self):
        locales = self.load(
            "locales:\n"
            "  - tag: en-XA\n"
            "    django: null\n"
            "    transifex: null\n"
            "    ship: true\n"
        )
        self.assertEqual(len(locales), 1)
        self.assertIsNone(locales[0].catalog_path)
