from django.test import SimpleTestCase

from authentik.events.logs import LogEvent, capture_logs


class TestLogEvent(SimpleTestCase):

    def test_log_replays_with_stable_event(self):
        with capture_logs() as logs:
            LogEvent(
                "runtime event",
                log_level="info",
                logger="authentik.test",
                attributes={"event": "caller event", "foo": "bar"},
            ).log()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].event, "Captured log event")
        self.assertEqual(logs[0].attributes["log_event"], "runtime event")
        self.assertEqual(logs[0].attributes["log_logger"], "authentik.test")
        self.assertEqual(logs[0].attributes["log_event_attribute"], "caller event")
        self.assertEqual(logs[0].attributes["foo"], "bar")
