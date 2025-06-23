from typing import Any

from dramatiq import get_logger
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware

from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string
from authentik.tasks.models import Task, TaskStatus
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


class LoggingMiddleware(Middleware):
    def after_enqueue(self, broker: Broker, message: Message, delay: int):
        task: Task = message.options["task"]
        task_created: bool = message.options["task_created"]
        task._messages.append(
            Task._make_message(
                str(type(self)),
                TaskStatus.INFO,
                "Task is being queued" if task_created else "Task is being retried",
                delay=delay,
            )
        )
        task.save(update_fields=("_messages",))

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


class DescriptionMiddleware(Middleware):
    @property
    def actor_options(self):
        return {"description"}
