"""core Configs API"""
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ReadOnlyField, Serializer
from rest_framework.viewsets import ViewSet

from passbook.lib.config import CONFIG


class ConfigSerializer(Serializer):
    """Serialize passbook Config into DRF Object"""

    branding_logo = ReadOnlyField()
    branding_title = ReadOnlyField()

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class ConfigsViewSet(ViewSet):
    """Read-only view set that returns the current session's Configs"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={200: ConfigSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Retrive public configuration options"""
        config = ConfigSerializer(
            {
                "branding_logo": CONFIG.y("passbook.branding.logo"),
                "branding_title": CONFIG.y("passbook.branding.title"),
            }
        )
        return Response(config.data)
