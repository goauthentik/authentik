from django.test import TransactionTestCase
from dramatiq import Worker, get_broker


class TaskTestCase(TransactionTestCase):
    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()
