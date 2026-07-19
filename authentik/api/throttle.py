"""Custom DRF throttle classes for authentik."""

from django.core.cache import caches
from rest_framework.throttling import AnonRateThrottle


class LocalAnonRateThrottle(AnonRateThrottle):
    """Anonymous IP-based rate throttle backed by an in-process cache.

    DRF's stock ``AnonRateThrottle`` uses the default cache. With authentik's
    PG-backed default cache, every API request issues a ``cache.get`` +
    ``cache.set`` against PG just to make the throttle decision — the
    protective layer amplifies DB load under flood.

    Points the throttle's cache at the ``throttle`` LocMemCache alias instead.
    Counters are per-process (per gunicorn worker)
    """

    cache = caches["throttle"]
