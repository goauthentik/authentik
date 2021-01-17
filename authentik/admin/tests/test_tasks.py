"""test admin tasks"""
import json
from dataclasses import dataclass
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import TestCase
from requests.exceptions import RequestException

from authentik.admin.tasks import VERSION_CACHE_KEY, update_latest_version
from authentik.events.models import Event, EventAction


@dataclass
class MockResponse:
    """Mock class to emulate the methods of requests's Response we need"""

    status_code: int
    response: str

    def json(self) -> dict:
        """Get json parsed response"""
        return json.loads(self.response)

    def raise_for_status(self):
        """raise RequestException if status code is 400 or more"""
        if self.status_code >= 400:
            raise RequestException


REQUEST_MOCK_VALID = Mock(
    return_value=MockResponse(
        200,
        """{
            "tag_name": "version/99999999.9999999"
        }""",
    )
)

REQUEST_MOCK_INVALID = Mock(return_value=MockResponse(400, "{}"))


class TestAdminTasks(TestCase):
    """test admin tasks"""

    @patch("authentik.admin.tasks.get", REQUEST_MOCK_VALID)
    def test_version_valid_response(self):
        """Test Update checker with valid response"""
        update_latest_version.delay().get()
        self.assertEqual(cache.get(VERSION_CACHE_KEY), "99999999.9999999")
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE,
                context__new_version="99999999.9999999",
            ).exists()
        )
        # test that a consecutive check doesn't create a duplicate event
        update_latest_version.delay().get()
        self.assertEqual(
            len(
                Event.objects.filter(
                    action=EventAction.UPDATE_AVAILABLE,
                    context__new_version="99999999.9999999",
                )
            ),
            1,
        )

    @patch("authentik.admin.tasks.get", REQUEST_MOCK_INVALID)
    def test_version_error(self):
        """Test Update checker with invalid response"""
        update_latest_version.delay().get()
        self.assertEqual(cache.get(VERSION_CACHE_KEY), "0.0.0")
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE, context__new_version="0.0.0"
            ).exists()
        )
