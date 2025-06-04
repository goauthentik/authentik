from enum import StrEnum, auto
from uuid import uuid4

from django.contrib.contenttypes.fields import ContentType, GenericForeignKey
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

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


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

    uid = models.TextField(blank=True, null=True)
    messages = models.JSONField(default=list)

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        default_permissions = ("view",)
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
        )

    def __str__(self):
        return str(self.message_id)

    @property
    def serializer(self):
        from authentik.tasks.api import TaskSerializer

        return TaskSerializer

    def set_uid(self, uid: str, save: bool = False):
        self.uid = uid
        if save:
            self.save()

    def log(self, status: TaskStatus, *messages: str | LogEvent | Exception, save: bool = False):
        self.messages: list
        for msg in messages:
            message = msg
            if isinstance(message, Exception):
                message = exception_to_string(message)
            if not isinstance(message, LogEvent):
                message = LogEvent(message, logger=self.actor_name, log_level=status.value)
            self.messages.append(sanitize_item(message))
        if save:
            self.save()

    def info(self, *messages: str | LogEvent | Exception, save: bool = False):
        self.log(TaskStatus.INFO, *messages, save=save)

    def warning(self, *messages: str | LogEvent | Exception, save: bool = False):
        self.log(TaskStatus.WARNING, *messages, save=save)

    def error(self, *messages: str | LogEvent | Exception, save: bool = False):
        self.log(TaskStatus.ERROR, *messages, save=save)
