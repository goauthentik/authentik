"""core Configs API"""
from pathlib import Path

from django.conf import settings
from django.db import models
from django.dispatch import Signal
from drf_spectacular.utils import extend_schema
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    FloatField,
    IntegerField,
    ListField,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.events.geo import GEOIP_READER
from authentik.lib.config import CONFIG

capabilities = Signal()


class Capabilities(models.TextChoices):
    """Define capabilities which influence which APIs can/should be used"""

    CAN_SAVE_MEDIA = "can_save_media"
    CAN_GEO_IP = "can_geo_ip"
    CAN_IMPERSONATE = "can_impersonate"
    CAN_DEBUG = "can_debug"
    IS_ENTERPRISE = "is_enterprise"


class ErrorReportingConfigSerializer(PassiveSerializer):
    """Config for error reporting"""

    enabled = BooleanField(read_only=True)
    sentry_dsn = CharField(read_only=True)
    environment = CharField(read_only=True)
    send_pii = BooleanField(read_only=True)
    traces_sample_rate = FloatField(read_only=True)


class ConfigSerializer(PassiveSerializer):
    """Serialize authentik Config into DRF Object"""

    error_reporting = ErrorReportingConfigSerializer(required=True)
    capabilities = ListField(child=ChoiceField(choices=Capabilities.choices))

    cache_timeout = IntegerField(required=True)
    cache_timeout_flows = IntegerField(required=True)
    cache_timeout_policies = IntegerField(required=True)
    cache_timeout_reputation = IntegerField(required=True)


class ConfigView(APIView):
    """Read-only view set that returns the current session's Configs"""

    permission_classes = [AllowAny]

    def get_capabilities(self) -> list[Capabilities]:
        """Get all capabilities this server instance supports"""
        caps = []
        deb_test = settings.DEBUG or settings.TEST
        if Path(settings.MEDIA_ROOT).is_mount() or deb_test:
            caps.append(Capabilities.CAN_SAVE_MEDIA)
        if GEOIP_READER.enabled:
            caps.append(Capabilities.CAN_GEO_IP)
        if CONFIG.get_bool("impersonation"):
            caps.append(Capabilities.CAN_IMPERSONATE)
        if settings.DEBUG:  # pragma: no cover
            caps.append(Capabilities.CAN_DEBUG)
        if "authentik.enterprise" in settings.INSTALLED_APPS:
            caps.append(Capabilities.IS_ENTERPRISE)
        for _, result in capabilities.send(sender=self):
            if result:
                caps.append(result)
        return caps

    def get_config(self) -> ConfigSerializer:
        """Get Config"""
        return ConfigSerializer(
            {
                "error_reporting": {
                    "enabled": CONFIG.get("error_reporting.enabled"),
                    "sentry_dsn": CONFIG.get("error_reporting.sentry_dsn"),
                    "environment": CONFIG.get("error_reporting.environment"),
                    "send_pii": CONFIG.get("error_reporting.send_pii"),
                    "traces_sample_rate": float(CONFIG.get("error_reporting.sample_rate", 0.4)),
                },
                "capabilities": self.get_capabilities(),
                "cache_timeout": CONFIG.get_int("redis.cache_timeout"),
                "cache_timeout_flows": CONFIG.get_int("redis.cache_timeout_flows"),
                "cache_timeout_policies": CONFIG.get_int("redis.cache_timeout_policies"),
                "cache_timeout_reputation": CONFIG.get_int("redis.cache_timeout_reputation"),
            }
        )

    @extend_schema(responses={200: ConfigSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Retrieve public configuration options"""
        return Response(self.get_config().data)
