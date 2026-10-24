"""in_memory_cache tests"""

from unittest.mock import patch

from django.test import TestCase

from authentik.admin.models import SystemSettings
from authentik.root.cache import in_memory_cache, models_version


class TestInMemoryCache(TestCase):
    def test_version_check(self):
        """Fresh values are cached, expired ones are only refetched when the version changed"""
        calls = []
        version = [1]

        @in_memory_cache(key=lambda x: x, version=lambda: version[0], timeout=10)
        def counter(x):
            calls.append(x)
            return len(calls)

        with patch("authentik.root.cache.monotonic", return_value=0):
            self.assertEqual(counter(1), 1)
            self.assertEqual(counter(1), 1)
        with patch("authentik.root.cache.monotonic", return_value=100):
            # expired, but unchanged version keeps the value
            self.assertEqual(counter(1), 1)
        version[0] = 2
        with patch("authentik.root.cache.monotonic", return_value=200):
            self.assertEqual(counter(1), 2)
        counter.cache_clear()
        self.assertEqual(counter(1), 3)

    def test_models_version(self):
        """models_version changes on save and on queryset updates"""
        before = models_version(SystemSettings)
        SystemSettings.objects.get(pk=True).save()
        after_save = models_version(SystemSettings)
        self.assertNotEqual(before, after_save)
        SystemSettings.objects.update(avatars="none")
        self.assertNotEqual(after_save, models_version(SystemSettings))
