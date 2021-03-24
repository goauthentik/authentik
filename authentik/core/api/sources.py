"""Source API Views"""
from typing import Iterable

from django.urls import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.core.models import Source
from authentik.core.types import UserSettingSerializer
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("source", "")

    class Meta:

        model = Source
        fields = [
            "pk",
            "name",
            "slug",
            "enabled",
            "authentication_flow",
            "enrollment_flow",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class SourceViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Source Viewset"""

    queryset = Source.objects.none()
    serializer_class = SourceSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Source.objects.select_subclasses()

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable source types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:source-create")
                    + f"?type={subclass.__name__}",
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @swagger_auto_schema(responses={200: UserSettingSerializer(many=True)})
    @action(detail=False)
    def user_settings(self, request: Request) -> Response:
        """Get all sources the user can configure"""
        _all_sources: Iterable[Source] = Source.objects.filter(
            enabled=True
        ).select_subclasses()
        matching_sources: list[UserSettingSerializer] = []
        for source in _all_sources:
            user_settings = source.ui_user_settings
            if not user_settings:
                continue
            policy_engine = PolicyEngine(source, request.user, request)
            policy_engine.build()
            if not policy_engine.passing:
                continue
            source_settings = source.ui_user_settings
            source_settings.initial_data["object_uid"] = source.slug
            if not source_settings.is_valid():
                LOGGER.warning(source_settings.errors)
            matching_sources.append(source_settings.validated_data)
        return Response(matching_sources)
