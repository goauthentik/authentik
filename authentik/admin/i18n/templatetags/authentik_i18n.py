"""i18n template tags"""

from django import template
from django.utils.translation import get_language

from authentik.admin.i18n.catalog import CATALOG_STORE, canonicalize_language

register = template.Library()


@register.simple_tag(takes_context=True)
def custom_locale_catalog(context: template.Context) -> dict:
    """Custom messages of the current brand for the active language, so the web interface
    doesn't have to fetch them before rendering"""
    locale = canonicalize_language(get_language() or "")
    brand = getattr(context.get("request"), "brand", None)
    messages = {
        source: translation
        for source, translation in CATALOG_STORE.messages(
            locale, brand_pk=brand.pk if brand else None
        ).items()
        if isinstance(translation, str)
    }
    return {"locale": locale, "messages": messages}
