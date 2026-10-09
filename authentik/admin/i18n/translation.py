"""Overlay custom locale catalogs on top of Django's translations"""

from django.utils.translation import trans_real

from authentik.admin.i18n.catalog import CATALOG_STORE


class CatalogTranslation(trans_real.DjangoTranslation):
    """Django translation which prefers messages from custom locale catalogs.

    All of Django's translation functions (gettext, pgettext, ngettext, npgettext and their
    lazy variants) end up calling gettext or ngettext on this object."""

    def gettext(self, message: str) -> str:
        custom = CATALOG_STORE.lookup(self.language(), message)
        if isinstance(custom, list):
            custom = custom[0] if custom else None
        if custom:
            return custom
        return super().gettext(message)

    def ngettext(self, msgid1: str, msgid2: str, n: int) -> str:
        custom = CATALOG_STORE.lookup(self.language(), msgid1)
        if isinstance(custom, list) and custom:
            # Plural forms, indexed by the language's plural rule
            index = int(self.plural(n))
            return custom[min(max(index, 0), len(custom) - 1)]
        if n == 1 and isinstance(custom, str) and custom:
            return custom
        if n != 1:
            custom_plural = CATALOG_STORE.lookup(self.language(), msgid2)
            if isinstance(custom_plural, str) and custom_plural:
                return custom_plural
        return super().ngettext(msgid1, msgid2, n)


def install_catalog_translation():
    """Make Django use `CatalogTranslation` for all languages"""
    trans_real.DjangoTranslation = CatalogTranslation
    # Drop translations that might have been created before
    trans_real._translations = {}
    trans_real._default = None
