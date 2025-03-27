from django.test import TestCase
from dramatiq import Worker, get_broker


class TaskTestCase(TestCase):
    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()

    def tasks_join(self, queue_name: str | None = None):
        if queue_name is None:
            for queue in self.broker.get_declared_queues():
                self.broker.join(queue)
        else:
            self.broker.join(queue_name)
        self.worker.join()
