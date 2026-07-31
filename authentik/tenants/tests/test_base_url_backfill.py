"""Tests for backfilling base_url during tenant reconciliation"""

from django.apps import apps
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.apps import Setup
from authentik.events.logs import capture_logs
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostConfig
from authentik.tenants.apps import BASE_URL_UNSET_DEPRECATION
from authentik.tenants.flags import patch_flag
from authentik.tenants.utils import get_current_tenant


class TestBaseURLBackfill(APITestCase):
    """The backfill reconcile seeds base_url from the config value or the embedded outpost host,
    and warns when neither source is available"""

    def setUp(self):
        super().setUp()
        self.tenant = get_current_tenant()
        self.tenant.base_url = ""
        self.tenant.save()

    @reconcile_app("authentik_outposts")
    def test_backfill_from_outpost(self):
        """base_url is backfilled from the embedded outpost host when empty"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://outpost.example.com")

    @reconcile_app("authentik_outposts")
    def test_backfill_from_config(self):
        """The AUTHENTIK_WEB__BASE_URL config value takes precedence over the outpost host"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        with CONFIG.patch("web.base_url", "https://config.example.com"):
            apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://config.example.com")

    @reconcile_app("authentik_outposts")
    def test_backfill_does_not_overwrite(self):
        """An already-configured base_url is never overwritten by the backfill"""
        self.tenant.base_url = "https://set.example.com"
        self.tenant.save()
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://set.example.com")

    @reconcile_app("authentik_outposts")
    def test_backfill_normalizes_trailing_slash(self):
        """A trailing slash on the outpost host is stripped by the backfill"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com/")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://outpost.example.com")

    def test_backfill_no_outpost(self):
        """With no embedded outpost (e.g. disable_embedded_outpost) and no config value,
        base_url is left empty and the backfill does not error"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "")

    @reconcile_app("authentik_outposts")
    def test_backfill_idempotent(self):
        """Re-running the backfill is stable: once set, a later run (even with a changed
        outpost host) never re-writes base_url"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://outpost.example.com")

        # A subsequent boot with a different outpost host must not overwrite it
        outpost.config = OutpostConfig(authentik_host="https://changed.example.com")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://outpost.example.com")

    @patch_flag(Setup, True)
    def test_backfill_no_source_logs_warning(self):
        """With no config value and no outpost, the reconcile logs that the base URL is unset"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        with capture_logs() as logs:
            apps.get_app_config("authentik_tenants").backfill_base_url()
        self.assertTrue(any("Base URL is not configured" in log.event for log in logs))

    @patch_flag(Setup, True)
    def test_backfill_no_source_files_deprecation_event(self):
        """With no source available, the reconcile files a configuration-warning event so the
        missing base URL surfaces in the event log and to notification rules"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_WARNING,
                context__deprecation=BASE_URL_UNSET_DEPRECATION,
            ).count(),
            1,
        )

    @patch_flag(Setup, True)
    def test_backfill_no_source_event_deduplicated(self):
        """Re-running the reconcile does not pile up duplicate configuration-warning events"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_WARNING,
                context__deprecation=BASE_URL_UNSET_DEPRECATION,
            ).count(),
            1,
        )

    @reconcile_app("authentik_outposts")
    def test_backfill_from_source_files_no_event(self):
        """When a source is available the base URL is backfilled and no warning event is filed"""
        outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)
        outpost.config = OutpostConfig(authentik_host="https://outpost.example.com")
        outpost.save()
        apps.get_app_config("authentik_tenants").backfill_base_url()
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_WARNING,
                context__deprecation=BASE_URL_UNSET_DEPRECATION,
            ).exists()
        )

    @patch_flag(Setup, False)
    def test_backfill_no_source_before_setup_stays_quiet(self):
        """Before setup completes (fresh install), a missing base URL is not yet nagged: the
        required OOBE prompt will set it, so no warning is logged and no event is filed"""
        Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
        with capture_logs() as logs:
            apps.get_app_config("authentik_tenants").backfill_base_url()
        self.assertFalse(any("Base URL is not configured" in log.event for log in logs))
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_WARNING,
                context__deprecation=BASE_URL_UNSET_DEPRECATION,
            ).exists()
        )
