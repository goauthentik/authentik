"""test sentry integration"""
from django.test import TestCase

from authentik.lib.sentry import SentryIgnoredException, before_send


class TestSentry(TestCase):
    """test sentry integration"""

    def error_not_sent(self):
        """Test SentryIgnoredError not sent"""
        self.assertIsNone(
            before_send(None, {"exc_info": (0, SentryIgnoredException(), 0)})
        )

    def error_sent(self):
        """Test error sent"""
        self.assertIsNone(before_send(None, {"exc_info": (0, ValueError(), 0)}))
