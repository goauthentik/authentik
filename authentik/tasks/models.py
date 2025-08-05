from typing import Any
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
    def _make_message(
        cls, logger: str, log_level: TaskStatus, message: str | Exception, **attributes
    ) -> dict[str, Any]:
        if isinstance(message, Exception):
            attributes = {
                "exception": exception_to_dict(message),
                **attributes,
            }
            message = str(message)
        log = LogEvent(
            message,
            logger=logger,
            log_level=log_level.value,
            attributes=attributes,
        )
        return sanitize_item(log)

    def logs(self, logs: list[LogEvent]):
        for log in logs:
            self._messages.append(sanitize_item(log))

    def log(
        self,
        logger: str,
        log_level: TaskStatus,
        message: str | Exception,
        save: bool = False,
        **attributes,
    ):
        self._messages: list
        self._messages.append(
            self._make_message(
                logger,
                log_level,
                message,
                **attributes,
            )
        )
        if save:
            self.save()

    def info(self, message: str | Exception, save: bool = False, **attributes):
        self.log(self.uid, TaskStatus.INFO, message, save=save, **attributes)

    def warning(self, message: str | Exception, save: bool = False, **attributes):
        self.log(self.uid, TaskStatus.WARNING, message, save=save, **attributes)

    def error(self, message: str | Exception, save: bool = False, **attributes):
        self.log(self.uid, TaskStatus.ERROR, message, save=save, **attributes)


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
