"""Serializer for brands models"""
import re
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
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import SecretKeyFilter
from authentik.brands.models import Brand
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.lib.config import CONFIG
from authentik.tenants.filters import TenantFilter
from authentik.tenants.serializers import TenantSerializer


class FooterLinkSerializer(PassiveSerializer):
    """Links returned in Config API"""

    href = CharField(read_only=True)
    name = CharField(read_only=True)


class BrandSerializer(TenantSerializer, ModelSerializer):
    """Brand Serializer"""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        tenant = self.context["request"].tenant
        domain = attrs.get("domain", None)
        if domain and not re.match(re.compile(tenant.domain_regex), domain):
            raise ValidationError(
                {
                    "domain",
                    f"Unauthorized domain. Domain must match the following regex <{tenant.domain_regex}>",
                }
            )
        if attrs.get("default", False):
            brands = Brand.objects.filter(tenant=tenant, default=True)
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
            "flow_authentication",
            "flow_invalidation",
            "flow_recovery",
            "flow_unenrollment",
            "flow_user_settings",
            "flow_device_code",
            "event_retention",
            "web_certificate",
            "attributes",
        ]


class Themes(models.TextChoices):
    """Themes"""

    AUTOMATIC = "automatic"
    LIGHT = "light"
    DARK = "dark"


class CurrentBrandUIFooterLinksDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["request"].tenant.footer_links

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class CurrentBrandSerializer(PassiveSerializer):
    """Partial brand information for styling"""

    matched_domain = CharField(source="domain")
    branding_title = CharField()
    branding_logo = CharField()
    branding_favicon = CharField()
    ui_footer_links = ListField(
        child=FooterLinkSerializer(),
        read_only=True,
        default=CurrentBrandUIFooterLinksDefault(),
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
        "event_retention",
        "web_certificate",
    ]
    ordering = ["domain"]

    filter_backends = [TenantFilter, SecretKeyFilter, OrderingFilter, SearchFilter]

    @extend_schema(
        responses=CurrentBrandSerializer(many=False),
    )
    @action(methods=["GET"], detail=False, permission_classes=[AllowAny])
    def current(self, request: Request) -> Response:
        """Get current brand"""
        brand: Brand = request._request.brand
        return Response(CurrentBrandSerializer(brand).data)
