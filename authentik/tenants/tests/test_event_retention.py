"""Test event retention"""

from django.test.client import RequestFactory
from rest_framework.test import APITestCase

from authentik.admin.utils import get_system_settings
from authentik.events.models import Event, EventAction
from authentik.lib.utils.time import timedelta_from_string


class TestEventRetention(APITestCase):
    """Test event retention"""

    def test_event_retention(self):
        """Test brand's event retention"""
        settings = get_system_settings()
        settings.event_retention = "weeks=3"
        settings.save()
        factory = RequestFactory()
        request = factory.get("/")
        event = Event.new(action=EventAction.SYSTEM_EXCEPTION, message="test").from_http(request)
        self.assertEqual(event.expires.day, (event.created + timedelta_from_string("weeks=3")).day)
        self.assertEqual(
            event.expires.month,
            (event.created + timedelta_from_string("weeks=3")).month,
        )
        self.assertEqual(
            event.expires.year, (event.created + timedelta_from_string("weeks=3")).year
        )
