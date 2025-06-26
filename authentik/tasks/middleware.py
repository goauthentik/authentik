import os
from pathlib import Path
from signal import pause
from socket import gethostname
from tempfile import gettempdir
from time import sleep
from typing import Any

import pglock
from django.conf import settings
from django.utils.timezone import now
from dramatiq.broker import Broker
from dramatiq.common import current_millis
from dramatiq.message import Message
from dramatiq.middleware import Middleware
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.utils.errors import exception_to_string
from authentik.tasks.models import Task, TaskStatus, WorkerStatus
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


class TenantMiddleware(Middleware):
    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        message.options["model_defaults"]["tenant"] = get_current_tenant()

    def before_process_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.tenant.activate()

    def after_process_message(self, *args, **kwargs):
        Tenant.deactivate()


class RelObjMiddleware(Middleware):
    @property
    def actor_options(self):
        return {"rel_obj"}

    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        if rel_obj := message.options.get("rel_obj"):
            del message.options["rel_obj"]
        message.options["model_defaults"]["rel_obj"] = rel_obj


class MessagesMiddleware(Middleware):
    def after_enqueue(self, broker: Broker, message: Message, delay: int):
        task: Task = message.options["task"]
        task_created: bool = message.options["task_created"]
        if task_created:
            task._messages.append(
                Task._make_message(
                    str(type(self)),
                    TaskStatus.INFO,
                    "Task has been queued",
                    delay=delay,
                )
            )
        else:
            task._previous_messages.extend(task._messages)
            task._messages = [
                Task._make_message(
                    str(type(self)),
                    TaskStatus.INFO,
                    "Task will be retried",
                    delay=delay,
                )
            ]
        task.save(update_fields=("_messages", "_previous_messages"))

    def before_process_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.log(str(type(self)), TaskStatus.INFO, "Task is being processed")

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        task: Task = message.options["task"]
        if exception is None:
            task.log(str(type(self)), TaskStatus.INFO, "Task finished processing without errors")
        else:
            task.log(
                str(type(self)),
                TaskStatus.ERROR,
                "Task finished processing with errors",
                exception=exception_to_string(exception),
            )
            Event.new(
                EventAction.SYSTEM_TASK_EXCEPTION,
                message=f"Task {task.actor_name} encountered an error: "
                "{exception_to_string(exception)}",
            ).save()

    def after_skip_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.log(str(type(self)), TaskStatus.INFO, "Task has been skipped")


class LoggingMiddleware(Middleware):
    def __init__(self):
        self.logger = get_logger()

    def after_enqueue(self, broker: Broker, message: Message, delay: int):
        self.logger.info(
            "Task enqueued",
            task_id=message.message_id,
            task_name=message.actor_name,
        )

    def before_process_message(self, broker: Broker, message: Message):
        self.logger.info("Task started", task_id=message.message_id, task_name=message.actor_name)

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        self.logger.info(
            "Task finished",
            task_id=message.message_id,
            task_name=message.actor_name,
            exc=exception,
        )

    def after_skip_message(self, broker: Broker, message: Message):
        self.logger.info("Task skipped", task_id=message.message_id, task_name=message.actor_name)


class DescriptionMiddleware(Middleware):
    @property
    def actor_options(self):
        return {"description"}


class WorkerStatusMiddleware(Middleware):
    @property
    def forks(self):
        from authentik.tasks.forks import worker_status

        return [worker_status]

    @staticmethod
    def worker_status():
        status = WorkerStatus.objects.create(
            hostname=gethostname(),
            version=get_full_version(),
        )
        lock_id = f"goauthentik.io/worker/status/{status.pk}"
        with pglock.advisory(lock_id, side_effect=pglock.Raise):
            while True:
                status.last_seen = now()
                status.save(update_fields=("last_seen",))
                sleep(30)


class MetricsMiddleware(Middleware):
    def __init__(self):
        super().__init__()
        self.delayed_messages = set()
        self.message_start_times = {}

        _tmp = Path(gettempdir())
        prometheus_tmp_dir = str(_tmp.joinpath("authentik_prometheus_tmp"))
        os.makedirs(prometheus_tmp_dir, exist_ok=True)
        os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", prometheus_tmp_dir)

    @property
    def forks(self):
        from authentik.tasks.forks import worker_metrics

        return [worker_metrics]

    def before_worker_boot(self, broker: Broker, worker):
        if settings.TEST:
            return

        from prometheus_client import Counter, Gauge, Histogram

        self.total_messages = Counter(
            "authentik_tasks_total",
            "The total number of tasks processed.",
            ["queue_name", "actor_name"],
        )
        self.total_errored_messages = Counter(
            "authentik_tasks_errors_total",
            "The total number of errored tasks.",
            ["queue_name", "actor_name"],
        )
        self.total_retried_messages = Counter(
            "authentik_tasks_retries_total",
            "The total number of retried tasks.",
            ["queue_name", "actor_name"],
        )
        self.total_rejected_messages = Counter(
            "authentik_tasks_rejected_total",
            "The total number of dead-lettered tasks.",
            ["queue_name", "actor_name"],
        )
        self.inprogress_messages = Gauge(
            "authentik_tasks_inprogress",
            "The number of tasks in progress.",
            ["queue_name", "actor_name"],
            multiprocess_mode="livesum",
        )
        self.inprogress_delayed_messages = Gauge(
            "authentik_tasks_delayed_inprogress",
            "The number of delayed tasks in memory.",
            ["queue_name", "actor_name"],
        )
        self.messages_durations = Histogram(
            "authentik_tasks_duration_miliseconds",
            "The time spent processing tasks.",
            ["queue_name", "actor_name"],
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

    def _make_labels(self, message: Message) -> tuple[str, str]:
        return (message.queue_name, message.actor_name)

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
    def run():
        from prometheus_client import CollectorRegistry, multiprocess, start_http_server

        addr, _, port = CONFIG.get("listen.listen_metrics").rpartition(":")

        try:
            port = int(port)

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            start_http_server(port, addr, registry)
        except ValueError:
            LOGGER.error(f"Invalid port entered: {port}")
        except OSError:
            LOGGER.warning("Port is already in use, not starting metrics server")
        pause()
