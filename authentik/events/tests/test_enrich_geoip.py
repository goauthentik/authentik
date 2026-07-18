"""Test GeoIP Wrapper"""

from django.test import TestCase

from authentik.events.context_processors.base import get_context_processors
from authentik.events.context_processors.geoip import GeoIPContextProcessor
from authentik.events.models import Event, EventAction


class TestGeoIP(TestCase):
    """Test GeoIP Wrapper"""

    def setUp(self) -> None:
        self.reader = GeoIPContextProcessor()

    def test_simple(self):
        """Test simple city wrapper"""
        # IPs from https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-City-Test.json
        self.assertEqual(
            self.reader.city_dict("2.125.160.216"),
            {
                "city": "Boxford",
                "continent": "EU",
                "country": "GB",
                "lat": 51.75,
                "long": -1.25,
            },
        )

    def test_special_chars(self):
        """Test city name with special characters"""
        # IPs from https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-City-Test.json
        event = Event.new(EventAction.LOGIN)
        event.client_ip = "89.160.20.112"
        for processor in get_context_processors():
            processor.enrich_event(event)
        event.save()
