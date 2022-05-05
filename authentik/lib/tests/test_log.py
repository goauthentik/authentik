"""Test log utils"""
from unittest import TestCase

from structlog.stdlib import get_logger

from authentik.lib.utils.log import capture_logs_tee


class TestLog(TestCase):
    """Test log utils"""

    def test_capture_logs_tee(self):
        """test capture_logs_tee"""
        logger = get_logger()
        with capture_logs_tee() as logs:
            logger.info("test", foo="bar")
        self.assertEqual(logs, [{"event": "test", "log_level": "info", "foo": "bar"}])
