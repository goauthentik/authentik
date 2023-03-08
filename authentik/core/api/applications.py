"""Application API Views"""
from datetime import timedelta
from typing import Optional

from django.core.cache import cache
from django.db.models import QuerySet
from django.db.models.functions import ExtractHour
from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter
from structlog.stdlib import get_logger
from structlog.testing import capture_logs

from authentik.admin.api.metrics import CoordinateSerializer
from authentik.api.decorators import permission_required
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import Application, User
from authentik.events.models import EventAction
from authentik.events.utils import sanitize_dict
from authentik.lib.utils.file import (
    FilePathSerializer,
    FileUploadSerializer,
    set_file,
    set_file_url,
)
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import PolicyResult

LOGGER = get_logger()


def user_app_cache_key(user_pk: str) -> str:
    """Cache key where application list for user is saved"""
    return f"goauthentik.io/core/app_access/{user_pk}"


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    launch_url = SerializerMethodField()
    provider_obj = ProviderSerializer(source="get_provider", required=False, read_only=True)
    backchannel_providers_obj = ProviderSerializer(
        source="backchannel_providers", required=False, read_only=True, many=True
    )

    meta_icon = ReadOnlyField(source="get_meta_icon")

    def get_launch_url(self, app: Application) -> Optional[str]:
        """Allow formatting of launch URL"""
        user = None
        if "request" in self.context:
            user = self.context["request"].user
        return app.get_launch_url(user)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["icon"] = CharField(source="meta_icon", required=False)

    class Meta:
        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "provider",
            "provider_obj",
            "backchannel_providers",
            "backchannel_providers_obj",
            "launch_url",
            "open_in_new_tab",
            "meta_launch_url",
            "meta_icon",
            "meta_description",
            "meta_publisher",
            "policy_engine_mode",
            "group",
        ]
        extra_kwargs = {
            "meta_icon": {"read_only": True},
            "backchannel_providers": {"required": False},
        }


class ApplicationViewSet(UsedByMixin, ModelViewSet):
    """Application Viewset"""

    queryset = Application.objects.all().prefetch_related("provider")
    serializer_class = ApplicationSerializer
    search_fields = [
        "name",
        "slug",
        "meta_launch_url",
        "meta_description",
        "meta_publisher",
        "group",
    ]
    filterset_fields = [
        "name",
        "slug",
        "meta_launch_url",
        "meta_description",
        "meta_publisher",
        "group",
    ]
    lookup_field = "slug"
    ordering = ["name"]

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectPermissionsFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def _get_allowed_applications(self, queryset: QuerySet) -> list[Application]:
        applications = []
        for application in queryset:
            engine = PolicyEngine(application, self.request.user, self.request)
            engine.build()
            if engine.passing:
                applications.append(application)
        return applications

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="for_user",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
            )
        ],
        responses={
            200: PolicyTestResultSerializer(),
            404: OpenApiResponse(description="for_user user not found"),
        },
    )
    @action(detail=True, methods=["GET"])
    def check_access(self, request: Request, slug: str) -> Response:
        """Check access to a single application by slug"""
        # Don't use self.get_object as that checks for view_application permission
        # which the user might not have, even if they have access
        application = get_object_or_404(Application, slug=slug)
        # If the current user is superuser, they can set `for_user`
        for_user = request.user
        if request.user.is_superuser and "for_user" in request.query_params:
            try:
                for_user = get_object_or_404(User, pk=request.query_params.get("for_user"))
            except ValueError:
                return HttpResponseBadRequest("for_user must be numerical")
        engine = PolicyEngine(application, for_user, request)
        engine.use_cache = False
        with capture_logs() as logs:
            engine.build()
            result = engine.result
        response = PolicyTestResultSerializer(PolicyResult(False))
        if result.passing:
            response = PolicyTestResultSerializer(PolicyResult(True))
        if request.user.is_superuser:
            log_messages = []
            for log in logs:
                if log.get("process", "") == "PolicyProcess":
                    continue
                log_messages.append(sanitize_dict(log))
            result.log_messages = log_messages
            response = PolicyTestResultSerializer(result)
        return Response(response.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="superuser_full_list",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            )
        ]
    )
    def list(self, request: Request) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        should_cache = request.GET.get("search", "") == ""

        superuser_full_list = str(request.GET.get("superuser_full_list", "false")).lower() == "true"
        if superuser_full_list and request.user.is_superuser:
            return super().list(request)

        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)

        allowed_applications = []
        if not should_cache:
            allowed_applications = self._get_allowed_applications(queryset)
        if should_cache:
            allowed_applications = cache.get(user_app_cache_key(self.request.user.pk))
            if not allowed_applications:
                LOGGER.debug("Caching allowed application list")
                allowed_applications = self._get_allowed_applications(queryset)
                cache.set(
                    user_app_cache_key(self.request.user.pk),
                    allowed_applications,
                    timeout=86400,
                )
        serializer = self.get_serializer(allowed_applications, many=True)
        return self.get_paginated_response(serializer.data)

    @permission_required("authentik_core.change_application")
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
        """Set application icon"""
        app: Application = self.get_object()
        return set_file(request, app, "meta_icon")

    @permission_required("authentik_core.change_application")
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
        """Set application icon (as URL)"""
        app: Application = self.get_object()
        return set_file_url(request, app, "meta_icon")

    @permission_required("authentik_core.view_application", ["authentik_events.view_event"])
    @extend_schema(responses={200: CoordinateSerializer(many=True)})
    @action(detail=True, pagination_class=None, filter_backends=[])
    def metrics(self, request: Request, slug: str):
        """Metrics for application logins"""
        app = self.get_object()
        return Response(
            get_objects_for_user(request.user, "authentik_events.view_event").filter(
                action=EventAction.AUTHORIZE_APPLICATION,
                context__authorized_application__pk=app.pk.hex,
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )
