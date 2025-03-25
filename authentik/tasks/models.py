from enum import StrEnum, auto
from uuid import uuid4

import pgtrigger
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


class TaskStatus(models.TextChoices):
    """Task soft-state. Self-reported by the task"""

    UNKNOWN = "unknown"
    SUCCESSFUL = "successful"
    WARNING = "warning"
    ERROR = "error"


# class Task(SerializerModel):
class Task(models.Model):
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

    # Probably only have one `logs` field
    uid = models.TextField(blank=True)
    description = models.TextField(blank=True)
    status = models.TextField(blank=True, choices=TaskStatus.choices)
    messages = models.JSONField(default=list)

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        indexes = (models.Index(fields=("state", "mtime")),)
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
        )

    def __str__(self):
        return str(self.message_id)

    # @property
    # def serializer(self):
    #     # TODO: fixme
    #     pass

    def set_uid(self, uid: str):
        """Set UID, so in the case of an unexpected error its saved correctly"""
        self.uid = uid

    def set_status(self, status: TaskStatus, *messages: LogEvent | str):
        """Set result for current run, will overwrite previous result."""
        self.status = status
        self.messages = list(messages)
        for idx, msg in enumerate(self.messages):
            if not isinstance(msg, LogEvent):
                self.messages[idx] = LogEvent(msg, logger=self.__name__, log_level="info")
        self.messages = sanitize_item(self.messages)

    def set_error(self, exception: Exception, *messages: LogEvent | str):
        """Set result to error and save exception"""
        self.status = TaskStatus.ERROR
        self.messages = list(messages)
        self.messages.extend(
            [LogEvent(exception_to_string(exception), logger=self.__name__, log_level="error")]
        )
        self.messages = sanitize_item(self.messages)
