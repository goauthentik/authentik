from socket import gethostname
from time import sleep
from typing import Any

import pglock
from django.utils.timezone import now
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string
from authentik.tasks.models import Task, TaskStatus, WorkerStatus
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant


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
