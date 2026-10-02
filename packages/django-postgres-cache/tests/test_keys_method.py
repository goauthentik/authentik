"""Tests for ``DatabaseCache.keys`` glob-to-SQL translation.

``cache.keys("prefix*")`` must use ``__startswith`` (LIKE), not the regex
path. Pure unit tests — ``CacheEntry.objects`` is mocked.
"""

from typing import Any, cast
from unittest import TestCase, mock

from django_postgres_cache.backend import DatabaseCache


def _make_cache() -> DatabaseCache:
    """Construct a ``DatabaseCache`` without Django settings or a real DB."""
    cache = DatabaseCache.__new__(DatabaseCache)
    cache.key_prefix = ""
    cache.version = 1
    cache.key_func = lambda key, key_prefix, version: f":{version}:{key}"
    # Reverse-key is not invoked in these tests (filter mocks return []), so
    # an identity function is enough.
    cache.reverse_key_func = lambda k: k
    return cache


class TestKeysGlobToLookup(TestCase):
    """The SQL lookup chosen for each glob pattern shape."""

    def _captured_filter_kwargs(self, pattern: str) -> dict[str, Any]:
        """Run ``cache.keys(pattern)`` and return the kwargs passed to
        ``CacheEntry.objects.filter(...)``."""
        cache = _make_cache()
        with mock.patch("django_postgres_cache.backend.CacheEntry") as mock_entry:
            mock_entry.objects.filter.return_value.values_list.return_value = []
            cache.keys(pattern)
            self.assertEqual(mock_entry.objects.filter.call_count, 1)
            return cast(dict[str, Any], mock_entry.objects.filter.call_args.kwargs)

    def test_simple_prefix_glob_uses_startswith(self) -> None:
        """``cache.keys("foo*")`` uses ``__startswith``, not ``__regex``."""
        kwargs = self._captured_filter_kwargs("foo*")
        self.assertIn("cache_key__startswith", kwargs)
        self.assertNotIn("cache_key__regex", kwargs)
        self.assertNotIn("cache_key", kwargs)

    def test_realistic_authentik_prefix_glob_uses_startswith(self) -> None:
        """The actual hot-query pattern from the bug report uses ``__startswith``."""
        kwargs = self._captured_filter_kwargs("goauthentik.io/policies/app_access/*")
        self.assertIn("cache_key__startswith", kwargs)
        self.assertNotIn("cache_key__regex", kwargs)

    def test_exact_match_uses_equality(self) -> None:
        """No-wildcard patterns use primary-key equality."""
        kwargs = self._captured_filter_kwargs("exact")
        self.assertIn("cache_key", kwargs)
        self.assertNotIn("cache_key__startswith", kwargs)
        self.assertNotIn("cache_key__regex", kwargs)

    def test_complex_glob_falls_back_to_regex(self) -> None:
        """Multiple wildcards or non-suffix wildcards fall back to ``__regex``."""
        kwargs = self._captured_filter_kwargs("foo*bar*")
        self.assertIn("cache_key__regex", kwargs)
        self.assertNotIn("cache_key__startswith", kwargs)

    def test_leading_wildcard_falls_back_to_regex(self) -> None:
        """A leading wildcard cannot reduce to LIKE — fall back to ``__regex``."""
        kwargs = self._captured_filter_kwargs("*foo")
        self.assertIn("cache_key__regex", kwargs)
        self.assertNotIn("cache_key__startswith", kwargs)
