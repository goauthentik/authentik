"""test sentry integration"""

from django.test import TestCase

from authentik.common.exceptions import NotReportedException
from authentik.root.sentry import before_send


class TestSentry(TestCase):
    """test sentry integration"""

    def test_error_not_sent(self):
        """Test SentryIgnoredError not sent"""
        self.assertIsNone(before_send({}, {"exc_info": (0, NotReportedException(), 0)}))

    def test_error_sent(self):
        """Test error sent"""
        self.assertEqual({}, before_send({}, {"exc_info": (0, ValueError(), 0)}))
