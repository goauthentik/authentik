"""Backend translation catalog tests"""

from gettext import GNUTranslations
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import translation
from django.utils.translation import to_locale
from yaml import safe_load

REPO_ROOT = Path(__file__).resolve().parents[3]


def registry() -> list[dict]:
    return safe_load((REPO_ROOT / "locales.yaml").read_text())["locales"]


class TestLocales(SimpleTestCase):
    """Every catalog in locales.yaml must be where Django looks for it"""

    def test_django_directory_names(self):
        """The registry's directory name is the one Django derives from the tag"""
        for row in registry():
            if row["django"]:
                self.assertEqual(row["django"], to_locale(row["tag"]), row["tag"])

    def test_shipped_catalogs_load(self):
        """Activating a shipped tag serves translations from its catalog"""
        for row in registry():
            if not row["ship"] or row["django"] in (None, "en"):
                continue
            with self.subTest(row["tag"]):
                mo = REPO_ROOT / "locale" / row["django"] / "LC_MESSAGES" / "django.mo"
                with mo.open("rb") as file:
                    catalog = GNUTranslations(file)._catalog
                messages = {
                    msgid: msgstr
                    for msgid, msgstr in catalog.items()
                    # Plural and contextual entries are skipped. So are entries that match
                    # their msgid, which an English fallback would also satisfy.
                    if isinstance(msgid, str)
                    and msgid
                    and "\x04" not in msgid
                    and msgstr
                    and msgstr != msgid
                }
                self.assertTrue(messages)
                with translation.override(row["tag"]):
                    served = sum(
                        translation.gettext(msgid) == msgstr for msgid, msgstr in messages.items()
                    )
                # Django's own catalogs may override a few common strings.
                self.assertGreater(served / len(messages), 0.5)


def load_script() -> ModuleType:
    spec = spec_from_file_location("locales_script", REPO_ROOT / "scripts" / "locales.py")
    if not spec or not spec.loader:
        raise ImportError("scripts/locales.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


XLIFF = """<?xml version="1.0" ?><xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
<file target-language="{language}" source-language="en" original="lit-localize-inputs">
<body>
<trans-unit id="s1">
  <source>Save</source>
  <target>{target}</target>
</trans-unit>
</body>
</file>
</xliff>
"""

PO = """msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: {language}\\n"

msgid "Save"
msgstr "{target}"
"""


class TestLocalesScript(SimpleTestCase):
    """scripts/locales.py normalization, against a scratch tree"""

    def setUp(self):
        self.script = load_script()
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.locale = root / "locale"
        self.xliff = root / "web" / "xliff"
        self.xliff.mkdir(parents=True)
        self.locale.mkdir()
        patcher = patch.multiple(
            self.script, ROOT=root, LOCALE_DIR=self.locale, XLIFF_DIR=self.xliff
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.registry = self.script.load_registry()

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_canonical_xliff_language_is_normalized(self):
        """A mapped Transifex export keeps its alias target-language; normalize fixes it"""
        for tag, alias in (("ar", "ar-AA"), ("nb-NO", "no-NO")):
            self.write(self.xliff / f"{tag}.xlf", XLIFF.format(language=alias, target="x"))
        self.script.normalize_xliff_files(self.registry)
        for tag in ("ar", "nb-NO"):
            self.assertEqual(self.script.xliff_language(self.xliff / f"{tag}.xlf"), tag)

    def test_merge_keeps_other_catalogs(self):
        """Merging a Transifex directory moves files it doesn't merge"""
        self.write(
            self.locale / "fr_FR/LC_MESSAGES/django.po", PO.format(language="fr_FR", target="Old")
        )
        self.write(
            self.locale / "fr-FR/LC_MESSAGES/django.po", PO.format(language="fr-FR", target="New")
        )
        self.write(
            self.locale / "fr-FR/LC_MESSAGES/djangojs.po", PO.format(language="fr-FR", target="JS")
        )
        _, errors = self.script.normalize_locale_dirs(self.registry)
        self.assertEqual(errors, [])
        self.assertFalse((self.locale / "fr-FR").exists())
        merged = (self.locale / "fr_FR/LC_MESSAGES/django.po").read_text()
        self.assertIn('msgstr "New"', merged)
        self.assertIn('"Language: fr_FR\\n"', merged)
        self.assertTrue((self.locale / "fr_FR/LC_MESSAGES/djangojs.po").exists())
        self.assertTrue((self.locale / "fr_FR/LC_MESSAGES/django.mo").exists())

    def test_merge_conflict_deletes_nothing(self):
        """A file that would overwrite different content stops the merge"""
        self.write(
            self.locale / "fr_FR/LC_MESSAGES/django.po", PO.format(language="fr_FR", target="Old")
        )
        self.write(self.locale / "fr_FR/NOTES", "canonical")
        incoming = self.write(self.locale / "fr-FR/NOTES", "incoming")
        _, errors = self.script.normalize_locale_dirs(self.registry)
        self.assertEqual(len(errors), 1)
        self.assertEqual(incoming.read_text(), "incoming")
