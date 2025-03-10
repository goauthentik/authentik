"""Serializer for tenants models"""

from django_tenants.utils import get_public_schema_name
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS

from authentik.core.api.utils import ModelSerializer
from authentik.rbac.permissions import HasPermission
from authentik.tenants.models import Tenant


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
            "impersonation_require_reason",
            "default_token_duration",
            "default_token_length",
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

    def perform_update(self, serializer):
        # We need to be in the public schema to actually modify a tenant
        with Tenant.objects.get(schema_name=get_public_schema_name()):
            super().perform_update(serializer)
