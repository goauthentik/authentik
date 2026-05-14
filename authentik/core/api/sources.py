"""Source API Views"""

from collections.abc import Iterable

from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.object_types import TypesMixin
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer, ThemedUrlsSerializer
from authentik.core.models import GroupSourceConnection, Source, UserSourceConnection
from authentik.core.types import UserSettingSerializer
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    managed = ReadOnlyField()
    component = SerializerMethodField()
    icon_url = ReadOnlyField()
    icon_themed_urls = ThemedUrlsSerializer(read_only=True, allow_null=True)

    def get_component(self, obj: Source) -> str:
        """Get object component so that we know how to edit the object"""
        if obj.__class__ == Source:
            return ""
        return obj.component

    class Meta:
        model = Source
        fields = [
            "pk",
            "name",
            "slug",
            "enabled",
            "promoted",
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
            "icon_url",
            "icon_themed_urls",
        ]


class SourceViewSet(
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
    search_fields = ["slug", "name"]
    filterset_fields = ["slug", "name", "managed", "pbm_uuid"]

    def get_queryset(self):  # pragma: no cover
        return Source.objects.select_subclasses()

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

    def destroy(self, request: Request, *args, **kwargs):
        """Prevent deletion of built-in sources"""
        instance: Source = self.get_object()

        if instance.managed == Source.MANAGED_INBUILT:
            raise ValidationError(
                {"detail": "Built-in sources cannot be deleted"}, code="protected"
            )

        return super().destroy(request, *args, **kwargs)


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
            "identifier",
            "created",
            "last_updated",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
            "last_updated": {"read_only": True},
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
    filterset_fields = ["user", "source__slug"]
    search_fields = ["user__username", "source__slug", "identifier"]
    ordering = ["source__slug", "pk"]
    owner_field = "user"


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
            "last_updated",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
            "last_updated": {"read_only": True},
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
    filterset_fields = ["group", "source__slug"]
    search_fields = ["group__name", "source__slug", "identifier"]
    ordering = ["source__slug", "pk"]
