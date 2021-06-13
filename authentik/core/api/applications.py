"""Application API Views"""
from django.core.cache import cache
from django.db.models import QuerySet
from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework.decorators import action
from rest_framework.fields import (
    BooleanField,
    CharField,
    FileField,
    IntegerField,
    ReadOnlyField,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter
from structlog.stdlib import get_logger

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.api.decorators import permission_required
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import Application, User
from authentik.events.models import EventAction
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import PolicyResult
from authentik.stages.user_login.stage import USER_LOGIN_AUTHENTICATED

LOGGER = get_logger()


def user_app_cache_key(user_pk: str) -> str:
    """Cache key where application list for user is saved"""
    return f"user_app_cache_{user_pk}"


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    launch_url = ReadOnlyField(source="get_launch_url")
    provider_obj = ProviderSerializer(source="get_provider", required=False)

    meta_icon = ReadOnlyField(source="get_meta_icon")

    class Meta:

        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "provider",
            "provider_obj",
            "launch_url",
            "meta_launch_url",
            "meta_icon",
            "meta_description",
            "meta_publisher",
            "policy_engine_mode",
        ]
        extra_kwargs = {
            "meta_icon": {"read_only": True},
        }


class ApplicationViewSet(UsedByMixin, ModelViewSet):
    """Application Viewset"""

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    search_fields = [
        "name",
        "slug",
        "meta_launch_url",
        "meta_description",
        "meta_publisher",
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
    # pylint: disable=unused-argument
    def check_access(self, request: Request, slug: str) -> Response:
        """Check access to a single application by slug"""
        # Don't use self.get_object as that checks for view_application permission
        # which the user might not have, even if they have access
        application = get_object_or_404(Application, slug=slug)
        # If the current user is superuser, they can set `for_user`
        for_user = self.request.user
        if self.request.user.is_superuser and "for_user" in request.data:
            for_user = get_object_or_404(User, pk=request.data.get("for_user"))
        engine = PolicyEngine(application, for_user, self.request)
        engine.build()
        result = engine.result
        response = PolicyTestResultSerializer(PolicyResult(False))
        if result.passing:
            response = PolicyTestResultSerializer(PolicyResult(True))
        if self.request.user.is_superuser:
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
        self.request.session.pop(USER_LOGIN_AUTHENTICATED, None)
        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)

        should_cache = request.GET.get("search", "") == ""

        superuser_full_list = (
            str(request.GET.get("superuser_full_list", "false")).lower() == "true"
        )
        if superuser_full_list and request.user.is_superuser:
            serializer = self.get_serializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)

        allowed_applications = []
        if not should_cache:
            allowed_applications = self._get_allowed_applications(queryset)
        if should_cache:
            LOGGER.debug("Caching allowed application list")
            allowed_applications = cache.get(user_app_cache_key(self.request.user.pk))
            if not allowed_applications:
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
            "multipart/form-data": inline_serializer(
                "SetIcon",
                fields={
                    "file": FileField(required=False),
                    "clear": BooleanField(default=False),
                },
            )
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
    # pylint: disable=unused-argument
    def set_icon(self, request: Request, slug: str):
        """Set application icon"""
        app: Application = self.get_object()
        icon = request.FILES.get("file", None)
        clear = request.data.get("clear", False)
        if clear:
            # .delete() saves the model by default
            app.meta_icon.delete()
            return Response({})
        if icon:
            app.meta_icon = icon
            app.save()
            return Response({})
        return HttpResponseBadRequest()

    @permission_required("authentik_core.change_application")
    @extend_schema(
        request=inline_serializer("SetIconURL", fields={"url": CharField()}),
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
    # pylint: disable=unused-argument
    def set_icon_url(self, request: Request, slug: str):
        """Set application icon (as URL)"""
        app: Application = self.get_object()
        url = request.data.get("url", None)
        if url is None:
            return HttpResponseBadRequest()
        app.meta_icon.name = url
        app.save()
        return Response({})

    @permission_required(
        "authentik_core.view_application", ["authentik_events.view_event"]
    )
    @extend_schema(responses={200: CoordinateSerializer(many=True)})
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=unused-argument
    def metrics(self, request: Request, slug: str):
        """Metrics for application logins"""
        app = self.get_object()
        return Response(
            get_events_per_1h(
                action=EventAction.AUTHORIZE_APPLICATION,
                context__authorized_application__pk=app.pk.hex,
            )
        )
