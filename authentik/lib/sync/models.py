from uuid import uuid4

from django.db import models
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import get_broker
from dramatiq.message import Message

from authentik.core.models import ExpiringModel
from authentik.tasks.models import Task


class Sync(ExpiringModel):
    uuid = models.UUIDField(default=uuid4)

    tasks = models.ManyToManyField(Task, related_name="+")

    started_at = models.DateTimeField(auto_now_add=True)

    def is_done(self) -> bool:
        return any(
            state not in (TaskState.DONE, TaskState.REJECTED)
            for state in self.tasks.values_list("state", flat=True)
        )

    def enqueue(self, messages: list[Message], existing_tasks_as_dependencies: bool = True) -> None:
        broker = get_broker()
        if existing_tasks_as_dependencies:
            dependencies = self.tasks.values_list("pk", flat=True)
            for message in messages:
                message.options.setdefault("dependencies", []).extend(dependencies)
        new_tasks: list[Task] = []
        for message in messages:
            new_message = broker.enqueue(message)
            new_tasks.append(new_message.options["task"])
        self.tasks.add(*new_tasks)

    class Meta:
        abstract = True
