"""authentik core tags"""

from functools import lru_cache
from json import JSONDecodeError, loads

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static as static_loader
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from authentik import authentik_full_version

register = template.Library()

LOCALE_MANIFEST_PATH = "dist/manifest.json"
# Neither the source locale nor the pseudo-locale ship a catalog worth preloading.
SOURCE_LANGUAGE = "en"
PSEUDO_LOCALE = "en-xa"


@register.simple_tag()
def versioned_script(path: str) -> str:
    """Wrapper around {% static %} tag that supports setting the version"""
    return static_loader(path.replace("%v", authentik_full_version()))


@lru_cache
def read_locale_manifest() -> dict[str, str]:
    """Read the manifest emitted by the web build, mapping each locale tag to its
    content-hashed catalog chunk. A missing or malformed manifest is read as no catalogs
    being known, so the interface still renders, just without the preload."""
    result = finders.find(LOCALE_MANIFEST_PATH)
    if not result:
        return {}
    try:
        with open(result, encoding="utf8") as _file:
            manifest = loads(_file.read())
    except OSError, JSONDecodeError:
        return {}
    if not isinstance(manifest, dict):
        return {}
    return manifest


def resolve_catalog_tag(manifest: dict[str, str], language_code: str | None) -> str | None:
    """Map an active language code to a catalog tag in the manifest, mirroring the web
    client's best match: an exact (case-insensitive) tag wins, otherwise the first catalog
    sharing the base language."""
    if not language_code:
        return None
    normalized = language_code.lower()
    by_language_code = {tag.lower(): tag for tag in manifest}
    if normalized in by_language_code:
        return by_language_code[normalized]
    base_language = normalized.split("-", 1)[0]
    if base_language == SOURCE_LANGUAGE:
        return None
    for lowered, tag in by_language_code.items():
        if lowered == PSEUDO_LOCALE:
            continue
        if lowered.split("-", 1)[0] == base_language:
            return tag
    return None


@register.simple_tag()
def locale_modulepreload() -> str:
    """Preload the active locale's catalog chunk, so the browser fetches it before the
    entry bundle boots instead of after, removing the flash of untranslated content.
    Emits nothing for the source locale, or when the build manifest is unavailable."""
    manifest = read_locale_manifest()
    tag = resolve_catalog_tag(manifest, get_language())
    if not tag:
        return ""
    href = static_loader(f"dist/{manifest[tag]}")
    # href comes from our own build manifest, not from user input.
    return mark_safe(f'<link rel="modulepreload" href="{href}">')  # nosec
