"""Custom locale catalog store"""

from collections.abc import Callable
from threading import Lock, local
from time import monotonic
from uuid import UUID, uuid4

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


def catalog_query(language: str, prefix: str = "") -> Q:
    """Query for all catalogs applicable to `language`.

    `de-AT` uses catalogs for `de` and `de-AT`. A language without a region (Django
    activates `de`, while the web interface uses `de-DE`) additionally falls back to
    catalogs of any regional variant."""
    language = canonicalize_language(language)
    base = language.split("-", 1)[0]
    field = f"{prefix}locale"
    query = Q(**{field: base}) | Q(**{field: language})
    if language == base:
        query |= Q(**{f"{field}__startswith": f"{base}-"})
    return query


def specificity(catalog_locale: str, language: str) -> int:
    """How closely a catalog's locale matches the requested language"""
    if catalog_locale == language:
        return 2
    if catalog_locale == language.split("-", 1)[0]:
        return 1
    return 0


class CatalogStore:
    """Per-process cache of custom messages, per brand and language.

    Lookups happen on every gettext call, so messages are kept in memory and only
    re-checked against a version key in the cache every few seconds."""

    def __init__(self, refresh_interval: float = REFRESH_INTERVAL):
        self.refresh_interval = refresh_interval
        self._lock = Lock()
        self._local = local()
        self._messages: dict[tuple[UUID, str], Messages] = {}
        # Primary key of the default brand, used outside of requests
        self._default_brand: UUID | None = None
        self._default_brand_loaded = False
        self._version: str | None = None
        self._next_check = 0.0

    def messages(self, language: str, brand_pk: UUID | None = None) -> Messages:
        """All custom messages for `language` of the given brand, by default the brand of the
        current request, or the default brand outside of requests"""
        language = canonicalize_language(language)
        if monotonic() >= self._next_check:
            self._guarded(self._check_version)
        brand_pk = brand_pk or self._current_brand()
        if not brand_pk:
            return {}
        key = (brand_pk, language)
        messages = self._messages.get(key)
        if messages is None:
            messages = self._guarded(
                lambda: self._load(key),
                # Don't retry on every call, only after the next version check
                on_error=lambda: self._messages.setdefault(key, {}),
            )
        return messages or {}

    def lookup(self, language: str, message: str) -> Message | None:
        """Get the custom translation of `message`, if any"""
        return self.messages(language).get(message)

    def _current_brand(self) -> UUID | None:
        from authentik.brands.utils import CTX_BRAND

        brand = CTX_BRAND.get()
        if brand:
            return brand.pk
        if not self._default_brand_loaded:
            self._guarded(self._load_default_brand)
        return self._default_brand

    def _load_default_brand(self):
        from authentik.brands.models import Brand

        # Also when loading fails, to only retry after the next version check
        self._default_brand_loaded = True
        self._default_brand = (
            Brand.objects.filter(default=True).values_list("pk", flat=True).first()
        )

    def invalidate(self):
        """Signal all processes to reload their catalogs"""
        cache.set(CACHE_KEY_VERSION, uuid4().hex, timeout=None)
        self._messages = {}
        self._default_brand_loaded = False
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
            self._default_brand_loaded = False
            self._version = version

    def _load(self, key: tuple[UUID, str]) -> Messages:
        from authentik.admin.i18n.models import BrandLocaleCatalog

        brand_pk, language = key
        # Keep a reference, so results loaded while being invalidated are discarded
        loaded = self._messages
        bindings = BrandLocaleCatalog.objects.filter(
            catalog_query(language, prefix="catalog__"),
            brand_id=brand_pk,
            catalog__enabled=True,
        ).values_list("catalog__locale", "order", "catalog__name", "catalog__messages")
        merged: Messages = {}
        # Least specific locale first, then by order, so later catalogs override earlier ones
        for _locale, _order, _name, messages in sorted(
            bindings, key=lambda binding: (specificity(binding[0], language), *binding[1:3])
        ):
            if isinstance(messages, dict):
                merged.update(messages)
        loaded[key] = merged
        return merged


CATALOG_STORE = CatalogStore()
