from datetime import datetime
from uuid import uuid4

from django.db import models
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import get_broker
from dramatiq.message import Message

from authentik.lib.models import InternallyManagedMixin
from authentik.tasks.models import Task, TaskStatus


class SyncStatus(models.TextChoices):
    RUNNING = TaskStatus.RUNNING
    ERROR = TaskStatus.ERROR
    WARNING = TaskStatus.WARNING
    DONE = TaskStatus.DONE


class Sync(InternallyManagedMixin, models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    # Must be defined by subclasses with a through model
    # tasks = models.ManyToManyField(Task, related_name="+")
    tasks: models.ManyToManyField

    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    @classmethod
    def cleanup(cls) -> int:
        count = cls.objects.filter(tasks__count=0).delete()[0]
        count += cls.objects.exclude(pk__in=cls.objects.order_by("-started_at")[:20]).delete()[0]
        return count

    @property
    def done(self) -> bool:
        return not any(
            state not in (TaskState.DONE, TaskState.REJECTED)
            for state in self.tasks.values_list("state", flat=True)
        )

    @property
    def finished_at(self) -> datetime | None:
        last_task = self.tasks.order_by("-mtime").first()
        if last_task:
            return last_task.mtime
        return None

    @property
    def status(self) -> SyncStatus:
        states = self.tasks.values_list("aggregated_status", flat=True)
        if any(
            state
            in (
                TaskStatus.WAITING_FOR_DEPENDENCIES,
                TaskStatus.QUEUED,
                TaskStatus.CONSUMED,
                TaskStatus.PREPROCESS,
                TaskStatus.RUNNING,
                TaskStatus.POSTPROCESS,
            )
            for state in states
        ):
            return SyncStatus.RUNNING
        if any(
            state
            in (
                TaskStatus.REJECTED,
                TaskStatus.ERROR,
            )
            for state in states
        ):
            return SyncStatus.ERROR
        if any(state == TaskStatus.WARNING for state in states):
            return SyncStatus.WARNING
        return SyncStatus.DONE

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
