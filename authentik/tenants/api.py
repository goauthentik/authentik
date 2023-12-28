"""Serializer for tenants models"""
from datetime import timedelta
from hmac import compare_digest

from django.http import HttpResponseNotFound
from django.http.request import urljoin
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions
from rest_framework.authentication import get_authorization_header
from rest_framework.decorators import action
from rest_framework.fields import CharField, IntegerField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import DateTimeField, ModelSerializer
from rest_framework.views import View
from rest_framework.viewsets import ModelViewSet

from authentik.api.authentication import validate_auth
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.lib.config import CONFIG
from authentik.rbac.permissions import HasPermission
from authentik.recovery.lib import create_admin_group, create_recovery_token
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
            "ready",
        ]


class TenantAdminGroupRequestSerializer(PassiveSerializer):
    """Tenant admin group creation request serializer"""

    user = CharField()


class TenantRecoveryKeyRequestSerializer(PassiveSerializer):
    """Tenant recovery key creation request serializer"""

    user = CharField()
    duration_days = IntegerField(initial=365)


class TenantRecoveryKeyResponseSerializer(PassiveSerializer):
    """Tenant recovery key creation response serializer"""

    expiry = DateTimeField()
    url = CharField()


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
    filterset_fields = []

    def dispatch(self, request, *args, **kwargs):
        if not CONFIG.get_bool("tenants.enabled", True):
            return HttpResponseNotFound()
        return super().dispatch(request, *args, **kwargs)

    @extend_schema(
        request=TenantAdminGroupRequestSerializer(),
        responses={
            204: OpenApiResponse(description="Group created successfully."),
            400: OpenApiResponse(description="Bad request"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    @action(detail=True, pagination_class=None, methods=["POST"])
    def create_admin_group(self, request: Request, pk: str) -> Response:
        """Create admin group and add user to it."""
        tenant = self.get_object()
        with tenant:
            data = TenantAdminGroupRequestSerializer(data=request.data)
            if not data.is_valid():
                return Response(data.errors, status=400)
            user = User.objects.filter(username=data.validated_data.get("user")).first()
            if not user:
                return Response(status=404)
            _ = create_admin_group(user)
            return Response(status=200)

    @extend_schema(
        request=TenantRecoveryKeyRequestSerializer(),
        responses={
            200: TenantRecoveryKeyResponseSerializer(),
            400: OpenApiResponse(description="Bad request"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    @action(detail=True, pagination_class=None, methods=["POST"])
    def create_recovery_key(self, request: Request, pk: str) -> Response:
        """Create recovery key for user."""
        tenant = self.get_object()
        with tenant:
            data = TenantRecoveryKeyRequestSerializer(data=request.data)
            if not data.is_valid():
                return Response(data.errors, status=400)
            user = User.objects.filter(username=data.validated_data.get("user")).first()
            if not user:
                return Response(status=404)

            expiry = now() + timedelta(days=data.validated_data.get("duration_days"))

            token, url = create_recovery_token(user, expiry, "tenants API")

            domain = tenant.get_primary_domain()
            host = domain.domain if domain else request.get_host()

            url = urljoin(f"{request.scheme}://{host}", url)

            serializer = TenantRecoveryKeyResponseSerializer({"expiry": token.expires, "url": url})
            return Response(serializer.data)


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
    filterset_fields = []

    def dispatch(self, request, *args, **kwargs):
        if not CONFIG.get_bool("tenants.enabled", True):
            return HttpResponseNotFound()
        return super().dispatch(request, *args, **kwargs)


class SettingsSerializer(ModelSerializer):
    """Settings Serializer"""

    class Meta:
        model = Tenant
        fields = [
            "avatars",
            "default_user_change_name",
            "default_user_change_email",
            "default_user_change_username",
            "event_retention",
            "footer_links",
            "gdpr_compliance",
            "impersonation",
        ]


class SettingsView(RetrieveUpdateAPIView):
    """Settings view"""

    queryset = Tenant.objects.filter(ready=True)
    serializer_class = SettingsSerializer
    filter_backends = []

    def get_permissions(self):
        return [
            HasPermission(
                "authentik_rbac.view_system_settings"
                if self.request.method in SAFE_METHODS
                else "authentik_rbac.edit_system_settings"
            )()
        ]

    def get_object(self):
        obj = self.request.tenant
        self.check_object_permissions(self.request, obj)
        return obj
