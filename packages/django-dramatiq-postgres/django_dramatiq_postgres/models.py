import pickle  # nosec
from enum import StrEnum, auto
from uuid import uuid4

import pgtrigger
from cron_converter import Cron
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import datetime, now, timedelta
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor
from dramatiq.broker import Broker, get_broker
from dramatiq.message import Message

from django_dramatiq_postgres.conf import Conf

CHANNEL_PREFIX = f"{Conf().channel_prefix}.tasks"


class ChannelIdentifier(StrEnum):
    ENQUEUE = auto()
    LOCK = auto()


class TaskState(models.TextChoices):
    """Task system-state. Reported by the task runners"""

    QUEUED = "queued"
    CONSUMED = "consumed"
    REJECTED = "rejected"
    DONE = "done"


class TaskBase(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid4)
    queue_name = models.TextField(default="default", help_text=_("Queue name"))

    actor_name = models.TextField(help_text=_("Dramatiq actor name"))
    message = models.BinaryField(null=True, help_text=_("Message body"))
    state = models.CharField(
        default=TaskState.QUEUED,
        choices=TaskState.choices,
        help_text=_("Task status"),
    )
    mtime = models.DateTimeField(default=now, help_text=_("Task last modified time"))

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


def validate_crontab(value):
    try:
        Cron(value)
    except ValueError as exc:
        raise ValidationError(
            _("%(value)s is not a valid crontab"),
            params={"value": value},
        ) from exc


class ScheduleBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    actor_name = models.TextField(editable=False, help_text=_("Dramatiq actor to call"))
    args = models.BinaryField(editable=False, help_text=_("Args to send to the actor"))
    kwargs = models.BinaryField(editable=False, help_text=_("Kwargs to send to the actor"))
    options = models.BinaryField(editable=False, help_text=_("Options to send to the actor"))

    rel_obj_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    rel_obj_id = models.TextField(null=True)
    rel_obj = GenericForeignKey("rel_obj_content_type", "rel_obj_id")

    crontab = models.TextField(validators=[validate_crontab], help_text=_("When to schedule tasks"))
    paused = models.BooleanField(default=False, help_text=_("Pause this schedule"))

    next_run = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        triggers = (
            pgtrigger.Trigger(
                name="set_next_run_on_paused",
                operation=pgtrigger.Update,
                when=pgtrigger.Before,
                condition=pgtrigger.Q(new__paused=True) & pgtrigger.Q(old__paused=False),
                func="""
                    NEW.next_run = to_timestamp(0);
                    RETURN NEW;
                """,
            ),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_crontab = self.crontab

    def __str__(self):
        return f"Schedule {self.actor_name} ({self.id})"

    def save(self, *args, **kwargs):
        if self.crontab != self._original_crontab:
            self.next_run = self.compute_next_run(now())

        super().save(*args, **kwargs)

        self._original_crontab = self.crontab

    @classmethod
    def dispatch_by_actor(cls, actor: Actor):
        """Dispatch a schedule by looking up its actor.
        Only available for schedules without custom arguments."""
        schedule = cls.objects.filter(actor_name=actor.actor_name, paused=False).first()
        if schedule:
            schedule.send()

    def send(self, broker: Broker | None = None) -> Message:
        broker = broker or get_broker()
        actor: Actor = broker.get_actor(self.actor_name)
        return actor.send_with_options(
            args=pickle.loads(self.args),  # nosec
            kwargs=pickle.loads(self.kwargs),  # nosec
            rel_obj=self,
            **pickle.loads(self.options),  # nosec
        )

    def compute_next_run(self, next_run: datetime | None = None) -> datetime:
        next_run: datetime = self.next_run if not next_run else next_run
        while True:
            next_run = Cron(self.crontab).schedule(next_run).next()
            if next_run > now():
                return next_run
            # Force to calculate the one after
            next_run += timedelta(minutes=1)
