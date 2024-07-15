"""RadiusProvider API Views"""

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ListField
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Application
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import PolicyResult
from authentik.providers.radius.models import RadiusProvider


class RadiusProviderSerializer(ProviderSerializer):
    """RadiusProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = RadiusProvider
        fields = ProviderSerializer.Meta.fields + [
            "client_networks",
            # Shared secret is not a write-only field, as
            # an admin might have to view it
            "shared_secret",
            "outpost_set",
            "mfa_support",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class RadiusProviderViewSet(UsedByMixin, ModelViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.all()
    serializer_class = RadiusProviderSerializer
    ordering = ["name"]
    search_fields = ["name", "client_networks"]
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
        "client_networks": ["iexact"],
    }


class RadiusOutpostConfigSerializer(ModelSerializer):
    """RadiusProvider Serializer"""

    application_slug = CharField(source="application.slug")
    auth_flow_slug = CharField(source="authorization_flow.slug")

    class Meta:
        model = RadiusProvider
        fields = [
            "pk",
            "name",
            "application_slug",
            "auth_flow_slug",
            "client_networks",
            "shared_secret",
            "mfa_support",
        ]


class RadiusOutpostConfigViewSet(ListModelMixin, GenericViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.filter(application__isnull=False)
    serializer_class = RadiusOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]

    class RadiusCheckAccessSerializer(PassiveSerializer):
        attributes = CharField()
        access = PolicyTestResultSerializer()

    @extend_schema(
        request=None,
        parameters=[OpenApiParameter("app_slug", OpenApiTypes.STR)],
        responses={
            200: RadiusCheckAccessSerializer(),
        },
    )
    @action(detail=True, methods=["POST"])
    def check_access(self, request: Request, *args, **kwargs) -> Response:
        """Check access to a single application by slug"""
        provider: RadiusProvider = self.get_object()
        application = get_object_or_404(Application, slug=request.query_params["app_slug"])
        engine = PolicyEngine(application, request.user, request)
        engine.use_cache = False
        engine.build()
        result = engine.result
        access_response = PolicyTestResultSerializer(PolicyResult(result.passing))
        response = self.RadiusCheckAccessSerializer(
            instance={
                "attributes": provider.get_attributes(request),
                "access": access_response,
            }
        )
        return Response(response.data)
