import contextvars
from typing import Any

from django.db import (
    close_old_connections,
    connections,
)
from dramatiq.actor import Actor
from dramatiq.broker import Broker
from dramatiq.logging import get_logger
from dramatiq.message import Message
from dramatiq.middleware.middleware import Middleware

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import TaskBase


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
            raise RuntimeError("CurrentTask.get_task() can only be called in a running task")
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
            self.logger.warning("Task was None, not saving. This should not happen.")
            return
        else:
            tasks[-1].save()
        self._TASKS.set(tasks[:-1])
