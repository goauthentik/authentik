"""Managed secret models."""

from base64 import b64decode
from collections.abc import Callable
from json import JSONDecodeError, dumps, loads
from typing import TYPE_CHECKING
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _
from guardian.models import RoleModelPermission
from yaml import YAMLError, safe_load

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
        """Replace and audit a value that `validate_value` accepted, then signal consumers."""
        if value == self.secret_value:
            return
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
        """Generate and store a new text value with the same length as the current one.

        Consumers and the clients they talk to may limit the length, such as RADIUS clients
        that accept at most 16 characters, or expect their own, such as 128 character OAuth2
        client secrets.
        """
        if self.type != SecretType.TEXT:
            raise ValueError("Only text secrets can be rotated.")
        value = generate_secret_value(len(self.secret_value))
        self.validate_value(value)
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
    """Create a secret called `name`, with a random suffix when that name is taken.

    Generated secrets outlive the objects they were created for, so a name can be taken
    any number of times, for example by a client that registers again after being deleted.
    """
    try:
        with transaction.atomic():
            return Secret.objects.create(name=name, **fields)
    except IntegrityError:
        return Secret.objects.create(name=f"{name} ({generate_id(8)})", **fields)


class GeneratedSecretsMixin:
    """Create the secrets a model needs when it is saved without them.

    `generated_secrets` maps each reference field to the suffix of the secret's name and
    the function that generates its value. `secret_value_permission` is the permission
    on the model that declares a field, "view" or "change", that let roles read the
    credential through the API before it moved to a secret. It matches `value_permission`
    in that model's migration.
    """

    generated_secrets: dict[str, tuple[str, Callable[[], str]]] = {}
    secret_value_permission: str | None = None

    def save(self, *args, **kwargs):
        missing = [
            field for field in self.generated_secrets if getattr(self, f"{field}_id") is None
        ]
        with transaction.atomic():
            for field in missing:
                label, generate = self.generated_secrets[field]
                secret = create_named_secret(f"{self.name} {label}", secret_value=generate())
                self.grant_generated_secret(field, secret)
                setattr(self, field, secret)
            if missing and (update_fields := kwargs.get("update_fields")) is not None:
                kwargs["update_fields"] = {*update_fields, *missing}
            return super().save(*args, **kwargs)

    def grant_generated_secret(self, field: str, secret: Secret) -> None:
        """Give roles with access to every object of the model that declares `field` the
        access to a new secret that the credential migrations gave them on existing secrets.

        The migrations go by the declaring model, so a proxy provider's client secret follows
        OAuth2 provider permissions. Keep in sync with `preserve_permissions` in
        migrations/_permissions.py. Initial permissions cover the user who creates the object.
        """
        owner = self._meta.get_field(field).model
        model_name = owner._meta.model_name
        grants = {f"view_{model_name}": ["view_secret"], f"change_{model_name}": ["view_secret"]}
        if owner.secret_value_permission:
            grants[f"{owner.secret_value_permission}_{model_name}"].append("view_secret_value")
        for granted in RoleModelPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(owner),
            permission__codename__in=grants,
        ).select_related("role", "permission"):
            granted.role.assign_perms(
                [
                    f"authentik_crypto_secrets.{perm}"
                    for perm in grants[granted.permission.codename]
                ],
                secret,
            )
