"""Managed secrets API."""

from base64 import b64decode
from binascii import Error as BinasciiError

from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.events.models import Event, EventAction
from authentik.rbac.decorators import permission_required
from authentik.rbac.permissions import ObjectPermissions
from authentik.secrets.models import Secret, SecretType


class SecretSerializer(ManagedSerializer, ModelSerializer):
    """Create and configure a secret without exposing its value."""

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        if values.get("value") == "":
            values.pop("value")
        return values

    def validate_value(self, value: str) -> str:
        instance = self.instance
        if not instance or value == instance.value:
            return value
        request = self.context.get("request")
        if request and not (
            request.user.has_perm("authentik_secrets.rotate_secret")
            or request.user.has_perm("authentik_secrets.rotate_secret", instance)
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
        if secret_type == SecretType.FILE and attrs.get("value"):
            try:
                b64decode(attrs["value"], validate=True)
            except BinasciiError, ValueError:
                raise ValidationError({"value": _("Value must be base64-encoded.")}) from None
        return attrs

    def update(self, instance: Secret, validated_data: dict) -> Secret:
        value = validated_data.pop("value", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if value is not None:
                instance.replace_value(value, self.context.get("request"))
        return instance

    class Meta:
        model = Secret
        fields = ["pk", "name", "type", "managed", "value", "created", "last_updated"]
        extra_kwargs = {
            "managed": {"read_only": True},
            "value": {"write_only": True, "required": False, "allow_blank": True},
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
    filterset_fields = ["name", "type", "managed"]

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                _("Secret is in use. Remove it from the objects referencing it first.")
            ) from None

    @permission_required("authentik_secrets.view_secret_value")
    @extend_schema(responses={200: SecretValueSerializer})
    @action(detail=True, pagination_class=None)
    def view_value(self, request: Request, pk: str) -> Response:
        """Return and audit a secret value."""
        secret = self.get_object()
        Event.new(EventAction.SECRET_VIEW, secret=secret).from_http(request)  # noqa: S105
        return Response(SecretValueSerializer({"value": secret.get_value()}).data)

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
        value = secret.rotate(request)
        can_view = request.user.has_perm("authentik_secrets.view_secret_value") or (
            request.user.has_perm("authentik_secrets.view_secret_value", secret)
        )
        return Response(RotatedSecretSerializer({"value": value if can_view else None}).data)
