from datetime import datetime, timedelta
from uuid import uuid4

import pgtrigger
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


def _default_group_expiry() -> datetime:
    return now() + timedelta(seconds=86400)


def _default_message_expiry() -> datetime:
    return now() + timedelta(minutes=1)


class GroupChannel(models.Model):
    """
    A model that represents a group channel.

    Groups are used to send messages to multiple channels.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    group_key = models.TextField(db_index=True)
    channel = models.TextField(db_index=True)
    expires = models.DateTimeField(db_index=True, default=_default_group_expiry)

    class Meta:
        verbose_name = _("Group channel")
        verbose_name_plural = _("Group channels")
        indexes = (
            models.Index(fields=("group_key", "channel")),
            models.Index(fields=("group_key", "expires")),
        )

    def __str__(self) -> str:
        return f"Group '{self.group_key}' on channel '{self.channel}'"


class Message(models.Model):
    """
    A model that represents a message.

    Messages are used to send messages to a specific channel.
    E.g for user to user private messages.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    channel = models.TextField(db_index=True)
    message = models.BinaryField()
    expires = models.DateTimeField(db_index=True, default=_default_message_expiry)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        indexes = (models.Index(fields=("channel", "expires")),)
        triggers = (
            pgtrigger.Trigger(
                name="notify_new_channels_message",
                operation=pgtrigger.Insert,
                when=pgtrigger.After,
                timing=pgtrigger.Deferred,
                declare=[
                    ("payload", "text"),
                    ("encoded_message", "text"),
                    ("epoch", "text"),
                ],
                func="""
                    encoded_message := encode(NEW.message, 'base64');
                    epoch := extract(epoch from NEW.expire)::text;
                    IF octet_length(NEW.pk::text) + octet_length(NEW.channel) + octet_length(encoded_message) + octet_length(epoch) + 3 <= 8000 THEN
                        payload := NEW.id::text || ':' || NEW.channel || ':' || encoded_message || ':' || epoch;
                    ELSE
                        payload := NEW.id::text || ':' || NEW.channel;
                    END IF;

                    PERFORM pg_notify('channels_messages', payload);
                    RETURN NEW;
                """,  # noqa: E501
            ),
        )

    def __str__(self) -> str:
        return f"Message '{self.pk}' on channel '{self.channel}'"
