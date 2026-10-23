"""Test MMDB path resolution"""

from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from django.test import TestCase

from authentik.events.context_processors.geoip import GeoIPContextProcessor
from authentik.lib.config import CONFIG

TEST_DB = Path(__file__).parents[3] / "tests" / "geoip" / "GeoLite2-City-Test.mmdb"


class TestMMDBPath(TestCase):
    """Test MMDB path resolution"""

    def setUp(self) -> None:
        self.dir = TemporaryDirectory()
        self.default = str(Path(self.dir.name) / "dbip-city-lite.mmdb")
        self.legacy = str(Path(self.dir.name) / "GeoLite2-City.mmdb")

    def tearDown(self) -> None:
        self.dir.cleanup()

    def processor(self) -> GeoIPContextProcessor:
        processor = GeoIPContextProcessor()
        processor.default_path = self.default
        processor.legacy_path = self.legacy
        processor.load()
        return processor

    def test_default(self):
        """Default file is loaded when present"""
        copyfile(TEST_DB, self.default)
        copyfile(TEST_DB, self.legacy)
        with CONFIG.patch("events.context_processors.geoip", self.default):
            processor = self.processor()
            self.assertEqual(processor.resolved_path(), self.default)
            self.assertTrue(processor.configured())

    def test_legacy_fallback(self):
        """Legacy file is loaded when the default file is missing"""
        copyfile(TEST_DB, self.legacy)
        with CONFIG.patch("events.context_processors.geoip", self.default):
            processor = self.processor()
            self.assertEqual(processor.resolved_path(), self.legacy)
            self.assertTrue(processor.configured())
            self.assertEqual(processor.city_dict("2.125.160.216")["city"], "Boxford")

    def test_no_fallback_custom_path(self):
        """Legacy file is not used when a non-default path is configured"""
        copyfile(TEST_DB, self.legacy)
        custom = str(Path(self.dir.name) / "custom.mmdb")
        with CONFIG.patch("events.context_processors.geoip", custom):
            processor = self.processor()
            self.assertEqual(processor.resolved_path(), custom)
            self.assertFalse(processor.configured())
