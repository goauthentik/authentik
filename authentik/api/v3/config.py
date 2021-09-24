"""core Configs API"""
from os import environ, path

from django.conf import settings
from django.db import models
from drf_spectacular.utils import extend_schema
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME
from rest_framework.fields import BooleanField, CharField, ChoiceField, IntegerField, ListField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.events.geo import GEOIP_READER
from authentik.lib.config import CONFIG


class Capabilities(models.TextChoices):
    """Define capabilities which influence which APIs can/should be used"""

    CAN_SAVE_MEDIA = "can_save_media"
    CAN_GEO_IP = "can_geo_ip"
    CAN_BACKUP = "can_backup"


class ConfigSerializer(PassiveSerializer):
    """Serialize authentik Config into DRF Object"""

    error_reporting_enabled = BooleanField(read_only=True)
    error_reporting_environment = CharField(read_only=True)
    error_reporting_send_pii = BooleanField(read_only=True)

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
        if path.ismount(settings.MEDIA_ROOT) or deb_test:
            caps.append(Capabilities.CAN_SAVE_MEDIA)
        if GEOIP_READER.enabled:
            caps.append(Capabilities.CAN_GEO_IP)
        if SERVICE_HOST_ENV_NAME in environ:
            # Running in k8s, only s3 backup is supported
            if CONFIG.y("postgresql.s3_backup"):
                caps.append(Capabilities.CAN_BACKUP)
        else:
            # Running in compose, backup is always supported
            caps.append(Capabilities.CAN_BACKUP)
        return caps

    @extend_schema(responses={200: ConfigSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Retrieve public configuration options"""
        config = ConfigSerializer(
            {
                "error_reporting_enabled": CONFIG.y("error_reporting.enabled"),
                "error_reporting_environment": CONFIG.y("error_reporting.environment"),
                "error_reporting_send_pii": CONFIG.y("error_reporting.send_pii"),
                "capabilities": self.get_capabilities(),
                "cache_timeout": int(CONFIG.y("redis.cache_timeout")),
                "cache_timeout_flows": int(CONFIG.y("redis.cache_timeout_flows")),
                "cache_timeout_policies": int(CONFIG.y("redis.cache_timeout_policies")),
                "cache_timeout_reputation": int(CONFIG.y("redis.cache_timeout_reputation")),
            }
        )
        return Response(config.data)
