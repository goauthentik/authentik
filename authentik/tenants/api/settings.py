"""Serializer for tenants models"""

from typing import get_args

from django.utils.translation import gettext_lazy as _
from django_tenants.utils import get_public_schema_name
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type, build_object_type
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS

from authentik.core.api.utils import JSONDictField, ModelSerializer
from authentik.rbac.permissions import HasPermission
from authentik.tenants.flags import Flag
from authentik.tenants.models import Tenant


class FlagJSONField(JSONDictField):

    def run_validators(self, value: dict):
        super().run_validators(value)
        for flag in Flag.available():
            _flag = flag()
            if _flag.key in value:
                flag_value = value.get(_flag.key)
                flag_type = get_args(_flag.__orig_bases__[0])[0]
                if flag_value and not isinstance(flag_value, flag_type):
                    raise ValidationError(
                        _("Value for flag {flag_key} needs to be of type {type}.").format(
                            flag_key=_flag.key, type=flag_type.__name__
                        )
                    )


class FlagsJSONExtension(OpenApiSerializerFieldExtension):
    """Generate API Schema for JSON fields as"""

    target_class = "authentik.tenants.api.settings.FlagJSONField"

    def map_serializer_field(self, auto_schema, direction):
        props = {}
        for flag in Flag.available():
            _flag = flag()
            props[_flag.key] = build_basic_type(get_args(_flag.__orig_bases__[0])[0])
        return build_object_type(props, required=props.keys())


class SettingsSerializer(ModelSerializer):
    """Settings Serializer"""

    footer_links = JSONField(required=False)
    flags = FlagJSONField()

    class Meta:
        model = Tenant
        fields = [
            "avatars",
            "default_user_change_name",
            "default_user_change_email",
            "default_user_change_username",
            "event_retention",
            "reputation_lower_limit",
            "reputation_upper_limit",
            "footer_links",
            "gdpr_compliance",
            "impersonation",
            "impersonation_require_reason",
            "default_token_duration",
            "default_token_length",
            "pagination_default_page_size",
            "pagination_max_page_size",
            "flags",
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
