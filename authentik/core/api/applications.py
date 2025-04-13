"""Application API Views"""

import os
import uuid
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
from rest_framework.fields import CharField, ReadOnlyField, SerializerMethodField, FileField
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
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Application, User
from authentik.events.logs import LogEventSerializer, capture_logs
from authentik.events.models import EventAction
from authentik.lib.utils.file import (
    FileUploadSerializer,
)
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import CACHE_PREFIX, PolicyResult
from authentik.rbac.decorators import permission_required
from authentik.rbac.filters import ObjectFilter

LOGGER = get_logger()


def user_app_cache_key(user_pk: str, page_number: int | None = None) -> str:
    """Cache key where application list for user is saved"""
    key = f"{CACHE_PREFIX}app_access/{user_pk}"
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


class IconResponseSerializer(PassiveSerializer):
    """Serializer for icon operations"""
    meta_icon = CharField(required=False)
    message = CharField(required=False)
    error = CharField(required=False)

class IconRequestSerializer(PassiveSerializer):
    """Serializer for icon operations"""
    file = FileField(required=False)
    url = CharField(required=False)

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("url"):
            raise ValidationError("Either file or url must be provided")
        return attrs


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

    def get_serializer_class(self):
        """Return serializer based on action"""
        if self.action == "icon":
            return IconRequestSerializer
        return super().get_serializer_class()

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

    def _handle_icon_delete(self, app: Application):
        """Helper to handle icon deletion"""
        field = app.meta_icon

        if not field or not field.name:
            return Response({"error": "No icon exists to delete"}, status=404)

        try:
            field.delete(save=False)
            app.save()
            return Response({"meta_icon": None, "message": "Icon successfully removed"})
        except Exception as exc:
            LOGGER.warning("Failed to remove icon", exc=exc)
            return Response({"error": f"Failed to remove icon: {str(exc)}"}, status=500)

    def _handle_icon_url(self, app: Application, url: str, is_post: bool):
        """Helper to handle URL-based icon update"""
        # Validate URL format
        try:
            from urllib.parse import urlparse

            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return Response({"error": "Invalid URL format"}, status=400)
        except Exception:
            return Response({"error": "Invalid URL format"}, status=400)

        field_obj = app.meta_icon

        # For POST, delete old file if exists
        if is_post and field_obj and field_obj.name:
            try:
                field_obj.delete(save=False)
            except Exception as exc:
                LOGGER.warning("Failed to delete old icon", exc=exc)

        field_obj.name = url
        app.save()
        message = "Icon successfully created" if is_post else "Icon successfully updated"
        return Response({"meta_icon": app.get_meta_icon, "message": message})

    def _handle_icon_file(self, app: Application, file, is_post: bool):
        """Helper to handle file-based icon update"""
        field = app.meta_icon

        # For POST, delete old file if exists
        if is_post and field and field.name:
            try:
                field.delete(save=False)
            except Exception as exc:
                LOGGER.warning("Failed to delete old icon", exc=exc)

        # Get the upload_to path from the model field
        upload_to = field.field.upload_to

        # If upload_to is set, ensure the file name includes the directory
        if upload_to:
            # Generate a unique filename to prevent conflicts
            filename, extension = os.path.splitext(os.path.basename(file.name))
            unique_filename = f"{filename}_{uuid.uuid4().hex[:8]}{extension}"
            # Construct a clean path within the upload directory
            file.name = f"{upload_to}/{unique_filename}"

        app.meta_icon = file
        try:
            app.save()
        except Exception as exc:
            LOGGER.error("Unexpected error saving file", exc=exc)
            return Response(
                {"error": f"An unexpected error occurred while saving the file: {str(exc)}"},
                status=500,
            )

        message = "Icon successfully created" if is_post else "Icon successfully updated"
        return Response({"meta_icon": app.get_meta_icon, "message": message})

    @action(
        detail=True,
        pagination_class=None,
        filter_backends=[],
        methods=["POST", "PATCH", "DELETE"],
        parser_classes=(MultiPartParser,),
        url_path="icon",
        url_name="icon",
    )
    @permission_required("authentik_core.change_application")
    @extend_schema(
        methods=["POST"],
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "url": {"type": "string"},
                },
            },
            "application/json": IconRequestSerializer,
        },
        responses={
            200: IconResponseSerializer,
            400: OpenApiResponse(description="Bad request", response={"error": str}),
            403: OpenApiResponse(description="Permission denied", response={"error": str}),
            415: OpenApiResponse(description="Unsupported Media Type", response={"error": str}),
            500: OpenApiResponse(description="Internal server error", response={"error": str}),
        },
        operation_id="coreApplicationsIconCreate",
        parameters=[{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
        tags=["core"],
    )
    @extend_schema(
        methods=["PATCH"],
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "url": {"type": "string"},
                },
            },
            "application/json": IconRequestSerializer,
        },
        responses={
            200: IconResponseSerializer,
            400: OpenApiResponse(description="Bad request", response={"error": str}),
            403: OpenApiResponse(description="Permission denied", response={"error": str}),
            404: OpenApiResponse(description="No icon exists", response={"error": str}),
            415: OpenApiResponse(description="Unsupported Media Type", response={"error": str}),
            500: OpenApiResponse(description="Internal server error", response={"error": str}),
        },
        operation_id="coreApplicationsIconUpdate",
        parameters=[{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
        tags=["core"],
    )
    @extend_schema(
        methods=["DELETE"],
        responses={
            200: IconResponseSerializer,
            404: OpenApiResponse(description="No icon exists", response={"error": str}),
            500: OpenApiResponse(description="Internal server error", response={"error": str}),
        },
        operation_id="coreApplicationsIconDelete",
        parameters=[{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
        tags=["core"],
    )
    def icon(self, request: Request, slug: str):
        """RESTful endpoint for application icon management"""
        app: Application = self.get_object()

        is_post = request.method == "POST"

        # Handle DELETE request
        if request.method == "DELETE":
            return self._handle_icon_delete(app)

        # For PATCH, verify that icon exists
        if request.method == "PATCH":
            field = app.meta_icon
            if not field or not field.name:
                return Response(
                    {"error": "Cannot update icon: No icon exists. Use POST to create a new icon."},
                    status=404,
                )

        # Handle URL-based icon
        if request.data.get("url"):
            return self._handle_icon_url(app, request.data.get("url"), is_post)

        # Handle file upload
        file = request.FILES.get("file", None)
        if not file:
            return Response({"error": "No file or URL provided"}, status=400)

        return self._handle_icon_file(app, file, is_post)
