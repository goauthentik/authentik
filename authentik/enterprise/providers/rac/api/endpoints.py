"""RAC Provider API Views"""
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.rac.models import Endpoint
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


def user_endpoint_cache_key(user_pk: str) -> str:
    """Cache key where endpoint list for user is saved"""
    return f"goauthentik.io/providers/rac/endpoint_access/{user_pk}"


class EndpointSerializer(ModelSerializer):
    """Endpoint Serializer"""

    class Meta:
        model = Endpoint
        fields = ["name", "protocol", "host", "settings", "property_mappings"]


class EndpointViewSet(UsedByMixin, ModelViewSet):
    """Endpoint Viewset"""

    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer
    search_fields = ["name", "protocol"]
    ordering = ["name", "protocol"]

    def _get_allowed_endpoints(self, queryset: QuerySet) -> list[Endpoint]:
        endpoints = []
        for endpoint in queryset:
            engine = PolicyEngine(endpoint, self.request.user, self.request)
            engine.build()
            if engine.passing:
                endpoints.append(endpoint)
        return endpoints

    def list(self, request: Request) -> Response:
        """Custom list method that checks Policy based access instead of guardian"""
        should_cache = request.GET.get("search", "") == ""

        queryset = self._filter_queryset_for_list(self.get_queryset())
        self.paginate_queryset(queryset)

        allowed_endpoints = []
        if not should_cache:
            allowed_endpoints = self._get_allowed_endpoints(queryset)
        if should_cache:
            allowed_endpoints = cache.get(user_endpoint_cache_key(self.request.user.pk))
            if not allowed_endpoints:
                LOGGER.debug("Caching allowed endpoint list")
                allowed_endpoints = self._get_allowed_endpoints(queryset)
                cache.set(
                    user_endpoint_cache_key(self.request.user.pk),
                    allowed_endpoints,
                    timeout=86400,
                )
        serializer = self.get_serializer(allowed_endpoints, many=True)
        return self.get_paginated_response(serializer.data)
