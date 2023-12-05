"""Serializer for tenants models"""
from hmac import compare_digest

from django.http import HttpResponseNotFound
from django_tenants.utils import get_tenant
from rest_framework import permissions
from rest_framework.authentication import get_authorization_header
from rest_framework.fields import ReadOnlyField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from rest_framework.views import View
from rest_framework.viewsets import ModelViewSet

from authentik.api.authentication import validate_auth
from authentik.lib.config import CONFIG
from authentik.tenants.models import Domain, Tenant


class TenantApiKeyPermission(permissions.BasePermission):
    """Authentication based on tenants.api_key"""

    def has_permission(self, request: Request, view: View) -> bool:
        key = CONFIG.get("tenants.api_key", "")
        if not key:
            return False
        token = validate_auth(get_authorization_header(request))
        if token is None:
            return False
        return compare_digest(token, key)


class TenantSerializer(ModelSerializer):
    """Tenant Serializer"""

    class Meta:
        model = Tenant
        fields = [
            "tenant_uuid",
            "schema_name",
            "name",
        ]


class TenantViewSet(ModelViewSet):
    """Tenant Viewset"""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    search_fields = [
        "name",
        "schema_name",
        "domains__domain",
    ]
    ordering = ["schema_name"]
    authentication_classes = []
    permission_classes = [TenantApiKeyPermission]
    filter_backends = [OrderingFilter, SearchFilter]

    def dispatch(self, request, *args, **kwargs):
        if not CONFIG.get_bool("tenants.enabled", True):
            return HttpResponseNotFound()
        return super().dispatch(request, *args, **kwargs)


class DomainSerializer(ModelSerializer):
    """Domain Serializer"""

    class Meta:
        model = Domain
        fields = "__all__"


class DomainViewSet(ModelViewSet):
    """Domain ViewSet"""

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    search_fields = [
        "domain",
        "tenant__name",
        "tenant__schema_name",
    ]
    ordering = ["domain"]
    authentication_classes = []
    permission_classes = [TenantApiKeyPermission]
    filter_backends = [OrderingFilter, SearchFilter]

    def dispatch(self, request, *args, **kwargs):
        if not CONFIG.get_bool("tenants.enabled", True):
            return HttpResponseNotFound()
        return super().dispatch(request, *args, **kwargs)


class SettingsSerializer(ModelSerializer):
    """Settings Serializer"""

    name = ReadOnlyField()
    domains = DomainSerializer(read_only=True, many=True)

    class Meta:
        model = Tenant
        fields = [
            "tenant_uuid",
            "name",
            "domains",
            "avatars",
            "default_user_change_name",
            "default_user_change_email",
            "default_user_change_username",
            "gdpr_compliance",
            "impersonation",
            "footer_links",
        ]


class SettingsView(RetrieveUpdateAPIView):
    """Settings view"""

    queryset = Tenant.objects.all()
    serializer_class = SettingsSerializer
    permission_classes = [IsAdminUser]
    filter_backends = []

    def get_object(self):
        obj = get_tenant(self.request)
        self.check_object_permissions(self.request, obj)
        return obj
