"""core Configs API"""
from os import path

from django.conf import settings
from django.db import models
from drf_spectacular.utils import extend_schema
from rest_framework.fields import BooleanField, CharField, ChoiceField, ListField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.lib.config import CONFIG


class FooterLinkSerializer(PassiveSerializer):
    """Links returned in Config API"""

    href = CharField(read_only=True)
    name = CharField(read_only=True)


class Capabilities(models.TextChoices):
    """Define capabilities which influence which APIs can/should be used"""

    CAN_SAVE_MEDIA = "can_save_media"


class ConfigSerializer(PassiveSerializer):
    """Serialize authentik Config into DRF Object"""

    branding_logo = CharField(read_only=True)
    branding_title = CharField(read_only=True)
    ui_footer_links = ListField(child=FooterLinkSerializer(), read_only=True)

    error_reporting_enabled = BooleanField(read_only=True)
    error_reporting_environment = CharField(read_only=True)
    error_reporting_send_pii = BooleanField(read_only=True)

    capabilities = ListField(child=ChoiceField(choices=Capabilities.choices))


class ConfigView(APIView):
    """Read-only view set that returns the current session's Configs"""

    permission_classes = [AllowAny]

    def get_capabilities(self) -> list[Capabilities]:
        """Get all capabilities this server instance supports"""
        caps = []
        deb_test = settings.DEBUG or settings.TEST
        if path.ismount(settings.MEDIA_ROOT) or deb_test:
            caps.append(Capabilities.CAN_SAVE_MEDIA)
        return caps

    @extend_schema(responses={200: ConfigSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Retrive public configuration options"""
        config = ConfigSerializer(
            {
                "branding_logo": CONFIG.y("authentik.branding.logo"),
                "branding_title": CONFIG.y("authentik.branding.title"),
                "error_reporting_enabled": CONFIG.y("error_reporting.enabled"),
                "error_reporting_environment": CONFIG.y("error_reporting.environment"),
                "error_reporting_send_pii": CONFIG.y("error_reporting.send_pii"),
                "ui_footer_links": CONFIG.y("authentik.footer_links"),
                "capabilities": self.get_capabilities(),
            }
        )
        return Response(config.data)
