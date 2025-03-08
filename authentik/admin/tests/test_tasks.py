"""test admin tasks"""

from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.admin.tasks import (
    VERSION_CACHE_KEY,
    clear_update_notifications,
)
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.tasks.tasks import async_task, result

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
            result(async_task("authentik.admin.tasks.update_latest_version"))
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "99999999.9999999")
            self.assertTrue(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE,
                    context__new_version="99999999.9999999",
                    context__message="New version 99999999.9999999 available!",
                ).exists()
            )
            # test that a consecutive check doesn't create a duplicate event
            result(async_task("authentik.admin.tasks.update_latest_version"))
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
            result(async_task("authentik.admin.tasks.update_latest_version"))
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")
            self.assertFalse(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE, context__new_version="0.0.0"
                ).exists()
            )

    def test_version_disabled(self):
        """Test Update checker while its disabled"""
        with CONFIG.patch("disable_update_check", True):
            result(async_task("authentik.admin.tasks.update_latest_version"))
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")

    def test_clear_update_notifications(self):
        """Test clear of previous notification"""
        Event.objects.create(
            action=EventAction.UPDATE_AVAILABLE, context={"new_version": "99999999.9999999.9999999"}
        )
        Event.objects.create(action=EventAction.UPDATE_AVAILABLE, context={"new_version": "1.1.1"})
        Event.objects.create(action=EventAction.UPDATE_AVAILABLE, context={})
        clear_update_notifications()
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE, context__new_version="1.1"
            ).exists()
        )
