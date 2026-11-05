from django.test import TestCase

from authentik.admin.models import SystemSettings
from authentik.admin.utils import get_system_settings


class TestSystemSettingsCache(TestCase):
    def test_cached(self):
        """Settings are cached across calls"""
        self.assertIs(get_system_settings(), get_system_settings())

    def test_cleared_on_save(self):
        """Saving the settings drops the cached instance"""
        first = get_system_settings()
        settings = SystemSettings.objects.get(pk=True)
        settings.avatars = "none"
        settings.save()
        second = get_system_settings()
        self.assertIsNot(first, second)
        self.assertEqual(second.avatars, "none")
