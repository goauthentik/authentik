"""Test GeoIP Wrapper"""
from django.test import TestCase

from authentik.events.context_processors.geoip import GeoIPContextProcessor


class TestGeoIP(TestCase):
    """Test GeoIP Wrapper"""

    def setUp(self) -> None:
        self.reader = GeoIPContextProcessor()

    def test_simple(self):
        """Test simple city wrapper"""
        # IPs from
        # https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-City-Test.json
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
