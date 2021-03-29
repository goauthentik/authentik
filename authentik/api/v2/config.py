"""core Configs API"""
from django.db.models import Model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.fields import BooleanField, CharField, ListField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from authentik.lib.config import CONFIG


class LinkSerializer(Serializer):
    """Links returned in Config API"""

    href = CharField(read_only=True)
    name = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class ConfigSerializer(Serializer):
    """Serialize authentik Config into DRF Object"""

    branding_logo = CharField(read_only=True)
    branding_title = CharField(read_only=True)
    ui_footer_links = ListField(child=LinkSerializer(), read_only=True)

    error_reporting_enabled = BooleanField(read_only=True)
    error_reporting_environment = CharField(read_only=True)
    error_reporting_send_pii = BooleanField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class ConfigsViewSet(ViewSet):
    """Read-only view set that returns the current session's Configs"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={200: ConfigSerializer(many=False)})
    def list(self, request: Request) -> Response:
        """Retrive public configuration options"""
        config = ConfigSerializer(
            {
                "branding_logo": CONFIG.y("authentik.branding.logo"),
                "branding_title": CONFIG.y("authentik.branding.title"),
                "error_reporting_enabled": CONFIG.y("error_reporting.enabled"),
                "error_reporting_environment": CONFIG.y("error_reporting.environment"),
                "error_reporting_send_pii": CONFIG.y("error_reporting.send_pii"),
                "ui_footer_links": CONFIG.y("authentik.footer_links"),
            }
        )
        return Response(config.data)
