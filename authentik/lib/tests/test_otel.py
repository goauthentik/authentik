"""test OpenTelemetry integration"""

from django.test import TestCase

from authentik.lib.tracing.exceptions import TracingIgnoredException, should_ignore_exception


class TestOtel(TestCase):
    """test OpenTelemetry integration"""

    def test_error_not_sent(self):
        """Test TracingIgnoredException not recorded"""
        self.assertTrue(should_ignore_exception(TracingIgnoredException()))

    def test_error_sent(self):
        """Test error recorded"""
        self.assertFalse(should_ignore_exception(ValueError()))
