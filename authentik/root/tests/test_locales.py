"""Backend translation catalog tests"""

from gettext import GNUTranslations
from pathlib import Path

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
                    if isinstance(msgid, str) and msgid and "\x04" not in msgid and msgstr
                }
                self.assertTrue(messages)
                with translation.override(row["tag"]):
                    served = sum(
                        translation.gettext(msgid) == msgstr for msgid, msgstr in messages.items()
                    )
                # Django's own catalogs may override a few common strings.
                self.assertGreater(served / len(messages), 0.5)
