from django.test import SimpleTestCase
from dramatiq import Worker, actor
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import Middleware
from dramatiq.middleware.time_limit import TimeLimitExceeded

from lifecycle.worker_process import crashed_threads


class TimeLimitInAfterHook(Middleware):
    """Raises what TimeLimit raises when the limit hits while after_process_message runs"""

    def after_process_message(self, broker, message, *, result=None, exception=None):
        raise TimeLimitExceeded()


class TestCrashedThreads(SimpleTestCase):
    def setUp(self):
        self.broker = StubBroker(middleware=[])
        self.worker = Worker(self.broker, worker_threads=1)

    def test_running_and_stopped_threads_are_not_crashed(self):
        self.worker.start()
        self.assertEqual(crashed_threads(self.worker), [])
        self.worker.stop(timeout=5_000)
        self.assertEqual(crashed_threads(self.worker), [])

    def test_thread_ended_by_time_limit_after_failed_task(self):
        @actor(broker=self.broker)
        def fails():
            raise ValueError("task failed")

        self.broker.add_middleware(TimeLimitInAfterHook())
        self.worker.start()
        self.addCleanup(self.worker.stop, timeout=5_000)
        fails.send()
        thread = self.worker.workers[0]
        thread.join(timeout=5)

        self.assertFalse(thread.is_alive())
        self.assertEqual(crashed_threads(self.worker), [thread.name])
