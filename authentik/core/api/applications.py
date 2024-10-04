"""Application API Views"""

from collections.abc import Iterator
from copy import copy
from datetime import timedelta

from django.core.cache import cache
from django.db.models import QuerySet
from django.db.models.functions import ExtractHour
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.admin.api.metrics import CoordinateSerializer
from authentik.api.pagination import Pagination
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import Application, User
from authentik.events.logs import LogEventSerializer, capture_logs
from authentik.events.models import EventAction
from authentik.lib.utils.file import (
    FilePathSerializer,
    FileUploadSerializer,
    set_file,
    set_file_url,
)
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import CACHE_PREFIX, PolicyResult
from authentik.rbac.decorators import permission_required
from authentik.rbac.filters import ObjectFilter

LOGGER = get_logger()


def user_app_cache_key(user_pk: str, page_number: int | None = None) -> str:
    """Cache key where application list for user is saved"""
    key = f"{CACHE_PREFIX}/app_access/{user_pk}"
    if page_number:
        key += f"/{page_number}"
    return key


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    launch_url = SerializerMethodField()
    provider_obj = ProviderSerializer(source="get_provider", required=False, read_only=True)
    backchannel_providers_obj = ProviderSerializer(
        source="backchannel_providers", required=False, read_only=True, many=True
    )

    meta_icon = ReadOnlyField(source="get_meta_icon")

    def get_launch_url(self, app: Application) -> str | None:
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

    queryset = (
        Application.objects.all()
        .with_provider()
        .prefetch_related("policies")
        .prefetch_related("backchannel_providers")
    )
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
            if backend == ObjectFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def _get_allowed_applications(
        self, pagined_apps: Iterator[Application], user: User | None = None
    ) -> list[Application]:
        applications = []
        request = self.request._request
        if user:
            request = copy(request)
            request.user = user
        for application in pagined_apps:
            engine = PolicyEngine(application, request.user, request)
            engine.build()
            if engine.passing:
                applications.append(application)
        return applications

    def _filter_applications_with_launch_url(
        self, pagined_apps: Iterator[Application]
    ) -> list[Application]:
        applications = []
        for app in pagined_apps:
            if app.get_launch_url():
                applications.append(app)
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
                for_user = User.objects.filter(pk=request.query_params.get("for_user")).first()
            except ValueError:
                raise ValidationError({"for_user": "for_user must be numerical"}) from None
            if not for_user:
                raise ValidationError({"for_user": "User not found"})
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
                if log.attributes.get("process", "") == "PolicyProcess":
                    continue
                log_messages.append(LogEventSerializer(log).data)
            result.log_messages = log_messages
            response = PolicyTestResultSerializer(result)
        return Response(response.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="superuser_full_list",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="for_user",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="only_with_launch_url",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            ),
        ]
    )
    def list(self, request: Request) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        should_cache = request.query_params.get("search", "") == ""

        superuser_full_list = (
            str(request.query_params.get("superuser_full_list", "false")).lower() == "true"
        )
        if superuser_full_list and request.user.is_superuser:
            return super().list(request)

        only_with_launch_url = str(
            request.query_params.get("only_with_launch_url", "false")
        ).lower()

        queryset = self._filter_queryset_for_list(self.get_queryset())
        paginator: Pagination = self.paginator
        paginated_apps = paginator.paginate_queryset(queryset, request)

        if "for_user" in request.query_params:
            try:
                for_user: int = int(request.query_params.get("for_user", 0))
                for_user = (
                    get_objects_for_user(request.user, "authentik_core.view_user_applications")
                    .filter(pk=for_user)
                    .first()
                )
                if not for_user:
                    raise ValidationError({"for_user": "User not found"})
            except ValueError as exc:
                raise ValidationError from exc
            allowed_applications = self._get_allowed_applications(paginated_apps, user=for_user)
            serializer = self.get_serializer(allowed_applications, many=True)
            return self.get_paginated_response(serializer.data)

        allowed_applications = []
        if not should_cache:
            allowed_applications = self._get_allowed_applications(paginated_apps)
        if should_cache:
            allowed_applications = cache.get(
                user_app_cache_key(self.request.user.pk, paginator.page.number)
            )
            if not allowed_applications:
                LOGGER.debug("Caching allowed application list", page=paginator.page.number)
                allowed_applications = self._get_allowed_applications(paginated_apps)
                cache.set(
                    user_app_cache_key(self.request.user.pk, paginator.page.number),
                    allowed_applications,
                    timeout=86400,
                )

        if only_with_launch_url == "true":
            allowed_applications = self._filter_applications_with_launch_url(allowed_applications)

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
