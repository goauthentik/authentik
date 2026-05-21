"""Tests for django_postgres_cache.backend"""

from django.test import SimpleTestCase, override_settings
from django.utils.timezone import is_aware, is_naive

from django_postgres_cache.backend import DatabaseCache


def _cache() -> DatabaseCache:
    return DatabaseCache(
        "django_postgres_cache_cacheentry",
        {
            "TIMEOUT": 300,
            "OPTIONS": {},
            "KEY_PREFIX": "",
            "VERSION": 1,
            "KEY_FUNCTION": "django.core.cache.backends.base.default_key_func",
            "REVERSE_KEY_FUNCTION": "django.core.cache.backends.base.default_key_func",
        },
    )


class BaseSetExpiryTests(SimpleTestCase):
    """Regression tests for _base_set_expiry with timeout=None.

    Previously, timeout=None returned datetime.max (naive) even when USE_TZ=True,
    causing Django to emit a RuntimeWarning when saving to CacheEntry.expires.
    """

    @override_settings(USE_TZ=True)
    def test_timeout_none_is_aware_when_use_tz_enabled(self):
        """timeout=None must return a timezone-aware datetime when USE_TZ=True."""
        expiry = _cache()._base_set_expiry(None)

        self.assertTrue(is_aware(expiry), "Expected a timezone-aware datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=False)
    def test_timeout_none_is_naive_when_use_tz_disabled(self):
        """timeout=None must return a naive datetime when USE_TZ=False."""
        expiry = _cache()._base_set_expiry(None)

        self.assertTrue(is_naive(expiry), "Expected a naive datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=True)
    def test_timeout_value_is_aware_when_use_tz_enabled(self):
        """A numeric timeout must also return a timezone-aware datetime when USE_TZ=True."""
        expiry = _cache()._base_set_expiry(300)

        self.assertTrue(is_aware(expiry), "Expected a timezone-aware datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=True)
    def test_timeout_none_produces_no_runtime_warning(self):
        """No RuntimeWarning should be emitted for timeout=None with USE_TZ=True."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            # Must not raise
            _cache()._base_set_expiry(None)
