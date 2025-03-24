import contextvars

from dramatiq.message import Message
from dramatiq.middleware import Middleware

from authentik.tasks.models import Task


class CurrentTask(Middleware):
    _TASK: contextvars.ContextVar[Task | None] = contextvars.ContextVar("_TASK", default=None)

    @classmethod
    def get_task(cls) -> Task | None:
        return cls._TASK.get()

    def before_process_message(self, _, message: Message):
        self._TASK.set(Task.objects.get(message_id=message.message_id))

    def after_process_message(self, *args, **kwargs):
        self._TASK.get().save()
        self._TASK.set(None)
