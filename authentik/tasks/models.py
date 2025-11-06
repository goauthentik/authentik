from collections.abc import Iterable
from typing import Self
from uuid import UUID, uuid4

import pgtrigger
from django.contrib.contenttypes.fields import ContentType, GenericForeignKey, GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.models import TaskBase, TaskState

from authentik.events.logs import LogEvent
from authentik.events.utils import sanitize_item
from authentik.lib.models import SerializerModel
from authentik.lib.utils.errors import exception_to_dict
from authentik.tenants.models import Tenant


class TaskStatus(models.TextChoices):
    """Task aggregated status. Reported by the task runners"""

    QUEUED = TaskState.QUEUED
    CONSUMED = TaskState.CONSUMED
    PREPROCESS = TaskState.PREPROCESS
    RUNNING = TaskState.RUNNING
    POSTPROCESS = TaskState.POSTPROCESS
    REJECTED = TaskState.REJECTED
    DONE = TaskState.DONE
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Task(SerializerModel, TaskBase):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text=_("Tenant this task belongs to"),
    )

    rel_obj_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    rel_obj_id = models.TextField(null=True)
    rel_obj = GenericForeignKey("rel_obj_content_type", "rel_obj_id")

    _uid = models.TextField(blank=True, null=True)
    _messages = models.JSONField(default=list)
    _previous_messages = models.JSONField(default=list)

    aggregated_status = models.TextField(choices=TaskStatus.choices)

    class Meta(TaskBase.Meta):
        default_permissions = ("view",)
        permissions = [
            ("retry_task", _("Retry failed task")),
        ]
        indexes = TaskBase.Meta.indexes + (
            models.Index(fields=("rel_obj_content_type", "rel_obj_id")),
        )
        triggers = TaskBase.Meta.triggers + (
            pgtrigger.Trigger(
                name="update_aggregated_status",
                operation=pgtrigger.Insert | pgtrigger.Update,
                when=pgtrigger.Before,
                func=f"""
                    NEW.aggregated_status := CASE
                        WHEN NEW.state != '{TaskState.DONE.value}' THEN NEW.state
                        ELSE COALESCE((
                            SELECT CASE
                                WHEN bool_or(msg->>'log_level' = 'error') THEN 'error'
                                WHEN bool_or(msg->>'log_level' = 'warning') THEN 'warning'
                                WHEN bool_or(msg->>'log_level' = 'info') THEN 'info'
                                ELSE '{TaskState.DONE.value}'
                            END
                            FROM jsonb_array_elements(NEW._messages) AS msg
                        ), '{TaskState.DONE.value}')
                    END;

                    RETURN NEW;
                """,  # nosec
            ),
        )

    @property
    def uid(self) -> str:
        uid = str(self.actor_name)
        if self._uid:
            uid += f":{self._uid}"
        return uid

    @property
    def serializer(self):
        from authentik.tasks.api.tasks import TaskSerializer

        return TaskSerializer

    def set_uid(self, uid: str | UUID, save: bool = False):
        self._uid = str(uid)
        if save:
            self.save()

    @classmethod
    def _make_log(
        cls, logger: str, log_level: TaskStatus, message: str | Exception, **attributes
    ) -> LogEvent:
        if isinstance(message, Exception):
            attributes = {
                "exception": exception_to_dict(message),
                **attributes,
            }
            message = str(message)
        return LogEvent(
            message,
            logger=logger,
            log_level=log_level.value,
            attributes=attributes,
        )

    def logs(self, logs: Iterable[LogEvent]):
        TaskLog.bulk_create_from_log_events(self, logs)

    def log(
        self,
        logger: str,
        log_level: TaskStatus,
        message: str | Exception,
        **attributes,
    ) -> None:
        TaskLog.create_from_log_event(
            self,
            self._make_log(
                logger,
                log_level,
                message,
                **attributes,
            ),
        )

    def info(self, message: str | Exception, **attributes) -> None:
        self.log(self.uid, TaskStatus.INFO, message, **attributes)

    def warning(self, message: str | Exception, **attributes) -> None:
        self.log(self.uid, TaskStatus.WARNING, message, **attributes)

    def error(self, message: str | Exception, **attributes) -> None:
        self.log(self.uid, TaskStatus.ERROR, message, **attributes)


class TaskLog(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="tasklogs")
    event = models.TextField()
    log_level = models.TextField()
    logger = models.TextField()
    timestamp = models.DateTimeField()
    attributes = models.JSONField()

    previous = models.BooleanField(default=False, db_index=True)

    class Meta:
        default_permissions = []
        verbose_name = _("Task log")
        verbose_name_plural = _("Task logs")
        indexes = (models.Index(fields=("task", "previous")),)

    def __str__(self):
        return str(self.pk)

    @classmethod
    def create_from_log_event(cls, task: Task, log_event: LogEvent) -> Self | None:
        if not task.message:
            return None
        return cls.objects.create(
            task=task,
            event=log_event.event,
            log_level=log_event.log_level,
            logger=log_event.logger,
            timestamp=log_event.timestamp,
            attributes=sanitize_item(log_event.attributes),
        )

    @classmethod
    def bulk_create_from_log_events(
        cls,
        task: Task,
        log_events: Iterable[LogEvent],
    ) -> list[Self] | None:
        if not task.message:
            return None
        return cls.objects.bulk_create(
            [
                cls(
                    task=task,
                    event=log_event.event,
                    log_level=log_event.log_level,
                    logger=log_event.logger,
                    timestamp=log_event.timestamp,
                    attributes=sanitize_item(log_event.attributes),
                )
                for log_event in log_events
            ]
        )

    def to_log_event(self) -> LogEvent:
        return LogEvent(
            event=self.event,
            log_level=self.log_level,
            logger=self.logger,
            timestamp=self.timestamp,
            attributes=self.attributes,
        )


class TasksModel(models.Model):
    tasks = GenericRelation(
        Task, content_type_field="rel_obj_content_type", object_id_field="rel_obj_id"
    )

    class Meta:
        abstract = True


class WorkerStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    hostname = models.TextField()
    version = models.TextField()
    last_seen = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = []
        verbose_name = _("Worker status")
        verbose_name_plural = _("Worker statuses")

    def __str__(self):
        return f"{self.id} - {self.hostname} - {self.version} - {self.last_seen}"
