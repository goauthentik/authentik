"""i18n template tags"""

from django import template
from django.utils.translation import get_language

from authentik.admin.i18n.catalog import CATALOG_STORE, canonicalize_language

register = template.Library()


@register.simple_tag()
def custom_locale_catalog() -> dict:
    """Custom messages for the active language, so the web interface doesn't have to
    fetch them before rendering"""
    locale = canonicalize_language(get_language() or "")
    messages = {
        source: translation
        for source, translation in CATALOG_STORE.messages(locale).items()
        if isinstance(translation, str)
    }
    return {"locale": locale, "messages": messages}
