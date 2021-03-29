"""Application API Views"""
from django.core.cache import cache
from django.db.models import QuerySet
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter
from structlog.stdlib import get_logger

from authentik.admin.api.metrics import CoordinateSerializer, get_events_per_1h
from authentik.api.decorators import permission_required
from authentik.core.api.providers import ProviderSerializer
from authentik.core.models import Application
from authentik.events.models import EventAction
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


def user_app_cache_key(user_pk: str) -> str:
    """Cache key where application list for user is saved"""
    return f"user_app_cache_{user_pk}"


class ApplicationSerializer(ModelSerializer):
    """Application Serializer"""

    launch_url = SerializerMethodField()
    provider = ProviderSerializer(source="get_provider", required=False)

    def get_launch_url(self, instance: Application) -> str:
        """Get generated launch URL"""
        return instance.get_launch_url() or ""

    class Meta:

        model = Application
        fields = [
            "pk",
            "name",
            "slug",
            "provider",
            "launch_url",
            "meta_launch_url",
            "meta_icon",
            "meta_description",
            "meta_publisher",
        ]


class ApplicationViewSet(ModelViewSet):
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

    def list(self, request: Request) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)

        should_cache = request.GET.get("search", "") == ""

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

    @permission_required(
        "authentik_core.view_application", ["authentik_events.view_event"]
    )
    @swagger_auto_schema(responses={200: CoordinateSerializer(many=True)})
    @action(detail=True)
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
