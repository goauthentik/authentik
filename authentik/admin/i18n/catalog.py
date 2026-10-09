"""Custom locale catalog store"""

from collections.abc import Callable
from threading import Lock, local
from time import monotonic
from uuid import uuid4

from django.apps import apps
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from structlog.stdlib import get_logger

LOGGER = get_logger()

CACHE_KEY_VERSION = "goauthentik.io/admin/i18n/catalog_version"
# How often each process checks whether catalogs have been changed by another process
REFRESH_INTERVAL = 5.0

type Message = str | list[str]
type Messages = dict[str, Message]


def canonicalize_language(code: str) -> str:
    """Canonical casing of a language tag, so `de_de`, `de-DE` and `DE-de` compare equal
    (`de-DE`, `zh-Hans`, `es-419`)"""
    language, *subtags = code.strip().replace("_", "-").split("-")
    canonical = [language.lower()]
    for subtag in subtags:
        if len(subtag) == 4 and subtag.isalpha():  # noqa: PLR2004
            canonical.append(subtag.title())
        elif len(subtag) == 2 and subtag.isalpha():  # noqa: PLR2004
            canonical.append(subtag.upper())
        else:
            canonical.append(subtag.lower())
    return "-".join(canonical)


def catalog_query(language: str) -> Q:
    """Query for all catalogs applicable to `language`.

    `de-AT` uses catalogs for `de` and `de-AT`. A language without a region (Django
    activates `de`, while the web interface uses `de-DE`) additionally falls back to
    catalogs of any regional variant."""
    language = canonicalize_language(language)
    base = language.split("-", 1)[0]
    query = Q(locale=base) | Q(locale=language)
    if language == base:
        query |= Q(locale__startswith=f"{base}-")
    return query


def specificity(catalog_locale: str, language: str) -> int:
    """How closely a catalog's locale matches the requested language"""
    if catalog_locale == language:
        return 2
    if catalog_locale == language.split("-", 1)[0]:
        return 1
    return 0


class CatalogStore:
    """Per-process cache of custom messages, per language.

    Lookups happen on every gettext call, so messages are kept in memory and only
    re-checked against a version key in the cache every few seconds."""

    def __init__(self, refresh_interval: float = REFRESH_INTERVAL):
        self.refresh_interval = refresh_interval
        self._lock = Lock()
        self._local = local()
        self._messages: dict[str, Messages] = {}
        self._version: str | None = None
        self._next_check = 0.0

    def messages(self, language: str) -> Messages:
        """All custom messages for `language`"""
        language = canonicalize_language(language)
        if monotonic() >= self._next_check:
            self._guarded(self._check_version)
        messages = self._messages.get(language)
        if messages is None:
            messages = self._guarded(
                lambda: self._load(language),
                # Don't retry on every call, only after the next version check
                on_error=lambda: self._messages.setdefault(language, {}),
            )
        return messages or {}

    def lookup(self, language: str, message: str) -> Message | None:
        """Get the custom translation of `message`, if any"""
        return self.messages(language).get(message)

    def invalidate(self):
        """Signal all processes to reload their catalogs"""
        cache.set(CACHE_KEY_VERSION, uuid4().hex, timeout=None)
        self._messages = {}
        self._next_check = 0.0

    def _guarded[T](
        self, func: Callable[[], T], on_error: Callable[[], object] | None = None
    ) -> T | None:
        # Loading catalogs calls into the ORM, which may translate strings itself
        if getattr(self._local, "loading", False) or not apps.ready:
            return None
        # Another thread is already loading, don't wait for it
        if not self._lock.acquire(blocking=False):
            return None
        self._local.loading = True
        try:
            # Use a savepoint so a failing query doesn't break a surrounding transaction
            with transaction.atomic():
                return func()
        except Exception as exc:  # noqa: BLE001
            # Translating must never fail, e.g. before migrations have run, while the
            # current transaction is broken or when called from an async context.
            LOGGER.debug("Failed to load locale catalogs", exc=exc)
            # Force a reload with the next version check
            self._version = None
            if on_error:
                on_error()
            return None
        finally:
            self._local.loading = False
            self._lock.release()

    def _check_version(self):
        self._next_check = monotonic() + self.refresh_interval
        version = cache.get_or_set(CACHE_KEY_VERSION, lambda: uuid4().hex, timeout=None)
        if version != self._version:
            self._messages = {}
            self._version = version

    def _load(self, language: str) -> Messages:
        from authentik.admin.i18n.models import LocaleCatalog

        # Keep a reference, so results loaded while being invalidated are discarded
        loaded = self._messages
        catalogs = LocaleCatalog.objects.filter(catalog_query(language), enabled=True).values_list(
            "locale", "order", "name", "messages"
        )
        merged: Messages = {}
        # Least specific locale first, then by order, so later catalogs override earlier ones
        for _locale, _order, _name, messages in sorted(
            catalogs, key=lambda catalog: (specificity(catalog[0], language), *catalog[1:3])
        ):
            if isinstance(messages, dict):
                merged.update(messages)
        loaded[language] = merged
        return merged


CATALOG_STORE = CatalogStore()
