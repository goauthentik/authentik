"""Serializer for settings"""

from typing import get_args

from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type, build_object_type
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS

from authentik.admin.flags import Flag
from authentik.admin.models import SystemSettings
from authentik.core.api.utils import JSONDictField, ModelSerializer
from authentik.rbac.permissions import HasPermission


class FlagJSONField(JSONDictField):
    def to_internal_value(self, data: str):
        flags = super().to_internal_value(data)
        for flag in Flag.available(visibility="system", exclude_system=False):
            flags[flag().key] = flag.get()
        return flags

    def to_representation(self, value: dict) -> dict:
        new_value = value.copy()
        for flag in Flag.available(exclude_system=False):
            _flag = flag()
            # Exclude any system flags that aren't modifiable
            if _flag.visibility == "system":
                new_value.pop(_flag.key, None)
            # Explicitly present unset flags as if they were set to default
            if _flag.key not in value:
                value[_flag.key] = _flag.default
        return super().to_representation(new_value)

    def run_validators(self, value: dict):
        super().run_validators(value)
        for flag in Flag.available():
            _flag = flag()
            if _flag.key not in value:
                continue
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
            if _flag.description:
                props[_flag.key]["description"] = _flag.description
            if _flag.deprecated:
                props[_flag.key]["deprecated"] = _flag.deprecated
        return build_object_type(props, required=props.keys())


class SettingsSerializer(ModelSerializer):
    """Settings Serializer"""

    footer_links = JSONField(required=False)
    flags = FlagJSONField()

    class Meta:
        model = SystemSettings
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

    queryset = SystemSettings.objects.filter(pk=True)
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
