import contextvars
from typing import Any

from dramatiq.actor import Actor
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware
from structlog.stdlib import get_logger

from authentik.tasks.models import Task

LOGGER = get_logger()


class FullyQualifiedActorName(Middleware):
    def before_declare_actor(self, broker: Broker, actor: Actor):
        actor.actor_name = f"{actor.fn.__module__}.{actor.fn.__name__}"


class CurrentTask(Middleware):
    _TASK: contextvars.ContextVar[list[Task] | None] = contextvars.ContextVar(
        "_TASK",
        default=None,
    )

    @classmethod
    def get_task(cls) -> Task:
        task = cls._TASK.get()
        if not task:
            raise RuntimeError("CurrentTask.get_task() should only be called in a running task")
        return task[-1]

    def before_process_message(self, broker: Broker, message: Message):
        tasks = self._TASK.get()
        if tasks is None:
            tasks = []
        tasks.append(Task.objects.get(message_id=message.message_id))
        self._TASK.set(tasks)

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        tasks: list[Task] | None = self._TASK.get()
        if tasks is None or len(tasks) == 0:
            LOGGER.warn("Task was None, not saving. This should not happen")
            return
        else:
            tasks[-1].save()
        self._TASK.set(tasks[:-1])
