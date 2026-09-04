"""Managed secret models."""

from typing import TYPE_CHECKING
from uuid import uuid4

from django.db import IntegrityError, models, transaction
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

from authentik.blueprints.models import ManagedModel
from authentik.lib.generators import generate_id
from authentik.lib.models import CreatedUpdatedModel, SerializerModel

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.serializers import Serializer


class SecretType(models.TextChoices):
    """How a secret value is entered and displayed."""

    TEXT = "text", _("Text")
    MULTILINE = "multiline", _("Multi-line text")
    FILE = "file", _("File")


secret_value_changed = Signal()


def generate_secret_value() -> str:
    """Generate a value safe for HTTP Basic authentication and similar protocols."""
    return generate_id(128)


def create_named_secret(name: str, value: str | None = None) -> Secret:
    """Create a secret with a readable, collision-safe name."""
    for suffix in range(1, 100):
        candidate = name if suffix == 1 else f"{name} ({suffix})"
        try:
            with transaction.atomic():
                values = {} if value is None else {"value": value}
                return Secret.objects.create(name=candidate, **values)
        except IntegrityError:
            continue
    raise IntegrityError(f"Could not allocate a name for {name!r}")


class Secret(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """A named value that can be shared by configuration objects."""

    secret_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True)
    type = models.TextField(choices=SecretType.choices, default=SecretType.TEXT)
    value = models.TextField(default=generate_secret_value)

    def replace_value(self, value: str, request: Request | None = None) -> None:
        """Replace and audit the value, then notify consumers after commit."""
        if value == self.value:
            return
        from authentik.events.middleware import audit_ignore
        from authentik.events.models import Event, EventAction

        with transaction.atomic():
            self.value = value
            with audit_ignore():
                self.save(update_fields=["value", "last_updated"])
            event = Event.new(EventAction.SECRET_ROTATE, secret=self)
            if request:
                event.from_http(request)
            else:
                event.save()
            secret_value_changed.send(sender=Secret, secret=self)

    def rotate(self, request: Request | None = None) -> str:
        """Generate and store a new text value."""
        if self.type != SecretType.TEXT:
            raise ValueError("Only text secrets can be rotated.")
        value = generate_secret_value()
        self.replace_value(value, request)
        return value

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.secrets.api import SecretSerializer

        return SecretSerializer

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Secret")
        verbose_name_plural = _("Secrets")
        permissions = [
            ("view_secret_value", _("View secret's value")),
            ("rotate_secret", _("Rotate secret's value")),
        ]
