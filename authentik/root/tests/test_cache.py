"""in_memory_cache tests"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.root.cache import INVALIDATION_GROUP, in_memory_cache


class TestInMemoryCache(TestCase):
    def test_stale_while_revalidate(self):
        """Fresh values are cached, stale values are served while refreshed in the background"""
        calls = []
        cache = in_memory_cache(key=lambda x: x, timeout=10)

        @cache
        def counter(x):
            calls.append(x)
            return len(calls)

        with patch("authentik.root.cache.monotonic", return_value=0):
            self.assertEqual(counter(1), 1)
            self.assertEqual(counter(1), 1)
        with patch("authentik.root.cache.monotonic", return_value=100):
            # stale value returned immediately, refreshed once in the background
            self.assertEqual(counter(1), 1)
            counter(1)
            # single worker runs tasks in order, so this waits for queued refreshes
            cache._executor.submit(lambda: None).result()
            self.assertEqual(counter(1), 2)
            self.assertEqual(len(calls), 2)
        counter.cache_clear()
        self.assertEqual(counter(1), 3)

    def test_invalidate(self):
        """invalidate clears locally and notifies other processes after commit"""
        calls = []

        @in_memory_cache(key=lambda: None)
        def counter():
            calls.append(None)
            return len(calls)

        layer = MagicMock()
        counter()
        with (
            patch("authentik.root.cache.get_channel_layer", return_value=layer),
            self.captureOnCommitCallbacks(execute=True),
        ):
            counter.invalidate()
            layer.group_send_blocking.assert_not_called()
        layer.group_send_blocking.assert_called_once_with(
            INVALIDATION_GROUP,
            {"type": "cache.invalidate", "name": f"{__name__}.{counter.__qualname__}"},
        )
        self.assertEqual(counter(), 2)
