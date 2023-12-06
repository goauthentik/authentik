"""Test ASN Wrapper"""
from django.test import TestCase

from authentik.events.enrich.asn import ASNEnricher


class TestASN(TestCase):
    """Test ASN Wrapper"""

    def setUp(self) -> None:
        self.reader = ASNEnricher()

    def test_simple(self):
        """Test simple asn wrapper"""
        # IPs from
        # https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-ASN-Test.json
        self.assertEqual(
            self.reader.asn_dict("1.0.0.1"),
            {
                "asn": 15169,
                "as_org": "Google Inc.",
                "network": "1.0.0.0/24",
            },
        )
