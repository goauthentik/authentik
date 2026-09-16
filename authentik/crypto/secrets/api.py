"""Managed secrets API."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import CharField, SkipField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.events.models import Event, EventAction
from authentik.rbac.decorators import permission_required
from authentik.rbac.permissions import ObjectPermissions


class SecretReferenceField(PrimaryKeyRelatedField):
    """Attaching a credential can disclose it through the consumer."""

    allowed_types = (SecretType.TEXT,)

    def __init__(self, **kwargs):
        self.allowed_types = kwargs.pop("allowed_types", self.allowed_types)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        secret = super().to_internal_value(data)
        request = self.context.get("request")
        instance = self.parent.instance
        unchanged = instance and getattr(instance, f"{self.source}_id") == secret.pk
        if (
            request
            and not unchanged
            and not (
                request.user.has_perm("authentik_crypto_secrets.view_secret_value")
                or request.user.has_perm("authentik_crypto_secrets.view_secret_value", secret)
            )
        ):
            raise PermissionDenied(_("You do not have permission to use this secret."))
        if secret.type not in self.allowed_types:
            raise ValidationError(_("This secret type is not supported by this field."))
        return secret


class JSONSecretReferenceField(SecretReferenceField):
    """A reference to a structured credential."""

    allowed_types = (SecretType.MULTILINE, SecretType.FILE)

    def to_internal_value(self, data):
        secret = super().to_internal_value(data)
        try:
            secret.get_json()
        except ValueError:
            raise ValidationError(_("Secret must contain a JSON or YAML object.")) from None
        return secret


class SecretSerializer(ManagedSerializer, ModelSerializer):
    """Create and configure a secret without exposing its value."""

    def validate_value(self, value: str) -> str:
        if value == "":
            raise SkipField
        instance = self.instance
        if not instance:
            return value
        request = self.context.get("request")
        if request and not (
            request.user.has_perm("authentik_crypto_secrets.rotate_secret")
            or request.user.has_perm("authentik_crypto_secrets.rotate_secret", instance)
        ):
            raise PermissionDenied(_("You do not have permission to replace this value."))
        if instance.oauth2_providers.exists():
            from authentik.providers.oauth2.utils import is_all_vschar

            if not is_all_vschar(value):
                raise ValidationError(
                    _("OAuth client secrets must consist of only ASCII characters.")
                )
        return value

    def validate(self, attrs: dict) -> dict:
        instance = self.instance
        if instance and attrs.get("type", instance.type) != instance.type:
            raise ValidationError({"type": _("Type cannot be changed after creation.")})
        secret_type = attrs.get("type", instance.type if instance else SecretType.TEXT)
        if not instance and secret_type != SecretType.TEXT and not attrs.get("value"):
            raise ValidationError({"value": _("A value is required for this type.")})
        if "value" in attrs:
            try:
                (instance or Secret(type=secret_type)).validate_value(attrs["value"])
            except DjangoValidationError as exc:
                raise ValidationError({"value": exc.messages}) from exc
        return attrs

    def update(self, instance: Secret, validated_data: dict) -> Secret:
        value = validated_data.pop("value", None)
        with transaction.atomic():
            if validated_data:
                for field, field_value in validated_data.items():
                    setattr(instance, field, field_value)
                instance.save(update_fields=[*validated_data, "last_updated"])
            if value is not None:
                instance.replace_value(value, self.context.get("request"))
        return instance

    class Meta:
        model = Secret
        fields = ["pk", "name", "type", "managed", "value", "created", "last_updated"]
        extra_kwargs = {
            "managed": {"read_only": True},
            "value": {
                "write_only": True,
                "required": False,
                "allow_blank": True,
                "trim_whitespace": False,
            },
            "created": {"read_only": True},
            "last_updated": {"read_only": True},
        }


class SecretValueSerializer(PassiveSerializer):
    """A secret value."""

    value = CharField(read_only=True)


class RotatedSecretSerializer(PassiveSerializer):
    """A rotated value, hidden when the caller cannot view it."""

    value = CharField(read_only=True, allow_null=True)


class SecretRotatePermissions(ObjectPermissions):
    """Map rotation to its dedicated object permission."""

    perms_map = {**ObjectPermissions.perms_map, "POST": ["%(app_label)s.rotate_%(model_name)s"]}


class SecretViewSet(UsedByMixin, ModelViewSet):
    """Manage secrets."""

    queryset = Secret.objects.all()
    serializer_class = SecretSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = {"name": ["exact"], "type": ["exact", "in"], "managed": ["exact"]}

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                _("Secret is in use. Remove it from the objects referencing it first.")
            ) from None

    @permission_required("authentik_crypto_secrets.view_secret_value")
    @extend_schema(responses={200: SecretValueSerializer})
    @action(detail=True, pagination_class=None)
    def view_value(self, request: Request, pk: str) -> Response:
        """Return and audit a secret value."""
        secret = self.get_object()
        Event.new(EventAction.SECRET_VIEW, secret=secret).from_http(request)  # noqa: S105
        return Response(SecretValueSerializer({"value": secret.value}).data)

    @extend_schema(request=None, responses={200: RotatedSecretSerializer})
    @action(
        detail=True,
        methods=["POST"],
        pagination_class=None,
        permission_classes=[SecretRotatePermissions],
    )
    def rotate(self, request: Request, pk: str) -> Response:
        """Replace a text secret with a generated value."""
        secret = self.get_object()
        if secret.type != SecretType.TEXT:
            raise ValidationError({"non_field_errors": [_("Only text secrets can be rotated.")]})
        try:
            value = secret.rotate(request)
        except DjangoValidationError as exc:
            raise ValidationError({"non_field_errors": exc.messages}) from exc
        can_view = request.user.has_perm("authentik_crypto_secrets.view_secret_value") or (
            request.user.has_perm("authentik_crypto_secrets.view_secret_value", secret)
        )
        return Response(RotatedSecretSerializer({"value": value if can_view else None}).data)
