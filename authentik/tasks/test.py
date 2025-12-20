from queue import PriorityQueue

import dramatiq
from django.utils.module_loading import import_string
from django_dramatiq_postgres.conf import Conf
from dramatiq.broker import Broker, MessageProxy, get_broker
from dramatiq.middleware.retries import Retries
from dramatiq.results.middleware import Results
from dramatiq.worker import Worker, _ConsumerThread, _WorkerThread

from authentik.tasks.broker import PostgresBroker

TESTING_QUEUE = "testing"


class TestWorker(Worker):
    def __init__(self, broker: Broker):
        super().__init__(broker=broker)
        self.work_queue = PriorityQueue()
        self.consumers = {
            TESTING_QUEUE: _ConsumerThread(
                broker=self.broker,
                queue_name=TESTING_QUEUE,
                prefetch=2,
                work_queue=self.work_queue,
                worker_timeout=1,
            ),
        }
        self.consumers[TESTING_QUEUE].consumer = self.broker.consume(
            queue_name=TESTING_QUEUE,
            prefetch=2,
            timeout=1,
        )
        self._worker = _WorkerThread(
            broker=self.broker,
            consumers=self.consumers,
            work_queue=self.work_queue,
            worker_timeout=1,
        )

        self.broker.emit_before("worker_boot", self)
        self.broker.emit_after("worker_boot", self)
        self.broker.emit_after("process_boot")

    def process_message(self, message: MessageProxy):
        self.work_queue.put(message)
        self.consumers[TESTING_QUEUE].consumer.in_processing.add(message.message_id)
        self._worker.process_message(message)


class TestBroker(PostgresBroker):
    worker: TestWorker | None = None

    def start(self):
        self.worker = TestWorker(broker=self)

    def enqueue(self, *args, **kwargs):
        message = super().enqueue(*args, **kwargs).copy(queue_name=TESTING_QUEUE)
        if not self.worker:
            return message
        self.worker.process_message(MessageProxy(message))
        return message


def use_test_broker():
    old_broker = get_broker()

    broker = TestBroker()

    for actor_name in old_broker.get_declared_actors():
        actor = old_broker.get_actor(actor_name)
        actor.broker = broker
        actor.broker.declare_actor(actor)

    for middleware_class, middleware_kwargs in Conf().middlewares:
        middleware: dramatiq.middleware.middleware.Middleware = import_string(middleware_class)(
            **middleware_kwargs,
        )
        if isinstance(middleware, Retries):
            middleware.max_retries = 0
        if isinstance(middleware, Results):
            middleware.backend = import_string(Conf().result_backend)(
                *Conf().result_backend_args,
                **Conf().result_backend_kwargs,
            )
        broker.add_middleware(middleware)
    broker.start()
    dramatiq.set_broker(broker)
