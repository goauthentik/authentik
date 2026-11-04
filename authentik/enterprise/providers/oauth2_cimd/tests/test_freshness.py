"""HTTP freshness"""

from email.utils import formatdate

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.freshness import freshness

NOW = 1_800_000_000.0


class TestFreshness(SimpleTestCase):
    """HTTP freshness"""

    def check(self, headers, ttl, source):
        result = freshness(headers, NOW)
        self.assertEqual((result.ttl, result.source), (ttl, source))

    def test_default(self):
        self.check({}, 120, "default")

    def test_max_age(self):
        self.check({"cache-control": "public, max-age=200"}, 200, "max_age")
        self.check({"cache-control": 'max-age="90"'}, 90, "max_age")
        self.check({"cache-control": "MAX-AGE=90"}, 90, "max_age")

    def test_clamped(self):
        self.check({"cache-control": "max-age=86400"}, 300, "max_age")
        self.check({"cache-control": "max-age=5"}, 60, "max_age")
        self.check({"cache-control": "max-age=0"}, 60, "max_age")

    def test_invalid_max_age(self):
        self.check({"cache-control": "max-age=abc"}, 60, "max_age")
        self.check({"cache-control": "max-age=-1"}, 60, "max_age")
        self.check({"cache-control": "max-age=200, max-age=100"}, 60, "max_age")

    def test_no_store(self):
        """The 60-second minimum holds under no-store"""
        self.check({"cache-control": "no-store"}, 60, "no_store")
        self.check({"cache-control": "max-age=300, no-store"}, 60, "no_store")
        self.check({"cache-control": "no-cache"}, 60, "no_cache")
        self.check({"cache-control": "private, no-cache, max-age=300"}, 60, "no_cache")

    def test_age(self):
        self.check({"cache-control": "max-age=250", "age": "100"}, 150, "max_age")
        self.check({"cache-control": "max-age=250", "age": "x"}, 250, "max_age")

    def test_expires(self):
        self.check({"expires": formatdate(NOW + 200, usegmt=True)}, 200, "expires")
        self.check(
            {
                "expires": formatdate(NOW + 200, usegmt=True),
                "date": formatdate(NOW + 100, usegmt=True),
            },
            100,
            "expires",
        )
        self.check({"expires": formatdate(NOW - 100, usegmt=True)}, 60, "expires")
        self.check({"expires": "0"}, 60, "expires")
        self.check({"expires": "not a date"}, 60, "expires")

    def test_max_age_over_expires(self):
        self.check(
            {"cache-control": "max-age=100", "expires": formatdate(NOW + 250, usegmt=True)},
            100,
            "max_age",
        )
