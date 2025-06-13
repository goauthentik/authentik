"""test sentry integration"""

from django.test import TestCase

from authentik.lib.sentry import SentryIgnoredException, should_ignore_exception


class TestSentry(TestCase):
    """test sentry integration"""

    def test_error_not_sent(self):
        """Test SentryIgnoredError not sent"""
        self.assertIsNone(should_ignore_exception(SentryIgnoredException()))

    def test_error_sent(self):
        """Test error sent"""
        self.assertEqual({}, should_ignore_exception(ValueError()))
