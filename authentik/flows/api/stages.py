"""Flow Stage API Views"""

from uuid import uuid4

from django.db import transaction
from django.db.models import Model
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer, PassiveSerializer
from authentik.core.types import UserSettingSerializer
from authentik.flows.api.flows import FlowSetSerializer
from authentik.flows.models import ConfigurableStage, Stage
from authentik.lib.utils.reflection import all_subclasses
from authentik.rbac.permissions import ObjectPermissions

LOGGER = get_logger()


class StageSerializer(ModelSerializer, MetaNameSerializer):
    """Stage Serializer"""

    component = SerializerMethodField()
    flow_set = FlowSetSerializer(many=True, required=False, read_only=True)

    def to_representation(self, instance: Stage):
        if isinstance(instance, Stage) and instance.is_in_memory:
            instance.stage_uuid = uuid4()
        return super().to_representation(instance)

    def get_component(self, obj: Stage) -> str:
        """Get object type so that we know how to edit the object"""
        if obj.__class__ == Stage:
            return ""
        return obj.component

    class Meta:
        model = Stage
        fields = [
            "pk",
            "name",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "flow_set",
        ]


class StageDuplicateSerializer(PassiveSerializer):
    """Name of the copy a stage is duplicated into"""

    name = CharField()


def stage_perm(stage: Model, verb: str) -> str:
    """The permission to `verb` stages of this stage's own type, such as
    `authentik_stages_prompt.view_promptstage`"""
    return f"{stage._meta.app_label}.{verb}_{stage._meta.model_name}"


class StageDuplicatePermission(ObjectPermissions):
    """Duplicating a stage reads it and creates another of its type, so on top of seeing the stage
    in this endpoint, it needs view on the stage and add for its type. The all-stages endpoint
    would otherwise only check permissions on the base `Stage` model, which say nothing about a
    type."""

    def allows_object(self, request: Request, view: APIView, obj: Model) -> bool:
        return request.user.has_perm(stage_perm(obj, "view"), obj) and request.user.has_perm(
            stage_perm(obj, "add")
        )


class StageViewSet(
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Stage Viewset"""

    queryset = Stage.objects.none()
    serializer_class = StageSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]

    def get_queryset(self):  # pragma: no cover
        return Stage.objects.select_subclasses().prefetch_related("flow_set")

    @extend_schema(
        request=StageDuplicateSerializer,
        responses={201: StageSerializer},
    )
    @action(detail=True, methods=["POST"], permission_classes=[StageDuplicatePermission])
    @validate(StageDuplicateSerializer)
    @transaction.atomic
    def duplicate(self, request: Request, pk: str, body: StageDuplicateSerializer) -> Response:
        """Copy a stage under a new name. The copy refers to the same objects as the original,
        such as prompts, sources and flows, and is not bound to any flow."""
        stage: Stage = self.get_object()
        serializer_class = stage.serializer
        # Copy through the type's own serializer, as creating the stage through its endpoint
        # would, so the type's validation and the enterprise license check apply to the copy.
        # Its output already leaves out `secret_fields` for users who can't change the stage.
        original = serializer_class(stage, context={"request": request})
        data = dict(original.data)
        # Write-only fields hold secrets such as passwords and API keys, which no response
        # includes. Copy them only for users who could already change them on the original.
        if request.user.has_perm(stage_perm(stage, "change"), stage):
            for name, field in original.fields.items():
                if field.write_only:
                    data[name] = field.to_representation(field.get_attribute(stage))
        # What's still missing is a secret the type requires, which the user may not copy.
        if any(
            field.required and not field.read_only and name not in data
            for name, field in original.fields.items()
        ):
            raise PermissionDenied(
                _(
                    "Duplicating this stage copies its secrets, "
                    "which requires permission to change it."
                )
            )
        data["name"] = body.validated_data["name"]
        copy = serializer_class(data=data, context={"request": request})
        copy.is_valid(raise_exception=True)
        copy.save()
        return Response(
            StageSerializer(copy.instance, context={"request": request}).data,
            status=HTTP_201_CREATED,
        )

    @extend_schema(responses={200: UserSettingSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def user_settings(self, request: Request) -> Response:
        """Get all stages the user can configure"""
        stages = []
        for configurable_stage in all_subclasses(ConfigurableStage):
            stages += list(configurable_stage.objects.all().order_by("name"))
        matching_stages: list[dict] = []
        for stage in stages:
            user_settings = stage.ui_user_settings()
            if not user_settings:
                continue
            user_settings.initial_data["object_uid"] = str(stage.pk)
            if hasattr(stage, "configure_flow") and stage.configure_flow:
                user_settings.initial_data["configure_url"] = reverse(
                    "authentik_flows:configure",
                    kwargs={"stage_uuid": stage.pk},
                )
            if not user_settings.is_valid():
                LOGGER.warning(user_settings.errors)
            matching_stages.append(user_settings.initial_data)
        return Response(matching_stages)
