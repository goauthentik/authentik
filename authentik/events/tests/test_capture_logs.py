"""Tests for authentik.events.logs.capture_logs"""

import threading

from django.test import SimpleTestCase
from structlog import get_config, get_logger
from structlog.stdlib import ProcessorFormatter
from structlog.testing import LogCapture

from authentik.events.logs import capture_logs


class TestCaptureLogsThreadSafety(SimpleTestCase):
    def test_concurrent_capture_logs_restores_processors(self):
        a_in, b_in, a_out = threading.Event(), threading.Event(), threading.Event()

        def first():
            with capture_logs():
                a_in.set()
                b_in.wait()
            a_out.set()

        def second():
            a_in.wait()
            with capture_logs():
                b_in.set()
                a_out.wait()

        threads = [threading.Thread(target=first), threading.Thread(target=second)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        processors = get_config()["processors"]
        self.assertIn(ProcessorFormatter.wrap_for_formatter, processors)
        self.assertFalse(any(isinstance(p, LogCapture) for p in processors))

        log = get_logger("authentik.events.tests.test_capture_logs")
        for i in range(10):
            log.info("after concurrent capture_logs", i=i)
