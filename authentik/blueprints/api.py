"""Serializer mixin for managed models"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import BooleanField, CharField, DateTimeField
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.common import Blueprint
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.oci import OCI_PREFIX
from authentik.blueprints.v1.tasks import apply_blueprint, blueprints_find_dict
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField, ModelSerializer, PassiveSerializer
from authentik.core.models import User
from authentik.events.logs import LogEventSerializer
from authentik.lib.utils.file import FileUploadSerializer
from authentik.rbac.decorators import permission_required


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class MetadataSerializer(PassiveSerializer):
    """Serializer for blueprint metadata"""

    name = CharField()
    labels = JSONDictField()


class BlueprintInstanceSerializer(ModelSerializer):
    """Info about a single blueprint instance file"""

    def validate_path(self, path: str) -> str:
        """Ensure the path (if set) specified is retrievable"""
        if path == "" or path.startswith(OCI_PREFIX):
            return path
        files: list[dict] = blueprints_find_dict.send().get_result(block=True)
        if path not in [file["path"] for file in files]:
            raise ValidationError(_("Blueprint file does not exist"))
        return path

    def validate_content(self, content: str) -> str:
        """Ensure content (if set) is a valid blueprint"""
        if content == "":
            return content
        context = self.instance.context if self.instance else {}
        valid, logs = Importer.from_string(content, context).validate()
        if not valid:
            raise ValidationError(
                [
                    _("Failed to validate blueprint"),
                    *[f"- {x.event}" for x in logs],
                ]
            )
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


def check_blueprint_perms(blueprint: Blueprint, user: User, explicit_action: str | None = None):
    """Check for individual permissions for each model in a blueprint"""
    for entry in blueprint.entries:
        full_model = entry.get_model(blueprint)
        app, __, model = full_model.partition(".")
        perms = [
            f"{app}.add_{model}",
            f"{app}.change_{model}",
            f"{app}.delete_{model}",
        ]
        if explicit_action:
            perms = [f"{app}.{explicit_action}_{model}"]
        for perm in perms:
            if not user.has_perm(perm):
                raise PermissionDenied(
                    {
                        entry.id: _(
                            "User lacks permission to create {model}".format_map(
                                {
                                    "model": full_model,
                                }
                            )
                        )
                    }
                )


class BlueprintInstanceViewSet(UsedByMixin, ModelViewSet):
    """Blueprint instances"""

    serializer_class = BlueprintInstanceSerializer
    queryset = BlueprintInstance.objects.all()
    search_fields = ["name", "path"]
    filterset_fields = ["name", "path"]
    ordering = ["name"]

    class BlueprintImportResultSerializer(PassiveSerializer):
        """Logs of an attempted blueprint import"""

        logs = LogEventSerializer(many=True, read_only=True)
        success = BooleanField(read_only=True)

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
        files: list[dict] = blueprints_find_dict.send().get_result(block=True)
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
        apply_blueprint.send_with_options(args=(blueprint.pk,), rel_obj=blueprint)
        return self.retrieve(request, *args, **kwargs)

    @extend_schema(
        request={"multipart/form-data": FileUploadSerializer},
        responses={
            204: BlueprintImportResultSerializer,
            400: BlueprintImportResultSerializer,
        },
    )
    @action(url_path="import", detail=False, methods=["POST"], parser_classes=(MultiPartParser,))
    def import_(self, request: Request) -> Response:
        """Import blueprint from .yaml file and apply it once, without creating an instance"""
        import_response = self.BlueprintImportResultSerializer(
            data={
                "logs": [],
                "success": False,
            }
        )
        import_response.is_valid(raise_exception=True)
        file = request.FILES.get("file", None)
        if not file:
            return Response(data=import_response.initial_data, status=400)

        importer = Importer.from_string(file.read().decode())
        check_blueprint_perms(importer.blueprint, request.user)

        valid, logs = importer.validate()
        import_response.initial_data["logs"] = [LogEventSerializer(log).data for log in logs]
        import_response.initial_data["success"] = valid
        import_response.is_valid()
        if not valid:
            return Response(data=import_response.initial_data, status=200)

        successful = importer.apply()
        import_response.initial_data["success"] = successful
        import_response.is_valid()
        if not successful:
            return Response(data=import_response.initial_data, status=200)
        return Response(data=import_response.initial_data, status=200)
