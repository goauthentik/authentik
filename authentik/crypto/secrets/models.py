"""Managed secret models."""

from base64 import b64decode
from binascii import Error as BinasciiError
from typing import TYPE_CHECKING
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _
from yaml import YAMLError, safe_load

from authentik.blueprints.models import ManagedModel
from authentik.crypto.secrets.signals import secret_value_changed, secret_value_validating
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.models import CreatedUpdatedModel, SerializerModel

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.serializers import Serializer


class SecretType(models.TextChoices):
    """Input form and generation policy, not a content format.

    Text values can be generated and rotated. Multiline and file values must
    be supplied by the administrator and are never replaced with random text.
    Consumers validate content such as JSON or YAML separately.
    """

    TEXT = "text", _("Text")
    MULTILINE = "multiline", _("Multi-line text")
    FILE = "file", _("File")


def generate_secret_value() -> str:
    """Generate a value safe for HTTP Basic authentication and similar protocols."""
    return generate_id(128)


def create_named_secret(name: str) -> Secret:
    """Create a secret with a readable, collision-safe name."""
    for suffix in range(1, 100):
        candidate = name if suffix == 1 else f"{name} ({suffix})"
        try:
            with transaction.atomic():
                return Secret.objects.create(name=candidate)
        except IntegrityError:
            continue
    raise IntegrityError(f"Could not allocate a name for {name!r}")


class Secret(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """A named value that can be shared by configuration objects."""

    secret_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True)
    type = models.TextField(choices=SecretType.choices, default=SecretType.TEXT)
    value = models.TextField(default=generate_secret_value)

    def get_json(self) -> dict:
        """Read a JSON or YAML credential, including an uploaded file."""
        try:
            value = (
                b64decode(self.value, validate=True) if self.type == SecretType.FILE else self.value
            )
            data = safe_load(value)
        except BinasciiError, YAMLError, UnicodeError:
            raise ValueError("Invalid JSON or YAML credential") from None
        if not isinstance(data, dict):
            raise ValueError("Credential must be a JSON or YAML object")
        return data

    def validate_value(self, value: str) -> None:
        """Validate a replacement before changing the stored value."""
        if self.type == SecretType.FILE:
            try:
                b64decode(value, validate=True)
            except (BinasciiError, ValueError) as exc:
                raise ValidationError(_("Value must be base64-encoded.")) from exc
        if self._state.adding:
            return
        secret_value_validating.send(sender=Secret, secret=self, value=value)

    def replace_value(self, value: str, request: Request | None = None) -> None:
        """Replace and audit the value, then signal consumers."""
        if value == self.value:
            return

        self.validate_value(value)
        previous_value, previous_updated = self.value, self.last_updated
        with transaction.atomic():
            try:
                self.value = value
                with audit_ignore():
                    self.save(update_fields=["value", "last_updated"])
                event = Event.new(EventAction.SECRET_ROTATE, secret=self)
                if request:
                    event.from_http(request)
                else:
                    event.save()
                secret_value_changed.send(sender=Secret, secret=self)
            except Exception:
                self.value, self.last_updated = previous_value, previous_updated
                raise

    def rotate(self, request: Request | None = None) -> str:
        """Generate and store a new text value."""
        if self.type != SecretType.TEXT:
            raise ValueError("Only text secrets can be rotated.")
        value = generate_secret_value()
        self.replace_value(value, request)
        return value

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.crypto.secrets.api import SecretSerializer

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
