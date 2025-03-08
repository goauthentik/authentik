from uuid import uuid4
from django.db import models
from django.utils import timezone


class Queue(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued"
        CONSUMED = "consumed"
        REJECTED = "rejected"
        DONE = "done"

    message_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    queue_name = models.TextField(default="default")
    state = models.CharField(default=State.QUEUED, choices=State.choices)
    mtime = models.DateTimeField(default=timezone.now)
    message = models.JSONField(blank=True, null=True)
    result = models.JSONField(blank=True, null=True)
    result_ttl = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = (
            models.Index(fields=("state", "mtime")),
            models.Index(fields=("mesage__actor_name",)),
        )
