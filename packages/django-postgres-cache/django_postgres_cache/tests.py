"""Tests for django_postgres_cache.backend"""

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
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


class CountKeysTests(TestCase):
    """Counts use the same matching and expiry rules as key listing."""

    def test_matching_keys(self):
        cache.set_many({"count/first": 1, "count/last": 2}, version=7)
        cache.set("count/expired", 3, timeout=0, version=7)
        cache.set("count/other-version", 4, version=8)
        for pattern, expected in (
            ("count/first", 1),
            ("count/*", 3),
            ("count/*st", 2),
            ("count/missing*", 0),
        ):
            with self.subTest(pattern=pattern):
                self.assertEqual(cache.count_keys(pattern, version=7), expected)
                self.assertEqual(len(cache.keys(pattern, version=7)), expected)
        self.assertEqual(cache.count_keys("count/*", version=8), 1)


class MakeExpiryTests(SimpleTestCase):
    """Regression tests for _make_expiry with timeout=None.

    Previously, timeout=None returned datetime.max (naive) even when USE_TZ=True,
    causing Django to emit a RuntimeWarning when saving to CacheEntry.expires.
    """

    @override_settings(USE_TZ=True)
    def test_timeout_none_is_aware_when_use_tz_enabled(self) -> None:
        """timeout=None must return a timezone-aware datetime when USE_TZ=True."""
        expiry = _cache()._make_expiry(None)

        self.assertTrue(is_aware(expiry), "Expected a timezone-aware datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=False)
    def test_timeout_none_is_naive_when_use_tz_disabled(self) -> None:
        """timeout=None must return a naive datetime when USE_TZ=False."""
        expiry = _cache()._make_expiry(None)

        self.assertTrue(is_naive(expiry), "Expected a naive datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=True)
    def test_timeout_value_is_aware_when_use_tz_enabled(self) -> None:
        """A numeric timeout must also return a timezone-aware datetime when USE_TZ=True."""
        expiry = _cache()._make_expiry(300)

        self.assertTrue(is_aware(expiry), "Expected a timezone-aware datetime")
        self.assertEqual(expiry.microsecond, 0)

    @override_settings(USE_TZ=False)
    def test_timeout_value_is_naive_when_use_tz_disabled(self) -> None:
        """A numeric timeout must return a naive datetime when USE_TZ=False."""
        expiry = _cache()._make_expiry(300)

        self.assertTrue(is_naive(expiry), "Expected a naive datetime")
        self.assertEqual(expiry.microsecond, 0)
