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
from authentik.core.apps import AppAccessWithoutBindings
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

    def to_representation(self, instance: Endpoint) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        # `settings` may hold static-auth connection credentials; only callers who can
        # view the endpoint should receive it, not end-users listing it to launch.
        if request and not request.user.has_perm("authentik_providers_rac.view_endpoint", instance):
            data["settings"] = {}
        return data

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

    def _has_model_level_rbac_perm(self, user, endpoint: Endpoint) -> bool:
        """Check if user has a model-level (non-guardian) RAC permission.

        When a user has explicit model-level permissions, they should
        be able to list endpoints for management even without application-level
        access. Sensitive fields (e.g. settings) are already redacted by
        EndpointSerializer.to_representation().
        """
        if user.has_perm("authentik_providers_rac.view_endpoint"):
            return True
        if user.has_perm("authentik_providers_rac.change_endpoint"):
            return True
        if user.has_perm("authentik_providers_rac.delete_endpoint"):
            return True
        if user.has_perm("authentik_providers_rac.add_endpoint"):
            return True
        return False

    def _get_allowed_endpoints(self, queryset: QuerySet) -> list[Endpoint]:
        endpoints = []
        for endpoint in queryset:
            # If the user has a model-level RBAC permission for RAC endpoints,
            # include it in the list regardless of application access.
            # The serializer's to_representation() will redact sensitive
            # fields (e.g. connection credentials in "settings") for users
            # without the per-instance view_endpoint permission.
            # This keeps behavior consistent with the detail endpoint, which
            # returns the full object (with redacted settings) regardless of
            # application access.
            if self._has_model_level_rbac_perm(self.request.user, endpoint):
                endpoints.append(endpoint)
                continue

            # For users without model-level permissions (e.g. end-users), only
            # show endpoints reachable through their application access. This
            # mirrors the launch flow (PolicyAccessView.user_has_access).
            # Endpoints have no policy bindings by default, so the per-endpoint
            # check alone would let any caller see every endpoint.
            try:
                application = endpoint.provider.application
            except Provider.application.RelatedObjectDoesNotExist:
                continue
            application_access: dict[str, bool] = {}
            if application.pk not in application_access:
                app_engine = PolicyEngine(application, self.request.user, self.request)
                app_engine.empty_result = AppAccessWithoutBindings.get()
                app_engine.build()
                application_access[application.pk] = app_engine.passing
            if not application_access.get(application.pk, False):
                continue
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
