"""Source API Views"""

from collections.abc import Iterable

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer
from authentik.core.models import GroupSourceConnection, Source, UserSourceConnection
from authentik.core.types import UserSettingSerializer
from authentik.lib.api import MultipleFieldLookupMixin
from authentik.lib.utils.file import (
    FilePathSerializer,
    FileUploadSerializer,
    set_file,
    set_file_url,
)
from authentik.policies.engine import PolicyEngine
from authentik.rbac.decorators import permission_required

LOGGER = get_logger()


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    managed = ReadOnlyField()
    component = SerializerMethodField()
    icon = ReadOnlyField(source="icon_url")

    def get_component(self, obj: Source) -> str:
        """Get object component so that we know how to edit the object"""
        if obj.__class__ == Source:
            return ""
        return obj.component

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["icon"] = CharField(required=False)

    class Meta:
        model = Source
        fields = [
            "pk",
            "name",
            "slug",
            "enabled",
            "authentication_flow",
            "enrollment_flow",
            "user_property_mappings",
            "group_property_mappings",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "policy_engine_mode",
            "user_matching_mode",
            "managed",
            "user_path_template",
            "icon",
        ]


class SourceViewSet(
    MultipleFieldLookupMixin,
    TypesMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Source Viewset"""

    queryset = Source.objects.none()
    serializer_class = SourceSerializer
    lookup_field = "slug"
    lookup_fields = ["slug", "pbm_uuid"]
    search_fields = ["slug", "name"]
    filterset_fields = ["slug", "name", "managed"]

    def get_queryset(self):  # pragma: no cover
        return Source.objects.select_subclasses()

    @permission_required("authentik_core.change_source")
    @extend_schema(
        request={
            "multipart/form-data": FileUploadSerializer,
        },
        responses={
            200: OpenApiResponse(description="Success"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(
        detail=True,
        pagination_class=None,
        filter_backends=[],
        methods=["POST"],
        parser_classes=(MultiPartParser,),
    )
    def set_icon(self, request: Request, slug: str):
        """Set source icon"""
        source: Source = self.get_object()
        return set_file(request, source, "icon")

    @permission_required("authentik_core.change_source")
    @extend_schema(
        request=FilePathSerializer,
        responses={
            200: OpenApiResponse(description="Success"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(
        detail=True,
        pagination_class=None,
        filter_backends=[],
        methods=["POST"],
    )
    def set_icon_url(self, request: Request, slug: str):
        """Set source icon (as URL)"""
        source: Source = self.get_object()
        return set_file_url(request, source, "icon")

    @extend_schema(responses={200: UserSettingSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def user_settings(self, request: Request) -> Response:
        """Get all sources the user can configure"""
        _all_sources: Iterable[Source] = (
            Source.objects.filter(enabled=True).select_subclasses().order_by("name")
        )
        matching_sources: list[UserSettingSerializer] = []
        for source in _all_sources:
            user_settings = source.ui_user_settings()
            if not user_settings:
                continue
            policy_engine = PolicyEngine(source, request.user, request)
            policy_engine.build()
            if not policy_engine.passing:
                continue
            source_settings = source.ui_user_settings()
            source_settings.initial_data["object_uid"] = source.slug
            if not source_settings.is_valid():
                LOGGER.warning(source_settings.errors)
            matching_sources.append(source_settings.validated_data)
        return Response(matching_sources)


class UserSourceConnectionSerializer(SourceSerializer):
    """User source connection"""

    source_obj = SourceSerializer(read_only=True, source="source")

    class Meta:
        model = UserSourceConnection
        fields = [
            "pk",
            "user",
            "source",
            "source_obj",
            "created",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
        }


class UserSourceConnectionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """User-source connection Viewset"""

    queryset = UserSourceConnection.objects.all()
    serializer_class = UserSourceConnectionSerializer
    permission_classes = [OwnerSuperuserPermissions]
    filterset_fields = ["user", "source__slug"]
    search_fields = ["source__slug"]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug", "pk"]


class GroupSourceConnectionSerializer(SourceSerializer):
    """Group Source Connection"""

    source_obj = SourceSerializer(read_only=True)

    class Meta:
        model = GroupSourceConnection
        fields = [
            "pk",
            "group",
            "source",
            "source_obj",
            "identifier",
            "created",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
        }


class GroupSourceConnectionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Group-source connection Viewset"""

    queryset = GroupSourceConnection.objects.all()
    serializer_class = GroupSourceConnectionSerializer
    permission_classes = [OwnerSuperuserPermissions]
    filterset_fields = ["group", "source__slug"]
    search_fields = ["source__slug"]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug", "pk"]
