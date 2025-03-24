import contextvars
from typing import Any

from dramatiq.actor import Actor
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import Middleware

from authentik.tasks.models import Task


class FullyQualifiedActorName(Middleware):
    def before_declare_actor(self, broker: Broker, actor: Actor):
        actor.actor_name = f"{actor.fn.__module__}.{actor.fn.__name__}"


class CurrentTask(Middleware):
    _TASK: contextvars.ContextVar[Task | None] = contextvars.ContextVar("_TASK", default=None)

    @classmethod
    def get_task(cls) -> Task | None:
        return cls._TASK.get()

    def before_process_message(self, broker: Broker, message: Message):
        self._TASK.set(Task.objects.get(message_id=message.message_id))

    def after_process_message(
        self,
        broker: Broker,
        message: Message,
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ):
        self._TASK.get().save()
        self._TASK.set(None)
