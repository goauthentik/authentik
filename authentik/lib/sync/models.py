from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils.timezone import now
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

    tasks = ArrayField(base_field=models.UUIDField(), default=list)

    status = models.TextField(choices=SyncStatus, default=SyncStatus.RUNNING)

    started_at = models.DateTimeField(auto_now_add=True)

    finished_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True

    @classmethod
    def cleanup(cls) -> int:
        return cls.objects.exclude(pk__in=cls.objects.order_by("-started_at")[:20]).delete()[0]

    @property
    def tasks_status(self) -> SyncStatus:
        states = Task.objects.filter(pk__in=self.tasks).values_list("aggregated_status", flat=True)
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

    def persist_status(self) -> None:
        self.status = self.tasks_status
        update_fields = ["status"]
        if self.status != SyncStatus.RUNNING:
            self.finished_at = now()
            update_fields.append("finished_at")
        self.save(update_fields=update_fields)

    def enqueue(self, messages: list[Message], existing_tasks_as_dependencies: bool = True) -> None:
        broker = get_broker()
        if existing_tasks_as_dependencies:
            for message in messages:
                message.options.setdefault("dependencies", []).extend(self.tasks)
        new_tasks = [message.message_id for message in messages]
        with transaction.atomic():
            self.refresh_from_db()
            self.tasks += new_tasks
            self.save(update_fields=["tasks"])
            for message in messages:
                broker.enqueue(message)
