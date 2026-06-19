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


NOTIFY_CHANNEL = "channels_messages"


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

    @classmethod
    def delete_expired(cls) -> None:
        cls.objects.filter(expires__lt=now()).delete()


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
                func=f"""
                    encoded_message := encode(NEW.message, 'base64');
                    epoch := extract(epoch from NEW.expires)::text;
                    IF octet_length(NEW.id::text) + octet_length(NEW.channel) + octet_length(epoch) + octet_length(encoded_message) + 3 < 8000 THEN
                        payload := NEW.id::text || ':' || NEW.channel || ':' || epoch || ':' || encoded_message;
                    ELSE
                        payload := NEW.id::text || ':' || NEW.channel || ':' || epoch;
                    END IF;

                    PERFORM pg_notify('{NOTIFY_CHANNEL}', payload);
                    RETURN NEW;
                """,  # noqa: E501
            ),
        )

    def __str__(self) -> str:
        return f"Message '{self.pk}' on channel '{self.channel}'"

    @classmethod
    def delete_expired(cls) -> None:
        cls.objects.filter(expires__lt=now()).delete()
