"""Tests for backfilling base_url during the system settings reconcile"""

from django.apps import apps
from django.test import TestCase

from authentik.admin.utils import get_system_settings
from authentik.blueprints.tests import reconcile_app
from authentik.events.logs import capture_logs
from authentik.lib.config import CONFIG
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostConfig


class TestBaseURLBackfill(TestCase):
    """The system settings reconcile seeds base_url from the config value or the embedded
    outpost host"""

    def setUp(self):
        super().setUp()
        self.settings = get_system_settings()
        self.settings.base_url = ""
        self.settings.save()

    @reconcile_app("authentik_outposts")
    def test_backfill_from_outpost(self):
        """base_url is backfilled from the embedded outpost host, without a trailing slash"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com/")
        outpost.save()
        with CONFIG.patch("web.base_url", ""):
            apps.get_app_config("authentik_admin").system_settings()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.base_url, "https://outpost.example.com")

    @reconcile_app("authentik_outposts")
    def test_backfill_from_config(self):
        """The AUTHENTIK_WEB__BASE_URL config value takes precedence over the outpost host"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        with CONFIG.patch("web.base_url", "https://config.example.com"):
            apps.get_app_config("authentik_admin").system_settings()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.base_url, "https://config.example.com")

    def test_backfill_does_not_overwrite(self):
        """A configured base_url is never overwritten by the backfill"""
        self.settings.base_url = "https://set.example.com"
        self.settings.save()
        with CONFIG.patch("web.base_url", "https://config.example.com"):
            apps.get_app_config("authentik_admin").system_settings()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.base_url, "https://set.example.com")

    @reconcile_app("authentik_outposts")
    def test_backfill_discards_invalid_outpost_host(self):
        """An outpost host the settings API would reject is discarded rather than written,
        since the backfill's `.update()` skips field validation"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="outpost.example.com")
        outpost.save()
        with CONFIG.patch("web.base_url", ""), capture_logs() as logs:
            apps.get_app_config("authentik_admin").system_settings()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.base_url, "")
        self.assertTrue(any("Discarding invalid base_url" in log.event for log in logs))

    def test_backfill_no_outpost(self):
        """With no embedded outpost and no config value, base_url stays empty"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        with CONFIG.patch("web.base_url", ""):
            apps.get_app_config("authentik_admin").system_settings()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.base_url, "")
