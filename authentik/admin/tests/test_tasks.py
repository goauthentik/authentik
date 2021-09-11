"""test admin tasks"""
from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.admin.tasks import VERSION_CACHE_KEY, update_latest_version
from authentik.events.models import Event, EventAction

RESPONSE_VALID = {
    "$schema": "https://version.goauthentik.io/schema.json",
    "stable": {
        "version": "99999999.9999999",
        "changelog": "See https://goauthentik.io/test",
        "reason": "bugfix",
    },
}


class TestAdminTasks(TestCase):
    """test admin tasks"""

    def test_version_valid_response(self):
        """Test Update checker with valid response"""
        with Mocker() as mocker:
            mocker.get("https://version.goauthentik.io/version.json", json=RESPONSE_VALID)
            update_latest_version.delay().get()
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "99999999.9999999")
            self.assertTrue(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE,
                    context__new_version="99999999.9999999",
                    context__message="Changelog: https://goauthentik.io/test",
                ).exists()
            )
            # test that a consecutive check doesn't create a duplicate event
            update_latest_version.delay().get()
            self.assertEqual(
                len(
                    Event.objects.filter(
                        action=EventAction.UPDATE_AVAILABLE,
                        context__new_version="99999999.9999999",
                        context__message="Changelog: https://goauthentik.io/test",
                    )
                ),
                1,
            )

    def test_version_error(self):
        """Test Update checker with invalid response"""
        with Mocker() as mocker:
            mocker.get("https://version.goauthentik.io/version.json", status_code=400)
            update_latest_version.delay().get()
            self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")
            self.assertFalse(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE, context__new_version="0.0.0"
                ).exists()
            )
