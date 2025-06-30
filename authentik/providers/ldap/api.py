"""LDAPProvider API Views"""

from django.db.models import QuerySet
from django.db.models.query import Q
from django.shortcuts import get_object_or_404
from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ListField, SerializerMethodField
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
from authentik.providers.ldap.models import LDAPProvider


class LDAPProviderSerializer(ProviderSerializer):
    """LDAPProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = LDAPProvider
        fields = ProviderSerializer.Meta.fields + [
            "base_dn",
            "certificate",
            "tls_server_name",
            "uid_start_number",
            "gid_start_number",
            "outpost_set",
            "search_mode",
            "bind_mode",
            "mfa_support",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class LDAPProviderFilter(FilterSet):
    """LDAP Provider filters"""

    application__isnull = BooleanFilter(method="filter_application__isnull")

    def filter_application__isnull(self, queryset: QuerySet, name, value):
        """Only return providers that are neither assigned to application,
        both as provider or application provider"""
        return queryset.filter(
            Q(backchannel_application__isnull=value) | Q(application__isnull=value)
        )

    class Meta:
        model = LDAPProvider
        fields = {
            "application": ["isnull"],
            "name": ["iexact"],
            "authorization_flow__slug": ["iexact"],
            "base_dn": ["iexact"],
            "certificate__kp_uuid": ["iexact"],
            "certificate__name": ["iexact"],
            "tls_server_name": ["iexact"],
            "uid_start_number": ["iexact"],
            "gid_start_number": ["iexact"],
        }


class LDAPProviderViewSet(UsedByMixin, ModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.all()
    serializer_class = LDAPProviderSerializer
    filterset_class = LDAPProviderFilter
    search_fields = ["name"]
    ordering = ["name"]


class LDAPOutpostConfigSerializer(ModelSerializer):
    """LDAPProvider Serializer"""

    application_slug = SerializerMethodField()
    bind_flow_slug = CharField(source="authorization_flow.slug")
    unbind_flow_slug = SerializerMethodField()

    def get_application_slug(self, instance: LDAPProvider) -> str:
        """Prioritise backchannel slug over direct application slug"""
        if instance.backchannel_application:
            return instance.backchannel_application.slug
        return instance.application.slug

    def get_unbind_flow_slug(self, instance: LDAPProvider) -> str | None:
        """Get slug for unbind flow, defaulting to brand's default flow."""
        flow = instance.invalidation_flow
        if not flow and "request" in self.context:
            request = self.context.get("request")
            flow = request.brand.flow_invalidation
        if not flow:
            return None
        return flow.slug

    class Meta:
        model = LDAPProvider
        fields = [
            "pk",
            "name",
            "base_dn",
            "bind_flow_slug",
            "unbind_flow_slug",
            "application_slug",
            "certificate",
            "tls_server_name",
            "uid_start_number",
            "gid_start_number",
            "search_mode",
            "bind_mode",
            "mfa_support",
        ]


class LDAPOutpostConfigViewSet(ListModelMixin, GenericViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.filter(
        Q(application__isnull=False) | Q(backchannel_application__isnull=False)
    )
    serializer_class = LDAPOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]

    class LDAPCheckAccessSerializer(PassiveSerializer):
        has_search_permission = BooleanField(required=False)
        access = PolicyTestResultSerializer()

    @extend_schema(
        request=None,
        parameters=[OpenApiParameter("app_slug", OpenApiTypes.STR)],
        responses={
            200: LDAPCheckAccessSerializer(),
        },
        operation_id="outposts_ldap_access_check",
    )
    @action(detail=True)
    def check_access(self, request: Request, pk) -> Response:
        """Check access to a single application by slug"""
        provider = get_object_or_404(LDAPProvider, pk=pk)
        application = get_object_or_404(Application, slug=request.query_params["app_slug"])
        engine = PolicyEngine(application, request.user, request)
        engine.use_cache = False
        engine.build()
        result = engine.result
        access_response = PolicyResult(result.passing)
        response = self.LDAPCheckAccessSerializer(
            instance={
                "has_search_permission": (
                    request.user.has_perm("search_full_directory", provider)
                    or request.user.has_perm("authentik_providers_ldap.search_full_directory")
                ),
                "access": access_response,
            }
        )
        return Response(response.data)
