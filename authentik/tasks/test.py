from queue import PriorityQueue

from dramatiq.broker import Broker, MessageProxy
from dramatiq.worker import Worker, _ConsumerThread, _WorkerThread

from authentik.tasks.broker import PostgresBroker


class TestWorker(Worker):
    def __init__(self, queue_name: str, broker: Broker):
        super().__init__(broker=broker)
        self.work_queue = PriorityQueue()
        self.consumers = {
            queue_name: _ConsumerThread(
                broker=self.broker,
                queue_name=queue_name,
                prefetch=2,
                work_queue=self.work_queue,
                worker_timeout=1,
            ),
        }
        self.consumers[queue_name].consumer = self.broker.consume(
            queue_name=queue_name,
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

    def process_message(self, message: MessageProxy):
        self.logger.error(f"processing message {message}")
        self.work_queue.put(message)
        self.consumers[message.queue_name].consumer.in_processing.add(message.message_id)
        self._worker.process_message(message)


class TestBroker(PostgresBroker):
    def enqueue(self, *args, **kwargs):
        message = super().enqueue(*args, **kwargs)
        worker = TestWorker(message.queue_name, broker=self)
        worker.process_message(MessageProxy(message))
        return message
