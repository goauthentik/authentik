"""Tests for ``authentik.api.throttle.LocalAnonRateThrottle``."""

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase

from authentik.api.throttle import LocalAnonRateThrottle


class TestLocalAnonRateThrottle(TestCase):
    """The throttle must use the in-process LocMem cache, not the default
    (PG-backed) cache — otherwise every API request incurs 2 cache ops
    against PG just to make the throttle decision."""

    def test_throttle_uses_locmem_cache_backend(self):
        """The throttle's ``cache`` attribute is the ``throttle`` alias."""
        throttle = LocalAnonRateThrottle()
        self.assertIs(throttle.cache, caches["throttle"])

    def test_throttle_cache_alias_is_locmem(self):
        """The ``throttle`` cache alias is backed by LocMemCache."""
        self.assertEqual(
            settings.CACHES["throttle"]["BACKEND"],
            "django.core.cache.backends.locmem.LocMemCache",
        )

    def test_throttle_cache_has_sufficient_max_entries(self):
        """``MAX_ENTRIES`` is high enough to avoid LRU-evicting active
        counters under realistic IP diversity."""
        max_entries = settings.CACHES["throttle"].get("OPTIONS", {}).get("MAX_ENTRIES", 300)
        self.assertGreaterEqual(max_entries, 1000)

    def test_throttle_counter_isolated_from_default_cache(self):
        """Throttle writes go to the LocMem cache, not the default cache."""
        throttle = LocalAnonRateThrottle()
        test_key = "test-throttle-isolation-key"
        throttle.cache.set(test_key, ["a", "b", "c"], 30)
        self.assertEqual(throttle.cache.get(test_key), ["a", "b", "c"])
        self.assertIsNone(caches["default"].get(test_key))
        throttle.cache.delete(test_key)

    def test_default_throttle_class_is_local_throttle(self):
        """REST_FRAMEWORK uses ``LocalAnonRateThrottle``, not DRF's stock one."""
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"],
            ["authentik.api.throttle.LocalAnonRateThrottle"],
        )
