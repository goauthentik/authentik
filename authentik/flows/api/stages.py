"""Flow Stage API Views"""
from typing import Iterable

from django.urls import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ReadOnlyModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.flows.api.flows import FlowSerializer
from authentik.flows.challenge import Challenge
from authentik.flows.models import Stage
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses

LOGGER = get_logger()


class StageSerializer(ModelSerializer, MetaNameSerializer):
    """Stage Serializer"""

    object_type = SerializerMethodField()
    flow_set = FlowSerializer(many=True, required=False)

    def get_object_type(self, obj: Stage) -> str:
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("stage", "")

    class Meta:

        model = Stage
        fields = [
            "pk",
            "name",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
            "flow_set",
        ]


class StageViewSet(ReadOnlyModelViewSet):
    """Stage Viewset"""

    queryset = Stage.objects.all().select_related("flow_set")
    serializer_class = StageSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]

    def get_queryset(self):
        return Stage.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable stage types"""
        data = []
        for subclass in all_subclasses(self.queryset.model, False):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:stage-create")
                    + f"?type={subclass.__name__}",
                }
            )
        data = sorted(data, key=lambda x: x["name"])
        return Response(TypeCreateSerializer(data, many=True).data)

    @swagger_auto_schema(responses={200: Challenge(many=True)})
    @action(detail=False)
    def user_settings(self, request: Request) -> Response:
        """Get all stages the user can configure"""
        _all_stages: Iterable[Stage] = Stage.objects.all().select_subclasses()
        matching_stages: list[dict] = []
        for stage in _all_stages:
            user_settings = stage.ui_user_settings
            if not user_settings:
                continue
            stage_challenge = user_settings
            if not stage_challenge.is_valid():
                LOGGER.warning(stage_challenge.errors)
            matching_stages.append(stage_challenge.initial_data)
        return Response(matching_stages)
