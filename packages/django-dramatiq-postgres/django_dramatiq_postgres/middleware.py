import contextvars
import os
import socket
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer as BaseHTTPServer
from ipaddress import IPv6Address, ip_address
from typing import Any

from django.db import (
    close_old_connections,
    connections,
)
from dramatiq.actor import Actor
from dramatiq.broker import Broker
from dramatiq.common import current_millis
from dramatiq.logging import get_logger
from dramatiq.message import Message
from dramatiq.middleware.middleware import Middleware

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import TaskBase


class HTTPServer(BaseHTTPServer):
    def server_bind(self):
        self.socket.close()

        host, port = self.server_address[:2]
        if host == "0.0.0.0":  # nosec
            host = "::"  # nosec

        # Strip IPv6 brackets
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]

        self.server_address = (host, port)

        self.address_family = (
            socket.AF_INET6 if isinstance(ip_address(host), IPv6Address) else socket.AF_INET
        )

        self.socket = socket.create_server(
            self.server_address,
            family=self.address_family,
            dualstack_ipv6=self.address_family == socket.AF_INET6,
        )

        self.server_name = socket.getfqdn(host)
        self.server_port = port


class DbConnectionMiddleware(Middleware):
    def _close_old_connections(self, *args, **kwargs):
        if Conf().test:
            return
        close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections


class FullyQualifiedActorName(Middleware):
    def before_declare_actor(self, broker: Broker, actor: Actor):
        actor.actor_name = f"{actor.fn.__module__}.{actor.fn.__name__}"


class CurrentTaskNotFound(Exception):
    """
    Not current task found. Did you call get_task outside a running task?
    """


class CurrentTask(Middleware):
    def __init__(self):
        self.logger = get_logger(__name__, type(self))

    # This is a list of tasks, so that in tests, when a task calls another task, this acts as a pile
    _TASKS: contextvars.ContextVar[list[TaskBase] | None] = contextvars.ContextVar(
        "_TASKS",
        default=None,
    )

    @classmethod
    def get_task(cls) -> TaskBase:
        task = cls._TASKS.get()
        if not task:
            raise CurrentTaskNotFound()
        return task[-1]

    def before_process_message(self, broker: Broker, message: Message):
        tasks = self._TASKS.get()
        if tasks is None:
            tasks = []
        tasks.append(message.options["task"])
        self._TASKS.set(tasks)

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        tasks: list[TaskBase] | None = self._TASKS.get()
        if tasks is None or len(tasks) == 0:
            return

        task = tasks[-1]
        fields_to_exclude = {
            "message_id",
            "queue_name",
            "actor_name",
            "message",
            "state",
            "mtime",
            "result",
            "result_expiry",
        }
        fields_to_update = [
            f.name
            for f in task._meta.get_fields()
            if f.name not in fields_to_exclude and not f.auto_created and f.column
        ]
        if fields_to_update:
            task.save(update_fields=fields_to_update)
        self._TASKS.set(tasks[:-1])

    def after_skip_message(self, broker: Broker, message: Message):
        self.after_process_message(broker, message)


class MetricsMiddleware(Middleware):
    def __init__(
        self,
        prefix: str,
        multiproc_dir: str,
        labels: list[str] | None = None,
    ):
        super().__init__()
        self.prefix = prefix
        self.labels: list[str] = labels if labels is not None else ["queue_name", "actor_name"]

        self.delayed_messages = set()
        self.message_start_times = {}

        os.makedirs(multiproc_dir, exist_ok=True)
        os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", multiproc_dir)

    @property
    def forks(self):
        from django_dramatiq_postgres.forks import worker_metrics

        return [worker_metrics]

    def before_worker_boot(self, broker: Broker, worker):
        if Conf().test:
            return

        from prometheus_client import Counter, Gauge, Histogram

        self.total_messages = Counter(
            f"{self.prefix}_tasks_total",
            "The total number of tasks processed.",
            self.labels,
        )
        self.total_errored_messages = Counter(
            f"{self.prefix}_tasks_errors_total",
            "The total number of errored tasks.",
            self.labels,
        )
        self.total_retried_messages = Counter(
            f"{self.prefix}_tasks_retries_total",
            "The total number of retried tasks.",
            self.labels,
        )
        self.total_rejected_messages = Counter(
            f"{self.prefix}_tasks_rejected_total",
            "The total number of dead-lettered tasks.",
            self.labels,
        )
        self.inprogress_messages = Gauge(
            f"{self.prefix}_tasks_inprogress",
            "The number of tasks in progress.",
            self.labels,
            multiprocess_mode="livesum",
        )
        self.inprogress_delayed_messages = Gauge(
            f"{self.prefix}_tasks_delayed_inprogress",
            "The number of delayed tasks in memory.",
            self.labels,
        )
        self.messages_durations = Histogram(
            f"{self.prefix}_tasks_duration_miliseconds",
            "The time spent processing tasks.",
            self.labels,
            buckets=(
                5,
                10,
                25,
                50,
                75,
                100,
                250,
                500,
                750,
                1_000,
                2_500,
                5_000,
                7_500,
                10_000,
                30_000,
                60_000,
                600_000,
                900_000,
                1_800_000,
                3_600_000,
                float("inf"),
            ),
        )

    def after_worker_shutdown(self, broker: Broker, worker):
        from prometheus_client import multiprocess

        # TODO: worker_id
        multiprocess.mark_process_dead(os.getpid())

    def _make_labels(self, message: Message) -> list[str]:
        return [message.queue_name, message.actor_name]

    def after_nack(self, broker: Broker, message: Message):
        self.total_rejected_messages.labels(*self._make_labels(message)).inc()

    def after_enqueue(self, broker: Broker, message: Message, delay: int):
        if "retries" in message.options:
            self.total_retried_messages.labels(*self._make_labels(message)).inc()

    def before_delay_message(self, broker: Broker, message: Message):
        self.delayed_messages.add(message.message_id)
        self.inprogress_delayed_messages.labels(*self._make_labels(message)).inc()

    def before_process_message(self, broker: Broker, message: Message):
        labels = self._make_labels(message)
        if message.message_id in self.delayed_messages:
            self.delayed_messages.remove(message.message_id)
            self.inprogress_delayed_messages.labels(*labels).dec()

        self.inprogress_messages.labels(*labels).inc()
        self.message_start_times[message.message_id] = current_millis()

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        labels = self._make_labels(message)

        message_start_time = self.message_start_times.pop(message.message_id, current_millis())
        message_duration = current_millis() - message_start_time
        self.messages_durations.labels(*labels).observe(message_duration)

        self.inprogress_messages.labels(*labels).dec()
        self.total_messages.labels(*labels).inc()
        if exception is not None:
            self.total_errored_messages.labels(*labels).inc()

    after_skip_message = after_process_message

    @staticmethod
    def run(addr: str, port: int):
        try:
            server = HTTPServer((addr, port), _MetricsHandler)
            server.serve_forever()
        except OSError:
            get_logger(__name__, type(MetricsMiddleware)).warning(
                "Port is already in use, not starting metrics server"
            )


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            CollectorRegistry,
            generate_latest,
            multiprocess,
        )

        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        output = generate_latest(registry)
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, format, *args):
        logger = get_logger(__name__, type(self))
        logger.debug(format, *args)
