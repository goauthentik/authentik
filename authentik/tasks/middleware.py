import socket
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler
from threading import Thread
from time import sleep
from typing import Any, cast

import pglock
from django.db import OperationalError, connections, transaction
from django.utils.timezone import now
from django_dramatiq_postgres.middleware import (
    CurrentTask as BaseCurrentTask,
)
from django_dramatiq_postgres.middleware import HTTPServer
from django_dramatiq_postgres.middleware import (
    MetricsMiddleware as BaseMetricsMiddleware,
)
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware
from psycopg.errors import Error
from setproctitle import setthreadtitle
from structlog.stdlib import get_logger

from authentik import authentik_full_version
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.sentry import should_ignore_exception
from authentik.lib.utils.reflection import class_to_path
from authentik.root.signals import post_startup, pre_startup, startup
from authentik.tasks.models import Task, TaskLog, TaskStatus, WorkerStatus
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()
HEALTHCHECK_LOGGER = get_logger("authentik.worker").bind()
DB_ERRORS = (OperationalError, Error)


class StartupSignalsMiddleware(Middleware):
    def after_process_boot(self, broker: Broker):
        _startup_sender = type("WorkerStartup", (object,), {})
        pre_startup.send(sender=_startup_sender)
        startup.send(sender=_startup_sender)
        post_startup.send(sender=_startup_sender)


class CurrentTask(BaseCurrentTask):
    @classmethod
    def get_task(cls) -> Task:
        return cast(Task, super().get_task())


class TenantMiddleware(Middleware):
    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        message.options["model_create_defaults"]["tenant"] = get_current_tenant()

    def before_process_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.tenant.activate()

    def after_process_message(self, *args, **kwargs):
        Tenant.deactivate()

    after_skip_message = after_process_message


class ModelDataMiddleware(Middleware):
    @property
    def actor_options(self):
        return {"rel_obj", "uid"}

    def before_enqueue(self, broker: Broker, message: Message, delay: int):
        if "rel_obj" in message.options:
            message.options["model_defaults"]["rel_obj"] = message.options.pop("rel_obj")
        if "uid" in message.options:
            message.options["model_defaults"]["_uid"] = message.options.pop("uid")


class TaskLogMiddleware(Middleware):
    def after_enqueue(self, broker: Broker, message: Message, delay: int | None):
        task: Task = message.options["task"]
        task_created: bool = message.options["task_created"]
        if task_created:
            TaskLog.create_from_log_event(
                task,
                Task._make_log(
                    class_to_path(type(self)),
                    TaskStatus.INFO,
                    "Task has been queued",
                    delay=delay,
                ),
            )
        else:
            TaskLog.objects.filter(task=task).update(previous=True)
            TaskLog.create_from_log_event(
                task,
                Task._make_log(
                    class_to_path(type(self)),
                    TaskStatus.INFO,
                    "Task will be retried",
                    delay=delay,
                ),
            )

    def before_process_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.log(class_to_path(type(self)), TaskStatus.INFO, "Task is being processed")

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
            task.log(
                class_to_path(type(self)),
                TaskStatus.INFO,
                "Task finished processing without errors",
            )
            return
        task.log(
            class_to_path(type(self)),
            TaskStatus.ERROR,
            exception,
        )
        if should_ignore_exception(exception):
            return
        event_kwargs = {
            "actor": task.actor_name,
        }
        if task.rel_obj:
            event_kwargs["rel_obj"] = task.rel_obj
        Event.new(
            EventAction.SYSTEM_TASK_EXCEPTION,
            message=f"Task {task.actor_name} encountered an error",
            **event_kwargs,
        ).with_exception(exception).save()

    def after_skip_message(self, broker: Broker, message: Message):
        task: Task = message.options["task"]
        task.log(class_to_path(type(self)), TaskStatus.INFO, "Task has been skipped")


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


class _healthcheck_handler(BaseHTTPRequestHandler):
    def log_request(self, code="-", size="-"):
        HEALTHCHECK_LOGGER.info(
            self.path,
            method=self.command,
            status=code,
        )

    def log_error(self, format, *args):
        HEALTHCHECK_LOGGER.warning(format, *args)

    def do_HEAD(self):
        try:
            for db_conn in connections.all():
                # Force connection reload
                db_conn.connect()
                _ = db_conn.cursor()
            self.send_response(200)
        except DB_ERRORS:  # pragma: no cover
            self.send_response(503)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_GET = do_HEAD


class WorkerHealthcheckMiddleware(Middleware):

    thread: Thread | None

    def after_worker_boot(self, broker, worker):
        host, _, port = CONFIG.get("listen.http").rpartition(":")

        try:
            port = int(port)
        except ValueError:
            LOGGER.error(f"Invalid port entered: {port}")

        self.thread = Thread(target=WorkerHealthcheckMiddleware.run, args=(host, port))
        self.thread.start()

    @staticmethod
    def run(addr: str, port: int):
        setthreadtitle("authentik Worker Healthcheck server")
        try:
            httpd = HTTPServer((addr, port), _healthcheck_handler)
            httpd.serve_forever()
        except OSError as exc:
            get_logger(__name__, type(WorkerHealthcheckMiddleware)).warning(
                "Port is already in use, not starting healthcheck server",
                exc=exc,
            )


class WorkerStatusMiddleware(Middleware):
    thread: Thread | None

    def after_worker_boot(self, broker, worker):
        self.thread = Thread(target=WorkerStatusMiddleware.run)
        self.thread.start()

    @staticmethod
    def run():
        setthreadtitle("authentik Worker status")
        with transaction.atomic():
            hostname = socket.gethostname()
            WorkerStatus.objects.filter(hostname=hostname).delete()
            status, _ = WorkerStatus.objects.update_or_create(
                hostname=hostname,
                version=authentik_full_version(),
            )
        while True:
            try:
                WorkerStatusMiddleware.keep(status)
            except DB_ERRORS:  # pragma: no cover
                sleep(10)
                try:
                    connections.close_all()
                except DB_ERRORS:
                    pass

    @staticmethod
    def keep(status: WorkerStatus):
        lock_id = f"goauthentik.io/worker/status/{status.pk}"
        with pglock.advisory(lock_id, side_effect=pglock.Raise):
            while True:
                status.last_seen = now()
                status.save(update_fields=("last_seen",))
                sleep(30)


class MetricsMiddleware(BaseMetricsMiddleware):
    thread: Thread | None

    @property
    def forks(self) -> list[Callable[[], None]]:
        return []

    def after_worker_boot(self, broker, worker):
        addr, _, port = CONFIG.get("listen.metrics").rpartition(":")

        try:
            port = int(port)
        except ValueError:
            LOGGER.error(f"Invalid port entered: {port}")
        self.thread = Thread(target=MetricsMiddleware.run, args=(addr, port))
        self.thread.start()
