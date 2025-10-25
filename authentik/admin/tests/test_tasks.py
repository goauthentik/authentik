"""test admin tasks"""

from django.apps import apps
from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.admin.tasks import (
    VERSION_CACHE_KEY,
    update_latest_version,
)
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG

RESPONSE_VALID = {
    "$schema": "https://version.goauthentik.io/schema.json",
    "stable": {
        "version": "99999999.9999999",
        "changelog": "See https://goauthentik.io/test",
        "changelog_url": "https://goauthentik.io/test",
        "reason": "bugfix",
    },
}


class TestAdminTasks(TestCase):
    """test admin tasks"""

    def test_version_valid_response(self):
        """Test Update checker with valid response"""
        with Mocker() as mocker, CONFIG.patch("disable_update_check", False):
            mocker.get("https://version.goauthentik.io/version.json", json=RESPONSE_VALID)
            update_latest_version.send()
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "99999999.9999999")
            self.assertTrue(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE,
                    context__new_version="99999999.9999999",
                    context__message="New version 99999999.9999999 available!",
                ).exists()
            )
            # test that a consecutive check doesn't create a duplicate event
            update_latest_version.send()
            self.assertEqual(
                len(
                    Event.objects.filter(
                        action=EventAction.UPDATE_AVAILABLE,
                        context__new_version="99999999.9999999",
                        context__message="New version 99999999.9999999 available!",
                    )
                ),
                1,
            )

    def test_version_error(self):
        """Test Update checker with invalid response"""
        with Mocker() as mocker:
            mocker.get("https://version.goauthentik.io/version.json", status_code=400)
            update_latest_version.send()
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")
            self.assertFalse(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE, context__new_version="0.0.0"
                ).exists()
            )

    def test_version_disabled(self):
        """Test Update checker while its disabled"""
        with CONFIG.patch("disable_update_check", True):
            update_latest_version.send()
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")

    def test_clear_update_notifications(self):
        """Test clear of previous notification"""
        admin_config = apps.get_app_config("authentik_admin")
        Event.objects.create(
            action=EventAction.UPDATE_AVAILABLE,
            context={"new_version": "99999999.9999999.9999999"},
        )
        Event.objects.create(action=EventAction.UPDATE_AVAILABLE, context={"new_version": "1.1.1"})
        Event.objects.create(action=EventAction.UPDATE_AVAILABLE, context={})
        admin_config.clear_update_notifications()
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE, context__new_version="1.1"
            ).exists()
        )
