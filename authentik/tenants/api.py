"""Serializer for tenants models"""
from hmac import compare_digest

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
from authentik.tenants.models import Tenant


class TenantManagementKeyPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        token = validate_auth(get_authorization_header(request))
        tenant_management_key = CONFIG.get("tenant_management_key")
        if compare_digest("", tenant_management_key):
            return False
        return compare_digest(token, tenant_management_key)


class TenantSerializer(ModelSerializer):
    """Tenant Serializer"""

    class Meta:
        model = Tenant
        fields = [
            "tenant_uuid",
            "domain_regex",
        ]


class TenantViewSet(ModelViewSet):
    """Tenant Viewset"""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    search_fields = [
        "domain_regex",
    ]
    ordering = ["domain_regex"]
    permission_classes = [TenantManagementKeyPermission]
    filter_backends = [OrderingFilter, SearchFilter]


class SettingsSerializer(ModelSerializer):
    """Settings Serializer"""

    domain_regex = ReadOnlyField()

    class Meta:
        model = Tenant
        fields = "__all__"


class SettingsView(RetrieveUpdateAPIView):
    """Settings view"""

    queryset = Tenant.objects.all()
    serializer_class = SettingsSerializer
    permission_classes = [IsAdminUser]
    filter_backends = []

    def get_object(self):
        obj = self.request.tenant
        self.check_object_permissions(obj)
        return obj
