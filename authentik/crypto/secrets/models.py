"""Managed secret models."""

from base64 import b64decode
from json import JSONDecodeError, dumps, loads
from typing import TYPE_CHECKING
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _
from yaml import YAMLError, safe_load

from authentik.admin.utils import get_system_settings
from authentik.blueprints.models import ManagedModel
from authentik.core.models import default_token_key
from authentik.crypto.secrets.signals import secret_value_changed, secret_value_validating
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.models import CreatedUpdatedModel, SerializerModel

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.serializers import Serializer


class SecretType(models.TextChoices):
    """What a secret value contains.

    Only text values can be generated and rotated. JSON and file values are
    issued by another system and must be supplied by the administrator.
    """

    TEXT = "text", _("Text")
    JSON = "json", _("JSON")
    FILE = "file", _("File")


def generate_secret_value(length: int | None = None) -> str:
    """Generate a text value, by default with the configured default token length.

    Values only use ASCII letters and digits, which every consumer accepts: OAuth2 requires
    VSCHAR client secrets, and HTTP Basic authentication splits credentials on colons.
    """
    return generate_id(length) if length else default_token_key()


def parse_json(value: str) -> dict:
    """Parse a JSON object, accepting YAML syntax for files such as kubeconfigs.

    The parsed object must also be serializable as JSON, since consumers and
    downgrade migrations store it in JSON fields. YAML dates are rejected.
    """
    try:
        data = loads(value)
    except JSONDecodeError:
        try:
            data = safe_load(value)
        except YAMLError:
            # The parser error quotes the input, which is the credential.
            raise ValueError("Value is not valid JSON or YAML") from None
    if not isinstance(data, dict):
        raise ValueError("Value must be a JSON or YAML object")
    try:
        dumps(data)
    except TypeError:
        raise ValueError("Value must only contain JSON types") from None
    return data


class Secret(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """A named value that can be shared by configuration objects."""

    secret_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True)
    type = models.TextField(choices=SecretType.choices, default=SecretType.TEXT)
    # Named so that event diffs hide it, like other credential fields.
    secret_value = models.TextField(default=generate_secret_value)

    def get_json(self) -> dict:
        """Read the object stored in a JSON secret."""
        if self.type != SecretType.JSON:
            raise ValueError("Secret is not a JSON secret")
        return parse_json(self.secret_value)

    def validate_value(self, value: str) -> None:
        """Validate a value against this secret's type."""
        try:
            if self.type == SecretType.JSON:
                parse_json(value)
            elif self.type == SecretType.FILE:
                b64decode(value, validate=True)
        except ValueError as exc:
            raise ValidationError(
                _("Value must be base64-encoded.")
                if self.type == SecretType.FILE
                else _("Value must be a JSON or YAML object.")
            ) from exc
        if not self._state.adding:
            secret_value_validating.send(sender=Secret, secret=self, value=value)

    def replace_value(self, value: str, request: Request | None = None) -> None:
        """Replace and audit the value, then signal consumers."""
        if value == self.secret_value:
            return
        self.validate_value(value)
        with transaction.atomic():
            self.secret_value = value
            with audit_ignore():
                self.save(update_fields=["secret_value", "last_updated"])
            event = Event.new(EventAction.SECRET_ROTATE, secret=self)
            if request:
                event.from_http(request)
            else:
                event.save()
            secret_value_changed.send(sender=Secret, secret=self)

    def rotate(self, request: Request | None = None) -> str:
        """Generate and store a new text value.

        The new value is at least as long as the current one, so a secret generated with a
        consumer's own length, such as a 128 character OAuth2 client secret, keeps it.
        """
        if self.type != SecretType.TEXT:
            raise ValueError("Only text secrets can be rotated.")
        value = generate_secret_value(
            max(len(self.secret_value), get_system_settings().default_token_length)
        )
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


def create_named_secret(name: str, **fields) -> Secret:
    """Create a secret with a readable, collision-safe name."""
    for suffix in range(1, 100):
        candidate = name if suffix == 1 else f"{name} ({suffix})"
        try:
            with transaction.atomic():
                return Secret.objects.create(name=candidate, **fields)
        except IntegrityError:
            continue
    raise IntegrityError(f"Could not allocate a name for {name!r}")
