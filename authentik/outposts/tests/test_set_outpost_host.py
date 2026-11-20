"""Ensure when AuthentikOutpostConfig changes the embedded_outpost's host is correct afterward"""

from django.apps import apps
from django.test import TestCase

from authentik.admin.utils import get_system_settings
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost


class TestEmbeddedOutpostHost(TestCase):
    """Set the outpost.config.authentik_host from base_url"""

    def setUp(self):
        super().setUp()
        self.settings = get_system_settings()
        self.settings.base_url = ""
        self.settings.save()
        self.reconcile()
        self.outpost = Outpost.objects.get(managed=MANAGED_OUTPOST)

    def reconcile(self):
        apps.get_app_config("authentik_outposts").embedded_outpost()

    def set_base_url(self, base_url: str):
        self.settings.base_url = base_url
        self.settings.save()

    def set_host(self, host: str):
        config = self.outpost.config
        config.authentik_host = host
        self.outpost.config = config
        self.outpost.save()

    def get_host(self) -> str:
        self.outpost.refresh_from_db()
        return self.outpost.config.authentik_host

    def test_empty_host(self):
        """An empty host is set to base_url"""
        self.set_host("")
        self.set_base_url("https://goauthentik.io")
        self.reconcile()
        self.assertEqual(self.get_host(), "https://goauthentik.io")

    def test_host_without_https(self):
        """An invalid host needs to be updated with the base_url"""
        self.set_host("goauthentik.io")
        self.set_base_url("https://goauthentik.io")
        self.reconcile()
        self.assertEqual(self.get_host(), "https://goauthentik.io")

    # This is testing for the existing behavior. It may not be the *right* behavior.
    def test_existing_url_unchanged_after_update(self):
        """Never overwrite an existing valid host"""
        self.set_host("http://goauthentik.internal:9000")
        self.set_base_url("https://goauthentik.io")
        self.reconcile()
        self.assertEqual(self.get_host(), "http://goauthentik.internal:9000")
