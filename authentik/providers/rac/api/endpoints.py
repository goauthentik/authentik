"""RAC Provider API Views"""

from django.core.cache import cache
from django.db.models import QuerySet
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import Provider
from authentik.policies.engine import PolicyEngine
from authentik.providers.rac.api.providers import RACProviderSerializer
from authentik.providers.rac.models import Endpoint
from authentik.rbac.filters import ObjectFilter

LOGGER = get_logger()


def user_endpoint_cache_key(user_pk: str, provider_pk: str) -> str:
    """Cache key where endpoint list for user is saved"""
    return f"goauthentik.io/providers/rac/endpoint_access/{user_pk}/{provider_pk}"


class EndpointSerializer(ModelSerializer):
    """Endpoint Serializer"""

    provider_obj = RACProviderSerializer(source="provider", read_only=True)
    launch_url = SerializerMethodField()

    def get_launch_url(self, endpoint: Endpoint) -> str | None:
        """Build actual launch URL (the provider itself does not have one, just
        individual endpoints)"""
        try:

            return reverse(
                "authentik_providers_rac:start",
                kwargs={"app": endpoint.provider.application.slug, "endpoint": endpoint.pk},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    class Meta:
        model = Endpoint
        fields = [
            "pk",
            "name",
            "provider",
            "provider_obj",
            "protocol",
            "host",
            "settings",
            "property_mappings",
            "auth_mode",
            "launch_url",
            "maximum_connections",
        ]


class EndpointViewSet(UsedByMixin, ModelViewSet):
    """Endpoint Viewset"""

    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer
    filterset_fields = ["name", "provider"]
    search_fields = ["name", "protocol"]
    ordering = ["name", "protocol"]

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def _get_allowed_endpoints(self, queryset: QuerySet) -> list[Endpoint]:
        endpoints = []
        for endpoint in queryset:
            engine = PolicyEngine(endpoint, self.request.user, self.request)
            engine.build()
            if engine.passing:
                endpoints.append(endpoint)
        return endpoints

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="superuser_full_list",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: EndpointSerializer(many=True),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List accessible endpoints"""
        should_cache = request.GET.get("search", "") == "" and "provider" in request.query_params

        superuser_full_list = str(request.GET.get("superuser_full_list", "false")).lower() == "true"
        if superuser_full_list and request.user.is_superuser:
            return super().list(request)

        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)

        allowed_endpoints = []
        if not should_cache:
            allowed_endpoints = self._get_allowed_endpoints(queryset)
        if should_cache:
            provider = request.query_params.get("provider")
            allowed_endpoints = cache.get(user_endpoint_cache_key(self.request.user.pk, provider))
            if not allowed_endpoints:
                LOGGER.debug("Caching allowed endpoint list")
                allowed_endpoints = self._get_allowed_endpoints(queryset)
                cache.set(
                    user_endpoint_cache_key(self.request.user.pk, provider),
                    allowed_endpoints,
                    timeout=86400,
                )
        serializer = self.get_serializer(allowed_endpoints, many=True)
        return self.get_paginated_response(serializer.data)
