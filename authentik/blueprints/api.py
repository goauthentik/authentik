"""Serializer mixin for managed models"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateTimeField, JSONField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.tasks import apply_blueprint, blueprints_find_dict
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class MetadataSerializer(PassiveSerializer):
    """Serializer for blueprint metadata"""

    name = CharField()
    labels = JSONField()


class BlueprintInstanceSerializer(ModelSerializer):
    """Info about a single blueprint instance file"""

    def validate_path(self, path: str) -> str:
        """Ensure the path (if set) specified is retrievable"""
        if path == "":
            return path
        files: list[dict] = blueprints_find_dict.delay().get()
        if path not in [file["path"] for file in files]:
            raise ValidationError(_("Blueprint file does not exist"))
        return path

    def validate_content(self, content: str) -> str:
        """Ensure content (if set) is a valid blueprint"""
        if content == "":
            return content
        context = self.instance.context if self.instance else {}
        valid, logs = Importer(content, context).validate()
        if not valid:
            text_logs = "\n".join([x["event"] for x in logs])
            raise ValidationError(_("Failed to validate blueprint: %(logs)s" % {"logs": text_logs}))
        return content

    def validate(self, attrs: dict) -> dict:
        if attrs.get("path", "") == "" and attrs.get("content", "") == "":
            raise ValidationError(_("Either path or content must be set."))
        return super().validate(attrs)

    class Meta:
        model = BlueprintInstance
        fields = [
            "pk",
            "name",
            "path",
            "context",
            "last_applied",
            "last_applied_hash",
            "status",
            "enabled",
            "managed_models",
            "metadata",
            "content",
        ]
        extra_kwargs = {
            "status": {"read_only": True},
            "last_applied": {"read_only": True},
            "last_applied_hash": {"read_only": True},
            "managed_models": {"read_only": True},
            "metadata": {"read_only": True},
        }


class BlueprintInstanceViewSet(UsedByMixin, ModelViewSet):
    """Blueprint instances"""

    permission_classes = [IsAdminUser]
    serializer_class = BlueprintInstanceSerializer
    queryset = BlueprintInstance.objects.all()
    search_fields = ["name", "path"]
    filterset_fields = ["name", "path"]

    @extend_schema(
        responses={
            200: ListSerializer(
                child=inline_serializer(
                    "BlueprintFile",
                    fields={
                        "path": CharField(),
                        "last_m": DateTimeField(),
                        "hash": CharField(),
                        "meta": MetadataSerializer(required=False, read_only=True),
                    },
                )
            )
        }
    )
    @action(detail=False, pagination_class=None, filter_backends=[])
    def available(self, request: Request) -> Response:
        """Get blueprints"""
        files: list[dict] = blueprints_find_dict.delay().get()
        return Response(files)

    @permission_required("authentik_blueprints.view_blueprintinstance")
    @extend_schema(
        request=None,
        responses={
            200: BlueprintInstanceSerializer(),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def apply(self, request: Request, *args, **kwargs) -> Response:
        """Apply a blueprint"""
        blueprint = self.get_object()
        apply_blueprint.delay(str(blueprint.pk)).get()
        return self.retrieve(request, *args, **kwargs)
