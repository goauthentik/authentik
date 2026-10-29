"""capture_logs tests"""

from threading import Barrier, Thread

from django.test import TestCase
from structlog.stdlib import get_logger

from authentik.events.logs import capture_logs
from authentik.lib.logging import CAPTURED_LOGS


class TestCaptureLogs(TestCase):
    """Test capture_logs"""

    def test_capture(self):
        """Logs are captured, nested captures only see their own logs"""
        logger = get_logger()
        with capture_logs() as outer:
            logger.warning("outer")
            with capture_logs() as inner:
                logger.warning("inner")
        self.assertEqual([x.event for x in outer], ["outer"])
        self.assertEqual([x.event for x in inner], ["inner"])
        self.assertIsNone(CAPTURED_LOGS.get())

    def test_overlapping_threads(self):
        """Overlapping captures in different threads must not leak a capture once both exit"""
        logger = get_logger()
        entered = Barrier(2)
        a_exited = Barrier(2)
        results = {}

        def a():
            with capture_logs() as logs:
                entered.wait()
                logger.warning("a")
            a_exited.wait()
            results["a"] = logs

        def b():
            with capture_logs() as logs:
                entered.wait()
                a_exited.wait()
                logger.warning("b")
            results["b"] = logs
            results["b_after"] = CAPTURED_LOGS.get()

        threads = [Thread(target=a), Thread(target=b)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual([x.event for x in results["a"]], ["a"])
        self.assertEqual([x.event for x in results["b"]], ["b"])
        self.assertIsNone(results["b_after"])
        self.assertIsNone(CAPTURED_LOGS.get())
