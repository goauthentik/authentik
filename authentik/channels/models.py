from uuid import uuid4

import pgtrigger
from django.db import models


class GroupChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    group_key = models.TextField()
    channel = models.TextField()
    expire = models.DateTimeField()

    class Meta:
        default_permissions = []
        indexes = (
            models.Index(fields=("group_key", "expire")),
            models.Index(fields=("group_key", "channel")),
            models.Index(fields=("expire",)),
        )

    def __str__(self):
        return str(self.pk)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    channel_key = models.TextField()
    message = models.BinaryField()
    expire = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = []
        indexes = (
            models.Index(fields=("channel_key", "expire")),
            models.Index(fields=("expire",)),
        )
        triggers = (
            pgtrigger.Trigger(
                name="notify_insert",
                level=pgtrigger.Row,
                operation=pgtrigger.Insert,
                when=pgtrigger.After,
                timing=pgtrigger.Deferred,
                func="""
                    PERFORM pg_notify(NEW.channel_key, NEW.id::text);
                    RETURN NEW;
                """,
            ),
        )

    def __str__(self):
        return str(self.pk)
