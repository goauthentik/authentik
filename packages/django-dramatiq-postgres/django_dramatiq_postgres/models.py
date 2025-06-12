from enum import StrEnum, auto
from uuid import uuid4

import pgtrigger
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_dramatiq_postgres.conf import Conf

CHANNEL_PREFIX = f"{Conf.channel_prefix}.tasks"


class ChannelIdentifier(StrEnum):
    ENQUEUE = auto()
    LOCK = auto()


class TaskState(models.TextChoices):
    """Task system-state. Reported by the task runners"""

    QUEUED = "queued"
    CONSUMED = "consumed"
    REJECTED = "rejected"
    DONE = "done"


class Task(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid4)
    queue_name = models.TextField(default="default", help_text=_("Queue name"))

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

    class Meta:
        abstract = True
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
