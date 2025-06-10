from enum import StrEnum, auto
from uuid import UUID, uuid4

import pgtrigger
from django.contrib.contenttypes.fields import ContentType, GenericForeignKey
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from authentik.events.logs import LogEvent
from authentik.events.utils import sanitize_item
from authentik.lib.models import SerializerModel
from authentik.lib.utils.errors import exception_to_string
from authentik.tenants.models import Tenant

CHANNEL_PREFIX = "authentik.tasks"


class ChannelIdentifier(StrEnum):
    ENQUEUE = auto()
    LOCK = auto()


class TaskState(models.TextChoices):
    """Task system-state. Reported by the task runners"""

    QUEUED = "queued"
    CONSUMED = "consumed"
    REJECTED = "rejected"
    DONE = "done"


class Task(SerializerModel):
    message_id = models.UUIDField(primary_key=True, default=uuid4)
    queue_name = models.TextField(default="default", help_text=_("Queue name"))

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text=_("Tenant this task belongs to"),
    )
    actor_name = models.TextField(help_text=_("Dramatiq actor name"))
    message = models.BinaryField(null=True, help_text=_("Message body"))
    state = models.CharField(
        default=TaskState.QUEUED,
        choices=TaskState.choices,
        help_text=_("Task status"),
    )
    mtime = models.DateTimeField(default=timezone.now, help_text=_("Task last modified time"))

    result = models.BinaryField(null=True, help_text=_("Task result"))
    result_expiry = models.DateTimeField(null=True, help_text=_("Result expiry time"))

    rel_obj_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    rel_obj_id = models.TextField(null=True)
    rel_obj = GenericForeignKey("rel_obj_content_type", "rel_obj_id")

    _uid = models.TextField(blank=True, null=True)
    _messages = models.JSONField(default=list)

    aggregated_status = models.TextField()

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        default_permissions = ("view",)
        permissions = [
            ("retrigger_task", _("Restart failed task")),
        ]
        indexes = (
            models.Index(fields=("state", "mtime")),
            models.Index(fields=("rel_obj_content_type", "rel_obj_id")),
        )
        triggers = (
            pgtrigger.Trigger(
                name="notify_enqueueing",
                operation=pgtrigger.Insert | pgtrigger.Update,
                when=pgtrigger.After,
                condition=pgtrigger.Q(new__state=TaskState.QUEUED),
                timing=pgtrigger.Deferred,
                func=f"""
                    PERFORM pg_notify(
                        '{CHANNEL_PREFIX}.' || NEW.queue_name || '.{ChannelIdentifier.ENQUEUE.value}',
                        NEW.message_id::text
                    );
                    RETURN NEW;
                """,  # noqa: E501
            ),
            pgtrigger.Trigger(
                name="update_aggregated_status",
                operation=pgtrigger.Insert | pgtrigger.Update,
                when=pgtrigger.After,
                timing=pgtrigger.Immediate,
                declare=[("aggregated_status", "TEXT"), ("max_log_level", "TEXT")],
                func=f"""
                    NEW.aggregated_status := CASE
                        WHEN NEW.status != '{TaskState.DONE.value}' THEN NEW.status
                        ELSE COALESCE((
                            SELECT CASE
                                WHEN bool_or(msg->'log_level' = 'error') THEN 'error'
                                WHEN bool_or(msg->'log_level' = 'warning') THEN 'warning'
                                WHEN bool_or(msg->'log_level' = 'info') THEN 'info'
                                ELSE '{TaskState.DONE.value}'
                            END
                            FROM jsonb_array_elements(NEW._messages) AS msg
                        ), '{TaskState.DONE.value}')
                    END;

                    RETURN NEW;
                """,
            ),
        )

    def __str__(self):
        return str(self.message_id)

    @property
    def uid(self) -> str:
        uid = str(self.actor_name)
        if self._uid:
            uid += f":{self._uid}"
        return uid

    @property
    def serializer(self):
        from authentik.tasks.api import TaskSerializer

        return TaskSerializer

    def set_uid(self, uid: str | UUID, save: bool = False):
        self._uid = str(uid)
        if save:
            self.save()

    def log(self, log_level: str, message: str | Exception, save: bool = False, **attributes):
        self._messages: list
        if isinstance(message, Exception):
            message = exception_to_string(message)
        log = LogEvent(message, logger=self.uid, log_level=log_level, attributes=attributes)
        self._messages.append(sanitize_item(log))
        if save:
            self.save()

    def info(self, message: str | Exception, save: bool = False, **attributes):
        self.log("info", message, save=save, **attributes)

    def warning(self, message: str | Exception, save: bool = False, **attributes):
        self.log("warning", message, save=save, **attributes)

    def error(self, message: str | Exception, save: bool = False, **attributes):
        self.log("error", message, save=save, **attributes)
