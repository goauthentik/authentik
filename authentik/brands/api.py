"""Serializer for brands models"""

from typing import Any

from django.db import models
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, ListField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.brands.models import Brand
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.rbac.filters import SecretKeyFilter
from authentik.tenants.utils import get_current_tenant


class FooterLinkSerializer(PassiveSerializer):
    """Links returned in Config API"""

    href = CharField(read_only=True, allow_null=True)
    name = CharField(read_only=True)


class BrandSerializer(ModelSerializer):
    """Brand Serializer"""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("default", False):
            brands = Brand.objects.filter(default=True)
            if self.instance:
                brands = brands.exclude(pk=self.instance.pk)
            if brands.exists():
                raise ValidationError({"default": "Only a single brand can be set as default."})
        return super().validate(attrs)

    class Meta:
        model = Brand
        fields = [
            "brand_uuid",
            "domain",
            "default",
            "branding_title",
            "branding_logo",
            "branding_favicon",
            "branding_custom_css",
            "flow_authentication",
            "flow_invalidation",
            "flow_recovery",
            "flow_unenrollment",
            "flow_user_settings",
            "flow_device_code",
            "default_application",
            "web_certificate",
            "attributes",
        ]
        extra_kwargs = {
            # TODO: This field isn't unique on the database which is hard to backport
            # hence we just validate the uniqueness here
            "domain": {"validators": [UniqueValidator(Brand.objects.all())]},
        }


class Themes(models.TextChoices):
    """Themes"""

    AUTOMATIC = "automatic"
    LIGHT = "light"
    DARK = "dark"


def get_default_ui_footer_links():
    """Get default UI footer links based on current tenant settings"""
    return get_current_tenant().footer_links


class CurrentBrandSerializer(PassiveSerializer):
    """Partial brand information for styling"""

    matched_domain = CharField(source="domain")
    branding_title = CharField()
    branding_logo = CharField(source="branding_logo_url")
    branding_favicon = CharField(source="branding_favicon_url")
    branding_custom_css = CharField()
    ui_footer_links = ListField(
        child=FooterLinkSerializer(),
        read_only=True,
        default=get_default_ui_footer_links,
    )
    ui_theme = ChoiceField(
        choices=Themes.choices,
        source="attributes.settings.theme.base",
        default=Themes.AUTOMATIC,
        read_only=True,
    )

    flow_authentication = CharField(source="flow_authentication.slug", required=False)
    flow_invalidation = CharField(source="flow_invalidation.slug", required=False)
    flow_recovery = CharField(source="flow_recovery.slug", required=False)
    flow_unenrollment = CharField(source="flow_unenrollment.slug", required=False)
    flow_user_settings = CharField(source="flow_user_settings.slug", required=False)
    flow_device_code = CharField(source="flow_device_code.slug", required=False)

    default_locale = CharField(read_only=True)


class BrandViewSet(UsedByMixin, ModelViewSet):
    """Brand Viewset"""

    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    search_fields = [
        "domain",
        "branding_title",
        "web_certificate__name",
    ]
    filterset_fields = [
        "brand_uuid",
        "domain",
        "default",
        "branding_title",
        "branding_logo",
        "branding_favicon",
        "flow_authentication",
        "flow_invalidation",
        "flow_recovery",
        "flow_unenrollment",
        "flow_user_settings",
        "flow_device_code",
        "web_certificate",
    ]
    ordering = ["domain"]

    filter_backends = [SecretKeyFilter, OrderingFilter, SearchFilter]

    @extend_schema(
        responses=CurrentBrandSerializer(many=False),
    )
    @action(methods=["GET"], detail=False, permission_classes=[AllowAny])
    def current(self, request: Request) -> Response:
        """Get current brand"""
        brand: Brand = request._request.brand
        return Response(CurrentBrandSerializer(brand).data)
