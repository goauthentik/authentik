from enum import StrEnum, auto
from uuid import uuid4
import pgtrigger

from django.db import models
from django.utils import timezone

from authentik.lib.models import SerializerModel
from authentik.tenants.models import Tenant

CHANNEL_PREFIX = "authentik.tasks"


class ChannelIdentifier(StrEnum):
    ENQUEUE = auto()
    LOCK = auto()


class Task(SerializerModel):
    class State(models.TextChoices):
        QUEUED = "queued"
        CONSUMED = "consumed"
        REJECTED = "rejected"
        DONE = "done"

    message_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, editable=False)
    queue_name = models.TextField(default="default", editable=False)
    state = models.CharField(default=State.QUEUED, choices=State.choices, editable=False)
    mtime = models.DateTimeField(default=timezone.now, editable=False)
    message = models.JSONField(blank=True, null=True, editable=False)
    result = models.JSONField(blank=True, null=True, editable=False)
    result_ttl = models.DateTimeField(blank=True, null=True, editable=False)
    description = models.TextField(blank=True)
    messages = models.JSONField(blank=True, null=True, editable=False)

    class Meta:
        indexes = (models.Index(fields=("state", "mtime")),)
        triggers = (
            pgtrigger.Trigger(
                name="notify_enqueueing",
                operation=pgtrigger.Insert | pgtrigger.Update,
                when=pgtrigger.After,
                condition=pgtrigger.Q(new__state="queued"),
                timing=pgtrigger.Deferred,
                func=f"""
                    PERFORM pg_notify(
                        '{CHANNEL_PREFIX}' || NEW.queue_name || '.{ChannelIdentifier.ENQUEUE.value}',
                        CASE WHEN octet_length(NEW.message::text) >= 8000
                        THEN jsonb_build_object('message_id', NEW.message_id)::text
                        ELSE message::text
                        END
                    );
                    RETURN NEW;
                """,  # noqa: E501
            ),
        )

    def __str__(self):
        return str(self.message_id)

    @property
    def serializer(self):
        # TODO: fixme
        pass
