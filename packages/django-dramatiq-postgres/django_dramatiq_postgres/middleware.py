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
